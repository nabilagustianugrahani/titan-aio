"""Content Versioning — track, compare, and revert content versions."""

from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel


class ContentVersion(BaseModel):
    version_id: str = ""
    content_type: str  # hook/script/caption/thumbnail
    content: str
    version_number: int = 1
    created_at: str = ""
    author: str = "system"
    notes: str = ""
    tags: list[str] = []
    performance_score: float = 0.0
    is_current: bool = True


class ContentVersionManager:
    def __init__(self):
        self.versions: dict[str, list[ContentVersion]] = {}

    def _key(self, content_type: str, content_id: str) -> str:
        return f"{content_type}:{content_id}"

    async def create_version(self, content_type: str, content_id: str, content: str, author: str = "system", notes: str = "", tags: list[str] | None = None) -> ContentVersion:
        key = self._key(content_type, content_id)
        existing = self.versions.get(key, [])
        for v in existing:
            v.is_current = False
        version_num = len(existing) + 1
        vid = hashlib.md5(f"{key}:v{version_num}".encode()).hexdigest()[:10]
        version = ContentVersion(
            version_id=vid, content_type=content_type, content=content,
            version_number=version_num, created_at=datetime.now().isoformat(),
            author=author, notes=notes, tags=tags or [], is_current=True,
        )
        existing.append(version)
        self.versions[key] = existing
        return version

    async def get_versions(self, content_type: str, content_id: str) -> list[ContentVersion]:
        key = self._key(content_type, content_id)
        return self.versions.get(key, [])

    async def get_current(self, content_type: str, content_id: str) -> ContentVersion | None:
        versions = await self.get_versions(content_type, content_id)
        for v in reversed(versions):
            if v.is_current:
                return v
        return versions[-1] if versions else None

    async def revert(self, content_type: str, content_id: str, version_id: str) -> ContentVersion | None:
        versions = await self.get_versions(content_type, content_id)
        for v in versions:
            v.is_current = v.version_id == version_id
        target = next((v for v in versions if v.version_id == version_id), None)
        if target:
            return await self.create_version(content_type, content_id, target.content, author="revert", notes=f"Reverted to v{target.version_number}")
        return None

    async def compare(self, content_type: str, content_id: str, v1_id: str, v2_id: str) -> dict:
        versions = await self.get_versions(content_type, content_id)
        v1 = next((v for v in versions if v.version_id == v1_id), None)
        v2 = next((v for v in versions if v.version_id == v2_id), None)
        if not v1 or not v2:
            return {"error": "Version not found"}
        return {
            "version_1": v1.model_dump(), "version_2": v2.model_dump(),
            "length_diff": len(v2.content) - len(v1.content),
            "content_changed": v1.content != v2.content,
        }

    async def update_score(self, content_type: str, content_id: str, version_id: str, score: float) -> bool:
        versions = self.versions.get(self._key(content_type, content_id), [])
        for v in versions:
            if v.version_id == version_id:
                v.performance_score = score
                return True
        return False

    async def get_stats(self) -> dict:
        total = sum(len(v) for v in self.versions.values())
        by_type = {k.split(":")[0]: len(v) for k, v in self.versions.items()}
        return {"total_versions": total, "by_type": by_type, "total_contents": len(self.versions)}
