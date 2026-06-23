"""Integration tests for TITAN AIO."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestFullPipeline:
    """Test the complete affiliate package pipeline end-to-end."""

    async def test_ceo_pipeline(self):
        """CEO Agent creates a full affiliate package."""
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        package = await ceo.create_affiliate_package(
            "https://shopee.co.id/test-product-abc12345"
        )
        assert package is not None
        assert package.product.title
        assert package.product.price > 0
        assert package.review_summary.total_reviews_analyzed > 0
        assert package.hooks is not None
        assert len(package.hooks.hooks) >= 5
        assert package.scripts is not None
        assert len(package.scripts.scripts) >= 5
        assert package.thumbnail.thumbnail.concept
        assert package.campaign_id

    async def test_with_video_and_avatar(self):
        """Pipeline with video and avatar generation."""
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        package = await ceo.create_affiliate_package(
            "https://tokopedia.com/test-product-xyz67890",
            include_video=True,
            include_avatar=True,
        )
        assert package.video is not None
        assert package.avatar is not None


@pytest.mark.asyncio
class TestMarketIntelligence:
    """Test market intelligence features."""

    async def test_trend_analysis(self):
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        trends = await ceo.analyze_trends(category="elektronik")
        assert "trend_score" in trends
        assert "trend_direction" in trends

    async def test_financial_evaluation(self):
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        result = await ceo.evaluate_finance(
            "campaign-1", revenue=1000000, ad_spend=200000
        )
        assert result["recorded"] is True
        assert result["roi"] == 4.0

    async def test_growth_decision(self):
        from Services.orchestrator import CEOAgent
        ceo = CEOAgent()
        result = await ceo.growth_decision(roi=3.0)
        assert result["action"] == "scale"
        result_low = await ceo.growth_decision(roi=0.3)
        assert result_low["action"] == "kill"
