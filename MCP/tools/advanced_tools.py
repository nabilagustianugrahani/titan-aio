"""MCP tools for Advanced Features — Reports, Budget, Smart Scheduler, Alerts, Ideas, Competitor Monitor, Social Listener, Influencer Finder, Multi-Account."""

from __future__ import annotations

from MCP.server import mcp


# ── Auto Reports ─────────────────────────────────────────────────

_report_gen = None

def _get_report_gen():
    global _report_gen
    if _report_gen is None:
        from Services.analytics.auto_reports import AutoReportGenerator
        _report_gen = AutoReportGenerator()
    return _report_gen


@mcp.tool()
async def generate_auto_report(report_type: str = "weekly") -> dict:
    """Generate an automatic performance report (daily/weekly/monthly)."""
    gen = _get_report_gen()
    result = await gen.generate_report(report_type=report_type)
    return result.model_dump()


@mcp.tool()
async def record_report_data(category: str, data: str) -> dict:
    """Record data for report generation. Category: revenue/campaigns/content."""
    import json
    gen = _get_report_gen()
    d = json.loads(data) if isinstance(data, str) else {}
    await gen.record_data(category=category, data=d)
    return {"recorded": True, "category": category}


# ── Budget Optimizer ────────────────────────────────────────────

_budget = None

def _get_budget():
    global _budget
    if _budget is None:
        from Services.agents.budget_optimizer import BudgetOptimizer
        _budget = BudgetOptimizer()
    return _budget


@mcp.tool()
async def set_total_budget(budget: float) -> dict:
    """Set total advertising budget for optimization."""
    b = _get_budget()
    await b.set_total_budget(budget=budget)
    return {"total_budget": budget}


@mcp.tool()
async def register_campaign_budget(campaign_id: str, platform: str, current_budget: float = 0.0, roi: float = 0.0) -> dict:
    """Register a campaign for budget optimization."""
    b = _get_budget()
    result = await b.register_campaign(campaign_id=campaign_id, platform=platform, current_budget=current_budget, roi=roi)
    return result.model_dump()


@mcp.tool()
async def optimize_budget() -> list[dict]:
    """Auto-allocate budget across campaigns for maximum ROI."""
    b = _get_budget()
    results = await b.optimize()
    return [r.model_dump() for r in results]


@mcp.tool()
async def get_budget_summary() -> dict:
    """Get budget allocation summary."""
    b = _get_budget()
    return await b.get_summary()


# ── Smart Scheduler ─────────────────────────────────────────────

_smart_sched = None

def _get_smart_sched():
    global _smart_sched
    if _smart_sched is None:
        from Services.scheduler.smart_scheduler import SmartScheduler
        _smart_sched = SmartScheduler()
    return _smart_sched


@mcp.tool()
async def get_optimal_posting_times(platform: str = "tiktok", count: int = 5) -> list[dict]:
    """Get ML-optimized posting times for a platform."""
    sched = _get_smart_sched()
    times = await sched.get_optimal_times(platform=platform, count=count)
    return [t.model_dump() for t in times]


@mcp.tool()
async def suggest_posting_schedule(platform: str = "tiktok", posts_per_day: int = 2) -> list[dict]:
    """Suggest a daily posting schedule based on engagement patterns."""
    sched = _get_smart_sched()
    return await sched.suggest_posting_schedule(platform=platform, posts_per_day=posts_per_day)


@mcp.tool()
async def record_engagement_data(platform: str, hour: int, day_of_week: str, engagement_rate: float) -> dict:
    """Record engagement data to improve scheduling recommendations."""
    sched = _get_smart_sched()
    await sched.record_engagement(platform=platform, hour=hour, day_of_week=day_of_week, engagement_rate=engagement_rate)
    return {"recorded": True}


# ── Performance Alerts ──────────────────────────────────────────

_alerts = None

def _get_alerts():
    global _alerts
    if _alerts is None:
        from Services.analytics.performance_alerts import PerformanceAlertManager
        _alerts = PerformanceAlertManager()
    return _alerts


@mcp.tool()
async def create_alert_rule(name: str, metric: str, condition: str, threshold: float, platform: str = "") -> dict:
    """Create a performance alert rule."""
    mgr = _get_alerts()
    result = await mgr.create_rule(name=name, metric=metric, condition=condition, threshold=threshold, platform=platform)
    return result.model_dump()


@mcp.tool()
async def record_performance_metric(metric: str, value: float, platform: str = "", campaign_id: str = "") -> dict:
    """Record a performance metric. Triggers alerts if thresholds are breached."""
    mgr = _get_alerts()
    await mgr.record_metric(metric=metric, value=value, platform=platform, campaign_id=campaign_id)
    return {"recorded": True, "alerts_triggered": len([a for a in mgr.alerts if not a.acknowledged])}


@mcp.tool()
async def get_performance_alerts(limit: int = 20) -> list[dict]:
    """Get unacknowledged performance alerts."""
    mgr = _get_alerts()
    alerts = await mgr.get_alerts(limit=limit)
    return [a.model_dump() for a in alerts]


@mcp.tool()
async def acknowledge_alert(alert_id: str) -> dict:
    """Acknowledge a performance alert."""
    mgr = _get_alerts()
    success = await mgr.acknowledge_alert(alert_id=alert_id)
    return {"success": success}


# ── Content Ideas Generator ─────────────────────────────────────

_ideas = None

