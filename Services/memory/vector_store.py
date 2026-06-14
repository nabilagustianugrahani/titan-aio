"""ChromaDB vector store for semantic memory."""

from __future__ import annotations

from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from titan.config import settings


class VectorStore:
    """Vector memory store using ChromaDB."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, name: str) -> Any:
        """Get or create a collection by name."""
        try:
            return self._client.get_collection(name)
        except (ValueError, chromadb.errors.NotFoundError):
            return self._client.create_collection(name)

    def add_texts(
        self,
        collection_name: str,
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
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
                    }
                )
        return output

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self._client.delete_collection(name)
        except (ValueError, chromadb.errors.NotFoundError):
            pass
