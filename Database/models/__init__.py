"""SQLAlchemy ORM models for TITAN AIO."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from Database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True,
    )


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="IDR")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(256), nullable=True)
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    competition_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pain_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extracted_quotes: Mapped[list | None] = mapped_column(JSON, nullable=True)


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AffiliateLink(Base, TimestampMixin):
    __tablename__ = "affiliate_links"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)


class GeneratedAsset(Base, TimestampMixin):
    __tablename__ = "generated_assets"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    asset_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)


class WinningHook(Base, TimestampMixin):
    __tablename__ = "winning_hooks"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    hook_text: Mapped[str] = mapped_column(Text, nullable=False)
    hook_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)


class WinningProduct(Base, TimestampMixin):
    __tablename__ = "winning_products"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(256), nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    roi: Mapped[float] = mapped_column(Float, default=0.0)


class WinningCTA(Base, TimestampMixin):
    __tablename__ = "winning_cta"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    cta_text: Mapped[str] = mapped_column(Text, nullable=False)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class FailedCampaign(Base, TimestampMixin):
    __tablename__ = "failed_campaigns"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    actionable_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)


class AvatarProfile(Base, TimestampMixin):
    __tablename__ = "avatar_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    persona: Mapped[dict] = mapped_column(JSON, nullable=False)
    character_sheet: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    base_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProductProfile(Base, TimestampMixin):
    __tablename__ = "product_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_intelligence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    competitor_intelligence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    offer_strategy: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ViralPrediction(Base, TimestampMixin):
    __tablename__ = "viral_predictions"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    script: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_posting_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    optimization_tips: Mapped[list | None] = mapped_column(JSON, nullable=True)
    feature_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class TrendRecord(Base, TimestampMixin):
    __tablename__ = "trend_records"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    niche: Mapped[str] = mapped_column(String(128), nullable=False)
    topic: Mapped[str] = mapped_column(String(256), nullable=False)
    velocity: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class CompetitorProfile(Base, TimestampMixin):
    __tablename__ = "competitor_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    followers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_engagement: Mapped[float | None] = mapped_column(Float, nullable=True)
    posting_frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    top_hooks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    content_gaps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    threat_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class ContentRemix(Base, TimestampMixin):
    __tablename__ = "content_remixes"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_content: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    viral_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cta_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContentVersion(Base, TimestampMixin):
    __tablename__ = "content_versions"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_current: Mapped[bool] = mapped_column(Integer, default=1)


class ScheduledPost(Base, TimestampMixin):
    __tablename__ = "scheduled_posts"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    campaign_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    media_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ABTestResult(Base, TimestampMixin):
    __tablename__ = "ab_test_results"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    test_name: Mapped[str] = mapped_column(String(256), nullable=False)
    niche: Mapped[str | None] = mapped_column(String(128), nullable=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    winner_variant_id: Mapped[str | None] = mapped_column(String, nullable=True)
    variants: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ComplianceCheck(Base, TimestampMixin):
    __tablename__ = "compliance_checks"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Integer, default=1)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    issues: Mapped[list | None] = mapped_column(JSON, nullable=True)
    affiliate_disclosed: Mapped[bool] = mapped_column(Integer, default=0)


class AuditLogEntry(Base, TimestampMixin):
    __tablename__ = "audit_log"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str | None] = mapped_column(String(256), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Integer, default=1)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)


class PerformanceAlert(Base, TimestampMixin):
    __tablename__ = "performance_alerts"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    rule_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(256), nullable=False)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="info")
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    acknowledged: Mapped[bool] = mapped_column(Integer, default=0)


class RevenueDataPoint(Base, TimestampMixin):
    __tablename__ = "revenue_data_points"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    ad_spend: Mapped[float] = mapped_column(Float, default=0.0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    net_profit: Mapped[float] = mapped_column(Float, default=0.0)


class RevenueForecast(Base, TimestampMixin):
    __tablename__ = "revenue_forecasts"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    period: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_roi: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend: Mapped[str | None] = mapped_column(String(32), nullable=True)
    daily_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_day: Mapped[str | None] = mapped_column(String(32), nullable=True)
    worst_day: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)


class VoiceProfile(Base, TimestampMixin):
    __tablename__ = "voice_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    characteristics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sample_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)


class WebhookConfig(Base, TimestampMixin):
    __tablename__ = "webhook_configs"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    events: Mapped[list | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Integer, default=1)


class TelegramConfig(Base, TimestampMixin):
    __tablename__ = "telegram_configs"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    bot_token: Mapped[str] = mapped_column(String(256), nullable=False)
    chat_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Integer, default=1)


class AffiliateAccount(Base, TimestampMixin):
    __tablename__ = "affiliate_accounts"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    total_conversions: Mapped[int] = mapped_column(Integer, default=0)


class BrandMention(Base, TimestampMixin):
    __tablename__ = "brand_mentions"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    author_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class InfluencerProfile(Base, TimestampMixin):
    __tablename__ = "influencer_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    niche: Mapped[str | None] = mapped_column(String(128), nullable=True)
    followers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    collaboration_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class CompetitorWatch(Base, TimestampMixin):
    __tablename__ = "competitor_watches"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    competitor_name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alerts: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ContentIdea(Base, TimestampMixin):
    __tablename__ = "content_ideas"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hook_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_engagement: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    niche: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cta_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)


class PricingAnalysis(Base, TimestampMixin):
    __tablename__ = "pricing_analyses"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    commission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitor_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    demand_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    supply_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_commission: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(128), nullable=True)


class BudgetAllocation(Base, TimestampMixin):
    __tablename__ = "budget_allocations"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    current_budget: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class BatchJob(Base, TimestampMixin):
    __tablename__ = "batch_jobs"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    successful: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    results: Mapped[list | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    concurrency: Mapped[int] = mapped_column(Integer, default=1)
    delay_between: Mapped[float | None] = mapped_column(Float, nullable=True)


class AutoReport(Base, TimestampMixin):
    __tablename__ = "auto_reports"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    report_type: Mapped[str] = mapped_column(String(128), nullable=False)
    period: Mapped[str | None] = mapped_column(String(64), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections: Mapped[list | None] = mapped_column(JSON, nullable=True)


class PipelineRun(Base, TimestampMixin):
    __tablename__ = "pipeline_runs"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    pipeline_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    features_used: Mapped[list | None] = mapped_column(JSON, nullable=True)
    started_at_iso: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at_iso: Mapped[str | None] = mapped_column(String(64), nullable=True)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    hooks_count: Mapped[int] = mapped_column(Integer, default=0)
    scripts_count: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)


class SmartScheduleSlot(Base, TimestampMixin):
    __tablename__ = "smart_schedule_slots"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_engagement: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)


class CrossPlatformMetric(Base, TimestampMixin):
    __tablename__ = "cross_platform_metrics"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    engagement: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    ad_spend: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)
