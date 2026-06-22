from pydantic import BaseModel
from datetime import datetime
import hashlib
import json


class CacheEntry(BaseModel):
    cache_key: str
    content_type: str
    content: dict
    created_at: str
    ttl_seconds: int = 3600
    hits: int = 0


class ContentCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl

    def _make_key(self, content_type: str, params: dict) -> str:
        raw = json.dumps({"type": content_type, **params}, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    async def get(self, content_type: str, params: dict) -> dict | None:
        key = self._make_key(content_type, params)
        entry = self.cache.get(key)
        if entry is None:
            return None
        created = datetime.fromisoformat(entry.created_at)
        elapsed = (datetime.now() - created).total_seconds()
        if elapsed > entry.ttl_seconds:
            del self.cache[key]
            return None
        entry.hits += 1
        return entry.content

    async def set(self, content_type: str, params: dict, content: dict, ttl: int = 0):
        key = self._make_key(content_type, params)
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.values(), key=lambda e: e.hits)
            del self.cache[oldest.cache_key]
        self.cache[key] = CacheEntry(
            cache_key=key,
            content_type=content_type,
            content=content,
            created_at=datetime.now().isoformat(),
            ttl_seconds=ttl or self.default_ttl,
        )

    async def invalidate(self, content_type: str = ""):
        if content_type:
            self.cache = {k: v for k, v in self.cache.items() if v.content_type != content_type}
        else:
            self.cache.clear()

    async def get_stats(self) -> dict:
        total_hits = sum(e.hits for e in self.cache.values())
        by_type: dict[str, int] = {}
        for e in self.cache.values():
            by_type[e.content_type] = by_type.get(e.content_type, 0) + 1
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "by_type": by_type,
        }
