"""MCP tools module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from MCP.instance import mcp
from Services.agents.competitor_spy import (
    CompetitorInput,
    CompetitorProfile,
    spy_competitor,
    spy_multiple,
)


class SpyCompetitorInput(BaseModel):
    competitor_url: str
    platform: str = "tiktok"
    niche: str = "general"


class SpyMultipleInput(BaseModel):
    competitor_urls: list[str]
    platform: str = "auto"
    niche: str = "general"


@mcp.tool()
async def spy_competitor(competitor_url: str, platform: str = "tiktok", niche: str = "general") -> dict[str, Any]:
    """Analyze a competitor's strategy. Returns profile with hooks, gaps, and recommendations."""
    input_model = CompetitorInput(
        competitor_url=competitor_url,
        platform=platform,
        niche=niche,
    )
    profile: CompetitorProfile = await spy_competitor(input_model)
    return profile.model_dump()


@mcp.tool()
async def spy_multiple_competitors(
    competitor_urls: list[str],
    platform: str = "auto",
    niche: str = "general",
) -> dict[str, Any]:
    """Analyze multiple competitors at once. Returns list of profiles with comparative data."""
    profiles = await spy_multiple(competitor_urls, platform=platform, niche=niche)
    results = [p.model_dump() for p in profiles]

    # Build summary comparison
    if results:
        followers_sorted = sorted(results, key=lambda r: r.get("followers", 0), reverse=True)
        engagement_sorted = sorted(results, key=lambda r: r.get("avg_engagement", 0), reverse=True)
        summary = {
            "total_competitors": len(results),
            "market_leader": followers_sorted[0]["name"] if followers_sorted else None,
            "highest_engagement": engagement_sorted[0]["name"] if engagement_sorted else None,
            "avg_followers": round(sum(r.get("followers", 0) for r in results) / len(results)),
            "avg_engagement": round(
                sum(r.get("avg_engagement", 0) for r in results) / len(results), 2,
            ),
            "top_threats": [
                r["name"] for r in results if r.get("threat_level") in ("high", "critical")
            ],
        }
    else:
        summary = {"total_competitors": 0}

    return {
        "competitors": results,
        "summary": summary,
    }