def _get_ideas():
    global _ideas
    if _ideas is None:
        from Services.content.ideas_generator import IdeasGenerator
        _ideas = IdeasGenerator()
    return _ideas


@mcp.tool()
async def generate_content_ideas(niche: str = "general", platform: str = "tiktok", count: int = 5) -> list[dict]:
    """Generate AI-powered content ideas for a niche and platform."""
    gen = _get_ideas()
    ideas = await gen.generate_ideas(niche=niche, platform=platform, count=count)
    return [i.model_dump() for i in ideas]


@mcp.tool()
async def get_saved_ideas(niche: str = "", platform: str = "") -> list[dict]:
    """Get previously generated content ideas."""
    gen = _get_ideas()
    ideas = await gen.get_ideas(niche=niche, platform=platform)
    return [i.model_dump() for i in ideas]


# ── Competitor Monitor ──────────────────────────────────────────

_competitor_mon = None

def _get_competitor_mon():
    global _competitor_mon
    if _competitor_mon is None:
        from Services.agents.competitor_monitor import CompetitorMonitor
        _competitor_mon = CompetitorMonitor()
    return _competitor_mon


@mcp.tool()
async def add_competitor_watch(name: str, platform: str, url: str = "") -> dict:
    """Add a competitor to monitor."""
    mon = _get_competitor_mon()
    result = await mon.add_competitor(name=name, platform=platform, url=url)
    return result.model_dump()


@mcp.tool()
async def check_competitor_metrics(watch_id: str) -> dict:
    """Check metrics for a monitored competitor."""
    mon = _get_competitor_mon()
    result = await mon.check_competitor(watch_id=watch_id)
    return result.model_dump() if result else {"error": "Watch not found"}


@mcp.tool()
async def list_competitor_watches(platform: str = "") -> list[dict]:
    """List all monitored competitors."""
    mon = _get_competitor_mon()
    watches = await mon.list_competitors(platform=platform)
    return [w.model_dump() for w in watches]


# ── Social Listener ─────────────────────────────────────────────

_listener = None

def _get_listener():
    global _listener
    if _listener is None:
        from Services.agents.social_listener import SocialListener
        _listener = SocialListener()
    return _listener


@mcp.tool()
async def add_brand_to_watch(brand: str) -> dict:
    """Add a brand to social listening."""
    listener = _get_listener()
    await listener.add_brand(brand=brand)
    return {"brand": brand, "watching": True}


@mcp.tool()
async def record_brand_mention(brand: str, platform: str, text: str = "", sentiment: str = "neutral", author: str = "") -> dict:
    """Record a brand mention."""
    listener = _get_listener()
    result = await listener.record_mention(brand=brand, platform=platform, text=text, sentiment=sentiment, author=author)
    return result.model_dump()


@mcp.tool()
async def get_brand_mentions(brand: str = "", platform: str = "", sentiment: str = "", limit: int = 50) -> list[dict]:
    """Get brand mentions with optional filters."""
    listener = _get_listener()
    mentions = await listener.get_mentions(brand=brand, platform=platform, sentiment=sentiment, limit=limit)
    return [m.model_dump() for m in mentions]


@mcp.tool()
async def get_sentiment_summary(brand: str = "") -> dict:
    """Get sentiment summary for a brand."""
    listener = _get_listener()
    return await listener.get_sentiment_summary(brand=brand)


# ── Influencer Finder ───────────────────────────────────────────

_influencer = None

def _get_influencer():
    global _influencer
    if _influencer is None:
        from Services.agents.influencer_finder import InfluencerFinder
        _influencer = InfluencerFinder()
    return _influencer


@mcp.tool()
async def find_influencers(niche: str = "general", platform: str = "tiktok", min_followers: int = 0, max_followers: int = 999999999, count: int = 5) -> list[dict]:
    """Find influencers in a niche with follower and engagement data."""
    finder = _get_influencer()
    results = await finder.find_influencers(niche=niche, platform=platform, min_followers=min_followers, max_followers=max_followers, count=count)
    return [r.model_dump() for r in results]


# ── Multi-Account Manager ──────────────────────────────────────

_multi_acct = None

def _get_multi_acct():
    global _multi_acct
    if _multi_acct is None:
        from Services.agents.multi_account import MultiAccountManager
        _multi_acct = MultiAccountManager()
    return _multi_acct


@mcp.tool()
async def add_affiliate_account(name: str, platform: str, commission_rate: float = 0.0) -> dict:
    """Add an affiliate account to manage."""
    mgr = _get_multi_acct()
    result = await mgr.add_account(name=name, platform=platform, commission_rate=commission_rate)
    return result.model_dump()


@mcp.tool()
async def record_account_earnings(account_id: str, earnings: float, clicks: int = 0, conversions: int = 0) -> dict:
    """Record earnings for an affiliate account."""
    mgr = _get_multi_acct()
    success = await mgr.record_earnings(account_id=account_id, earnings=earnings, clicks=clicks, conversions=conversions)
    return {"success": success}


@mcp.tool()
async def list_affiliate_accounts(platform: str = "") -> list[dict]:
    """List all affiliate accounts."""
    mgr = _get_multi_acct()
    accounts = await mgr.list_accounts(platform=platform)
    return [a.model_dump() for a in accounts]


@mcp.tool()
async def get_earnings_summary() -> dict:
    """Get total earnings across all accounts."""
    mgr = _get_multi_acct()
    return await mgr.get_total_earnings()
