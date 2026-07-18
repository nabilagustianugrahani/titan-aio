"""Content cache with optional SQLite persistence.

In-memory dict cache by default, falls back to SQLite for large/tiered caching.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from pydantic import BaseModel

try:
    import aiosqlite

    _HAS_SQLITE_BACKEND = True
except ImportError:
    _HAS_SQLITE_BACKEND = False


class CacheEntry(BaseModel):
    cache_key: str
    content_type: str
    content: dict
    created_at: str
    ttl_seconds: int = 3600
    hits: int = 0


class ContentCache:
    """In-memory content cache with optional SQLite backend for persistence.

    Design: Primary storage is an in-memory dict (fast).
    If CACHE_DB_PATH is set, also persists to SQLite so cache survives restarts.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        db_path: str = "",
    ):
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._db_path = db_path
        self._sqlite: aiosqlite.Connection | None = None

    async def _ensure_db(self):
        if self._db_path and _HAS_SQLITE_BACKEND and self._sqlite is None:
            self._sqlite = await aiosqlite.connect(self._db_path)
            await self._sqlite.execute(
                "CREATE TABLE IF NOT EXISTS content_cache ("
                "  cache_key TEXT PRIMARY KEY,"
                "  content_type TEXT NOT NULL,"
                "  content TEXT NOT NULL,"
                "  created_at TEXT NOT NULL,"
                "  ttl_seconds INTEGER NOT NULL DEFAULT 3600,"
                "  hits INTEGER NOT NULL DEFAULT 0"
                ")",
            )
            await self._sqlite.commit()

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
        entry = CacheEntry(
            cache_key=key,
            content_type=content_type,
            content=content,
            created_at=datetime.now().isoformat(),
            ttl_seconds=ttl or self.default_ttl,
        )
        self.cache[key] = entry

        # Persist to SQLite if available
        try:
            if self._db_path and _HAS_SQLITE_BACKEND:
                await self._ensure_db()
                if self._sqlite:
                    await self._sqlite.execute(
                        "INSERT OR REPLACE INTO content_cache VALUES (?,?,?,?,?,?)",
                        (
                            key,
                            content_type,
                            json.dumps(content),
                            entry.created_at,
                            entry.ttl_seconds,
                            0,
                        ),
                    )
                    await self._sqlite.commit()
        except Exception:
            pass

    async def invalidate(self, content_type: str = ""):
        if content_type:
            self.cache = {k: v for k, v in self.cache.items() if v.content_type != content_type}
        else:
            self.cache.clear()

        try:
            if self._sqlite:
                if content_type:
                    await self._sqlite.execute(
                        "DELETE FROM content_cache WHERE content_type = ?", (content_type,),
                    )
                else:
                    await self._sqlite.execute("DELETE FROM content_cache")
                await self._sqlite.commit()
        except Exception:
            pass

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

    async def close(self):
        """Close SQLite connection if open."""
        if self._sqlite:
            await self._sqlite.close()
            self._sqlite = None
