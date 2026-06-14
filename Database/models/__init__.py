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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="IDR")
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_sales: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    commission_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competition_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pain_points: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    extracted_quotes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    platform: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


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
    campaign_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    asset_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)


class WinningHook(Base, TimestampMixin):
    __tablename__ = "winning_hooks"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    hook_text: Mapped[str] = mapped_column(Text, nullable=False)
    hook_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ctr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


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
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class FailedCampaign(Base, TimestampMixin):
    __tablename__ = "failed_campaigns"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    actionable_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class AvatarProfile(Base, TimestampMixin):
    __tablename__ = "avatar_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    persona: Mapped[dict] = mapped_column(JSON, nullable=False)
    character_sheet: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    base_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ProductProfile(Base, TimestampMixin):
    __tablename__ = "product_profiles"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_intelligence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    competitor_intelligence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    offer_strategy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
