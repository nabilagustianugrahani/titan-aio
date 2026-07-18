"""Tests for database models and persistence layer."""

import pytest

from Database.models import (
    ABTestResult,
    AffiliateAccount,
    AlertRule,
    AuditLogEntry,
    AutoReport,
    BatchJob,
    BrandMention,
    BudgetAllocation,
    CompetitorProfile,
    CompetitorWatch,
    ComplianceCheck,
    ContentIdea,
    ContentRemix,
    ContentVersion,
    CrossPlatformMetric,
    InfluencerProfile,
    PerformanceAlert,
    PipelineRun,
    PricingAnalysis,
    RevenueDataPoint,
    RevenueForecast,
    ScheduledPost,
    SmartScheduleSlot,
    TrendRecord,
    ViralPrediction,
    VoiceProfile,
    WebhookConfig,
)

# ── Model Instantiation Tests ───────────────────────────────────

def test_viral_prediction_model():
    m = ViralPrediction(id="test-1", hook="Test hook", platform="tiktok", score=85)
    assert m.id == "test-1"
    assert m.score == 85

def test_trend_record_model():
    m = TrendRecord(id="test-1", platform="tiktok", topic="Test trend", velocity=0.8)
    assert m.velocity == 0.8

def test_competitor_profile_model():
    m = CompetitorProfile(id="test-1", name="Rival", platform="tiktok", followers=50000)
    assert m.followers == 50000

def test_content_remix_model():
    m = ContentRemix(id="test-1", source_content="Original", platform="tiktok", content_text="Remixed")
    assert m.content_text == "Remixed"

def test_content_version_model():
    m = ContentVersion(id="test-1", content_type="hook", content_id="h1", content_text="V1", version_number=1)
    assert m.version_number == 1

def test_scheduled_post_model():
    m = ScheduledPost(id="test-1", platform="tiktok", content_text="Post", scheduled_time="2026-06-25T19:00:00", status="scheduled")
    assert m.status == "scheduled"
    assert m.platform == "tiktok"

def test_ab_test_result_model():
    m = ABTestResult(id="test-1", test_name="Test A/B", status="running")
    assert m.test_name == "Test A/B"

def test_compliance_check_model():
    m = ComplianceCheck(id="test-1", content_text="Test", platform="tiktok", passed=True, score=95)
    assert m.passed is True

def test_audit_log_entry_model():
    m = AuditLogEntry(id="test-1", action="test.action", actor="user")
    assert m.action == "test.action"

def test_alert_rule_model():
    m = AlertRule(id="test-1", name="Low CTR", metric="ctr", condition="below", threshold=2.0)
    assert m.threshold == 2.0

def test_performance_alert_model():
    m = PerformanceAlert(id="test-1", rule_name="Low CTR", metric="ctr", current_value=0.5, severity="warning")
    assert m.severity == "warning"

def test_revenue_data_point_model():
    m = RevenueDataPoint(id="test-1", platform="tiktok", revenue=100.0, ad_spend=50.0, net_profit=50.0)
    assert m.net_profit == 50.0

def test_revenue_forecast_model():
    m = RevenueForecast(id="test-1", period="30d", predicted_revenue=5000.0, trend="growing")
    assert m.trend == "growing"

def test_voice_profile_model():
    m = VoiceProfile(id="test-1", name="Test Voice", style="enthusiastic")
    assert m.name == "Test Voice"

def test_webhook_config_model():
    m = WebhookConfig(id="test-1", name="Discord", url="https://discord.com/api", platform="discord")
    assert m.platform == "discord"

def test_affiliate_account_model():
    m = AffiliateAccount(id="test-1", name="Shopee Main", platform="shopee", commission_rate=5.0)
    assert m.commission_rate == 5.0

def test_brand_mention_model():
    m = BrandMention(id="test-1", brand="TestBrand", platform="tiktok", sentiment="positive")
    assert m.sentiment == "positive"

def test_influencer_profile_model():
    m = InfluencerProfile(id="test-1", name="Influencer1", platform="tiktok", niche="beauty", followers=100000)
    assert m.followers == 100000

def test_competitor_watch_model():
    m = CompetitorWatch(id="test-1", competitor_name="Rival", platform="tiktok", status="active")
    assert m.status == "active"

def test_content_idea_model():
    m = ContentIdea(id="test-1", title="Test Idea", platform="tiktok", content_type="video")
    assert m.content_type == "video"

def test_pricing_analysis_model():
    m = PricingAnalysis(id="test-1", product_id="p1", base_price=100000, strategy="premium")
    assert m.strategy == "premium"

def test_budget_allocation_model():
    m = BudgetAllocation(id="test-1", campaign_id="c1", platform="tiktok", recommended_budget=500.0)
    assert m.recommended_budget == 500.0

def test_batch_job_model():
    m = BatchJob(id="test-1", status="running", total_items=100)
    assert m.total_items == 100

def test_auto_report_model():
    m = AutoReport(id="test-1", report_type="weekly", score=85)
    assert m.score == 85

def test_pipeline_run_model():
    m = PipelineRun(id="test-1", pipeline_id="pipe-123", status="complete", features_used=["viral", "sentiment"])
    assert len(m.features_used) == 2

def test_smart_schedule_slot_model():
    m = SmartScheduleSlot(id="test-1", platform="tiktok", hour=19, avg_engagement=0.95)
    assert m.hour == 19

