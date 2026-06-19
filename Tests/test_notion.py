"""Test Notion API integration."""

from __future__ import annotations

import pytest


class TestNotionClient:
    """Test Notion client initialization and config."""

    def test_config_loads_token(self):
        from titan.config import settings
        token = settings.NOTION_TOKEN
        assert token, "NOTION_TOKEN should be set in .env"

    def test_notion_client_import(self):
        from Services.notion.client import NotionClient
        assert NotionClient is not None

    def test_notion_client_singleton(self):
        from Services.notion.client import NotionClient
        nc1 = NotionClient.get_instance()
        nc2 = NotionClient.get_instance()
        assert nc1 is nc2

    def test_notion_client_has_token(self):
        from Services.notion.client import NotionClient
        nc = NotionClient.get_instance()
        assert nc._token, "Client should have token from settings"
        assert nc._token

    def test_notion_property_helpers(self):
        from Services.notion.client import NotionClient
        nc = NotionClient.get_instance()
        title = nc.title("Test Campaign")
        assert title["title"][0]["text"]["content"] == "Test Campaign"
        number = nc.number(42.5)
        assert number["number"] == 42.5
        select = nc.select("High")
        assert select["select"]["name"] == "High"

    def test_notion_tools_import(self):
        from MCP.tools.notion_tools import (
            notion_save_campaign,
            notion_save_knowledge,
            notion_create_task,
            notion_query_campaigns,
        )
        assert notion_save_campaign is not None
        assert notion_save_knowledge is not None
        assert notion_create_task is not None
        assert notion_query_campaigns is not None

    def test_notion_tools_registered(self):
        """Verify Notion MCP tool functions exist and have correct signatures."""
        import inspect
        from MCP.tools.notion_tools import (
            notion_save_campaign,
            notion_save_knowledge,
            notion_create_task,
            notion_query_campaigns,
        )
        sig = inspect.signature(notion_save_campaign)
        params = list(sig.parameters.keys())
        assert "campaign_id" in params
        assert "name" in params

        sig2 = inspect.signature(notion_create_task)
        params2 = list(sig2.parameters.keys())
        assert "title" in params2
        assert "status" in params2

        sig3 = inspect.signature(notion_save_knowledge)
        params3 = list(sig3.parameters.keys())
        assert "category" in params3
        assert "pattern" in params3
