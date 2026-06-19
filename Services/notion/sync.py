"""Notion sync — auto-push campaign results to Notion dashboards."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from MCP.schemas import AffiliatePackageOutput
import httpx

from Services.notion.client import NotionClient


class NotionDashboard:
    """Two-way sync between TITAN AIO and Notion dashboards."""

    def __init__(self) -> None:
        self._nc = NotionClient.get_instance()
        self._client = self._nc.client

    def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        """Make an HTTP request to the Notion API (bypasses SDK limitations)."""
        from titan.config import settings
        headers = {
            "Authorization": f"Bearer {settings.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        url = f"https://api.notion.com/v1/{path}"
        if method == "POST":
            r = httpx.post(url, headers=headers, json=json_data or {})
        else:
            r = httpx.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

    # ── Push: Campaign Results ─────────────────────────────────

    def push_campaign(self, package: AffiliatePackageOutput) -> dict:
        """Push an affiliate package result to Notion Campaigns DB."""
        from titan.config import settings
        db_id = settings.NOTION_CAMPAIGN_DB
        if not db_id:
            return {"error": "NOTION_CAMPAIGN_DB not set"}

        props = {
            "Name": self._nc.title(package.product.title or "Untitled Campaign"),
            "Campaign ID": self._nc.rich_text(package.campaign_id or ""),
            "Product": self._nc.rich_text(package.product.title),
            "URL": self._nc.url(package.product.url),
            "Revenue": self._nc.number(package.product.price or 0),
            "Status": self._nc.select("Active"),
            "Platform": self._nc.select("Shopee"),
            "Created": self._nc.date(datetime.utcnow().isoformat()),
        }

        page = self._client.pages.create(
            parent={"type": "database_id", "database_id": db_id},
            properties=props,
        )
        return {"page_id": page.get("id"), "url": page.get("url")}

    # ── Push: Knowledge / Insights ─────────────────────────────

    def push_knowledge(
        self,
        category: str,
        pattern: str,
        confidence: float,
        advice: str = "",
        source_campaign: str = "",
    ) -> dict:
        """Push a winning insight to Notion Knowledge DB."""
        from titan.config import settings
        db_id = settings.NOTION_KNOWLEDGE_DB
        if not db_id:
            return {"error": "NOTION_KNOWLEDGE_DB not set"}

        props = {
            "Name": self._nc.title(pattern[:100]),
            "Category": self._nc.select(category),
            "Pattern": self._nc.rich_text(pattern),
            "Confidence": self._nc.number(confidence),
            "Advice": self._nc.rich_text(advice[:2000]),
            "Source Campaign": self._nc.rich_text(source_campaign),
        }

        page = self._client.pages.create(
            parent={"type": "database_id", "database_id": db_id},
            properties=props,
        )
        return {"page_id": page.get("id"), "url": page.get("url")}

    # ── Push: Task Update ──────────────────────────────────────

    def update_task_status(self, task_title: str, new_status: str = "Done") -> dict:
        """Find a task by title and update its status."""
        from titan.config import settings
        db_id = settings.NOTION_TASKS_DB
        if not db_id:
            return {"error": "NOTION_TASKS_DB not set"}

        # Query for the task
        results = self._request("POST", f"databases/{db_id}/query", {
            "page_size": 10,
            "filter": {
                "property": "Name",
                "title": {"contains": task_title},
            },
        })
        pages = results.get("results", [])
        if not pages:
            return {"error": f"Task '{task_title}' not found"}

        page = pages[0]
        self._client.pages.update(
            page_id=page["id"],
            properties={
                "Status": self._nc.select(new_status),
            },
        )
        return {"page_id": page["id"], "status": new_status}

    # ── Push: Full Package (all-in-one) ────────────────────────

    def push_affiliate_package(self, package: AffiliatePackageOutput) -> dict:
        """Push everything from a completed package to Notion."""
        results = {"campaign": None, "knowledge": []}

        # 1. Campaign
        results["campaign"] = self.push_campaign(package)

        # 2. Knowledge: top pain points
        if package.review_summary:
            for pp in package.review_summary.pain_points[:3]:
                k = self.push_knowledge(
                    category="Products",
                    pattern=f"Pain point: {pp.point}",
                    confidence=pp.frequency,
                    advice=f"Found in reviews for {package.product.title}",
                    source_campaign=package.campaign_id or "",
                )
                results["knowledge"].append(k)

        # 3. Knowledge: winning hooks
        if package.hooks:
            for h in package.hooks.hooks[:5]:
                k = self.push_knowledge(
                    category="Hooks",
                    pattern=h.hook,
                    confidence=0.7 if h.predicted_ctr == "high" else 0.5,
                    advice=f"Type: {h.type}, predicted CTR: {h.predicted_ctr}",
                    source_campaign=package.campaign_id or "",
                )
                results["knowledge"].append(k)

        return results

    # ── Push: Scraped Product Discovery ─────────────────────────

    def push_product_discovery(self, product: dict, category: str = "", score: float = 0.0) -> dict:
        """Push a discovered/scraped product to the Knowledge DB for review."""
        from titan.config import settings
        db_id = settings.NOTION_KNOWLEDGE_DB
        if not db_id:
            return {"error": "NOTION_KNOWLEDGE_DB not set"}

        title = product.get("title", "Unknown Product")[:100]
        price = product.get("price", 0) or 0
        platform = product.get("platform", "shopee")
        commission = product.get("commission_estimate", {})

        props = {
            "Name": self._nc.title(title),
            "Category": self._nc.select("Products"),
            "Pattern": self._nc.rich_text(f"💰 Rp{price:,} | {platform} | Score: {score}"),
            "Confidence": self._nc.number(score / 100 if score > 1 else score),
            "Advice": self._nc.rich_text(
                f"Komisi: Rp{commission.get('commission_per_item', 0):,}/item | "
                f"Potensi: Rp{commission.get('monthly_potential_rp', 0):,}/bulan | "
                f"Rate: {commission.get('avg_rate_pct', '?')}%"
            ),
            "Source Campaign": self._nc.rich_text(f"scraped:{platform}"),
            "Tags": {"multi_select": [{"name": cat.strip()} for cat in category.split(",") if cat.strip()]},
        }

        page = self._client.pages.create(
            parent={"type": "database_id", "database_id": db_id},
            properties=props,
        )
        return {"page_id": page.get("id"), "url": page.get("url"), "title": title}

    # ── Pull: Campaign Status ──────────────────────────────────

    def list_active_campaigns(self, limit: int = 10) -> list[dict]:
        """Pull active campaigns from Notion."""
        from titan.config import settings
        db_id = settings.NOTION_CAMPAIGN_DB
        if not db_id:
            return []

        results = self._request("POST", f"databases/{db_id}/query", {"page_size": limit})
        campaigns = []
        for page in results.get("results", []):
            props = page.get("properties", {})
            campaigns.append({
                "id": page.get("id"),
                "name": self._extract_title(props.get("Name", {})),
                "campaign_id": self._extract_text(props.get("Campaign ID", {})),
                "product": self._extract_text(props.get("Product", {})),
                "revenue": self._extract_number(props.get("Revenue", {})),
                "status": self._extract_select(props.get("Status", {})),
                "url": page.get("url"),
            })
        return campaigns

    # ── Pull: Pending Tasks ────────────────────────────────────

    def list_pending_tasks(self, limit: int = 10) -> list[dict]:
        """Pull incomplete tasks from Notion."""
        from titan.config import settings
        db_id = settings.NOTION_TASKS_DB
        if not db_id:
            return []

        results = self._request("POST", f"databases/{db_id}/query", {"page_size": limit})
        tasks = []
        for page in results.get("results", []):
            props = page.get("properties", {})
            tasks.append({
                "id": page.get("id"),
                "title": self._extract_title(props.get("Name", {})),
                "status": self._extract_select(props.get("Status", {})),
                "priority": self._extract_select(props.get("Priority", {})),
                "url": page.get("url"),
            })
        return tasks

    # ── Pull: Knowledge Query ──────────────────────────────────

    def query_knowledge(self, category: str = "", limit: int = 10) -> list[dict]:
        """Pull knowledge entries from Notion."""
        from titan.config import settings
        db_id = settings.NOTION_KNOWLEDGE_DB
        if not db_id:
            return []

        filter_data = None
        if category:
            filter_data = {
                "property": "Category",
                "select": {"equals": category},
            }

        results = self._request("POST", f"databases/{db_id}/query", {"page_size": limit})
        entries = []
        for page in results.get("results", []):
            props = page.get("properties", {})
            entries.append({
                "id": page.get("id"),
                "title": self._extract_title(props.get("Name", {})),
                "category": self._extract_select(props.get("Category", {})),
                "pattern": self._extract_text(props.get("Pattern", {})),
                "confidence": self._extract_number(props.get("Confidence", {})),
                "url": page.get("url"),
            })
        return entries

    # ── Property extractors ────────────────────────────────────

    @staticmethod
    def _extract_title(prop: dict) -> str:
        titles = prop.get("title", [])
        return titles[0].get("plain_text", "") if titles else ""

    @staticmethod
    def _extract_text(prop: dict) -> str:
        texts = prop.get("rich_text", [])
        return texts[0].get("plain_text", "") if texts else ""

    @staticmethod
    def _extract_number(prop: dict) -> Optional[float]:
        return prop.get("number")

    @staticmethod
    def _extract_select(prop: dict) -> Optional[str]:
        sel = prop.get("select")
        return sel.get("name") if sel else None
