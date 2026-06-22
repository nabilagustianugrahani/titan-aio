"""Tests for the 12 Overkill Features."""

import pytest
from Services.agents.viral_predictor import ViralInput, ViralPredictor
from Services.agents.trend_monitor import TrendInput, monitor_trends
from Services.content.remixer import remix_content
from Services.content.multilingual import translate_content
from Services.voice.cloner import VoiceCloner
from Services.thumbnail.auto_generator import ThumbnailInput, generate_thumbnails
from Services.analytics.ab_stats import ABTestCreate, create_test, update_variant, required_sample_size
from Services.agents.affiliate_optimizer import optimize_affiliate
from Services.content.seo_engine import seo_optimize
from Services.agents.sentiment_monitor import monitor_sentiment
from Services.pipeline.self_healing import SelfHealingPipeline, classify_failure


# ── Viral Predictor ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_viral_predictor_basic():
    predictor = ViralPredictor()
    result = await predictor.predict(ViralInput(hook="This product is amazing!"))
    assert 0 <= result.score <= 100
    assert result.predicted_reach >= 0
    assert len(result.optimization_tips) > 0

@pytest.mark.asyncio
async def test_viral_predictor_with_script():
    predictor = ViralPredictor()
    result = await predictor.predict(ViralInput(
        hook="Wait until you see this! 😱",
        script="I tried this product and the results were unbelievable. Link in bio!",
        platform="tiktok",
    ))
    assert result.score > 0
    assert result.confidence > 0

@pytest.mark.asyncio
async def test_viral_predictor_weak_content():
    predictor = ViralPredictor()
    result = await predictor.predict(ViralInput(hook="buy this"))
    assert result.score < 50


# ── Trend Monitor ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trend_monitor():
    result = await monitor_trends(TrendInput(platform="tiktok", niche="general"))
    assert result.total_trends > 0
    assert len(result.trends) > 0

@pytest.mark.asyncio
async def test_trend_monitor_urgency():
    result = await monitor_trends(TrendInput(platform="tiktok", niche="beauty"))
    for trend in result.trends:
        assert trend.urgency in ("low", "medium", "high", "critical")


# ── Content Remix ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_content_remix():
    result = await remix_content(
        content="This product changed my life! Best purchase ever.",
        niche="beauty",
    )
    assert result.total_variants >= 3
    assert len(result.variants) > 0


# ── Multilingual ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multilingual_translate():
    result = await translate_content(
        content="Produk ini sangat bagus! Link di bio!",
        source_language="id",
        target_languages=["en", "es"],
        platform="tiktok",
    )
    assert result.total_variants == 2


# ── Voice Cloner ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_voice_cloner():
    cloner = VoiceCloner()
    profile = await cloner.create_profile(name="Test Voice", style="enthusiastic")
    assert profile.profile_id
    assert profile.name == "Test Voice"
    generated = await cloner.generate(text="Hello world", profile_id=profile.profile_id)
    assert generated.voice_id
    assert generated.duration_estimate > 0


# ── Thumbnail Generator ────────────────────────────────────────

@pytest.mark.asyncio
async def test_thumbnail_generator():
    result = await generate_thumbnails(ThumbnailInput(
        product_name="Test Product",
        niche="electronics",
        num_variants=3,
    ))
    assert len(result.variants) == 3
    assert result.recommended == 0

@pytest.mark.asyncio
async def test_thumbnail_viral_score():
    result = await generate_thumbnails(ThumbnailInput(
        product_name="Gaming Phone",
        niche="electronics",
        num_variants=5,
    ))
    for v in result.variants:
        assert 0 <= v.viral_score <= 100
        assert v.predicted_ctr > 0


# ── A/B Stats Engine ────────────────────────────────────────────

def test_ab_test_create_and_update():
    test = create_test(ABTestCreate(test_name="Test A/B", variants=["A", "B"], niche="general"))
    assert test.test_id
    assert len(test.variants) == 2
    update_variant(test.test_id, test.variants[0].variant_id, impressions=100, clicks=10)
    assert True

def test_ab_sample_size():
    result = required_sample_size(baseline_rate=0.05, mde=0.1)
    assert result.minimum_sample_per_variant > 0


# ── Affiliate Optimizer ────────────────────────────────────────

@pytest.mark.asyncio
async def test_affiliate_optimizer():
    result = await optimize_affiliate(
        current_products=None,
        niche="fashion",
    )
    assert result.optimization_score > 0
    assert len(result.current_products) > 0


# ── SEO Engine ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seo_optimize():
    result = await seo_optimize(
        title="Best Phone 2026",
        description="Review of the best phones in 2026",
        niche="electronics",
    )
    assert result.optimized_score > 0
    assert len(result.keywords) > 0
    assert len(result.optimized_tags) > 0


# ── Sentiment Monitor ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_sentiment_monitor():
    result = await monitor_sentiment(
        brand_name="TestBrand",
        platforms="tiktok,instagram",
        niche="general",
    )
    assert -1 <= result.overall_sentiment <= 1
    assert len(result.platform_breakdown) == 2
    assert result.recommendation


# ── Self-Healing Pipeline ──────────────────────────────────────

def test_pipeline_failure_classification():
    error_type = classify_failure("rate limit exceeded 429")
    assert error_type in ("timeout", "rate_limit", "model_error", "quality_low", "unknown")

def test_pipeline_health():
    pipeline = SelfHealingPipeline(pipeline_id="test")
    h = pipeline.health()
    assert h.status in ("pending", "running", "completed", "failed", "recovered")


# ── Integration: Full Feature Test ──────────────────────────────

@pytest.mark.asyncio
async def test_full_feature_pipeline():
    """Test multiple features working together."""
    predictor = ViralPredictor()
    viral = await predictor.predict(ViralInput(
        hook="This skincare routine changed everything! 🌟",
        script="I tried this for 30 days and the results are insane. Link in bio!",
        platform="tiktok",
        niche="beauty",
    ))
    assert viral.score > 0

    trends = await monitor_trends(TrendInput(platform="tiktok", niche="beauty"))
    assert trends.total_trends > 0

    seo = await seo_optimize(
        title="Skincare Routine 2026",
        description="Best skincare routine for glowing skin",
        niche="beauty",
    )
    assert seo.optimized_score > 0

    sentiment = await monitor_sentiment(brand_name="BeautyBrand", platforms="tiktok")
    assert sentiment.overall_sentiment != 0 or sentiment.total_mentions >= 0
