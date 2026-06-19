"""CEO Agent -- orchestrates the entire TITAN AIO workflow with MessageBus."""

from __future__ import annotations

from typing import Any

from Database.connection import async_session_factory
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import (
    AffiliatePackageOutput,
    AnalyzeProductOutput,
    GenerateHooksOutput,
    GenerateScriptOutput,
    GenerateThumbnailOutput,
    GenerateImageOutput,
)
from Services.agents.message_bus import get_bus
from Services.agents.affiliate import AffiliateAgent
from Services.agents.analytics import AnalyticsAgent
from Services.agents.asset import AssetAgent
from Services.agents.avatar import AvatarAgent
from Services.agents.campaign_builder import CampaignBuilder
from Services.agents.competitor import CompetitorAgent
from Services.agents.creative import CreativeAgent
from Services.agents.finance import FinanceAgent
from Services.agents.growth import GrowthAgent
from Services.agents.knowledge import KnowledgeAgent
from Services.agents.memory import MemoryAgent
from Services.agents.offer import OfferAgent
from Services.agents.product import ProductAgent
from Services.agents.publisher import PublisherAgent
from Services.agents.review import ReviewAgent
from Services.agents.trend import TrendAgent
from Services.agents.ugc import UGCAgent
from Services.agents.video import VideoAgent


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
    """CEO Agent -- orchestrates using MessageBus for agent communication."""

    def __init__(self) -> None:
        self.product = ProductAgent("ProductAgent")
        self.review = ReviewAgent("ReviewAgent")
        self.ugc = UGCAgent("UGCAgent")
        self.creative = CreativeAgent("CreativeAgent")
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

    async def create_affiliate_package(self, url: str, include_video: bool = False, include_avatar: bool = False) -> AffiliatePackageOutput:
        """Orchestrate the full affiliate package pipeline with MessageBus events."""
        bus = get_bus()

        # 1. Product analysis
        product_data = await self.product(url=url)
        bus.publish("product.analyzed", product_data, "ProductAgent")
        product = AnalyzeProductOutput(
            product_id=product_data.get("product_id", ""),
            title=product_data.get("title", ""),
            price=product_data.get("price", 0),
            currency=product_data.get("currency", "IDR"),
            rating=product_data.get("rating"),
            total_sales=product_data.get("total_sales"),
            category=product_data.get("category"),
            commission_estimate=product_data.get("price", 0) * 0.05,
            competition_level=product_data.get("competition_level", "medium"),
            product_score=product_data.get("product_score", 0),
            url=product_data.get("url", ""),
        )

        # 2. Reviews
        reviews = await self.review(product_id=product.product_id)
        bus.publish("reviews.analyzed", {"product_id": product.product_id, "count": reviews.total_reviews_analyzed}, "ReviewAgent")

        # 3. Competitors
        competitors = await self.competitor(category=product.category or "umum")
        bus.publish("competitors.analyzed", {"category": product.category, "count": competitors.competitors_analyzed}, "CompetitorAgent")

        # 4. Offer
        offer = await self.offer(product=product, reviews=reviews, competitors=competitors)
        bus.publish("offer.created", {"product_id": product.product_id, "angle": offer.primary_angle}, "OfferAgent")

        # 5. UGC
        ugc_result = await self.ugc(product_id=product.product_id, offer_strategy=offer)
        bus.publish("ugc.generated", {"product_id": product.product_id, "hooks": len(ugc_result.get("hooks", GenerateHooksOutput(product_id="")).hooks)}, "UGCAgent")

        # 6. Creative
        creative_result = await self.creative(product_id=product.product_id)
        bus.publish("creative.generated", {"product_id": product.product_id}, "CreativeAgent")

        hooks_output = ugc_result.get("hooks", GenerateHooksOutput(product_id=product.product_id))
        scripts_output = ugc_result.get("scripts", GenerateScriptOutput(product_id=product.product_id))
        thumbnail_output = creative_result.get("thumbnail", GenerateThumbnailOutput(product_id=product.product_id))
        image_output = GenerateImageOutput(image_url="", model_used="flux-schnell", seed=0)

        result = AffiliatePackageOutput(
            product=product, review_summary=reviews, competitor_analysis=competitors,
            offer_strategy=offer, hooks=hooks_output, scripts=scripts_output,
            thumbnail=thumbnail_output, image=image_output,
        )

        # Phase 3
        if include_video and scripts_output.scripts:
            video_result = await self.video(script=scripts_output.scripts[0].full_script)
            result.video = _SimpleVideoOutput(video_result["url"], video_result["model_used"], video_result["duration_seconds"])
            bus.publish("video.generated", {"url": video_result["url"]}, "VideoAgent")

        if include_avatar:
            avatar_result = await self.avatar(name="AI Spokesperson")
            result.avatar = _SimpleAvatarOutput(avatar_result["avatar_id"], avatar_result.get("image_url", ""), avatar_result["persona"])

        # Save
        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            campaign = await repo.create(product_id=product.product_id, name=f"Campaign - {product.title[:50]}", status="active")
            result.campaign_id = campaign.id
            await session.commit()

        bus.publish("campaign.created", {"campaign_id": result.campaign_id, "product": product.title}, "CEOAgent")
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
