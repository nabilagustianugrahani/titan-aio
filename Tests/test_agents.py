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
        import uuid

        from Database.connection import async_session_factory
        from Database.models import Product, Review
        from Database.repository import Repository
        from Services.agents.review import ReviewAgent

        agent = ReviewAgent()
        pid = f"test-{uuid.uuid4().hex[:8]}"

        # Create a product and reviews so the agent has real data
        async with async_session_factory() as session:
            repo_p = Repository(session, Product)
            await repo_p.create(
                external_id=pid, title="Serum Wajah Test",
                price=85000, category="skincare", url="https://test.com/product",
            )
            repo_r = Repository(session, Review)
            await repo_r.create(
                product_id=pid, rating=4.5, text="Bagus banget produknya, jerawat langsung kempes!",
            )
            await repo_r.create(
                product_id=pid, rating=3.0, text="Cukup oke tapi agak lama hasilnya.",
            )

        result = await agent(product_id=pid)
        assert result.total_reviews_analyzed > 0
        assert result.average_rating > 0


@pytest.mark.asyncio
class TestContentAgent:
    """Test Content Agent (unified UGC + Creative)."""

    async def test_generate(self):
        from MCP.schemas import GenerateOfferOutput
        from Services.agents.content import ContentAgent

        agent = ContentAgent()
        offer = GenerateOfferOutput(
            product_id="p1", primary_angle="test", value_proposition="vp",
        )
        result = await agent(product_id="p1", offer_strategy=offer)
        assert "hooks" in result
        assert "scripts" in result
        assert "thumbnail" in result
        assert len(result["hooks"].hooks) > 0
        assert result["thumbnail"].thumbnail.concept


@pytest.mark.asyncio
class TestCEOAgent:
    """Test CEO Agent orchestrator."""

    async def test_create_package(self):
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        package = await ceo.create_affiliate_package(
            "https://shopee.co.id/test-abc12345",
        )
        assert package.product
        assert package.review_summary
        assert package.hooks
        assert package.scripts
        assert package.thumbnail
        assert package.campaign_id
