"""Knowledge base for storing and retrieving campaign intelligence."""

from __future__ import annotations


from Services.memory.vector_store import VectorStore


class KnowledgeBase:
    """Reusable intelligence layer over vector store + structured DB."""

    def __init__(self) -> None:
        self._vector = VectorStore()
        self._hook_collection = "winning_hooks"
        self._product_collection = "winning_products"

    def store_winning_hook(self, hook_text: str, metadata: dict | None = None) -> str:
        """Store a winning hook for future retrieval."""
        ids = self._vector.add_texts(
            self._hook_collection,
            [hook_text],
            metadatas=[metadata or {}],
        )
        return ids[0]

    def find_similar_hooks(self, query: str, top_k: int = 5) -> list[dict]:
        """Find hooks similar to query."""
        return self._vector.similarity_search(self._hook_collection, query, top_k)

    def store_product_knowledge(self, product_id: str, knowledge: str, metadata: dict | None = None) -> str:
        """Store product knowledge."""
        ids = self._vector.add_texts(
            self._product_collection,
            [knowledge],
            metadatas=[{"product_id": product_id, **(metadata or {})}],
        )
        return ids[0]

    def find_similar_products(self, query: str, top_k: int = 5) -> list[dict]:
        """Find products similar to query."""
        return self._vector.similarity_search(self._product_collection, query, top_k)
