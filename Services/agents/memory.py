"""Memory Agent — persists and retrieves campaign knowledge with keyword similarity."""

from __future__ import annotations

import re
from typing import Any

from Database.models import KnowledgeEntry, WinningHook
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class MemoryAgent(BaseAgent):
    """Stores and retrieves winning/failed campaign data.

    Actions:
      store         — save a winning hook or knowledge pattern
      find_similar  — keyword-based similarity search across hooks + knowledge
      learn         — extract and store a pattern from campaign results
    """

    async def execute(self, ctx: AgentContext, action: str = "store", **kwargs: Any) -> dict:
        if action == "store":
            return await self._store(ctx, **kwargs)
        if action == "find_similar":
            return await self._find_similar(ctx, **kwargs)
        if action == "learn":
            return await self._learn(ctx, **kwargs)
        return {"error": f"Unknown action: {action}"}

    # ── store ───────────────────────────────────────────────────────
    async def _store(self, ctx: AgentContext, hook: str = "", **kwargs: Any) -> dict:
        if not hook:
            return {"stored": False, "note": "No hook provided"}

        repo = Repository(ctx.session, WinningHook)
        record = await repo.create(
            campaign_id=kwargs.get("campaign_id", ""),
            hook_text=hook,
            hook_type=kwargs.get("hook_type", "curiosity"),
            ctr=kwargs.get("ctr"),
            embedding=kwargs.get("embedding"),
        )
        await ctx.session.commit()
        return {"stored": True, "hook_id": record.id, "hook_text": hook}

    # ── find_similar ────────────────────────────────────────────────
    async def _find_similar(self, ctx: AgentContext, query: str = "", top_k: int = 5, **kwargs: Any) -> dict:
        if not query:
            return {"results": [], "note": "No query provided"}

        query_tokens = self._tokenize(query)

        # Search winning hooks
        hook_repo = Repository(ctx.session, WinningHook)
        all_hooks = await hook_repo.list_all(limit=500)
        scored_hooks = []
        for h in all_hooks:
            sim = self._keyword_similarity(query_tokens, self._tokenize(h.hook_text))
            if sim > 0:
                scored_hooks.append({
                    "type": "hook",
                    "id": h.id,
                    "text": h.hook_text,
                    "hook_type": h.hook_type,
                    "ctr": h.ctr,
                    "similarity": round(sim, 3),
                })

        # Search knowledge entries
        kb_repo = Repository(ctx.session, KnowledgeEntry)
        all_kb = await kb_repo.list_all(limit=200)
        scored_kb = []
        for k in all_kb:
            combined = f"{k.category} {k.pattern} {k.actionable_advice or ''}"
            sim = self._keyword_similarity(query_tokens, self._tokenize(combined))
            if sim > 0:
                scored_kb.append({
                    "type": "knowledge",
                    "id": k.id,
                    "category": k.category,
                    "pattern": k.pattern,
                    "confidence": k.confidence,
                    "advice": k.actionable_advice,
                    "similarity": round(sim, 3),
                })

        # Merge + sort by similarity
        all_results = scored_hooks + scored_kb
        all_results.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "query": query,
            "results": all_results[:top_k],
            "total_matches": len(all_results),
        }

    # ── learn ───────────────────────────────────────────────────────
    async def _learn(
        self,
        ctx: AgentContext,
        category: str = "hooks",
        pattern: str = "",
        evidence: list[str] | None = None,
        advice: str = "",
        confidence: float = 0.5,
        **_: Any,
    ) -> dict:
        if not pattern:
            return {"learned": False, "note": "No pattern provided"}

        repo = Repository(ctx.session, KnowledgeEntry)
        entry = await repo.create(
            category=category,
            pattern=pattern,
            evidence=evidence or [],
            actionable_advice=advice,
            confidence=min(max(confidence, 0.0), 1.0),
        )
        await ctx.session.commit()
        return {"learned": True, "entry_id": entry.id, "category": category, "confidence": confidence}

    # ── helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase, split on non-alphanumeric, drop short tokens."""
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if len(t) > 2]

    @staticmethod
    def _keyword_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
        """Simple Jaccard-like similarity weighted by token overlap."""
        if not query_tokens or not doc_tokens:
            return 0.0
        query_set = set(query_tokens)
        doc_set = set(doc_tokens)
        intersection = query_set & doc_set
        if not intersection:
            return 0.0
        # Weight: intersection / smaller set (recall-oriented)
        return len(intersection) / min(len(query_set), len(doc_set))
