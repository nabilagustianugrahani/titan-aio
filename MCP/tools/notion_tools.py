"""Notion API tools for TITAN AIO — campaign tracking & knowledge base."""

from __future__ import annotations

from typing import Any, Optional

from Services.notion.client import NotionClient
from titan.config import settings


async def notion_save_campaign(
    campaign_id: str,
    name: str,
    product_title: str,
    revenue: float = 0.0,
    status: str = "Active",
    database_id: Optional[str] = None,
) -> dict:
    """Save campaign data to a Notion database."""
    db_id = database_id or settings.NOTION_CAMPAIGN_DB
    if not db_id:
        return {"error": "NOTION_CAMPAIGN_DB not configured"}

    nc = NotionClient.get_instance()
    props = {
        "Name": nc.title(name),
        "Campaign ID": nc.rich_text(campaign_id),
        "Product": nc.rich_text(product_title),
        "Revenue": nc.number(revenue),
        "Status": nc.status(status),
    }
    page = await nc.create_page(parent_id=db_id, properties=props)
    return {"page_id": page.get("id", ""), "url": page.get("url", "")}


async def notion_save_knowledge(
    category: str,
    pattern: str,
    confidence: float,
    actionable_advice: str = "",
    database_id: Optional[str] = None,
) -> dict:
    """Save a knowledge entry to a Notion database."""
    db_id = database_id or settings.NOTION_KNOWLEDGE_DB
    if not db_id:
        return {"error": "NOTION_KNOWLEDGE_DB not configured"}

    nc = NotionClient.get_instance()
    props = {
        "Category": nc.select(category),
        "Pattern": nc.title(pattern),
        "Confidence": nc.number(confidence),
        "Advice": nc.rich_text(actionable_advice),
    }
    page = await nc.create_page(parent_id=db_id, properties=props)
    return {"page_id": page.get("id", ""), "url": page.get("url", "")}


async def notion_create_task(
    title: str,
    status: str = "Not started",
    priority: str = "Medium",
    database_id: Optional[str] = None,
) -> dict:
    """Create a task in the Notion tasks database."""
    db_id = database_id or settings.NOTION_TASKS_DB
    if not db_id:
        return {"error": "NOTION_TASKS_DB not configured"}

    nc = NotionClient.get_instance()
    props = {
        "Title": nc.title(title),
        "Status": nc.status(status),
        "Priority": nc.select(priority),
    }
    page = await nc.create_page(parent_id=db_id, properties=props)
    return {"page_id": page.get("id", ""), "url": page.get("url", "")}


async def notion_query_campaigns(
    status_filter: Optional[str] = None,
    database_id: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Query campaigns from Notion database."""
    db_id = database_id or settings.NOTION_CAMPAIGN_DB
    if not db_id:
        return []

    nc = NotionClient.get_instance()
    filters: dict[str, Any] = {}
    if status_filter:
        filters = {
            "filter": {
                "property": "Status",
                "status": {"equals": status_filter},
            }
        }

    results = await nc.query_database(db_id, **filters)
    pages = []
    for page in results[:limit]:
        pages.append(
            {
                "id": page.get("id"),
                "url": page.get("url"),
                "properties": _simplify_properties(page.get("properties", {})),
            }
        )
    return pages


def _simplify_properties(props: dict) -> dict:
    """Extract plain values from Notion property objects."""
    simplified = {}
    for key, value in props.items():
        ptype = value.get("type", "")
        if ptype == "title":
            titles = value.get("title", [])
            simplified[key] = titles[0].get("plain_text", "") if titles else ""
        elif ptype == "rich_text":
            texts = value.get("rich_text", [])
            simplified[key] = texts[0].get("plain_text", "") if texts else ""
        elif ptype == "number":
            simplified[key] = value.get("number")
        elif ptype == "select":
            sel = value.get("select")
            simplified[key] = sel.get("name") if sel else None
        elif ptype == "status":
            stat = value.get("status")
            simplified[key] = stat.get("name") if stat else None
        elif ptype == "url":
            simplified[key] = value.get("url")
        else:
            simplified[key] = str(value)
    return simplified
