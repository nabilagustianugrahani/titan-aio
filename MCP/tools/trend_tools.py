"""MCP tools for trend analysis."""
from __future__ import annotations

from Services.orchestrator import CEOAgent

_ceo = CEOAgent()


async def analyze_trend(category: str = "") -> dict:
    """Analyze market trends for a category."""
    ceo = CEOAgent()
    return await ceo.analyze_trends(category=category)


async def analyze_competitor(category: str = "umum") -> dict:
    """Analyze competitor landscape for a category."""
    ceo = CEOAgent()
    result = await ceo.competitor(category=category)
    return {
        "category": result.category,
        "competitors_analyzed": result.competitors_analyzed,
        "winning_hooks": [h.model_dump() for h in result.winning_hooks],
        "common_angles": result.common_angles,
        "gaps_identified": result.gaps_identified,
        "recommended_differentiation": result.recommended_differentiation,
    }


async def store_winning_hook(hook_text: str, hook_type: str = "curiosity", campaign_id: str = "") -> dict:
    """Store a winning hook in memory."""
    ceo = CEOAgent()
    return await ceo.memory(action="store", hook=hook_text, hook_type=hook_type, campaign_id=campaign_id)


async def evaluate_campaign_finance(campaign_id: str, revenue: float, ad_spend: float) -> dict:
    """Evaluate campaign financials."""
    ceo = CEOAgent()
    return await ceo.evaluate_finance(campaign_id=campaign_id, revenue=revenue, ad_spend=ad_spend)


async def decide_growth_action(roi: float) -> dict:
    """Decide whether to scale, kill, or maintain a campaign based on ROI."""
    ceo = CEOAgent()
    return await ceo.growth_decision(roi=roi)
