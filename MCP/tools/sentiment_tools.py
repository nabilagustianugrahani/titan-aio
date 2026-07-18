"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp
from Services.agents.sentiment_monitor import monitor_sentiment


@mcp.tool()
async def monitor_sentiment(
    brand_name: str,
    platforms: str = "tiktok,instagram,twitter",
    niche: str = "general",
) -> dict:
    """Monitor brand sentiment across platforms. Detect crises and suggest content pivots.

    Args:
        brand_name: Brand/product name to monitor
        platforms: Comma-separated platform names
        niche: Product niche for context

    """
    result = await monitor_sentiment(
        brand_name=brand_name,
        platforms=platforms,
        niche=niche,
    )
    return result.model_dump()
