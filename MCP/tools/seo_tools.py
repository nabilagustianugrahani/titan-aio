"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp
from Services.content.seo_engine import seo_optimize


@mcp.tool()
async def seo_optimize(
    title: str,
    description: str = "",
    niche: str = "general",
    platform: str = "youtube",
) -> dict:
    """Optimize content for search rankings with keyword research and SEO scoring.

    Args:
        title: Content title to optimize
        description: Content description (optional)
        niche: Product niche for keyword research
        platform: Target platform (youtube/tiktok/instagram)

    """
    result = await seo_optimize(
        title=title,
        description=description,
        niche=niche,
        platform=platform,
    )
    return result.model_dump()
