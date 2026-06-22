"""Persistence layer — saves/loads data for all 35+ features to database."""

from __future__ import annotations

from Database.connection import async_session_factory
from Database.repository import Repository
from Database.models import (
    ViralPrediction, TrendRecord, CompetitorProfile, ContentRemix,
    ContentVersion, ScheduledPost, ABTestResult, ComplianceCheck,
    AuditLogEntry, AlertRule, PerformanceAlert, RevenueDataPoint,
    RevenueForecast, VoiceProfile, WebhookConfig, AffiliateAccount,
    BrandMention, InfluencerProfile, CompetitorWatch, ContentIdea,
    PricingAnalysis, BudgetAllocation, BatchJob, AutoReport,
    PipelineRun, SmartScheduleSlot, CrossPlatformMetric,
)


class PersistenceService:
    """Unified persistence layer for all 35+ features.

    Usage:
        async with PersistenceService() as db:
            await db.save_viral_prediction(hook="test", score=85, ...)
            predictions = await db.load_viral_predictions(campaign_id="xxx")
    """

    async def __aenter__(self):
        self.session = async_session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session.is_active:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        await self.session.close()

    # ── Viral Predictions ──────────────────────────────────────
    async def save_viral_prediction(self, campaign_id: str = "", hook: str = "", script: str = "", platform: str = "tiktok", score: int = 0, predicted_reach: int = 0, predicted_engagement_rate: float = 0.0, best_posting_time: str = "", optimization_tips: list[str] | None = None, feature_breakdown: dict | None = None) -> ViralPrediction:
        repo = Repository(self.session, ViralPrediction)
        return await repo.create(campaign_id=campaign_id, hook=hook, script=script, platform=platform, score=score, predicted_reach=predicted_reach, predicted_engagement_rate=predicted_engagement_rate, best_posting_time=best_posting_time, optimization_tips=optimization_tips or [], feature_breakdown=feature_breakdown or {})

    async def load_viral_predictions(self, campaign_id: str = "", limit: int = 50) -> list[ViralPrediction]:
        repo = Repository(self.session, ViralPrediction)
        if campaign_id:
            return await repo.find(campaign_id=campaign_id)
        return await repo.list_all(limit=limit)

    # ── Trend Records ──────────────────────────────────────────
    async def save_trend_record(self, platform: str = "tiktok", niche: str = "general", topic: str = "", velocity: float = 0.0, relevance_score: float = 0.0, urgency: str = "medium", hashtags: list[str] | None = None, engagement_score: float = 0.0) -> TrendRecord:
        repo = Repository(self.session, TrendRecord)
        return await repo.create(platform=platform, niche=niche, topic=topic, velocity=velocity, relevance_score=relevance_score, urgency=urgency, hashtags=hashtags or [], engagement_score=engagement_score)

    async def load_trend_records(self, platform: str = "", niche: str = "", limit: int = 50) -> list[TrendRecord]:
        repo = Repository(self.session, TrendRecord)
        filters = {}
        if platform: filters["platform"] = platform
        if niche: filters["niche"] = niche
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Competitor Profiles ────────────────────────────────────
    async def save_competitor_profile(self, platform: str = "tiktok", name: str = "", url: str = "", followers: int = 0, avg_engagement: float = 0.0, posting_frequency: str = "", top_hooks: list[str] | None = None, content_gaps: list[str] | None = None, threat_level: str = "medium", recommendations: list[str] | None = None, growth_rate: float = 0.0) -> CompetitorProfile:
        repo = Repository(self.session, CompetitorProfile)
        return await repo.create(platform=platform, name=name, url=url, followers=followers, avg_engagement=avg_engagement, posting_frequency=posting_frequency, top_hooks=top_hooks or [], content_gaps=content_gaps or [], threat_level=threat_level, recommendations=recommendations or [], growth_rate=growth_rate)

    async def load_competitor_profiles(self, platform: str = "", limit: int = 50) -> list[CompetitorProfile]:
        repo = Repository(self.session, CompetitorProfile)
        return await repo.find(platform=platform) if platform else await repo.list_all(limit=limit)

    # ── Content Versions ───────────────────────────────────────
    async def save_content_version(self, content_type: str = "", content_id: str = "", content_text: str = "", version_number: int = 1, author: str = "system", notes: str = "", tags: list[str] | None = None, performance_score: float = 0.0, is_current: bool = True) -> ContentVersion:
        repo = Repository(self.session, ContentVersion)
        return await repo.create(content_type=content_type, content_id=content_id, content_text=content_text, version_number=version_number, author=author, notes=notes, tags=tags or [], performance_score=performance_score, is_current=is_current)

    async def load_content_versions(self, content_type: str = "", content_id: str = "") -> list[ContentVersion]:
        repo = Repository(self.session, ContentVersion)
        filters = {}
        if content_type: filters["content_type"] = content_type
        if content_id: filters["content_id"] = content_id
        return await repo.find(**filters) if filters else await repo.list_all()

    # ── Scheduled Posts ────────────────────────────────────────
    async def save_scheduled_post(self, platform: str = "", content_text: str = "", scheduled_time: str = "", status: str = "scheduled", campaign_id: str = "", hashtags: list[str] | None = None, media_urls: list[str] | None = None) -> ScheduledPost:
        from datetime import datetime as _dt
        repo = Repository(self.session, ScheduledPost)
        if isinstance(scheduled_time, str) and scheduled_time:
            st = _dt.fromisoformat(scheduled_time)
        elif isinstance(scheduled_time, _dt):
            st = scheduled_time
        else:
            st = _dt.now()
        return await repo.create(platform=platform, content_text=content_text, scheduled_time=st, status=status, campaign_id=campaign_id or None, hashtags=hashtags or None, media_urls=media_urls or None)

    async def load_scheduled_posts(self, platform: str = "", status: str = "", limit: int = 100) -> list[ScheduledPost]:
        repo = Repository(self.session, ScheduledPost)
        filters = {}
        if platform: filters["platform"] = platform
        if status: filters["status"] = status
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── A/B Test Results ──────────────────────────────────────
    async def save_ab_test(self, test_name: str = "", niche: str = "general", platform: str = "tiktok", status: str = "running", confidence: float = 0.0, winner_variant_id: str = "", variants: list[dict] | None = None) -> ABTestResult:
        repo = Repository(self.session, ABTestResult)
        return await repo.create(test_name=test_name, niche=niche, platform=platform, status=status, confidence=confidence, winner_variant_id=winner_variant_id, variants=variants or [])

    async def load_ab_tests(self, status: str = "", limit: int = 50) -> list[ABTestResult]:
        repo = Repository(self.session, ABTestResult)
        return await repo.find(status=status) if status else await repo.list_all(limit=limit)

    # ── Revenue Data ───────────────────────────────────────────
    async def save_revenue_data(self, campaign_id: str = "", platform: str = "", revenue: float = 0.0, ad_spend: float = 0.0, clicks: int = 0, conversions: int = 0) -> RevenueDataPoint:
        repo = Repository(self.session, RevenueDataPoint)
        return await repo.create(campaign_id=campaign_id, platform=platform, revenue=revenue, ad_spend=ad_spend, clicks=clicks, conversions=conversions, net_profit=revenue - ad_spend)

    async def load_revenue_data(self, campaign_id: str = "", platform: str = "", limit: int = 100) -> list[RevenueDataPoint]:
        repo = Repository(self.session, RevenueDataPoint)
        filters = {}
        if campaign_id: filters["campaign_id"] = campaign_id
        if platform: filters["platform"] = platform
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Audit Logs ─────────────────────────────────────────────
    async def save_audit_log(self, action: str = "", actor: str = "system", target: str = "", details: dict | None = None) -> AuditLogEntry:
        repo = Repository(self.session, AuditLogEntry)
        return await repo.create(action=action, actor=actor, target=target, details=details or {})

    async def load_audit_logs(self, action: str = "", actor: str = "", limit: int = 100) -> list[AuditLogEntry]:
        repo = Repository(self.session, AuditLogEntry)
        filters = {}
        if action: filters["action"] = action
        if actor: filters["actor"] = actor
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Performance Alerts ─────────────────────────────────────
    async def save_performance_alert(self, rule_id: str = "", rule_name: str = "", metric: str = "", current_value: float = 0.0, previous_value: float = 0.0, threshold: float = 0.0, condition: str = "", message: str = "", severity: str = "info", platform: str = "", campaign_id: str = "", acknowledged: bool = False) -> PerformanceAlert:
        repo = Repository(self.session, PerformanceAlert)
        return await repo.create(rule_id=rule_id, rule_name=rule_name, metric=metric, current_value=current_value, previous_value=previous_value, threshold=threshold, condition=condition, message=message, severity=severity, platform=platform, campaign_id=campaign_id, acknowledged=acknowledged)

    async def load_performance_alerts(self, acknowledged: bool = False, severity: str = "", limit: int = 50) -> list[PerformanceAlert]:
        repo = Repository(self.session, PerformanceAlert)
        filters = {"acknowledged": acknowledged}
        if severity: filters["severity"] = severity
        return await repo.find(**filters)

    # ── Brand Mentions ─────────────────────────────────────────
    async def save_brand_mention(self, brand: str = "", platform: str = "", text_content: str = "", sentiment: str = "neutral", author_url: str = "", source_url: str = "") -> BrandMention:
        repo = Repository(self.session, BrandMention)
        return await repo.create(brand=brand, platform=platform, text_content=text_content, sentiment=sentiment, author_url=author_url, source_url=source_url)

    async def load_brand_mentions(self, brand: str = "", platform: str = "", sentiment: str = "", limit: int = 100) -> list[BrandMention]:
        repo = Repository(self.session, BrandMention)
        filters = {}
        if brand: filters["brand"] = brand
        if platform: filters["platform"] = platform
        if sentiment: filters["sentiment"] = sentiment
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Content Ideas ──────────────────────────────────────────
    async def save_content_idea(self, title: str = "", description: str = "", platform: str = "tiktok", content_type: str = "video", hook_suggestion: str = "", estimated_engagement: float = 0.0, difficulty: str = "easy", tags: list[str] | None = None, niche: str = "general", cta_suggestion: str = "") -> ContentIdea:
        repo = Repository(self.session, ContentIdea)
        return await repo.create(title=title, description=description or None, platform=platform, content_type=content_type, hook_suggestion=hook_suggestion or None, estimated_engagement=estimated_engagement, difficulty=difficulty or None, tags=tags or None, niche=niche or None, cta_suggestion=cta_suggestion or None)

    async def load_content_ideas(self, niche: str = "", platform: str = "", limit: int = 50) -> list[ContentIdea]:
        repo = Repository(self.session, ContentIdea)
        filters = {}
        if niche: filters["niche"] = niche
        if platform: filters["platform"] = platform
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Pricing Analysis ───────────────────────────────────────
    async def save_pricing_analysis(self, product_id: str = "", base_price: float = 0.0, commission_rate: float = 0.0, market_avg: float = 0.0, competitor_avg: float = 0.0, demand_score: float = 0.5, supply_score: float = 0.5, recommended_price: float = 0.0, recommended_commission: float = 0.0, strategy: str = "match") -> PricingAnalysis:
        repo = Repository(self.session, PricingAnalysis)
        return await repo.create(product_id=product_id, base_price=base_price, commission_rate=commission_rate, market_avg=market_avg, competitor_avg=competitor_avg, demand_score=demand_score, supply_score=supply_score, recommended_price=recommended_price, recommended_commission=recommended_commission, strategy=strategy)

    async def load_pricing_analyses(self, product_id: str = "", limit: int = 50) -> list[PricingAnalysis]:
        repo = Repository(self.session, PricingAnalysis)
        return await repo.find(product_id=product_id) if product_id else await repo.list_all(limit=limit)

    # ── Pipeline Runs ──────────────────────────────────────────
    async def save_pipeline_run(self, pipeline_id: str = "", product_url: str = "", status: str = "running", features_used: list[str] | None = None, errors: list[dict] | None = None, hooks_count: int = 0, scripts_count: int = 0, video_count: int = 0) -> PipelineRun:
        repo = Repository(self.session, PipelineRun)
        return await repo.create(pipeline_id=pipeline_id, product_url=product_url, status=status, features_used=features_used or [], errors=errors or [], hooks_count=hooks_count, scripts_count=scripts_count, video_count=video_count)

    async def load_pipeline_runs(self, status: str = "", limit: int = 50) -> list[PipelineRun]:
        repo = Repository(self.session, PipelineRun)
        return await repo.find(status=status) if status else await repo.list_all(limit=limit)

    # ── Cross-Platform Metrics ─────────────────────────────────
    async def save_cross_platform_metric(self, platform: str = "", campaign_id: str = "", impressions: int = 0, reach: int = 0, engagement: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0, ad_spend: float = 0.0) -> CrossPlatformMetric:
        er = round(engagement / max(1, impressions) * 100, 2)
        ctr = round(clicks / max(1, impressions) * 100, 2)
        cr = round(conversions / max(1, clicks) * 100, 2)
        roi = round((revenue - ad_spend) / max(1, ad_spend) * 100, 1)
        repo = Repository(self.session, CrossPlatformMetric)
        return await repo.create(platform=platform, campaign_id=campaign_id, impressions=impressions, reach=reach, engagement=engagement, clicks=clicks, conversions=conversions, revenue=revenue, ad_spend=ad_spend, engagement_rate=er, ctr=ctr, conversion_rate=cr, roi=roi)

    async def load_cross_platform_metrics(self, campaign_id: str = "", platform: str = "", limit: int = 100) -> list[CrossPlatformMetric]:
        repo = Repository(self.session, CrossPlatformMetric)
        filters = {}
        if campaign_id: filters["campaign_id"] = campaign_id
        if platform: filters["platform"] = platform
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Batch Jobs ─────────────────────────────────────────────
    async def save_batch_job(self, status: str = "pending", total_items: int = 0, processed: int = 0, successful: int = 0, failed: int = 0, items: list[dict] | None = None, results: list[dict] | None = None, errors: list[dict] | None = None, concurrency: int = 3, delay_between: float = 1.0) -> BatchJob:
        repo = Repository(self.session, BatchJob)
        return await repo.create(status=status, total_items=total_items, processed=processed, successful=successful, failed=failed, items=items or [], results=results or [], errors=errors or [], concurrency=concurrency, delay_between=delay_between)

    async def load_batch_jobs(self, status: str = "", limit: int = 50) -> list[BatchJob]:
        repo = Repository(self.session, BatchJob)
        return await repo.find(status=status) if status else await repo.list_all(limit=limit)

    # ── Auto Reports ───────────────────────────────────────────
    async def save_auto_report(self, report_type: str = "weekly", period: str = "", score: int = 0, summary: str = "", sections: list[dict] | None = None) -> AutoReport:
        repo = Repository(self.session, AutoReport)
        return await repo.create(report_type=report_type, period=period, score=score, summary=summary, sections=sections or [])

    async def load_auto_reports(self, report_type: str = "", limit: int = 20) -> list[AutoReport]:
        repo = Repository(self.session, AutoReport)
        return await repo.find(report_type=report_type) if report_type else await repo.list_all(limit=limit)

    # ── Voice Profiles ─────────────────────────────────────────
    async def save_voice_profile(self, name: str = "", style: str = "enthusiastic", characteristics: dict | None = None, sample_duration: float = 0.0, languages: list[str] | None = None) -> VoiceProfile:
        repo = Repository(self.session, VoiceProfile)
        return await repo.create(name=name, style=style, characteristics=characteristics or {}, sample_duration=sample_duration, languages=languages or [])

    async def load_voice_profiles(self, limit: int = 50) -> list[VoiceProfile]:
        repo = Repository(self.session, VoiceProfile)
        return await repo.list_all(limit=limit)

    # ── Webhook Configs ────────────────────────────────────────
    async def save_webhook_config(self, name: str = "", url: str = "", platform: str = "discord", events: list[str] | None = None, enabled: bool = True) -> WebhookConfig:
        repo = Repository(self.session, WebhookConfig)
        return await repo.create(name=name, url=url, platform=platform, events=events or [], enabled=enabled)

    async def load_webhook_configs(self, enabled: bool = True, limit: int = 50) -> list[WebhookConfig]:
        repo = Repository(self.session, WebhookConfig)
        return await repo.find(enabled=enabled)

    # ── Affiliate Accounts ─────────────────────────────────────
    async def save_affiliate_account(self, name: str = "", platform: str = "", status: str = "active", commission_rate: float = 0.0, total_earnings: float = 0.0, total_clicks: int = 0, total_conversions: int = 0) -> AffiliateAccount:
        repo = Repository(self.session, AffiliateAccount)
        return await repo.create(name=name, platform=platform, status=status, commission_rate=commission_rate, total_earnings=total_earnings, total_clicks=total_clicks, total_conversions=total_conversions)

    async def load_affiliate_accounts(self, platform: str = "", status: str = "", limit: int = 50) -> list[AffiliateAccount]:
        repo = Repository(self.session, AffiliateAccount)
        filters = {}
        if platform: filters["platform"] = platform
        if status: filters["status"] = status
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Influencer Profiles ────────────────────────────────────
    async def save_influencer_profile(self, name: str = "", platform: str = "", niche: str = "", followers: int = 0, engagement_rate: float = 0.0, content_type: str = "", collaboration_cost: float = 0.0, relevance_score: float = 0.0) -> InfluencerProfile:
        repo = Repository(self.session, InfluencerProfile)
        return await repo.create(name=name, platform=platform, niche=niche or None, followers=followers, engagement_rate=engagement_rate, content_type=content_type or None, collaboration_cost=collaboration_cost, relevance_score=relevance_score)

    async def load_influencer_profiles(self, niche: str = "", platform: str = "", limit: int = 50) -> list[InfluencerProfile]:
        repo = Repository(self.session, InfluencerProfile)
        filters = {}
        if niche: filters["niche"] = niche
        if platform: filters["platform"] = platform
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Budget Allocations ─────────────────────────────────────
    async def save_budget_allocation(self, campaign_id: str = "", platform: str = "", current_budget: float = 0.0, recommended_budget: float = 0.0, roi: float = 0.0, priority: str = "medium", reason: str = "") -> BudgetAllocation:
        repo = Repository(self.session, BudgetAllocation)
        return await repo.create(campaign_id=campaign_id, platform=platform, current_budget=current_budget, recommended_budget=recommended_budget, roi=roi, priority=priority, reason=reason)

    async def load_budget_allocations(self, limit: int = 50) -> list[BudgetAllocation]:
        repo = Repository(self.session, BudgetAllocation)
        return await repo.list_all(limit=limit)

    # ── Competitor Watches ─────────────────────────────────────
    async def save_competitor_watch(self, competitor_name: str = "", platform: str = "", url: str = "", status: str = "active", metrics: dict | None = None, alerts: list[str] | None = None) -> CompetitorWatch:
        repo = Repository(self.session, CompetitorWatch)
        return await repo.create(competitor_name=competitor_name, platform=platform, url=url, status=status, metrics=metrics or {}, alerts=alerts or [])

    async def load_competitor_watches(self, platform: str = "", status: str = "active", limit: int = 50) -> list[CompetitorWatch]:
        repo = Repository(self.session, CompetitorWatch)
        filters = {"status": status}
        if platform: filters["platform"] = platform
        return await repo.find(**filters)

    # ── Content Remix ──────────────────────────────────────────
    async def save_content_remix(self, source_content: str = "", platform: str = "", format_type: str = "", content_text: str = "", char_count: int = 0, viral_score: int = 0, hashtags: list[str] | None = None, cta_text: str = "") -> ContentRemix:
        repo = Repository(self.session, ContentRemix)
        return await repo.create(source_content=source_content, platform=platform, format_type=format_type, content_text=content_text, char_count=char_count, viral_score=viral_score, hashtags=hashtags or [], cta_text=cta_text)

    async def load_content_remixes(self, platform: str = "", limit: int = 50) -> list[ContentRemix]:
        repo = Repository(self.session, ContentRemix)
        return await repo.find(platform=platform) if platform else await repo.list_all(limit=limit)

    # ── Compliance Checks ──────────────────────────────────────
    async def save_compliance_check(self, content_text: str = "", platform: str = "tiktok", passed: bool = True, score: int = 100, issues: list[dict] | None = None, affiliate_disclosed: bool = True) -> ComplianceCheck:
        repo = Repository(self.session, ComplianceCheck)
        return await repo.create(content_text=content_text, platform=platform, passed=passed, score=score, issues=issues or [], affiliate_disclosed=affiliate_disclosed)

    async def load_compliance_checks(self, platform: str = "", passed: bool | None = None, limit: int = 50) -> list[ComplianceCheck]:
        repo = Repository(self.session, ComplianceCheck)
        filters = {}
        if platform: filters["platform"] = platform
        if passed is not None: filters["passed"] = passed
        return await repo.find(**filters) if filters else await repo.list_all(limit=limit)

    # ── Alert Rules ────────────────────────────────────────────
    async def save_alert_rule(self, name: str = "", metric: str = "", condition: str = "", threshold: float = 0.0, platform: str = "", campaign_id: str = "", enabled: bool = True, cooldown_minutes: int = 60) -> AlertRule:
        repo = Repository(self.session, AlertRule)
        return await repo.create(name=name, metric=metric, condition=condition, threshold=threshold, platform=platform, campaign_id=campaign_id, enabled=enabled, cooldown_minutes=cooldown_minutes)

    async def load_alert_rules(self, enabled: bool | None = None, limit: int = 50) -> list[AlertRule]:
        repo = Repository(self.session, AlertRule)
        if enabled is not None: return await repo.find(enabled=enabled)
        return await repo.list_all(limit=limit)

    # ── Revenue Forecasts ──────────────────────────────────────
    async def save_revenue_forecast(self, period: str = "30d", predicted_revenue: float = 0.0, predicted_roi: float = 0.0, confidence: float = 0.0, trend: str = "stable", daily_average: float = 0.0, best_day: str = "", worst_day: str = "", recommendations: list[str] | None = None) -> RevenueForecast:
        repo = Repository(self.session, RevenueForecast)
        return await repo.create(period=period, predicted_revenue=predicted_revenue, predicted_roi=predicted_roi, confidence=confidence, trend=trend, daily_average=daily_average, best_day=best_day, worst_day=worst_day, recommendations=recommendations or [])

    async def load_revenue_forecasts(self, period: str = "", limit: int = 20) -> list[RevenueForecast]:
        repo = Repository(self.session, RevenueForecast)
        return await repo.find(period=period) if period else await repo.list_all(limit=limit)

    # ── Smart Schedule Slots ───────────────────────────────────
    async def save_smart_schedule_slot(self, platform: str = "", hour: int = 12, day_of_week: str = "any", avg_engagement: float = 0.0, post_count: int = 0, score: float = 0.0) -> SmartScheduleSlot:
        repo = Repository(self.session, SmartScheduleSlot)
        return await repo.create(platform=platform, hour=hour, day_of_week=day_of_week, avg_engagement=avg_engagement, post_count=post_count, score=score)

    async def load_smart_schedule_slots(self, platform: str = "", limit: int = 50) -> list[SmartScheduleSlot]:
        repo = Repository(self.session, SmartScheduleSlot)
        return await repo.find(platform=platform) if platform else await repo.list_all(limit=limit)
