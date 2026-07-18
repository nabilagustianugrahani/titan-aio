"""HuggingFace Agent — automated HF Space management during campaigns.

Extends BaseAgent to provide HF operations that can be integrated
into the CEO pipeline:
- Health check on HF Space after deployment
- Auto-backup DB snapshots to Hub after each campaign
- Scale hardware based on usage metrics

Usage:
    from Services.agents.hf_agent import HFAgent
    agent = HFAgent()
    result = await agent(ctx, action="health_check", space_id="Badjals/TitanAIO")
"""

from __future__ import annotations

from typing import Any

from Services.agents.base import BaseAgent, AgentContext
from Services.hf_client import hf_client


class HFAgent(BaseAgent):
    """Agent for HuggingFace automation tasks during campaigns."""

    def __init__(self, name: str = "HFAgent") -> None:
        super().__init__(name=name)
        self._default_space = "Badjals/TitanAIO"

    async def execute(self, ctx: AgentContext, **kwargs: Any) -> dict:
        """Execute HF operations.

        Supported actions via kwargs:
            action: "health_check" | "backup_db" | "space_status"
            space_id: Target Space ID (default: Badjals/TitanAIO)
            local_path: For backup_db — path to snapshot file
        """
        action = kwargs.get("action", "health_check")
        space_id = kwargs.get("space_id", self._default_space)

        if action == "health_check":
            return await self._health_check(space_id)
        elif action == "backup_db":
            local_path = kwargs.get("local_path", "")
            return await self._backup_db(space_id, local_path, ctx)
        elif action == "space_status":
            return await self._space_status(space_id)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _health_check(self, space_id: str) -> dict:
        """Check if a Space is running and healthy."""
        info = await hf_client.space_info(space_id)
        runtime = info.get("runtime", info) if isinstance(info, dict) else {}
        stage = runtime.get("stage", "UNKNOWN")
        return {
            "space_id": space_id,
            "status": "ok" if stage == "RUNNING" else "degraded",
            "stage": stage,
            "hardware": runtime.get("hardware", {}),
            "domain": runtime.get("domains", []),
            "healthy": stage == "RUNNING",
        }

    async def _backup_db(
        self, space_id: str, local_path: str, ctx: AgentContext,
    ) -> dict:
        """Upload a database snapshot to the Space's Hub repo."""
        if not local_path:
            return {"error": "local_path required for backup_db action"}
        result = await hf_client.hub_upload_file(
            repo_id=space_id,
            path=f"snapshots/titan-{ctx.session.info.db_name}.db",
            local_path=local_path,
            repo_type="space",
        )
        if isinstance(result, dict) and "error" not in result:
            return {"status": "ok", "backup": "uploaded", "space_id": space_id}
        return {"status": "error", "error": result.get("error", "unknown"), "space_id": space_id}

    async def _space_status(self, space_id: str) -> dict:
        """Get comprehensive Space status with health assessment."""
        info = await hf_client.space_info(space_id)
        if not isinstance(info, dict):
            return {"space_id": space_id, "raw": str(info)}

        runtime = info.get("runtime", info)
        card_data = info.get("cardData", {})

        return {
            "space_id": space_id,
            "title": card_data.get("title", ""),
            "sdk": card_data.get("sdk", ""),
            "stage": runtime.get("stage", "unknown"),
            "hardware": runtime.get("hardware", {}),
            "replicas": runtime.get("replicas", {}),
            "dev_mode": runtime.get("devMode", False),
            "domains": [
                {"url": d.get("domain", ""), "ready": d.get("stage") == "READY"}
                for d in runtime.get("domains", [])
            ],
            "likes": card_data.get("likes", info.get("likes", 0)),
            "last_modified": info.get("lastModified", ""),
            "private": info.get("private", False),
            "disabled": info.get("disabled", False),
        }
