"""Pydantic schemas for MCP tool inputs and outputs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Health ──────────────────────────────────────────────────────

class HealthOutput(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0


# ── Search Product ──────────────────────────────────────────────

class SearchProductInput(BaseModel):
    query: str = Field(..., min_length=1, description="Search query for affiliate products")
    platform: Optional[str] = Field(None, description="Platform filter: shopee, tokopedia")
    limit: int = Field(10, ge=1, le=50)


class SearchProductItem(BaseModel):
    external_id: str
    title: str
    price: float
    currency: str = "IDR"
    rating: Optional[float] = None
    total_sales: Optional[int] = None
    url: str
    platform: str = "shopee"


class SearchProductOutput(BaseModel):
    results: list[SearchProductItem]
    total: int


# ── Analyze Product ─────────────────────────────────────────────

class AnalyzeProductInput(BaseModel):
    url: str = Field(..., min_length=1, description="Shopee/Tokopedia product URL")


class AnalyzeProductOutput(BaseModel):
    product_id: str
    title: str
    price: float
    currency: str = "IDR"
    rating: Optional[float] = None
    total_sales: Optional[int] = None
    category: Optional[str] = None
    commission_estimate: Optional[float] = None
    competition_level: Optional[str] = None
    product_score: float = 0.0
    url: str


# ── Analyze Reviews ─────────────────────────────────────────────

class AnalyzeReviewsInput(BaseModel):
    product_id: str = Field(..., description="Product ID to analyze reviews for")
    max_reviews: int = Field(100, ge=1, le=500)


class PainPoint(BaseModel):
    point: str
    frequency: float = 0.0
    top_quotes: list[str] = []


class ReviewSentiment(BaseModel):
    positive: float = 0.0
    neutral: float = 0.0
    negative: float = 0.0


class AnalyzeReviewsOutput(BaseModel):
    product_id: str
    total_reviews_analyzed: int = 0
    average_rating: Optional[float] = None
    pain_points: list[PainPoint] = []
    objections: list[PainPoint] = []
    benefits: list[PainPoint] = []
    complaints: list[PainPoint] = []
    sentiment_summary: ReviewSentiment = ReviewSentiment()


# ── Analyze Competitors ─────────────────────────────────────────

class AnalyzeCompetitorsInput(BaseModel):
    category: str = Field(..., min_length=1, description="Product category to analyze")
    limit: int = Field(10, ge=1, le=30)


class CompetitorHook(BaseModel):
    hook: str
    source: str = "unknown"
    engagement_est: str = "medium"


class AnalyzeCompetitorsOutput(BaseModel):
    category: str
    competitors_analyzed: int = 0
    winning_hooks: list[CompetitorHook] = []
    common_angles: list[str] = []
    creative_patterns: list[str] = []
    gaps_identified: list[str] = []
    recommended_differentiation: str = ""


# ── Generate Offer ──────────────────────────────────────────────

class GenerateOfferInput(BaseModel):
    product_id: str = Field(..., description="Product ID")
    product_analysis: AnalyzeProductOutput
    review_analysis: Optional[AnalyzeReviewsOutput] = None
    competitor_analysis: Optional[AnalyzeCompetitorsOutput] = None


class GenerateOfferOutput(BaseModel):
    product_id: str
    primary_angle: str = ""
    value_proposition: str = ""
    positioning_statement: str = ""
    target_audience: str = ""
    emotional_triggers: list[str] = []
    key_benefits_to_highlight: list[str] = []
    objections_to_address: list[str] = []
    recommended_cta: str = ""


# ── Generate Hooks ──────────────────────────────────────────────

class GenerateHooksInput(BaseModel):
    product_id: str
    offer_strategy: GenerateOfferOutput
    count: int = Field(10, ge=1, le=30)


class Hook(BaseModel):
    hook: str
    type: str = "curiosity"
    predicted_ctr: str = "medium"


class GenerateHooksOutput(BaseModel):
    product_id: str
    hooks: list[Hook] = []


# ── Generate Script ─────────────────────────────────────────────

class GenerateScriptInput(BaseModel):
    product_id: str
    hooks: list[Hook]
    offer_strategy: GenerateOfferOutput
    count: int = Field(10, ge=1, le=20)


class ScriptStructure(BaseModel):
    hook: str = ""
    problem: str = ""
    solution: str = ""
    social_proof: str = ""
    cta: str = ""


class Script(BaseModel):
    title: str
    duration_seconds: int = 30
    structure: ScriptStructure = ScriptStructure()
    full_script: str = ""


class GenerateScriptOutput(BaseModel):
    product_id: str
    scripts: list[Script] = []


# ── Generate Thumbnail ──────────────────────────────────────────

class GenerateThumbnailInput(BaseModel):
    product_id: str
    script_title: Optional[str] = None
    style: str = "bold"


class ThumbnailConcept(BaseModel):
    concept: str = ""
    description: str = ""
    text_overlay: str = ""
    style: str = "bold"


class GenerateThumbnailOutput(BaseModel):
    product_id: str
    thumbnail: ThumbnailConcept = ThumbnailConcept()
    image_url: Optional[str] = None


# ── Generate Image ──────────────────────────────────────────────

class GenerateImageInput(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    model: str = "flux-schnell"
    width: int = 1024
    height: int = 1024


class GenerateImageOutput(BaseModel):
    image_url: str
    model_used: str
    seed: int = 0


# ── Generate Video ──────────────────────────────────────────────

class GenerateVideoInput(BaseModel):
    script: str = Field(..., min_length=1)
    model: str = "wan-2-2"
    duration_seconds: int = 30


class GenerateVideoOutput(BaseModel):
    video_url: str
    model_used: str
    duration_seconds: int


# ── Generate Avatar ─────────────────────────────────────────────

class GenerateAvatarInput(BaseModel):
    persona_name: str = Field(..., min_length=1)
    style: str = "realistic"
    expression: str = "neutral"


class GenerateAvatarOutput(BaseModel):
    avatar_id: str
    image_url: str
    persona: dict = {}


# ── Create Affiliate Package ────────────────────────────────────

class CreateAffiliatePackageInput(BaseModel):
    url: str = Field(..., description="Affiliate product URL")
    include_video: bool = False
    include_avatar: bool = False
    include_image: bool = False


class AffiliatePackageOutput(BaseModel):
    product: AnalyzeProductOutput
    review_summary: Optional[AnalyzeReviewsOutput] = None
    competitor_analysis: Optional[AnalyzeCompetitorsOutput] = None
    offer_strategy: Optional[GenerateOfferOutput] = None
    hooks: Optional[GenerateHooksOutput] = None
    scripts: Optional[GenerateScriptOutput] = None
    thumbnail: Optional[GenerateThumbnailOutput] = None
    image: Optional[GenerateImageOutput] = None
    video: Optional[GenerateVideoOutput] = None
    avatar: Optional[GenerateAvatarOutput] = None
    campaign_id: Optional[str] = None


# ── Save / Load Campaign ────────────────────────────────────────

class SaveCampaignInput(BaseModel):
    product_id: str
    name: str = Field(..., min_length=1)
    platform: Optional[str] = None
    budget: Optional[float] = None
    config: Optional[dict] = None


class SaveCampaignOutput(BaseModel):
    campaign_id: str
    status: str = "draft"


class LoadCampaignInput(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID to load")


class LoadCampaignOutput(BaseModel):
    campaign_id: str
    product_id: str
    name: str
    status: str
    platform: Optional[str] = None
    budget: Optional[float] = None
    total_spent: float = 0.0
    total_revenue: float = 0.0
    created_at: Optional[datetime] = None


# ── Get Metrics ─────────────────────────────────────────────────

class GetMetricsInput(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID")


class PlatformMetrics(BaseModel):
    views: int = 0
    clicks: int = 0
    ctr: float = 0.0
    conversions: int = 0
    conversion_rate: float = 0.0


class GetMetricsOutput(BaseModel):
    campaign_id: str
    metrics: PlatformMetrics = PlatformMetrics()
    total_revenue: float = 0.0
    total_commission: float = 0.0
    roi: float = 0.0


# ── Get Recommendations ─────────────────────────────────────────

class GetRecommendationsInput(BaseModel):
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(5, ge=1, le=20)


class Recommendation(BaseModel):
    hook: str
    category: str
    predicted_ctr: str = "medium"
    source_campaign_id: Optional[str] = None


class GetRecommendationsOutput(BaseModel):
    recommendations: list[Recommendation] = []
    total: int = 0
