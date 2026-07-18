"""Tests for Batch 4 Advanced Features."""

import pytest

from Services.agents.budget_optimizer import BudgetOptimizer
from Services.agents.competitor_monitor import CompetitorMonitor
from Services.agents.influencer_finder import InfluencerFinder
from Services.agents.multi_account import MultiAccountManager
from Services.agents.revenue_forecaster import RevenueForecaster
from Services.agents.social_listener import SocialListener
from Services.analytics.auto_reports import AutoReportGenerator
from Services.analytics.performance_alerts import PerformanceAlertManager
from Services.content.ideas_generator import IdeasGenerator
from Services.notifications.telegram_bot import TelegramBot
from Services.scheduler.smart_scheduler import SmartScheduler

# ── Telegram Bot ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telegram_configure():
    bot = TelegramBot()
    config = await bot.configure(bot_token="test:token", chat_ids=["123", "456"])
    assert config.enabled
    assert len(config.chat_ids) == 2

@pytest.mark.asyncio
async def test_telegram_send():
    bot = TelegramBot()
    await bot.configure(bot_token="test:token", chat_ids=["123"])
    msgs = await bot.send_notification(title="Test", message="Hello!", severity="info")
    assert len(msgs) == 1

@pytest.mark.asyncio
async def test_telegram_command():
    bot = TelegramBot()
    response = await bot.handle_command(command="start", chat_id="123")
    assert "Welcome" in response or "Titan" in response


# ── Revenue Forecaster ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_revenue():
    f = RevenueForecaster()
    point = await f.record_revenue(revenue=100.0, ad_spend=50.0, platform="tiktok")
    assert point.revenue == 100.0

@pytest.mark.asyncio
async def test_forecast():
    f = RevenueForecaster()
    for i in range(10):
        await f.record_revenue(revenue=50.0 + i * 5, ad_spend=20.0)
    result = await f.forecast(period="30d")
    assert result.predicted_revenue > 0
    assert result.trend in ("growing", "stable", "declining")


# ── Smart Scheduler ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_optimal_times():
    sched = SmartScheduler()
    times = await sched.get_optimal_times(platform="tiktok", count=5)
    assert len(times) >= 3
    assert all(t.score > 0 for t in times)

@pytest.mark.asyncio
async def test_record_engagement():
    sched = SmartScheduler()
    for h in range(24):
        await sched.record_engagement(platform="tiktok", hour=h, day_of_week="Monday", engagement_rate=h / 24)
    times = await sched.get_optimal_times(platform="tiktok", count=3)
    assert len(times) == 3


# ── Performance Alerts ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_rule():
    mgr = PerformanceAlertManager()
    rule = await mgr.create_rule(name="Low CTR", metric="ctr", condition="below", threshold=1.0)
    assert rule.rule_id

@pytest.mark.asyncio
async def test_alert_triggered():
    mgr = PerformanceAlertManager()
    await mgr.create_rule(name="Low CTR", metric="ctr", condition="below", threshold=2.0)
    await mgr.record_metric(metric="ctr", value=0.5, platform="tiktok")
    alerts = await mgr.get_alerts()
    assert len(alerts) > 0


# ── Content Ideas ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_ideas():
    gen = IdeasGenerator()
    ideas = await gen.generate_ideas(niche="beauty", platform="instagram", count=5)
    assert len(ideas) >= 3
    assert all(i.hook_suggestion for i in ideas)

@pytest.mark.asyncio
async def test_ideas_by_niche():
    gen = IdeasGenerator()
    await gen.generate_ideas(niche="electronics", platform="tiktok")
    await gen.generate_ideas(niche="fashion", platform="tiktok")
    electronics = await gen.get_ideas(niche="electronics")
    assert len(electronics) > 0


# ── Competitor Monitor ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_competitor():
    mon = CompetitorMonitor()
    watch = await mon.add_competitor(name="RivalBrand", platform="tiktok")
    assert watch.watch_id

@pytest.mark.asyncio
async def test_check_competitor():
    mon = CompetitorMonitor()
    watch = await mon.add_competitor(name="RivalBrand", platform="tiktok")
    result = await mon.check_competitor(watch_id=watch.watch_id)
    assert result.metrics


# ── Social Listener ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_mention():
    listener = SocialListener()
    mention = await listener.record_mention(brand="MyBrand", platform="tiktok", text="Great product!", sentiment="positive")
    assert mention.mention_id

@pytest.mark.asyncio
async def test_sentiment_summary():
    listener = SocialListener()
    await listener.record_mention(brand="MyBrand", platform="tiktok", sentiment="positive")
    await listener.record_mention(brand="MyBrand", platform="tiktok", sentiment="negative")
    summary = await listener.get_sentiment_summary(brand="MyBrand")
    assert summary["total"] == 2


# ── Influencer Finder ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_find_influencers():
    finder = InfluencerFinder()
    results = await finder.find_influencers(niche="beauty", platform="tiktok", count=3)
    assert len(results) == 3
    assert all(i.followers > 0 for i in results)


# ── Multi-Account Manager ──────────────────────────────────────

@pytest.mark.asyncio
async def test_add_account():
    mgr = MultiAccountManager()
    acc = await mgr.add_account(name="Shopee Main", platform="shopee", commission_rate=5.0)
    assert acc.account_id

@pytest.mark.asyncio
async def test_earnings():
    mgr = MultiAccountManager()
    acc = await mgr.add_account(name="Shopee Main", platform="shopee")
    await mgr.record_earnings(account_id=acc.account_id, earnings=500.0, clicks=100, conversions=5)
    summary = await mgr.get_total_earnings()
    assert summary["total_earnings"] == 500.0


# ── Auto Reports ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_report():
    gen = AutoReportGenerator()
    await gen.record_data("revenue", {"revenue": 1000, "ad_spend": 500})
    await gen.record_data("campaigns", {"status": "active"})
    report = await gen.generate_report(report_type="weekly")
    assert report.report_id
    assert report.score > 0


# ── Budget Optimizer ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_optimize_budget():
    b = BudgetOptimizer()
    await b.set_total_budget(1000)
    await b.register_campaign("camp1", "tiktok", roi=150)
    await b.register_campaign("camp2", "instagram", roi=50)
    results = await b.optimize()
    assert len(results) == 2
    # High ROI campaign should get more budget
    assert results[0].recommended_budget > results[1].recommended_budget or results[0].roi > results[1].roi


# ── Integration ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_batch4_pipeline():
    # Revenue
    f = RevenueForecaster()
    await f.record_revenue(revenue=200, ad_spend=100, platform="tiktok")
    forecast = await f.forecast("30d")
    assert forecast.predicted_revenue > 0

    # Ideas
    gen = IdeasGenerator()
    ideas = await gen.generate_ideas(niche="general", platform="tiktok", count=3)
    assert len(ideas) == 3

    # Alerts
    mgr = PerformanceAlertManager()
    await mgr.create_rule(name="CTR Alert", metric="ctr", condition="below", threshold=2.0)
    await mgr.record_metric(metric="ctr", value=1.0)
    assert len(mgr.alerts) > 0

    # Budget
    b = BudgetOptimizer()
    await b.set_total_budget(500)
    await b.register_campaign("c1", "tiktok", roi=200)
    results = await b.optimize()
    assert len(results) == 1
