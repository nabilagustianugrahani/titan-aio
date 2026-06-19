"""MCP tools for publishing and finance operations."""
from __future__ import annotations

from Services.orchestrator import CEOAgent


async def prepare_platform_content(caption: str = "") -> list[dict]:
    """Prepare formatted content for all platforms."""
    ceo = CEOAgent()
    result = await ceo.publisher(caption=caption)
    return result.get("platforms", [])


async def track_campaign_metrics(campaign_id: str) -> dict:
    """Track campaign performance metrics."""
    ceo = CEOAgent()
    return await ceo.track_metrics(campaign_id=campaign_id)