def test_cross_platform_metric_model():
    m = CrossPlatformMetric(id="test-1", platform="tiktok", impressions=1000, engagement_rate=5.0, roi=100.0)
    assert m.engagement_rate == 5.0


# ── Persistence Service Tests ───────────────────────────────────

@pytest.mark.asyncio
async def test_persistence_viral_prediction():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_viral_prediction(hook="Test hook", platform="tiktok", score=85)
        assert result.id
        assert result.score == 85

@pytest.mark.asyncio
async def test_persistence_trend_record():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_trend_record(platform="tiktok", topic="Test trend", velocity=0.8)
        assert result.id
        assert result.velocity == 0.8

@pytest.mark.asyncio
async def test_persistence_competitor_profile():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_competitor_profile(name="Rival", platform="tiktok", followers=50000)
        assert result.id
        assert result.followers == 50000

@pytest.mark.asyncio
async def test_persistence_content_version():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_content_version(content_type="hook", content_id="h1", content_text="V1")
        assert result.id
        assert result.content_text == "V1"

@pytest.mark.asyncio
async def test_persistence_scheduled_post():
    from datetime import datetime as _dt

    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_scheduled_post(platform="tiktok", content_text="Post", scheduled_time=_dt.now().isoformat())
        assert result.id

@pytest.mark.asyncio
async def test_persistence_revenue_data():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_revenue_data(platform="tiktok", revenue=100.0, ad_spend=50.0)
        assert result.net_profit == 50.0

@pytest.mark.asyncio
async def test_persistence_audit_log():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_audit_log(action="test.action", actor="user")
        assert result.id
        assert result.action == "test.action"

@pytest.mark.asyncio
async def test_persistence_performance_alert():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_performance_alert(rule_name="Low CTR", metric="ctr", current_value=0.5, severity="warning")
        assert result.id
        assert result.severity == "warning"

@pytest.mark.asyncio
async def test_persistence_brand_mention():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_brand_mention(brand="TestBrand", platform="tiktok", sentiment="positive")
        assert result.id

@pytest.mark.asyncio
async def test_persistence_content_idea():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_content_idea(title="Test Idea", platform="tiktok", content_type="video", estimated_engagement=0.8)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_pricing_analysis():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_pricing_analysis(product_id="p1", base_price=100000, strategy="premium")
        assert result.id
        assert result.strategy == "premium"

@pytest.mark.asyncio
async def test_persistence_pipeline_run():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_pipeline_run(pipeline_id="pipe-123", status="complete", features_used=["viral", "sentiment"])
        assert result.id
        assert len(result.features_used) == 2

@pytest.mark.asyncio
async def test_persistence_cross_platform_metric():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_cross_platform_metric(platform="tiktok", impressions=1000, engagement=50, clicks=20, revenue=100.0, ad_spend=50.0)
        assert result.engagement_rate == 5.0
        assert result.roi == 100.0

@pytest.mark.asyncio
async def test_persistence_voice_profile():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_voice_profile(name="Test Voice", style="enthusiastic")
        assert result.id

@pytest.mark.asyncio
async def test_persistence_webhook_config():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_webhook_config(name="Discord", url="https://discord.com/api", platform="discord")
        assert result.id

@pytest.mark.asyncio
async def test_persistence_affiliate_account():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_affiliate_account(name="Shopee Main", platform="shopee", commission_rate=5.0)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_influencer_profile():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_influencer_profile(name="Influencer1", platform="tiktok", niche="beauty", followers=100000)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_competitor_watch():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_competitor_watch(competitor_name="Rival", platform="tiktok")
        assert result.id

@pytest.mark.asyncio
async def test_persistence_budget_allocation():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_budget_allocation(campaign_id="c1", platform="tiktok", recommended_budget=500.0)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_auto_report():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_auto_report(report_type="weekly", score=85)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_revenue_forecast():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_revenue_forecast(period="30d", predicted_revenue=5000.0, trend="growing")
        assert result.id

@pytest.mark.asyncio
async def test_persistence_smart_schedule_slot():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        result = await db.save_smart_schedule_slot(platform="tiktok", hour=19, avg_engagement=0.95)
        assert result.id

@pytest.mark.asyncio
async def test_persistence_load_viral_predictions():
    from Services.infra.persistence import PersistenceService
    async with PersistenceService() as db:
        await db.save_viral_prediction(hook="Hook 1", score=80)
        await db.save_viral_prediction(hook="Hook 2", score=90)
        results = await db.load_viral_predictions()
        assert len(results) >= 2


# ── WebSocket Tests ─────────────────────────────────────────────

def test_websocket_manager():
    from titan.websocket_server import ConnectionManager
    manager = ConnectionManager()
    assert manager.get_connection_count() == 0
    assert manager.get_metrics_buffer() == []


# ── Integration: Full Pipeline + DB ─────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_with_db():
    """Test that pipeline state can be saved to DB."""
    from Services.autonomous_pipeline import PipelineState
    from Services.infra.persistence import PersistenceService

    state = PipelineState(
        pipeline_id="test-pipe-001",
        product_url="https://shopee.co.id/product/123",
        status="complete",
        features_used=["viral_predictor", "sentiment_monitor", "ml_scorer"],
    )

    async with PersistenceService() as db:
        run = await db.save_pipeline_run(
            pipeline_id=state.pipeline_id,
            product_url=state.product_url,
            status=state.status,
            features_used=state.features_used,
        )
        assert run.id
        assert run.pipeline_id == "test-pipe-001"
        assert len(run.features_used) == 3
