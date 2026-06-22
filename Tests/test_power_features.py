"""Tests for Batch 2+3 Power Features."""

import pytest
from Services.scheduler.content_calendar import ContentCalendar
from Services.notifications.webhook import WebhookManager
from Services.infra.rate_limiter import APIRateLimiter
from Services.infra.content_cache import ContentCache
from Services.infra.audit_logger import AuditLogger
from Services.compliance.content_checker import ContentComplianceChecker
from Services.campaign.multi_niche import MultiNicheManager
from Services.campaign.batch_processor import BatchProcessor
from Services.analytics.ml_scorer import MLContentScorer
from Services.analytics.cross_platform import CrossPlatformAnalytics
from Services.content.versioning import ContentVersionManager
from Services.agents.dynamic_pricing import DynamicPricingEngine


# ── Content Calendar ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_schedule_post():
    cal = ContentCalendar()
    post = await cal.schedule_post(platform="tiktok", content="Test post!", scheduled_time="2026-06-25T19:00:00")
    assert post.post_id
    assert post.platform == "tiktok"

@pytest.mark.asyncio
async def test_find_optimal_slots():
    cal = ContentCalendar()
    slots = await cal.find_optimal_slots(platform="tiktok", count=5)
    assert len(slots) == 5
    assert all(s.score > 0 for s in slots)

@pytest.mark.asyncio
async def test_calendar_stats():
    cal = ContentCalendar()
    await cal.schedule_post(platform="tiktok", content="Post 1", scheduled_time="2026-06-25T19:00:00")
    await cal.schedule_post(platform="instagram", content="Post 2", scheduled_time="2026-06-25T20:00:00")
    stats = await cal.get_stats()
    assert stats["total_posts"] == 2


# ── Webhook Alerts ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_webhook():
    mgr = WebhookManager()
    wh = await mgr.register_webhook(name="Test", url="https://discord.com/api/test", platform="discord")
    assert wh.webhook_id
    assert wh.name == "Test"

@pytest.mark.asyncio
async def test_send_alert():
    mgr = WebhookManager()
    await mgr.register_webhook(name="Alerts", url="https://discord.com/api/test")
    result = await mgr.send_alert(event_type="campaign.created", title="New Campaign", message="Test")
    assert result["sent_to"] >= 0

@pytest.mark.asyncio
async def test_alert_history():
    mgr = WebhookManager()
    await mgr.send_alert(event_type="test", title="Test", message="Test msg")
    history = await mgr.get_alert_history()
    assert len(history) > 0


# ── Rate Limiter ────────────────────────────────────────────────

def test_rate_limiter_acquire():
    limiter = APIRateLimiter()
    result = limiter.can_request("gemini")
    assert result is True

def test_rate_limiter_usage():
    limiter = APIRateLimiter()
    usage = limiter.can_request("nonexistent")
    assert usage is True


# ── Content Cache ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = ContentCache()
    await cache.set("hook", {"text": "test"}, {"score": 85})
    result = await cache.get("hook", {"text": "test"})
    assert result is not None
    assert result["score"] == 85

@pytest.mark.asyncio
async def test_cache_miss():
    cache = ContentCache()
    result = await cache.get("hook", {"text": "nonexistent"})
    assert result is None

@pytest.mark.asyncio
async def test_cache_stats():
    cache = ContentCache()
    await cache.set("hook", {"text": "test"}, {"score": 85})
    stats = await cache.get_stats()
    assert stats["total_entries"] == 1


# ── Audit Logger ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_log():
    logger = AuditLogger()
    entry = await logger.log(action="campaign.created", actor="user", target="camp-123")
    assert entry.entry_id.startswith("AUD-")

@pytest.mark.asyncio
async def test_audit_query():
    logger = AuditLogger()
    await logger.log(action="test.action", actor="test_user")
    await logger.log(action="test.action", actor="test_user")
    entries = await logger.query(action="test.action")
    assert len(entries) == 2


# ── Compliance Checker ──────────────────────────────────────────

def test_compliance_short_content():
    checker = ContentComplianceChecker()
    result = checker.check_content("Great product! #ad Link in bio!", platform="tiktok")
    assert result.passed

def test_compliance_long_content():
    checker = ContentComplianceChecker()
    result = checker.check_content("x" * 400, platform="tiktok")
    assert not result.passed

def test_compliance_banned_words():
    checker = ContentComplianceChecker()
    result = checker.check_content("This is a guaranteed miracle cure!", platform="tiktok")
    assert not result.passed


# ── Multi-Niche Campaign ───────────────────────────────────────

