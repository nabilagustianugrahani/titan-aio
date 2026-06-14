"""CEO Agent -- orchestrates the entire TITAN AIO workflow."""

from __future__ import annotations

from typing import Any

from Database.connection import async_session_factory
from Database.models import Campaign
from Database.repository import Repository
from MCP.schemas import (
    AffiliatePackageOutput,
    GenerateHooksOutput,
    GenerateScriptOutput,
    GenerateThumbnailOutput,
    GenerateImageOutput,
)
from Services.agents.product import ProductAgent
from Services.agents.review import ReviewAgent
from Services.agents.ugc import UGCAgent
from Services.agents.creative import CreativeAgent
from Services.agents.offer import OfferAgent
from Services.agents.trend import TrendAgent
from Services.agents.competitor import CompetitorAgent
from Services.agents.avatar import AvatarAgent
from Services.agents.video import VideoAgent
from Services.agents.publisher import PublisherAgent
from Services.agents.analytics import AnalyticsAgent
from Services.agents.memory import MemoryAgent
from Services.agents.knowledge import KnowledgeAgent
from Services.agents.finance import FinanceAgent
from Services.agents.growth import GrowthAgent


class _SimpleVideoOutput:
    """Simple output object for video results."""

    def __init__(self, video_url: str, model_used: str, duration_seconds: int):
        self.video_url = video_url
        self.model_used = model_used
        self.duration_seconds = duration_seconds


class _SimpleAvatarOutput:
    """Simple output object for avatar results."""

    def __init__(self, avatar_id: str, image_url: str, persona: dict):
        self.avatar_id = avatar_id
        self.image_url = image_url
        self.persona = persona


class CEOAgent:
    """CEO Agent -- strategic orchestrator for TITAN AIO."""

    def __init__(self) -> None:
        # Core agents (Phase 1)
        self.product = ProductAgent("ProductAgent")
        self.review = ReviewAgent("ReviewAgent")
        self.ugc = UGCAgent("UGCAgent")
        self.creative = CreativeAgent("CreativeAgent")
        self.offer = OfferAgent("OfferAgent")

        # Phase 2 agents
        self.trend = TrendAgent("TrendAgent")
        self.competitor = CompetitorAgent("CompetitorAgent")
        self.memory = MemoryAgent("MemoryAgent")
        self.analytics = AnalyticsAgent("AnalyticsAgent")

        # Phase 3 agents
        self.avatar = AvatarAgent("AvatarAgent")
        self.video = VideoAgent("VideoAgent")

        # Phase 4 agents
        self.publisher = PublisherAgent("PublisherAgent")
        self.knowledge = KnowledgeAgent("KnowledgeAgent")
        self.finance = FinanceAgent("FinanceAgent")
        self.growth = GrowthAgent("GrowthAgent")

    async def create_affiliate_package(
        self,
        url: str,
        include_video: bool = False,
        include_avatar: bool = False,
    ) -> AffiliatePackageOutput:
        """Orchestrate the full affiliate package pipeline."""
        # Phase 1: Core pipeline
        product = await self.product(url=url)
        reviews = await self.review(product_id=product.product_id)
        competitors = await self.competitor(
            category=product.category or "umum"
        )
        offer = await self.offer(
            product=product, reviews=reviews, competitors=competitors
        )
        ugc_result = await self.ugc(
            product_id=product.product_id, offer_strategy=offer
        )
        creative_result = await self.creative(product_id=product.product_id)

        hooks_output: GenerateHooksOutput = ugc_result.get(
            "hooks", GenerateHooksOutput(product_id=product.product_id)
        )
        scripts_output: GenerateScriptOutput = ugc_result.get(
            "scripts", GenerateScriptOutput(product_id=product.product_id)
        )
        thumbnail_output: GenerateThumbnailOutput = creative_result.get(
            "thumbnail",
            GenerateThumbnailOutput(product_id=product.product_id),
        )

        image_output = GenerateImageOutput(
            image_url="https://storage.titan-aio.local/images/placeholder.png",
            model_used="flux-schnell",
            seed=0,
        )

        result = AffiliatePackageOutput(
            product=product,
            review_summary=reviews,
            competitor_analysis=competitors,
            offer_strategy=offer,
            hooks=hooks_output,
            scripts=scripts_output,
            thumbnail=thumbnail_output,
            image=image_output,
        )

        # Phase 3 extensions
        if include_video and scripts_output.scripts:
            video_result = await self.video(
                script=scripts_output.scripts[0].full_script
            )
            result.video = _SimpleVideoOutput(
                video_url=video_result["url"],
                model_used=video_result["model_used"],
                duration_seconds=video_result["duration_seconds"],
            )

        if include_avatar:
            avatar_result = await self.avatar(name="AI Spokesperson")
            result.avatar = _SimpleAvatarOutput(
                avatar_id=avatar_result["avatar_id"],
                image_url=avatar_result.get("image_url", ""),
                persona=avatar_result["persona"],
            )

        # Save campaign
        async with async_session_factory() as session:
            repo = Repository(session, Campaign)
            campaign = await repo.create(
                product_id=product.product_id,
                name=f"Campaign - {product.title[:50]}",
                status="active",
            )
            result.campaign_id = campaign.id
            await session.commit()

        return result

    async def analyze_trends(self, category: str = "") -> dict:
        """Analyze market trends."""
        return await self.trend(category=category)

    async def get_recommendations(self, category: str = "") -> dict:
        """Get campaign recommendations."""
        return await self.knowledge()

    async def track_metrics(self, campaign_id: str) -> dict:
        """Track campaign metrics."""
        return await self.analytics(campaign_id=campaign_id)

    async def evaluate_finance(
        self, campaign_id: str, revenue: float, ad_spend: float
    ) -> dict:
        """Evaluate campaign financials."""
        return await self.finance(
            campaign_id=campaign_id, revenue=revenue, ad_spend=ad_spend
        )

    async def growth_decision(self, roi: float) -> dict:
        """Make scale/kill decision."""
        return await self.growth(roi=roi)
