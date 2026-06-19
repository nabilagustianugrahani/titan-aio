"""MCP tools for LangGraph workflow engine."""

from __future__ import annotations

from Services.graph_workflow import run_campaign_with_bus


async def run_graph_campaign(
    url: str,
) -> dict:
    """Run a complete affiliate campaign using the LangGraph workflow engine.

    Analyzes product → reviews → competitors → offer → UGC → creative → save.
    Returns campaign_id and step results.
    """
    result = await run_campaign_with_bus(url=url)
    return {
        "campaign_id": result.get("campaign_id", ""),
        "product": result.get("product", {}).get("title", ""),
        "steps_completed": [k for k in ("product", "reviews", "offer", "hooks", "campaign_id") if result.get(k)],
        "status": "completed" if result.get("campaign_id") else "failed",
    }
