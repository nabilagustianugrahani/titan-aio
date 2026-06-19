"""MongoDB client wrapper with sync (PyMongo) and async (Motor) drivers."""

from __future__ import annotations

from typing import Any, Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

from titan.config import settings


class MongoDBClient:
    """MongoDB Atlas client. Supports both sync and async operations."""

    _instance: Optional["MongoDBClient"] = None

    def __init__(self, uri: str = "", db_name: str = "") -> None:
        self._uri = uri or settings.MONGODB_URI
        self._db_name = db_name or settings.MONGODB_DB_NAME
        self._sync_client: Optional[pymongo.MongoClient] = None
        self._async_client: Optional[AsyncIOMotorClient] = None

    @classmethod
    def get_instance(cls) -> "MongoDBClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def sync(self) -> pymongo.MongoClient:
        if self._sync_client is None:
            if not self._uri:
                raise RuntimeError("MONGODB_URI not set. Add it to .env")
            self._sync_client = pymongo.MongoClient(self._uri)
        return self._sync_client

    @property
    def async_client(self) -> AsyncIOMotorClient:
        if self._async_client is None:
            if not self._uri:
                raise RuntimeError("MONGODB_URI not set. Add it to .env")
            self._async_client = AsyncIOMotorClient(self._uri)
        return self._async_client

    @property
    def db(self) -> Any:
        """Get sync database handle."""
        return self.sync[self._db_name]

    @property
    def async_db(self) -> Any:
        """Get async database handle (Motor)."""
        return self.async_client[self._db_name]

    def collection(self, name: str) -> Any:
        return self.db[name]

    def async_collection(self, name: str) -> Any:
        return self.async_db[name]

    # ── Collections ────────────────────────────────────────────

    @property
    def products(self) -> Any:
        return self.collection("products")

    @property
    def reviews(self) -> Any:
        return self.collection("reviews")

    @property
    def campaigns(self) -> Any:
        return self.collection("campaigns")

    @property
    def winning_hooks(self) -> Any:
        return self.collection("winning_hooks")

    @property
    def metrics(self) -> Any:
        return self.collection("metrics")

    @property
    def knowledge(self) -> Any:
        return self.collection("knowledge")

    # ── Sync CRUD helpers ──────────────────────────────────────

    def insert_one(self, collection: str, doc: dict) -> str:
        return str(self.collection(collection).insert_one(doc).inserted_id)

    def find_one(self, collection: str, filter: dict) -> Optional[dict]:
        return self.collection(collection).find_one(filter)

    def find_many(self, collection: str, filter: dict, limit: int = 100) -> list[dict]:
        return list(self.collection(collection).find(filter).limit(limit))

    def update_one(self, collection: str, filter: dict, update: dict) -> int:
        return self.collection(collection).update_one(filter, {"$set": update}).modified_count

    def delete_one(self, collection: str, filter: dict) -> int:
        return self.collection(collection).delete_one(filter).deleted_count

    # ── Async CRUD helpers (Motor) ─────────────────────────────

    async def insert_one_async(self, collection: str, doc: dict) -> str:
        result = await self.async_collection(collection).insert_one(doc)
        return str(result.inserted_id)

    async def find_one_async(self, collection: str, filter: dict) -> Optional[dict]:
        return await self.async_collection(collection).find_one(filter)

    async def find_many_async(self, collection: str, filter: dict, limit: int = 100) -> list[dict]:
        cursor = self.async_collection(collection).find(filter).limit(limit)
        return [doc async for doc in cursor]

    async def update_one_async(self, collection: str, filter: dict, update: dict) -> int:
        result = await self.async_collection(collection).update_one(filter, {"$set": update})
        return result.modified_count

    async def delete_one_async(self, collection: str, filter: dict) -> int:
        result = await self.async_collection(collection).delete_one(filter)
        return result.deleted_count

    def close(self) -> None:
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            self._async_client.close()
            self._async_client = None

    def ping(self) -> bool:
        """Test connection."""
        try:
            self.sync.admin.command("ping")
            return True
        except Exception:
            return False

    async def ping_async(self) -> bool:
        try:
            await self.async_client.admin.command("ping")
            return True
        except Exception:
            return False