@pytest.mark.asyncio
async def test_create_niche_campaign():
    mgr = MultiNicheManager()
    campaign = await mgr.create_campaign(niche="electronics", name="Tech Deals")
    assert campaign.campaign_id
    assert campaign.niche == "electronics"

@pytest.mark.asyncio
async def test_niche_summary():
    mgr = MultiNicheManager()
    await mgr.create_campaign(niche="electronics", name="Tech 1")
    await mgr.create_campaign(niche="fashion", name="Fashion 1")
    summary = await mgr.get_niche_summary()
    assert "electronics" in summary
    assert "fashion" in summary


# ── Batch Processor ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_batch():
    proc = BatchProcessor()
    job = await proc.create_batch(items=[{"id": 1}, {"id": 2}, {"id": 3}])
    assert job.job_id
    assert job.total_items == 3

@pytest.mark.asyncio
async def test_batch_stats():
    proc = BatchProcessor()
    await proc.create_batch(items=[{"id": 1}])
    stats = await proc.get_stats()
    assert stats["total_jobs"] == 1


# ── ML Content Scorer ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_ml_score():
    scorer = MLContentScorer()
    result = await scorer.score(content="This product is amazing! You won't believe the results! 😱🔥 Link in bio!", platform="tiktok")
    assert 0 <= result.score <= 100
    assert result.predicted_ctr > 0

@pytest.mark.asyncio
async def test_ml_score_weak():
    scorer = MLContentScorer()
    result = await scorer.score(content="buy this", platform="tiktok")
    assert result.score < 60


# ── Cross-Platform Analytics ────────────────────────────────────

@pytest.mark.asyncio
async def test_record_metrics():
    analytics = CrossPlatformAnalytics()
    metrics = await analytics.record_metrics(platform="tiktok", impressions=1000, engagement=50, clicks=20, revenue=100.0)
    assert metrics.engagement_rate == 5.0

@pytest.mark.asyncio
async def test_cross_platform_report():
    analytics = CrossPlatformAnalytics()
    await analytics.record_metrics(platform="tiktok", impressions=1000, clicks=20, revenue=100.0, ad_spend=50.0)
    await analytics.record_metrics(platform="instagram", impressions=500, clicks=10, revenue=50.0, ad_spend=25.0)
    report = await analytics.generate_report()
    assert report.total_impressions == 1500
    assert report.best_platform


# ── Content Versioning ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_version():
    mgr = ContentVersionManager()
    v1 = await mgr.create_version("hook", "hook-1", "Version 1 content")
    assert v1.version_number == 1
    v2 = await mgr.create_version("hook", "hook-1", "Version 2 content")
    assert v2.version_number == 2

@pytest.mark.asyncio
async def test_revert_version():
    mgr = ContentVersionManager()
    v1 = await mgr.create_version("hook", "hook-1", "Original")
    v2 = await mgr.create_version("hook", "hook-1", "Changed")
    reverted = await mgr.revert("hook", "hook-1", v1.version_id)
    assert reverted.content == "Original"


# ── Dynamic Pricing ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_price():
    engine = DynamicPricingEngine()
    result = await engine.analyze_price(product_id="p1", base_price=100000, commission_rate=5.0, demand_score=0.8, supply_score=0.2)
    assert result.strategy in ("undercut", "match", "premium", "volume")
    assert result.recommended_price > 0

@pytest.mark.asyncio
async def test_pricing_recommendations():
    engine = DynamicPricingEngine()
    await engine.analyze_price(product_id="p1", base_price=100000, commission_rate=5.0)
    recs = await engine.get_recommendations()
    assert len(recs) > 0


# ── Integration Test ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_power_pipeline():
    """Test multiple power features working together."""
    # Calendar
    cal = ContentCalendar()
    post = await cal.schedule_post(platform="tiktok", content="Amazing product!", scheduled_time="2026-06-25T19:00:00")
    assert post.post_id

    # ML Scorer
    scorer = MLContentScorer()
    score = await scorer.score(content="Amazing product! Link in bio! 🔥", platform="tiktok")
    assert score.score > 0

    # Compliance
    checker = ContentComplianceChecker()
    compliance = checker.check_content("Amazing product! #ad Link in bio!", platform="tiktok")
    assert compliance.passed

    # Cross-platform
    analytics = CrossPlatformAnalytics()
    await analytics.record_metrics(platform="tiktok", impressions=1000, clicks=20, revenue=100.0)
    report = await analytics.generate_report()
    assert report.total_impressions == 1000

    # Pricing
    engine = DynamicPricingEngine()
    pricing = await engine.analyze_price(product_id="test", base_price=100000, commission_rate=5.0)
    assert pricing.strategy
