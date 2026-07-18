"""ChromaDB vector store for semantic memory.

Falls back to in-memory dict store if chromadb is not available
(protobuf dep conflict on some environments).
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from titan.config import settings

logger = logging.getLogger(__name__)

# Try to import chromadb; fall back to dict-based store
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _HAS_CHROMA = True
except (ImportError, TypeError):
    _HAS_CHROMA = False
    logger.warning("chromadb unavailable — using in-memory fallback")


class _FallbackStore:
    """Minimal in-memory vector store when chromadb is broken."""

    def __init__(self):
        self._collections: dict[str, list[dict]] = {}

    def get_collection(self, name: str):
        return _FallbackCollection(self._collections, name)

    def create_collection(self, name: str):
        self._collections.setdefault(name, [])
        return _FallbackCollection(self._collections, name)

    def delete_collection(self, name: str):
        self._collections.pop(name, None)


class _FallbackCollection:
    def __init__(self, store: dict, name: str):
        self._store = store
        self._name = name
        self._store.setdefault(name, [])

    def add(self, documents=None, metadatas=None, ids=None):
        docs = documents or []
        if metadatas is None:
            metas = [{} for _ in docs]  # list of distinct dicts, not [{}]*n
        else:
            metas = metadatas
        ids = ids or [str(i) for i in range(len(docs))]
        for i, doc in enumerate(docs):
            self._store[self._name].append({
                "id": ids[i] if i < len(ids) else str(i),
                "document": doc,
                "metadata": metas[i] if i < len(metas) else {},
            })

    def count(self) -> int:
        return len(self._store.get(self._name, []))

    def list_collections(self) -> list[str]:
        return list(self._store.keys())

    def query(self, query_texts=None, n_results=5):
        items = self._store[self._name][:n_results]
        return {
            "documents": [[it["document"] for it in items]] if items else [[]],
            "metadatas": [[it["metadata"] for it in items]] if items else [[]],
            "distances": [[0.0] * len(items)] if items else [[]],
        }


class VectorStore:
    """Vector memory store using ChromaDB (or in-memory fallback)."""

    def __init__(self) -> None:
        if _HAS_CHROMA:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        else:
            self._client = _FallbackStore()

    def get_or_create_collection(self, name: str) -> Any:
        """Get or create a collection by name."""
        try:
            return self._client.get_collection(name)
        except (ValueError, chromadb.errors.NotFoundError):
            return self._client.create_collection(name)

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        if hasattr(self._client, "list_collections"):
            return name in self._client.list_collections()
        try:
            self._client.get_collection(name)
            return True
        except (ValueError, chromadb.errors.NotFoundError, KeyError):
            return False
        except AttributeError:
            return False

    def is_chroma_available(self) -> bool:
        """Return True if real ChromaDB (not fallback) is active."""
        return _HAS_CHROMA

    def add_texts(
        self,
        collection_name: str,
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add texts to a collection."""
        import uuid

        collection = self.get_or_create_collection(collection_name)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        collection.add(
            documents=texts,
            metadatas=metadatas or None,
            ids=ids,
        )
        return ids

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Search for similar texts."""
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(query_texts=[query], n_results=min(top_k, 100))
        output = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append(
                    {
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    },
                )
        return output

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        with contextlib.suppress(ValueError, chromadb.errors.NotFoundError):
            self._client.delete_collection(name)
