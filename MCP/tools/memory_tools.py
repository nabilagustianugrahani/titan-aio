"""MCP tools for memory and knowledge operations."""
from __future__ import annotations

from Services.memory.knowledge_base import KnowledgeBase
from Services.memory.vector_store import VectorStore

_store = VectorStore()
_kb = KnowledgeBase()


async def memory_store_hook(hook_text: str, hook_type: str = "curiosity", campaign_id: str = "") -> dict:
    """Store a hook in vector memory for future retrieval."""
    collection = _store.get_or_create_collection("winning_hooks")
    import uuid
    hook_id = str(uuid.uuid4())
    collection.add(
        documents=[hook_text],
        metadatas=[{"type": hook_type, "campaign_id": campaign_id}],
        ids=[hook_id],
    )
    return {"hook_id": hook_id, "stored": True}


async def memory_find_similar_hooks(query: str, top_k: int = 5) -> list[dict]:
    """Find hooks similar to the query text using vector search."""
    return _store.similarity_search("winning_hooks", query, top_k=top_k)


async def memory_store_product_knowledge(product_id: str, knowledge: str) -> dict:
    """Store product knowledge in vector memory."""
    kid = _kb.store_product_knowledge(product_id, knowledge)
    return {"knowledge_id": kid, "stored": True}


async def memory_find_similar_products(query: str, top_k: int = 5) -> list[dict]:
    """Find products similar to query."""
    return _kb.find_similar_products(query, top_k=top_k)
