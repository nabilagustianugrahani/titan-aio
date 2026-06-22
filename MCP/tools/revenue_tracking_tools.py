"""MCP tools for Revenue Tracking."""

from __future__ import annotations

from MCP.server import mcp

_tracker = None


def _get_tracker():
    global _tracker
    if _tracker is None:
        from Services.revenue.tracker import RevenueTracker
        _tracker = RevenueTracker()
    return _tracker


@mcp.tool()
async def track_affiliate_click(link_id: str, platform: str, source: str = "") -> dict:
    """Record an affiliate link click."""
    tracker = _get_tracker()
    result = await tracker.record_click(link_id=link_id, platform=platform, source=source)
    return result.model_dump()


@mcp.tool()
async def track_conversion(
    link_id: str,
    platform: str,
    product_name: str = "",
    sale_amount: float = 0.0,
    commission_rate: float = 5.0,
) -> dict:
    """Record a conversion and calculate commission."""
    tracker = _get_tracker()
    result = await tracker.record_conversion(
        link_id=link_id,
        platform=platform,
        product_name=product_name,
        sale_amount=sale_amount,
        commission_rate=commission_rate,
    )
    return result.model_dump()


@mcp.tool()
async def get_revenue_summary(days: int = 30) -> dict:
    """Get revenue summary for the last N days."""
    tracker = _get_tracker()
    result = await tracker.get_summary(days=days)
    return result.model_dump()


@mcp.tool()
async def get_revenue_stats() -> dict:
    """Get overall revenue statistics."""
    tracker = _get_tracker()
    return await tracker.get_stats()
