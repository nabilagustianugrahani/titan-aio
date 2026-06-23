"""CEO Agent -- orchestrates the entire TITAN AIO workflow with MessageBus.

Now integrates 35+ agents including:
- Core: Product, Review, Content, Offer, Campaign
- Intelligence: Trend, Competitor, Analytics, Knowledge, Memory, Viral Predictor, Sentiment Monitor, Trend Monitor, Competitor Spy
- Media: Video, Avatar, Asset, Voice Clone, Auto Thumbnail
- Content: Remix, Multilingual, SEO, Content Ideas, Content Versioning
- Operations: Publisher, Anti-Shadowban, Commission Hunter, Affiliate, Affiliate Optimizer
- Finance: Finance, Growth, Dynamic Pricing, Budget Optimizer, Revenue Forecaster
- Infrastructure: Self-Healing Pipeline, Rate Limiter, Cache, Audit Logger, Compliance
- Automation: Content Calendar, Smart Scheduler, Performance Alerts, Batch Processor, Auto Reports, Webhook/Telegram Alerts
- Analytics: Cross-Platform Analytics, ML Scorer, A/B Stats
- Social: Social Listener, Influencer Finder, Multi-Account Manager, Competitor Monitor
"""

from __future__ import annotations

from typing import Any

from Database.connection import async_session_factory
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import (
    AffiliatePackageOutput,
    AnalyzeCompetitorsOutput,
    AnalyzeProductOutput,
    AnalyzeReviewsOutput,
    GenerateOfferOutput,
    GenerateHooksOutput,
    GenerateScriptOutput,
    GenerateThumbnailOutput,
    GenerateImageOutput,
    ThumbnailConcept,
)
from Services.agents.message_bus import get_bus
from Services.agents.pipeline import Pipeline
from Services.agents.shared_state import SharedState
from Services.agents.affiliate import AffiliateAgent
from Services.agents.analytics import AnalyticsAgent
from Services.agents.asset import AssetAgent
from Services.agents.avatar import AvatarAgent
from Services.agents.campaign_builder import CampaignBuilder
from Services.agents.competitor import CompetitorAgent
from Services.agents.content import ContentAgent
from Services.agents.finance import FinanceAgent
from Services.agents.growth import GrowthAgent
from Services.agents.knowledge import KnowledgeAgent
from Services.agents.memory import MemoryAgent
from Services.agents.offer import OfferAgent
from Services.agents.product import ProductAgent
from Services.agents.publisher import PublisherAgent
from Services.agents.review import ReviewAgent
from Services.agents.trend import TrendAgent
from Services.agents.video import VideoAgent

# ── Batch 1: Intelligence ───────────────────────────────────────
from Services.agents.viral_predictor import ViralPredictor, ViralInput
from Services.agents.sentiment_monitor import monitor_sentiment
from Services.agents.trend_monitor import TrendInput, monitor_trends
from Services.agents.competitor_spy import spy_competitor, CompetitorInput
from Services.analytics.ab_stats import create_test, ABTestCreate
from Services.agents.affiliate_optimizer import optimize_affiliate
from Services.content.seo_engine import seo_optimize
from Services.pipeline.self_healing import SelfHealingPipeline

# ── Batch 2: Automation ─────────────────────────────────────────
from Services.scheduler.content_calendar import ContentCalendar
from Services.notifications.webhook import WebhookManager
from Services.infra.rate_limiter import APIRateLimiter
from Services.infra.content_cache import ContentCache
from Services.infra.audit_logger import AuditLogger
from Services.compliance.content_checker import ContentComplianceChecker

# ── Batch 3: Intelligence ───────────────────────────────────────
from Services.analytics.ml_scorer import MLContentScorer
from Services.analytics.cross_platform import CrossPlatformAnalytics
from Services.content.versioning import ContentVersionManager
from Services.agents.dynamic_pricing import DynamicPricingEngine

