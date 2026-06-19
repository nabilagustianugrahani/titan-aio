"""MCP tools for Notion dashboard — push results, pull status."""

from __future__ import annotations

from Services.notion.sync import NotionDashboard
from MCP.schemas import AffiliatePackageOutput


async def dashboard_push_campaign(
    product_id: str,
    title: str,
    price: float,
    campaign_id: str = "",
    url: str = "",
) -> dict:
    """Push campaign result to Notion dashboard."""
    from MCP.schemas import AnalyzeProductOutput

    package = AffiliatePackageOutput(
        product=AnalyzeProductOutput(
            product_id=product_id,
            title=title,
            price=price,
            url=url,
        ),
        campaign_id=campaign_id,
    )
    db = NotionDashboard()
    return db.push_campaign(package)


async def dashboard_push_knowledge(
    category: str,
    pattern: str,
    confidence: float = 0.5,
    advice: str = "",
) -> dict:
    """Push an insight/knowledge entry to Notion dashboard."""
    db = NotionDashboard()
    return db.push_knowledge(
        category=category,
        pattern=pattern,
        confidence=confidence,
        advice=advice,
    )


async def dashboard_list_active_campaigns(limit: int = 10) -> list[dict]:
    """Pull active campaigns from Notion dashboard."""
    db = NotionDashboard()
    return db.list_active_campaigns(limit=limit)


async def dashboard_list_pending_tasks(limit: int = 10) -> list[dict]:
    """Pull pending tasks from Notion dashboard."""
    db = NotionDashboard()
    return db.list_pending_tasks(limit=limit)


async def dashboard_query_knowledge(category: str = "", limit: int = 10) -> list[dict]:
    """Query knowledge base from Notion dashboard."""
    db = NotionDashboard()
    return db.query_knowledge(category=category, limit=limit)
