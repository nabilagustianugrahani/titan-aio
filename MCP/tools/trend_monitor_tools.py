"""MCP tools for Real-Time Trend Monitor."""

from __future__ import annotations

from MCP.server import mcp
from Services.agents.trend_monitor import TrendInput, monitor_trends


@mcp.tool()
async def monitor_trends(
    platform: str = "tiktok",
    niche: str = "general",
    limit: int = 10,
) -> dict:
    """Get real-time trend alerts for a platform. Returns trending topics with velocity scores and urgency levels.

    Args:
        platform: Platform to monitor (tiktok/instagram/youtube/twitter/facebook)
        niche: Product niche for relevance scoring
        limit: Max trends to return
    """
    input_data = TrendInput(platform=platform, niche=niche, limit=limit)
    result = await monitor_trends(input_data)
    return result.model_dump()
