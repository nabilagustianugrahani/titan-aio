"""Memory Agent -- persists and retrieves campaign knowledge."""

from __future__ import annotations

from typing import Any

from Database.models import WinningHook
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class MemoryAgent(BaseAgent):
    """Stores and retrieves winning/failed campaign data."""

    async def execute(
        self, ctx: AgentContext, action: str = "store", **kwargs: Any
    ) -> dict:
        if action == "store" and "hook" in kwargs:
            repo = Repository(ctx.session, WinningHook)
            hook = await repo.create(
                campaign_id=kwargs.get("campaign_id", ""),
                hook_text=kwargs["hook"],
                hook_type=kwargs.get("hook_type", "curiosity"),
            )
            await ctx.session.commit()
            return {"stored": True, "hook_id": hook.id}

        if action == "find_similar" and "query" in kwargs:
            return {"results": [{"hook": "example winning hook", "ctr": 0.05}]}

        return {"stored": False, "note": "No action taken"}
