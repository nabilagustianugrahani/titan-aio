"""Test agent classes."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestProductAgent:
    """Test Product Agent."""

    async def test_analyze(self):
        from Services.agents.product import ProductAgent
        agent = ProductAgent()
        result = await agent(url="https://shopee.co.id/test-abc12345")
        assert result.get("title")
        assert result.get("price", 0) > 0
        assert result.get("product_id")


@pytest.mark.asyncio
class TestReviewAgent:
    """Test Review Agent."""

    async def test_analyze(self):
        from Services.agents.review import ReviewAgent
        from MCP.tools.analyze_product import analyze_product
        from MCP.schemas import AnalyzeProductInput

        agent = ReviewAgent()
        product = await analyze_product(
            AnalyzeProductInput(
                url="https://test.com/product-abc12345"
            )
        )
        result = await agent(product_id=product.product_id)
        assert result.total_reviews_analyzed > 0
        assert result.average_rating > 0
        assert len(result.pain_points) > 0


@pytest.mark.asyncio
class TestUGCAgent:
    """Test UGC Agent."""

    async def test_generate(self):
        from Services.agents.ugc import UGCAgent
        from MCP.schemas import GenerateOfferOutput

        agent = UGCAgent()
        offer = GenerateOfferOutput(
            product_id="p1", primary_angle="test", value_proposition="vp"
        )
        result = await agent(product_id="p1", offer_strategy=offer)
        assert "hooks" in result
        assert "scripts" in result
        assert len(result["hooks"].hooks) > 0


@pytest.mark.asyncio
class TestCreativeAgent:
    """Test Creative Agent."""

    async def test_generate(self):
        from Services.agents.creative import CreativeAgent
        agent = CreativeAgent()
        result = await agent(product_id="p1")
        assert "thumbnail" in result
        assert result["thumbnail"].thumbnail.concept


@pytest.mark.asyncio
class TestCEOAgent:
    """Test CEO Agent orchestrator."""

    async def test_create_package(self):
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        package = await ceo.create_affiliate_package(
            "https://shopee.co.id/test-abc12345"
        )
        assert package.product
        assert package.review_summary
        assert package.hooks
        assert package.scripts
        assert package.thumbnail
        assert package.campaign_id
