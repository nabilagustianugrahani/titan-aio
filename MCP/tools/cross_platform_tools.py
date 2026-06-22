"""MCP tools for Cross-Platform Analytics."""

from __future__ import annotations

from MCP.server import mcp

_analytics = None

def _get_analytics():
    global _analytics
    if _analytics is None:
        from Services.analytics.cross_platform import CrossPlatformAnalytics
        _analytics = CrossPlatformAnalytics()
    return _analytics


@mcp.tool()
async def record_platform_metrics(platform: str, impressions: int = 0, reach: int = 0, engagement: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0, ad_spend: float = 0.0) -> dict:
    """Record metrics for a platform. Tracks impressions, engagement, clicks, conversions, revenue."""
    analytics = _get_analytics()
    result = await analytics.record_metrics(platform=platform, impressions=impressions, reach=reach, engagement=engagement, clicks=clicks, conversions=conversions, revenue=revenue, ad_spend=ad_spend)
    return result.model_dump()


@mcp.tool()
async def generate_cross_platform_report(campaign_id: str = "") -> dict:
    """Generate unified cross-platform analytics report with recommendations."""
    analytics = _get_analytics()
    result = await analytics.generate_report(campaign_id=campaign_id)
    return result.model_dump()


@mcp.tool()
async def get_platform_comparison() -> dict:
    """Compare performance across all platforms side-by-side."""
    analytics = _get_analytics()
    return await analytics.get_comparison()
