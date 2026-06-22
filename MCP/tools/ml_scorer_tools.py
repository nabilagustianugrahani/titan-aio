"""MCP tools for ML Content Scorer."""

from __future__ import annotations

from MCP.server import mcp

_scorer = None

def _get_scorer():
    global _scorer
    if _scorer is None:
        from Services.analytics.ml_scorer import MLContentScorer
        _scorer = MLContentScorer()
    return _scorer


@mcp.tool()
async def ml_score_content(content: str, platform: str = "tiktok", niche: str = "general") -> dict:
    """ML-based content scoring with feature breakdown, risk factors, and improvement suggestions.

    Analyzes hook strength, emotional impact, story arc, CTA effectiveness,
    visual appeal, timing, platform fit, and niche relevance.
    """
    scorer = _get_scorer()
    result = await scorer.score(content=content, platform=platform, niche=niche)
    return result.model_dump()


@mcp.tool()
async def ml_batch_score(contents: str, platform: str = "tiktok", niche: str = "general") -> list[dict]:
    """Score multiple content pieces at once. Contents should be comma-separated."""
    scorer = _get_scorer()
    import json
    content_list = json.loads(contents) if contents.startswith("[") else [{"content": c.strip()} for c in contents.split("|||") if c.strip()]
    results = await scorer.batch_score(contents=content_list, platform=platform, niche=niche)
    return [r.model_dump() for r in results]
