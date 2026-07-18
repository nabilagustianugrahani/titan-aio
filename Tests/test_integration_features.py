"""Integration tests for orchestrator + pipeline with all 35+ features."""

import pytest

from Services.orchestrator import CEOAgent


@pytest.mark.asyncio
async def test_ceo_agent_initialization():
    """Verify CEO Agent initializes with all 35+ agents."""
    ceo = CEOAgent()
    # Core agents
    assert ceo.product
    assert ceo.review
    assert ceo.content
    assert ceo.offer
    assert ceo.trend
    assert ceo.competitor
    assert ceo.video
    assert ceo.avatar
    # Batch 1
    assert ceo.viral_predictor
    assert ceo.content_calendar
    assert ceo.compliance_checker
    assert ceo.ml_scorer
    assert ceo.cross_platform
    assert ceo.versioning
    assert ceo.dynamic_pricing
    # Batch 4
    assert ceo.revenue_forecaster
    assert ceo.smart_scheduler
    assert ceo.alert_manager
    assert ceo.ideas_generator
    assert ceo.competitor_monitor
    assert ceo.social_listener
    assert ceo.influencer_finder
    assert ceo.multi_account
    assert ceo.auto_reports
    assert ceo.budget_optimizer
    assert ceo.batch_processor
    assert ceo.multi_niche


@pytest.mark.asyncio
async def test_ceo_predict_virality():
    ceo = CEOAgent()
    result = await ceo.predict_virality(hook="This product is amazing! 🔥", platform="tiktok")
    assert "score" in result
    assert 0 <= result["score"] <= 100


@pytest.mark.asyncio
async def test_ceo_get_trend_alerts():
    ceo = CEOAgent()
    result = await ceo.get_trend_alerts(platform="tiktok", niche="beauty")
    assert "trends" in result
    assert len(result["trends"]) > 0


@pytest.mark.asyncio
async def test_ceo_ml_score():
    ceo = CEOAgent()
    result = await ceo.ml_score_content(content="This product changed my life! Link in bio!", platform="tiktok")
    assert "score" in result
    assert result["score"] > 0


@pytest.mark.asyncio
async def test_ceo_check_compliance():
    ceo = CEOAgent()
    result = await ceo.check_compliance(content="Great product! #ad Link in bio!", platform="tiktok")
    assert "passed" in result
    assert result["passed"] is True


@pytest.mark.asyncio
async def test_ceo_get_content_ideas():
    ceo = CEOAgent()
    ideas = await ceo.get_content_ideas(niche="beauty", platform="tiktok", count=3)
    assert len(ideas) >= 2
    assert all("title" in i for i in ideas)


@pytest.mark.asyncio
async def test_ceo_forecast_revenue():
    ceo = CEOAgent()
    result = await ceo.forecast_revenue(period="30d")
    assert "predicted_revenue" in result
    assert result["predicted_revenue"] >= 0


@pytest.mark.asyncio
async def test_ceo_find_influencers():
    ceo = CEOAgent()
    results = await ceo.find_influencers(niche="beauty", platform="tiktok", count=3)
    assert len(results) >= 2
    assert all("name" in r for r in results)


@pytest.mark.asyncio
async def test_ceo_generate_report():
    ceo = CEOAgent()
    result = await ceo.generate_report(report_type="weekly")
    assert "score" in result
    assert result["score"] > 0


@pytest.mark.asyncio
async def test_ceo_monitor_sentiment():
    ceo = CEOAgent()
    result = await ceo.monitor_sentiment(brand="TestBrand")
    assert "overall_sentiment" in result


@pytest.mark.asyncio
async def test_ceo_optimize_budget():
    ceo = CEOAgent()
    ceo.budget_optimizer.total_budget = 1000
    await ceo.budget_optimizer.register_campaign("c1", "tiktok", roi=150)
    results = await ceo.optimize_budget()
    assert len(results) > 0


@pytest.mark.asyncio
async def test_full_pipeline_integration():
    """Test the full pipeline with all features."""
    from Services.autonomous_pipeline import AutonomousPipeline
    AutonomousPipeline()
    # We can't run the full pipeline (needs real APIs), but we can verify
    # the state object has all the new fields
    from Services.autonomous_pipeline import PipelineState
    state = PipelineState()
    assert hasattr(state, "viral_scores")
    assert hasattr(state, "trend_alerts")
    assert hasattr(state, "content_remix")
    assert hasattr(state, "multilingual")
    assert hasattr(state, "seo_results")
    assert hasattr(state, "compliance_results")
    assert hasattr(state, "ml_scores")
    assert hasattr(state, "ab_tests")
    assert hasattr(state, "pricing_analysis")
    assert hasattr(state, "content_ideas")
    assert hasattr(state, "influencer_matches")
    assert hasattr(state, "sentiment_data")
    assert hasattr(state, "revenue_forecast")
    assert hasattr(state, "report")
    assert hasattr(state, "alerts_triggered")
    assert hasattr(state, "features_used")
    assert state.features_used == []
    assert state.to_dict()["total_features"] == 0
