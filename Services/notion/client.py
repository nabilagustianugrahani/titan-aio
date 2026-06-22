"""Notion API client wrapping the official notion-client SDK."""

from __future__ import annotations

from typing import Any, Optional

from notion_client import Client

from titan.config import settings


class NotionClient:
    """TITAN AIO Notion integration."""

    _instance: Optional["NotionClient"] = None

    def __init__(self, token: str = "") -> None:
        self._token = token or settings.NOTION_TOKEN or ""
        self._client: Optional[Client] = None

    @classmethod
    def get_instance(cls) -> "NotionClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def client(self) -> Client:
        if self._client is None:
            if not self._token:
                raise RuntimeError(
                    "NOTION_TOKEN not set. Add it to .env or settings."
                )
            self._client = Client(auth=self._token)
        return self._client

    # ── Database operations ──────────────────────────────────────────

    async def query_database(
        self, database_id: str, **kwargs: Any
    ) -> list[dict]:
        """Query a Notion database. Returns list of page results."""
        results = self.client.databases.query(
            database_id=database_id, **kwargs
        )
        return results.get("results", [])

    async def create_page(
        self,
        parent_id: str,
        properties: dict,
        parent_type: str = "database_id",
        children: Optional[list[dict]] = None,
    ) -> dict:
        """Create a new page in a database or under a parent page."""
        parent = {parent_type: parent_id}
        return self.client.pages.create(
            parent=parent, properties=properties, children=children or []
        )

    async def update_page(self, page_id: str, properties: dict) -> dict:
        """Update properties of a page."""
        return self.client.pages.update(page_id=page_id, properties=properties)

    async def get_page(self, page_id: str) -> dict:
        """Get a page by ID."""
        return self.client.pages.retrieve(page_id=page_id)

    async def append_blocks(
        self, block_id: str, children: list[dict]
    ) -> dict:
        """Append content blocks to a page."""
        return self.client.blocks.children.append(
            block_id=block_id, children=children
        )

    # ── Helper: build properties ─────────────────────────────────────

    @staticmethod
    def title(text: str) -> dict:
        return {"title": [{"type": "text", "text": {"content": text}}]}

    @staticmethod
    def rich_text(text: str) -> dict:
        return {"rich_text": [{"type": "text", "text": {"content": text}}]}

    @staticmethod
    def number(value: float) -> dict:
        return {"number": value}

    @staticmethod
    def select(name: str) -> dict:
        return {"select": {"name": name}}

    @staticmethod
    def status(name: str) -> dict:
        return {"status": {"name": name}}

    @staticmethod
    def date(start: str, end: Optional[str] = None) -> dict:
        d: dict[str, Optional[str]] = {"start": start}
        if end:
            d["end"] = end
        return {"date": d}

    @staticmethod
    def url(value: str) -> dict:
        return {"url": value}