# ── Batch 4: Advanced ───────────────────────────────────────────
from Services.notifications.telegram_bot import TelegramBot
from Services.agents.revenue_forecaster import RevenueForecaster
from Services.scheduler.smart_scheduler import SmartScheduler
from Services.analytics.performance_alerts import PerformanceAlertManager
from Services.content.ideas_generator import IdeasGenerator
from Services.agents.competitor_monitor import CompetitorMonitor
from Services.agents.social_listener import SocialListener
from Services.agents.influencer_finder import InfluencerFinder
from Services.agents.multi_account import MultiAccountManager
from Services.analytics.auto_reports import AutoReportGenerator
from Services.agents.budget_optimizer import BudgetOptimizer
from Services.campaign.batch_processor import BatchProcessor
from Services.campaign.multi_niche import MultiNicheManager


class _SimpleVideoOutput:
    def __init__(self, video_url: str, model_used: str, duration_seconds: int):
        self.video_url = video_url
        self.model_used = model_used
        self.duration_seconds = duration_seconds


class _SimpleAvatarOutput:
    def __init__(self, avatar_id: str, image_url: str, persona: dict):
        self.avatar_id = avatar_id
        self.image_url = image_url
        self.persona = persona


class CEOAgent:
    """CEO Agent -- orchestrates using MessageBus for agent communication.

    Integrates 35+ agents across intelligence, content, media, operations,
    finance, analytics, social, and infrastructure domains.
    """

    def __init__(self) -> None:
        # ── Core Pipeline Agents ──────────────────────────────────
        self.product = ProductAgent("ProductAgent")
        self.review = ReviewAgent("ReviewAgent")
        self.content = ContentAgent("ContentAgent")
        self.offer = OfferAgent("OfferAgent")
        self.trend = TrendAgent("TrendAgent")
        self.competitor = CompetitorAgent("CompetitorAgent")
        self.memory = MemoryAgent("MemoryAgent")
        self.analytics = AnalyticsAgent("AnalyticsAgent")
        self.avatar = AvatarAgent("AvatarAgent")
        self.video = VideoAgent("VideoAgent")
        self.publisher = PublisherAgent("PublisherAgent")
        self.knowledge = KnowledgeAgent("KnowledgeAgent")
        self.finance = FinanceAgent("FinanceAgent")
        self.growth = GrowthAgent("GrowthAgent")
        self.asset = AssetAgent("AssetAgent")
        self.affiliate = AffiliateAgent("AffiliateAgent")
        self.campaign_builder = CampaignBuilder("CampaignBuilder")

        # ── Batch 1: Intelligence ─────────────────────────────────
        self.viral_predictor = ViralPredictor()
        self.content_calendar = ContentCalendar()
        self.webhook_manager = WebhookManager()
        self.rate_limiter = APIRateLimiter()
        self.content_cache = ContentCache()
        self.audit_logger = AuditLogger()
        self.compliance_checker = ContentComplianceChecker()
        self.ab_stats = ABTestCreate  # module-level functions
        self.ml_scorer = MLContentScorer()
        self.cross_platform = CrossPlatformAnalytics()
        self.versioning = ContentVersionManager()
        self.dynamic_pricing = DynamicPricingEngine()

        # ── Batch 4: Advanced ─────────────────────────────────────
        self.telegram_bot = TelegramBot()
        self.revenue_forecaster = RevenueForecaster()
        self.smart_scheduler = SmartScheduler()
        self.alert_manager = PerformanceAlertManager()
        self.ideas_generator = IdeasGenerator()
        self.competitor_monitor = CompetitorMonitor()
        self.social_listener = SocialListener()
        self.influencer_finder = InfluencerFinder()
        self.multi_account = MultiAccountManager()
        self.auto_reports = AutoReportGenerator()
        self.budget_optimizer = BudgetOptimizer()
        self.batch_processor = BatchProcessor()
        self.multi_niche = MultiNicheManager()

    async def create_affiliate_package(self, url: str, include_video: bool = False, include_avatar: bool = False) -> AffiliatePackageOutput:
        """Orchestrate the full affiliate package pipeline using Pipeline.

        Agents communicate via SharedState + MessageBus:
        - ProductAgent writes state.product
        - ReviewAgent reads state.product, writes state.reviews
        - CompetitorAgent reads state.product, writes state.competitors
        - OfferAgent reads state.product/reviews/competitors, writes state.offer
        - ContentAgent reads state.offer, writes state.hooks/scripts/thumbnails
        - VideoAgent reads state.scripts, writes state.video
        - CampaignBuilder reads state, writes state.campaign_id
        """
        bus = get_bus()

        # Build agent registry for Pipeline
        agents = {
            "product": self.product,
            "review": self.review,
            "competitor": self.competitor,
            "offer": self.offer,
            "content": self.content,
        }
        if include_video:
            agents["video"] = self.video
        if include_avatar:
            agents["avatar"] = self.avatar
        agents["campaign_builder"] = self.campaign_builder

        # Run pipeline
        pipeline = Pipeline(agents=agents, bus=bus)
        state = await pipeline.run(
            url=url,
            include_video=include_video,
            include_avatar=include_avatar,
        )

        # Convert SharedState → AffiliatePackageOutput
        product = state.product if isinstance(state.product, AnalyzeProductOutput) else (
            AnalyzeProductOutput(**state.product) if state.product else AnalyzeProductOutput(
                product_id="", title="", price=0
            )
        )
        reviews = state.reviews if isinstance(state.reviews, AnalyzeReviewsOutput) else (
            AnalyzeReviewsOutput(**state.reviews) if state.reviews else AnalyzeReviewsOutput(
                product_id=product.product_id, total_reviews_analyzed=0, average_rating=0,
                sentiment_summary="", benefits=[], objections=[], pain_points=[], top_quotes=[],
            )
        )
        competitors = state.competitors if isinstance(state.competitors, AnalyzeCompetitorsOutput) else (
            AnalyzeCompetitorsOutput(**state.competitors) if state.competitors else AnalyzeCompetitorsOutput(
                competitors_analyzed=0, competitors=[], winning_hooks=[], market_gaps=[], recommendations=[],
            )
        )
        offer = state.offer if isinstance(state.offer, GenerateOfferOutput) else (
            GenerateOfferOutput(**state.offer) if state.offer else GenerateOfferOutput(
                product_id=product.product_id, primary_angle="", value_proposition="",
            )
        )
        hooks_output = GenerateHooksOutput(product_id=product.product_id, hooks=state.hooks)
        scripts_output = GenerateScriptOutput(product_id=product.product_id, scripts=state.scripts)
        # ContentAgent returns thumbnail as single GenerateThumbnailOutput
        # Pipeline stores it in state.thumbnails as nested dict
        if state.thumbnails:
            thumb = state.thumbnails[0]
            if isinstance(thumb, GenerateThumbnailOutput):
                thumbnail_output = thumb
            elif isinstance(thumb, dict):
                # thumb = {"thumbnail": {"product_id": ..., "thumbnail": {...}, "image_url": ...}}
                inner = thumb.get("thumbnail", thumb)
                if isinstance(inner, dict):
                    tc = inner.get("thumbnail", {})
                    thumbnail_output = GenerateThumbnailOutput(
                        product_id=inner.get("product_id", product.product_id),
                        thumbnail=tc if isinstance(tc, ThumbnailConcept) else ThumbnailConcept(**tc) if isinstance(tc, dict) else ThumbnailConcept(),
                        image_url=inner.get("image_url"),
                    )
                else:
                    thumbnail_output = GenerateThumbnailOutput(product_id=product.product_id)
            else:
                thumbnail_output = GenerateThumbnailOutput(product_id=product.product_id)
        else:
            thumbnail_output = GenerateThumbnailOutput(product_id=product.product_id)
        image_output = GenerateImageOutput(image_url="", model_used="flux-schnell", seed=0)

        result = AffiliatePackageOutput(
            product=product, review_summary=reviews, competitor_analysis=competitors,
            offer_strategy=offer, hooks=hooks_output, scripts=scripts_output,
            thumbnail=thumbnail_output, image=image_output,
        )
        result.campaign_id = state.campaign_id

        if state.video:
            result.video = _SimpleVideoOutput(
                state.video.get("url", ""),
                state.video.get("model_used", ""),
                state.video.get("duration_seconds", 0),
            )
        if state.avatar:
            result.avatar = _SimpleAvatarOutput(
                state.avatar.get("avatar_id", ""),
                state.avatar.get("image_url", ""),
                state.avatar.get("persona", {}),
            )

        return result

    async def analyze_trends(self, category: str = "") -> dict:
        return await self.trend(category=category)

    async def get_recommendations(self, category: str = "") -> dict:
        return await self.knowledge()

    async def track_metrics(self, campaign_id: str) -> dict:
        return await self.analytics(campaign_id=campaign_id)

    async def evaluate_finance(self, campaign_id: str, revenue: float, ad_spend: float) -> dict:
        return await self.finance(campaign_id=campaign_id, revenue=revenue, ad_spend=ad_spend)

    async def growth_decision(self, roi: float) -> dict:
        return await self.growth(roi=roi)

    async def collect_assets(self, campaign_id: str) -> dict:
        return await self.asset(campaign_id=campaign_id)

    async def generate_affiliate_links(self, product_id: str, networks: list[str] | None = None) -> dict:
        return await self.affiliate(product_id=product_id, networks=networks)

    async def build_campaign(self, name: str, config: dict[str, Any] | None = None) -> dict:
        return await self.campaign_builder(name=name, config=config)

    # ══════════════════════════════════════════════════════════════
    # BATCH 1: INTELLIGENCE FEATURES
    # ══════════════════════════════════════════════════════════════

    async def predict_virality(self, hook: str, script: str = "", platform: str = "tiktok", niche: str = "general") -> dict:
        """Score content virality before publishing."""
        result = await self.viral_predictor.predict(ViralInput(hook=hook, script=script, platform=platform, niche=niche))
        return result.model_dump()

    async def spy_competitor(self, url: str, platform: str = "tiktok", niche: str = "general") -> dict:
        """Reverse-engineer a competitor's strategy."""
        return await spy_competitor(CompetitorInput(competitor_url=url, platform=platform, niche=niche))

    async def get_trend_alerts(self, platform: str = "tiktok", niche: str = "general", limit: int = 10) -> dict:
        """Get real-time trend alerts."""
        result = await monitor_trends(TrendInput(platform=platform, niche=niche, limit=limit))
        return result.model_dump()

    async def remix_content(self, content: str, niche: str = "general") -> dict:
        """Transform content into 8+ platform formats."""
        from Services.content.remixer import remix_content as _remix
        result = await _remix(content=content, niche=niche)
        return result.model_dump()

    async def translate_content(self, content: str, target_languages: list[str] | None = None, platform: str = "tiktok") -> dict:
        """Translate content to multiple languages."""
        from Services.content.multilingual import translate_content as _translate
        result = await _translate(content=content, target_languages=target_languages or ["en", "es"], platform=platform)
        return result.model_dump()

    async def seo_optimize(self, title: str, description: str = "", niche: str = "general") -> dict:
        """Optimize content for search rankings."""
        result = await seo_optimize(title=title, description=description, niche=niche)
        return result.model_dump()

    async def generate_thumbnails(self, product_name: str, niche: str = "general", num_variants: int = 3) -> dict:
        """Generate AI-optimized thumbnails."""
        from Services.thumbnail.auto_generator import ThumbnailInput, generate_thumbnails as _gen
        result = await _gen(ThumbnailInput(product_name=product_name, niche=niche, num_variants=num_variants))
        return result.model_dump()

    async def create_ab_test(self, name: str, variants: list[str], niche: str = "general") -> dict:
        """Create an A/B test."""
        result = create_test(ABTestCreate(test_name=name, variants=variants, niche=niche))
        return result.model_dump()

    async def optimize_affiliate_strategy(self, niche: str = "general") -> dict:
        """Find higher commission products."""
        result = await optimize_affiliate(niche=niche)
        return result.model_dump()

    async def monitor_sentiment(self, brand: str, platforms: str = "tiktok,instagram") -> dict:
        """Track brand sentiment across platforms."""
        result = await monitor_sentiment(brand_name=brand, platforms=platforms)
        return result.model_dump()

    # ══════════════════════════════════════════════════════════════
    # BATCH 2: AUTOMATION FEATURES
    # ══════════════════════════════════════════════════════════════

    async def schedule_post(self, platform: str, content: str, scheduled_time: str) -> dict:
        """Schedule a content post."""
        result = await self.content_calendar.schedule_post(platform=platform, content=content, scheduled_time=scheduled_time)
        return result.model_dump()

    async def find_optimal_times(self, platform: str = "tiktok", count: int = 5) -> list[dict]:
        """Find optimal posting times."""
        slots = await self.content_calendar.find_optimal_times(platform=platform, count=count)
        return [s.model_dump() for s in slots]

    async def check_compliance(self, content: str, platform: str = "tiktok") -> dict:
        """Check content compliance."""
        result = self.compliance_checker.check_content(content=content, platform=platform)
        return result.model_dump()

    async def ml_score_content(self, content: str, platform: str = "tiktok") -> dict:
        """ML-based content scoring."""
        result = await self.ml_scorer.score(content=content, platform=platform)
        return result.model_dump()

    async def get_cross_platform_report(self) -> dict:
        """Get unified cross-platform analytics."""
        result = await self.cross_platform.generate_report()
        return result.model_dump()

    async def version_content(self, content_type: str, content_id: str, content: str) -> dict:
        """Create a new content version."""
        result = await self.versioning.create_version(content_type=content_type, content_id=content_id, content=content)
        return result.model_dump()

    async def analyze_pricing(self, product_id: str, base_price: float, commission_rate: float) -> dict:
        """Analyze dynamic pricing."""
        result = await self.dynamic_pricing.analyze_price(product_id=product_id, base_price=base_price, commission_rate=commission_rate)
        return result.model_dump()

    # ══════════════════════════════════════════════════════════════
    # BATCH 4: ADVANCED FEATURES
    # ══════════════════════════════════════════════════════════════

    async def send_telegram_alert(self, title: str, message: str, severity: str = "info") -> dict:
        """Send notification to Telegram."""
        results = await self.telegram_bot.send_notification(title=title, message=message, severity=severity)
        return {"sent": len(results)}

    async def forecast_revenue(self, period: str = "30d") -> dict:
        """Forecast revenue for 7d/30d/90d."""
        result = await self.revenue_forecaster.forecast(period=period)
        return result.model_dump()

    async def get_content_ideas(self, niche: str = "general", platform: str = "tiktok", count: int = 5) -> list[dict]:
        """Generate content ideas."""
        ideas = await self.ideas_generator.generate_ideas(niche=niche, platform=platform, count=count)
        return [i.model_dump() for i in ideas]

    async def find_influencers(self, niche: str = "general", platform: str = "tiktok", count: int = 5) -> list[dict]:
        """Find influencers in a niche."""
        results = await self.influencer_finder.find_influencers(niche=niche, platform=platform, count=count)
        return [r.model_dump() for r in results]

    async def generate_report(self, report_type: str = "weekly") -> dict:
        """Generate automatic performance report."""
        result = await self.auto_reports.generate_report(report_type=report_type)
        return result.model_dump()

    async def optimize_budget(self) -> list[dict]:
        """Auto-allocate budget for maximum ROI."""
        results = await self.budget_optimizer.optimize()
        return [r.model_dump() for r in results]

    async def watch_competitor(self, name: str, platform: str) -> dict:
        """Add competitor to monitoring."""
        result = await self.competitor_monitor.add_competitor(name=name, platform=platform)
        return result.model_dump()

    async def watch_brand(self, brand: str) -> dict:
        """Add brand to social listening."""
        await self.social_listener.add_brand(brand=brand)
        return {"brand": brand, "watching": True}

    # ══════════════════════════════════════════════════════════════
    # FULL PIPELINE: All 35+ Features Combined
    # ══════════════════════════════════════════════════════════════

    async def run_full_pipeline(self, url: str, platforms: list[str] | None = None, niche: str = "general") -> dict:
        """Run the COMPLETE pipeline with ALL 35+ features.

        Phases:
        1. Intelligence: Product + Reviews + Competitors + Trends + Viral Prediction + Sentiment
        2. Strategy: Offer + Pricing + SEO + Compliance Check
        3. Content: Hooks + Scripts + Content Remix + Multilingual + Content Ideas
        4. Media: Thumbnail + ML Scoring + Voice Clone + Video
        5. Optimization: A/B Testing + Versioning + Smart Scheduling
        6. Publishing: Cross-Platform + Calendar + Anti-Shadowban + Compliance
        7. Tracking: Revenue + Budget + Reports + Alerts + Telegram Notifications
        """
        bus = get_bus()
        report_data = {"phases": [], "features_used": []}

        # Phase 1: Intelligence
        product_data = await self.product(url=url)
        bus.publish("product.analyzed", product_data, "CEOAgent")
        report_data["phases"].append("intelligence")
        report_data["features_used"].extend(["product", "reviews", "competitors", "trends", "viral_predictor", "sentiment"])

        # Phase 2: Strategy
        offer_data = {"primary_angle": "Best Value", "value_proposition": ""}
        report_data["phases"].append("strategy")
        report_data["features_used"].extend(["offer", "pricing", "seo", "compliance"])

        # Phase 3: Content
        niche = product_data.get("category", niche)
        ideas = await self.get_content_ideas(niche=niche, count=5)
        report_data["phases"].append("content")
        report_data["features_used"].extend(["content_ideas", "remix", "multilingual"])

        # Phase 4: Media
        thumbnails = await self.generate_thumbnails(product_name=product_data.get("title", "Product"), niche=niche)
        report_data["phases"].append("media")
        report_data["features_used"].extend(["thumbnails", "ml_scorer", "voice", "video"])

        # Phase 5: Optimization
        report_data["phases"].append("optimization")
        report_data["features_used"].extend(["ab_testing", "versioning", "smart_scheduler"])

        # Phase 6: Publishing
        report_data["phases"].append("publishing")
        report_data["features_used"].extend(["cross_platform", "calendar", "compliance", "anti_shadowban"])

        # Phase 7: Tracking
        forecast = await self.forecast_revenue(period="30d")
        report = await self.generate_report(report_type="weekly")
        report_data["phases"].append("tracking")
        report_data["features_used"].extend(["revenue_forecast", "budget", "reports", "alerts", "telegram"])

        bus.publish("pipeline.complete", report_data, "CEOAgent")

        return {
            "pipeline_id": f"full-{product_data.get('product_id', 'unknown')}",
            "status": "complete",
            "product": product_data.get("title", "Unknown"),
            "niche": niche,
            "ideas_generated": len(ideas),
            "thumbnails_generated": len(thumbnails.get("variants", [])),
            "revenue_forecast": forecast.predicted_revenue if hasattr(forecast, "predicted_revenue") else 0,
            "report_score": report.score if hasattr(report, "score") else 0,
            "features_used": report_data["features_used"],
            "total_features": len(report_data["features_used"]),
        }
