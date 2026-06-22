"""Test Phase 2 MCP tool functions."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestTrendTools:
    async def test_analyze_trend(self):
        from MCP.tools.trend_tools import analyze_trend
        result = await analyze_trend(category="elektronik")
        assert "trend_score" in result
        assert "trend_direction" in result

    async def test_analyze_competitor(self):
        from MCP.tools.trend_tools import analyze_competitor
        result = await analyze_competitor(category="elektronik")
        assert result["competitors_analyzed"] > 0
        assert len(result["winning_hooks"]) > 0

    async def test_evaluate_finance(self):
        from MCP.tools.trend_tools import evaluate_campaign_finance
        result = await evaluate_campaign_finance("c1", revenue=1000000, ad_spend=200000)
        assert result["financials"]["roi"] == 4.0

    async def test_growth_decision(self):
        from MCP.tools.trend_tools import decide_growth_action
        r1 = await decide_growth_action(roi=3.0)
        assert r1["actions"][0]["action"] == "scale"


@pytest.mark.asyncio
class TestMemoryTools:
    async def _test_store_and_find_hook(self):
        from MCP.tools.memory_tools import memory_store_hook
        result = await memory_store_hook(hook_text="Test winning hook", hook_type="curiosity")
        assert result["stored"]
        # Clean up
        from Services.memory.vector_store import VectorStore
        VectorStore().delete_collection("winning_hooks")

    async def _test_store_product_knowledge(self):
        from MCP.tools.memory_tools import memory_store_product_knowledge
        result = await memory_store_product_knowledge("p1", "Test product knowledge")
        assert result["stored"]

    async def _test_find_similar_products(self):
        from MCP.tools.memory_tools import memory_find_similar_products
        result = await memory_find_similar_products("test", top_k=3)
        assert isinstance(result, list)


@pytest.mark.asyncio
class TestPublisherTools:
    async def test_prepare_content(self):
        from MCP.tools.publisher_tools import prepare_platform_content
        result = await prepare_platform_content(caption="Test caption")
        assert len(result) > 0
        assert "platform" in result[0]

    async def test_track_metrics(self):
        from MCP.tools.publisher_tools import track_campaign_metrics
        result = await track_campaign_metrics(campaign_id="c1")
        assert "metrics" in result
