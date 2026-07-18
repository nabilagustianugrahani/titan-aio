"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_forecaster = None


def _get_forecaster():
    global _forecaster
    if _forecaster is None:
        from Services.agents.revenue_forecaster import RevenueForecaster

        _forecaster = RevenueForecaster()
    return _forecaster


@mcp.tool()
async def record_revenue(
    revenue: float,
    ad_spend: float = 0.0,
    campaign_id: str = "",
    platform: str = "",
    clicks: int = 0,
    conversions: int = 0,
) -> dict:
    """Record revenue data point for forecasting."""
    f = _get_forecaster()
    result = await f.record_revenue(
        revenue=revenue,
        ad_spend=ad_spend,
        campaign_id=campaign_id,
        platform=platform,
        clicks=clicks,
        conversions=conversions,
    )
    return result.model_dump()


@mcp.tool()
async def forecast_revenue(period: str = "30d") -> dict:
    """Forecast revenue for 7d/30d/90d period."""
    f = _get_forecaster()
    result = await f.forecast(period=period)
    return result.model_dump()


@mcp.tool()
async def detect_revenue_trend(window: int = 14) -> dict:
    """Detect revenue trend over a given number of days."""
    f = _get_forecaster()
    return await f.detect_trend(window=window)


@mcp.tool()
async def forecast_break_even() -> dict:
    """Forecast when revenue will break even against ad spend."""
    f = _get_forecaster()
    return await f.forecast_break_even()


@mcp.tool()
async def get_revenue_breakdown() -> dict:
    """Get revenue breakdown by platform."""
    f = _get_forecaster()
    return await f.get_platform_breakdown()


@mcp.tool()
async def get_campaign_breakdown() -> dict:
    """Get revenue breakdown by campaign."""
    f = _get_forecaster()
    return await f.get_campaign_breakdown()


@mcp.tool()
async def get_revenue_stats() -> dict:
    """Get overall revenue statistics."""
    f = _get_forecaster()
    return await f.get_stats()


@mcp.tool()
async def get_revenue_report() -> dict:
    """Generate comprehensive revenue report with forecasts, trends, and breakdowns."""
    f = _get_forecaster()
    return await f.generate_report()
