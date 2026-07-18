"""TITAN AIO — Seed Data Generator.

Fills all 36 empty database tables with realistic sample data
matching the existing Indonesian e-commerce patterns.

Usage:
    python scripts/seed_data.py              # seed all empty tables
    python scripts/seed_data.py --force       # re-seed even if data exists
"""

from __future__ import annotations

import asyncio
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

from Database.connection import async_session_factory, close_db, init_db
from Database.models import (
    ABTestResult,
    AffiliateAccount,
    AffiliateLink,
    AlertRule,
    AuditLogEntry,
    AutoReport,
    AvatarProfile,
    BatchJob,
    BrandMention,
    BudgetAllocation,
    CompetitorProfile,
    CompetitorWatch,
    ComplianceCheck,
    ContentIdea,
    ContentRemix,
    ContentVersion,
    CrossPlatformMetric,
    FailedCampaign,
    GeneratedAsset,
    InfluencerProfile,
    KnowledgeEntry,
    Metric,
    PerformanceAlert,
    PipelineRun,
    PricingAnalysis,
    ProductProfile,
    RevenueDataPoint,
    RevenueForecast,
    ScheduledPost,
    SmartScheduleSlot,
    TelegramConfig,
    TrendRecord,
    ViralPrediction,
    VoiceProfile,
    WebhookConfig,
    WinningCTA,
    WinningProduct,
)

logger = logging.getLogger(__name__)

# ── Sample Data Pools ──────────────────────────────────────────

PRODUCT_TITLES = [
    "Skincare Wajah glowing - Vitamin C Serum 30ml",
    "Sepatu Running Pria - Ultralight 200g",
    "Smartwatch Fitness AMOLED Display 1.43",
    "Bluetooth Earphone TWS Noise Cancelling",
    "Tas Ransel Laptop Anti Air 40L",
    "Kopi Arabica Premium 250g - Single Origin",
    "Rice Cooker Digital 2L - Anti Lengket",
    "Handbody Whitening SPF 30 - 100ml",
    "Keyboard Mechanical Wireless RGB",
    "Kamera Action 4K Waterproof 10m",
    "Sunscreen SPF 50 PA++++ - No Whitecast",
    "Drone Mini 4K Camera - 30min Flight",
    "Mouse Gaming Wireless 16000 DPI",
    "Parfum Pria Long Lasting 100ml",
    "Headset Gaming 7.1 Surround Sound",
    "Botol Minum Stainless 1L - Thermal",
    "Car Charger Fast Charging 65W PD",
    "Yoga Mat Premium 6mm - Non Slip",
    "Power Bank 20000mAh - Fast Charging",
    "Jam Tangan Pria - Stainless Steel",
]

CATEGORIES = ["elektronik", "fashion", "kesehatan", "makanan", "olahraga", "kecantikan", "otomotif"]
PLATFORMS = ["shopee", "tokopedia", "tiktok", "bukalapak", "lazada"]
HOOK_TYPES = ["curiosity", "testimonial", "problem", "social_proof", "scarcity", "comparison"]

# ── Indonesian content pools ──────────────────────────────────

REVIEW_TEXTS = [
    "Beneran bagus banget, udah coba 2 minggu cocok!",
    "Pengiriman cepet, barang sesuai foto. Thanks seller!",
    "Recommended banget! Kualitasnya premium.",
    "Lumayan buat harganya, masih standar sih.",
    "Sayang barang agak lecet pas dateng, mungkin kena benturan.",
    "Udah order 3 kali, gak pernah kecewa.",
    "Cocok buat pemula yang baru mulai pake produk ini.",
    "Bikin ketagihan, bakal repeat order lagi!",
    "Gak nyangka kualitas sebagus ini, worth it banget.",
    "Dikit lagi sih bagus, cuma sayang ukurannya kurang pas.",
    "Berfungsi dengan baik, belum ada masalah setelah 1 bulan.",
    "Kualitas OK lah untuk harga segini.",
    "Wah ternyata bagus banget, bakal beli lagi!",
    "Cepat rusak setelah 3 hari, kecewa.",
    "Mantap jiwa! Sesuai deskripsi, gak boong.",
    "Kurang suka sama warnanya, beda dari foto.",
    "Sempurna! Packaging aman, barang gak rusak.",
    "Harga terjangkau, kualitas bintang 5!",
    "Size agak kecil, saranin beli 1 size lebih besar.",
    "Pengiriman super cepat, seller ramah!",
]

HOOK_TEXTS = [
    "Kamu gak akan percaya produk ini cuma segini...",
    "Udah 10.000+ orang beralih ke produk ini...",
    "Dalam 24 jam, produk ini ludes terjual...",
    "Gue udah nyoba 5 produk, ini yang paling worth it...",
    "Sebelum beli products ini, tonton dulu video ini...",
    "Harga segitu? Serius? Kualitasnya setara brand mahal...",
    "Aku gak nyangka kualitasnya sebagus ini...",
    "Dari rating 3.2 jadi 4.8 cuma pake produk ini...",
    "Jangan beli sebelum kamu tau fakta ini...",
    "Produk ini viral di TikTok, dan ini alasannya...",
    "Gak sengaja nemu, tapi jadi favorite banget...",
    "3 alasan kenapa produk ini wajib kamu punya...",
    "Antara kamu dan kulit glowing cuma beda produk ini...",
    "Stop! Jangan scroll dulu sebelum lihat ini...",
    "Yang suka hemat wajib nonton sampe habis...",
]

SCRIPTS = [
    "Halo guys! Hari ini gue mau review product yang lagi viral banget. Jujur aja, gue awalnya skeptis, tapi setelah nyobain sendiri... hasilnya bikin gue speechless. Dari segi kualitas, ini setara sama brand yang harganya 3x lipat. Apalagi dengan harga segini, menurut gue ini wajib banget masuk wishlist kalian. Link ada di bio ya!",
    "Pernah gak sih kalian beli produk online tapi ternyata gak sesuai ekspektasi? Nah kali ini gue kasih rekomendasi product yang bener-bener worth it. Udah ribuan orang review positif, dan gue buktiin sendiri. Kualitasnya premium, pengiriman cepet, packaging aman. Pokoknya gak bakal nyesel deh!",
    "POV: kamu nemu produk yang bikin hidup berubah. Iya segitunya! Dari pertama kali nyobain, langsung kerasa bedanya. Teksturnya ringan, wanginya enak, dan hasilnya bikin ketagihan. Cocok banget buat kalian yang baru mau mulai atau yang udah pro sekalipun. Cek link di bio buat order!",
    "Save this video before you forget! Ini dia product recommendation dari gue yang udah proven sama ribuan orang. Gak percaya? Cek aja review sectionnya. Yang bikin gue suka adalah konsistensi kualitasnya — dari batch pertama sampe sekarang always on point. 10/10 recommend!",
]

CAPTIONS = [
    "Produk wajib punya! Udah bukti sendiri 🫶 #rekomendasi #produkviraltiktok",
    "Gak bakal nyesel beli ini, udah review langsung! 🔥 #reviewproduct #recommended",
    "Jujur ini mah best banget, cobain dulu jangan sampai kehabisan ✨ #rekomendasi #fyp",
    "Worth it atau gak? Menurut gue 100% WORTH IT! 🤩 #produkrecommended #reviewjujur",
]

COMPETITOR_NAMES = [
    "Toko Sejahtera Official", "GadgetZone ID", "BeautyHunt Official",
    "TechPro Indonesia", "FashionFinder ID", "HomeLiving Official",
    "Sporty Official Store", "MomBaby Shop", "AutoParts ID", "GamingGear Indo",
]

SENTIMENTS = ["positive", "neutral", "negative"]
CONTENT_TYPES = ["video", "image", "article", "review", "tutorial", "comparison"]
ASSET_TYPES = ["thumbnail", "hook_image", "banner", "video_clip", "avatar", "voiceover"]


def _ts(days_ago: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


async def seed_all(force: bool = False) -> dict:
    """Seed all empty tables. Returns dict of table_name -> rows_created."""
    await init_db()
    results = {}

    async with async_session_factory() as session:
        from sqlalchemy import text

        # Check existing product IDs for FK references
        prod_result = await session.execute(text("SELECT id FROM products"))
        existing_product_ids = [r[0] for r in prod_result.fetchall()]

        camp_result = await session.execute(text("SELECT id FROM campaigns"))
        existing_campaign_ids = [r[0] for r in camp_result.fetchall()]

        if not existing_product_ids:
            # Fallback: create minimal product references
            logger.warning("No products exist — create some first via the app")
            return {"error": "No products found. Add products first via MCP tools."}

        # For cross-seeding, pick random existing IDs
        pid = random.choice(existing_product_ids)
        cid = random.choice(existing_campaign_ids) if existing_campaign_ids else ""

        tables_to_seed = [
            ("winning_cta", _seed_winning_cta, [session, existing_campaign_ids, cid]),
            ("winning_products", _seed_winning_products, [session, existing_product_ids, pid]),
            ("failed_campaigns", _seed_failed_campaigns, [session, existing_campaign_ids, cid]),
            ("metrics", _seed_metrics, [session, existing_campaign_ids, cid]),
            ("affiliate_links", _seed_affiliate_links, [session, existing_campaign_ids, cid]),
            ("generated_assets", _seed_generated_assets, [session, existing_campaign_ids, cid]),
            ("knowledge", _seed_knowledge, [session]),
            ("avatar_profiles", _seed_avatar_profiles, [session]),
            ("product_profiles", _seed_product_profiles, [session, existing_product_ids, pid]),
            ("viral_predictions", _seed_viral_predictions, [session, existing_campaign_ids, cid]),
            ("trend_records", _seed_trend_records, [session]),
            ("competitor_profiles", _seed_competitor_profiles, [session]),
            ("content_remixes", _seed_content_remixes, [session]),
            ("content_versions", _seed_content_versions, [session]),
            ("scheduled_posts", _seed_scheduled_posts, [session, existing_campaign_ids, cid]),
            ("ab_test_results", _seed_ab_test_results, [session, existing_campaign_ids, cid]),
            ("compliance_checks", _seed_compliance_checks, [session, existing_campaign_ids, cid]),
            ("audit_log", _seed_audit_log, [session]),
            ("alert_rules", _seed_alert_rules, [session, existing_campaign_ids, cid]),
            ("performance_alerts", _seed_performance_alerts, [session, existing_campaign_ids, cid]),
            ("revenue_data_points", _seed_revenue_data_points, [session, existing_campaign_ids, cid]),
            ("revenue_forecasts", _seed_revenue_forecasts, [session]),
            ("voice_profiles", _seed_voice_profiles, [session]),
            ("webhook_configs", _seed_webhook_configs, [session]),
            ("telegram_configs", _seed_telegram_configs, [session]),
            ("affiliate_accounts", _seed_affiliate_accounts, [session]),
            ("brand_mentions", _seed_brand_mentions, [session]),
            ("influencer_profiles", _seed_influencer_profiles, [session]),
            ("competitor_watches", _seed_competitor_watches, [session]),
            ("content_ideas", _seed_content_ideas, [session]),
            ("pricing_analyses", _seed_pricing_analyses, [session, existing_product_ids, pid]),
            ("budget_allocations", _seed_budget_allocations, [session, existing_campaign_ids, cid]),
            ("batch_jobs", _seed_batch_jobs, [session]),
            ("auto_reports", _seed_auto_reports, [session]),
            ("pipeline_runs", _seed_pipeline_runs, [session, existing_product_ids]),
            ("smart_schedule_slots", _seed_smart_schedule_slots, [session]),
            ("cross_platform_metrics", _seed_cross_platform_metrics, [session, existing_campaign_ids, cid]),
        ]

        for table_name, func, args in tables_to_seed:
            try:
                count = await func(*args, force=force)
                if count > 0:
                    await session.commit()
                results[table_name] = count
            except Exception as e:
                await session.rollback()
                results[table_name] = f"error: {e}"
                logger.warning(f"Failed to seed {table_name}: {e}")

    await close_db()
    return results


# ── Individual Seeders ─────────────────────────────────────────

async def _count(session, model):
    from sqlalchemy import func, select
    r = await session.execute(select(func.count(model.id)))
    return r.scalar() or 0


async def _seed_winning_cta(session, campaign_ids, cid, force=False):
    if await _count(session, WinningCTA) > 0 and not force:
        return 0
    ctas = [
        {"campaign_id": cid or random.choice(campaign_ids), "cta_text": "Beli Sekarang — Diskon 50%!", "conversion_rate": round(random.uniform(2.5, 8.0), 2)},
        {"campaign_id": cid or random.choice(campaign_ids), "cta_text": "Klik link di bio! 🚀", "conversion_rate": round(random.uniform(3.0, 7.5), 2)},
        {"campaign_id": cid or random.choice(campaign_ids), "cta_text": "Order sekarang, gratis ongkir!", "conversion_rate": round(random.uniform(1.8, 6.5), 2)},
        {"campaign_id": cid or random.choice(campaign_ids), "cta_text": "Buruan, stok terbatas!", "conversion_rate": round(random.uniform(4.0, 9.0), 2)},
    ]
    for c in ctas:
        await session.execute(WinningCTA.__table__.insert().values(id=str(uuid.uuid4()), **c))
    return len(ctas)


async def _seed_winning_products(session, product_ids, pid, force=False):
    if await _count(session, WinningProduct) > 0 and not force:
        return 0
    items = [
        {"product_id": pid or random.choice(product_ids), "category": "kecantikan", "total_revenue": round(random.uniform(5000000, 50000000), 0), "roi": round(random.uniform(1.5, 5.0), 2)},
        {"product_id": random.choice(product_ids), "category": "elektronik", "total_revenue": round(random.uniform(10000000, 100000000), 0), "roi": round(random.uniform(2.0, 4.5), 2)},
        {"product_id": random.choice(product_ids), "category": "fashion", "total_revenue": round(random.uniform(3000000, 30000000), 0), "roi": round(random.uniform(1.8, 3.5), 2)},
    ]
    for p in items:
        await session.execute(WinningProduct.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(items)


async def _seed_failed_campaigns(session, campaign_ids, cid, force=False):
    if await _count(session, FailedCampaign) > 0 and not force:
        return 0
    failures = [
        {"campaign_id": cid or random.choice(campaign_ids), "reason": "Low engagement rate (<1%)", "metrics_snapshot": {"impressions": 1200, "clicks": 8}},
        {"campaign_id": cid or random.choice(campaign_ids), "reason": "Budget exhausted before optimization", "metrics_snapshot": {"spent": 500000, "revenue": 120000}},
    ]
    for f in failures:
        await session.execute(FailedCampaign.__table__.insert().values(id=str(uuid.uuid4()), **f))
    return len(failures)


async def _seed_metrics(session, campaign_ids, cid, force=False):
    if await _count(session, Metric) > 0 and not force:
        return 0
    metrics = [
        {"campaign_id": cid or random.choice(campaign_ids), "views": random.randint(5000, 50000), "clicks": random.randint(200, 3000), "ctr": round(random.uniform(2.0, 8.0), 2), "conversions": random.randint(10, 200), "revenue": round(random.uniform(500000, 10000000), 0), "period_start": _ts(7), "period_end": _ts(0)},
    ]
    for m in metrics:
        await session.execute(Metric.__table__.insert().values(id=str(uuid.uuid4()), **m))
    return len(metrics)


async def _seed_affiliate_links(session, campaign_ids, cid, force=False):
    if await _count(session, AffiliateLink) > 0 and not force:
        return 0
    links = [
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "shopee", "url": f"https://shopee.co.id/product/{uuid.uuid4().hex[:12]}", "clicks": random.randint(50, 500), "conversions": random.randint(5, 50)},
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "tokopedia", "url": f"https://tokopedia.com/product/{uuid.uuid4().hex[:12]}", "clicks": random.randint(30, 300), "conversions": random.randint(3, 30)},
    ]
    for l in links:
        await session.execute(AffiliateLink.__table__.insert().values(id=str(uuid.uuid4()), **l))
    return len(links)


async def _seed_generated_assets(session, campaign_ids, cid, force=False):
    if await _count(session, GeneratedAsset) > 0 and not force:
        return 0
    assets = [
        {"campaign_id": cid or random.choice(campaign_ids), "asset_type": "thumbnail", "url": f"https://storage.titan-aio.ai/thumbnails/{uuid.uuid4().hex}.jpg", "model_used": "flux-schnell", "metadata": {"size": "1080x1920", "format": "jpg"}},
        {"campaign_id": cid or random.choice(campaign_ids), "asset_type": "video_clip", "url": f"https://storage.titan-aio.ai/videos/{uuid.uuid4().hex}.mp4", "model_used": "wan2.7-i2v", "metadata": {"duration": 15, "resolution": "720p"}},
        {"campaign_id": cid or random.choice(campaign_ids), "asset_type": "banner", "url": f"https://storage.titan-aio.ai/banners/{uuid.uuid4().hex}.png", "model_used": "flux-schnell", "metadata": {"size": "1200x628"}},
    ]
    for a in assets:
        await session.execute(GeneratedAsset.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(assets)


async def _seed_knowledge(session, force=False):
    if await _count(session, KnowledgeEntry) > 0 and not force:
        return 0
    entries = [
        {"category": "hook_patterns", "pattern": "Curiosity hooks perform 40% better for skincare products", "confidence": 0.85, "evidence": {"source": "campaign_analysis", "samples": 150}, "actionable_advice": "Start hooks with 'Kamu gak akan percaya...' for beauty niche"},
        {"category": "posting_time", "pattern": "Best posting time for TikTok affiliate is 19:00-21:00 WIB", "confidence": 0.78, "evidence": {"source": "engagement_tracking", "samples": 320}, "actionable_advice": "Schedule posts between 7-9 PM for max engagement"},
        {"category": "pricing", "pattern": "Products priced Rp50k-150k have highest conversion rate", "confidence": 0.82, "evidence": {"source": "product_analysis", "samples": 500}, "actionable_advice": "Focus on mid-range products for affiliate campaigns"},
        {"category": "content_mix", "pattern": "Video content gets 3x more clicks than image-only posts", "confidence": 0.90, "evidence": {"source": "a_b_testing", "samples": 200}, "actionable_advice": "Prioritize video content over static images"},
        {"category": "platform", "pattern": "Shopee affiliate links convert better than Tokopedia for fashion", "confidence": 0.72, "evidence": {"source": "cross_platform", "samples": 180}, "actionable_advice": "Use Shopee links for fashion campaigns"},
    ]
    for e in entries:
        await session.execute(KnowledgeEntry.__table__.insert().values(id=str(uuid.uuid4()), **e))
    return len(entries)


async def _seed_avatar_profiles(session, force=False):
    if await _count(session, AvatarProfile) > 0 and not force:
        return 0
    profiles = [
        {"name": "Sari Beauty", "gender": "female", "age_range": "20-30", "style": "beauty_influencer", "seed": 42, "metadata": {"hair": "black_long", "skin": "tan", "voice_id": "v-001"}},
        {"name": "Budi Tech", "gender": "male", "age_range": "25-35", "style": "tech_reviewer", "seed": 99, "metadata": {"hair": "black_short", "skin": "fair", "voice_id": "v-002"}},
        {"name": "Dewi Fashion", "gender": "female", "age_range": "22-32", "style": "fashion_blogger", "seed": 77, "metadata": {"hair": "brown_long", "skin": "fair", "voice_id": "v-003"}},
    ]
    for p in profiles:
        await session.execute(AvatarProfile.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(profiles)


async def _seed_product_profiles(session, product_ids, pid, force=False):
    if await _count(session, ProductProfile) > 0 and not force:
        return 0
    profiles = [
        {"product_id": pid or random.choice(product_ids), "target_audience": "Wanita 20-35 tahun", "unique_selling_points": ["Bahan premium", "Harga terjangkau", "Kualitas terjamin"], "content_angles": ["Skincare routine", "Before after", "Review jujur"]},
        {"product_id": random.choice(product_ids), "target_audience": "Pria 18-40 tahun", "unique_selling_points": ["Tahan lama", "Garansi 1 tahun", "Anti air"], "content_angles": ["Unboxing", "Test ketahanan", "Comparison"]},
    ]
    for p in profiles:
        await session.execute(ProductProfile.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(profiles)


async def _seed_viral_predictions(session, campaign_ids, cid, force=False):
    if await _count(session, ViralPrediction) > 0 and not force:
        return 0
    preds = [
        {"campaign_id": cid or random.choice(campaign_ids), "predicted_reach": random.randint(50000, 500000), "engagement": round(random.uniform(2.5, 8.0), 2), "best_posting_time": "19:30", "viral_score": random.randint(30, 95)},
        {"campaign_id": cid or random.choice(campaign_ids), "predicted_reach": random.randint(30000, 300000), "engagement": round(random.uniform(1.5, 6.0), 2), "best_posting_time": "12:00", "viral_score": random.randint(20, 80)},
    ]
    for p in preds:
        await session.execute(ViralPrediction.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(preds)


async def _seed_trend_records(session, force=False):
    if await _count(session, TrendRecord) > 0 and not force:
        return 0
    records = [
        {"platform": "tiktok", "niche": "kecantikan", "trend": "Skincare 3 langkah viral", "velocity": 85, "hashtags": ["#skincareviral", "#glowingskin", "#produklokal"]},
        {"platform": "tiktok", "niche": "fashion", "trend": "OOTD murah tapi kece", "velocity": 72, "hashtags": ["#ootdindonesia", "#fashionmurah", "#stylehack"]},
        {"platform": "instagram", "niche": "elektronik", "trend": "Tech gadget under 500k", "velocity": 60, "hashtags": ["#gadgetmurah", "#techreview", "#rekomendasigadget"]},
        {"platform": "tiktok", "niche": "makanan", "trend": "Resep viral 5 menit", "velocity": 90, "hashtags": ["#resepviral", "#masakcepat", "#foodtok"]},
    ]
    for r in records:
        await session.execute(TrendRecord.__table__.insert().values(id=str(uuid.uuid4()), **r))
    return len(records)


async def _seed_competitor_profiles(session, force=False):
    if await _count(session, CompetitorProfile) > 0 and not force:
        return 0
    comps = [
        {"name": "Toko Sejahtera Official", "platform": "shopee", "followers": 150000, "engagement": 3.5, "top_hooks": ["Diskon 70%!", "Gratis ongkir se-Indonesia"], "content_gaps": ["Video pendek", "UGC content"]},
        {"name": "GadgetZone ID", "platform": "tokopedia", "followers": 85000, "engagement": 4.2, "top_hooks": ["Harga termurah!", "Bergaransi resmi"], "content_gaps": ["Tutorial", "Review detail"]},
        {"name": "BeautyHunt Official", "platform": "tiktok", "followers": 250000, "engagement": 6.8, "top_hooks": ["Viral di TikTok!", "Produk glow up"], "content_gaps": ["Testimoni", "Before after"]},
    ]
    for c in comps:
        await session.execute(CompetitorProfile.__table__.insert().values(id=str(uuid.uuid4()), **c))
    return len(comps)


async def _seed_content_remixes(session, force=False):
    if await _count(session, ContentRemix) > 0 and not force:
        return 0
    remixes = [
        {"original_platform": "tiktok", "target_platform": "instagram", "original_content_id": "tt-123", "status": "completed", "content": {"caption": CAPTIONS[0], "hook": HOOK_TEXTS[0]}},
        {"original_platform": "tiktok", "target_platform": "facebook", "original_content_id": "tt-456", "status": "completed", "content": {"caption": CAPTIONS[1], "hook": HOOK_TEXTS[2]}},
        {"original_platform": "instagram", "target_platform": "twitter", "original_content_id": "ig-789", "status": "pending", "content": {"caption": CAPTIONS[2][:280]}},
    ]
    for r in remixes:
        await session.execute(ContentRemix.__table__.insert().values(id=str(uuid.uuid4()), **r))
    return len(remixes)


async def _seed_content_versions(session, force=False):
    if await _count(session, ContentVersion) > 0 and not force:
        return 0
    versions = [
        {"content_id": str(uuid.uuid4()), "version_number": 1, "content": {"title": "V1 - Original", "hook": HOOK_TEXTS[0][:100]}, "is_current": 1},
        {"content_id": str(uuid.uuid4()), "version_number": 2, "content": {"title": "V2 - A/B Test B", "hook": HOOK_TEXTS[1][:100]}, "is_current": 0},
    ]
    for v in versions:
        await session.execute(ContentVersion.__table__.insert().values(id=str(uuid.uuid4()), **v))
    return len(versions)


async def _seed_scheduled_posts(session, campaign_ids, cid, force=False):
    if await _count(session, ScheduledPost) > 0 and not force:
        return 0
    posts = [
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "tiktok", "content": {"caption": CAPTIONS[0], "video_url": "https://storage/vid1.mp4"}, "scheduled_at": _ts(-1), "status": "published"},
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "instagram", "content": {"caption": CAPTIONS[1], "image_url": "https://storage/img1.jpg"}, "scheduled_at": _ts(1), "status": "scheduled"},
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "facebook", "content": {"caption": CAPTIONS[2], "video_url": "https://storage/vid2.mp4"}, "scheduled_at": _ts(2), "status": "scheduled"},
    ]
    for p in posts:
        await session.execute(ScheduledPost.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(posts)


async def _seed_ab_test_results(session, campaign_ids, cid, force=False):
    if await _count(session, ABTestResult) > 0 and not force:
        return 0
    ab = [
        {"campaign_id": cid or random.choice(campaign_ids), "variants": [{"hook": HOOK_TEXTS[0], "ctr": 4.5}, {"hook": HOOK_TEXTS[1], "ctr": 6.2}], "winner": "variant_b", "confidence": 0.95},
        {"campaign_id": cid or random.choice(campaign_ids), "variants": [{"cta": "Beli sekarang", "conversion": 3.2}, {"cta": "Link di bio", "conversion": 5.1}], "winner": "variant_b", "confidence": 0.88},
    ]
    for a in ab:
        await session.execute(ABTestResult.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(ab)


async def _seed_compliance_checks(session, campaign_ids, cid, force=False):
    if await _count(session, ComplianceCheck) > 0 and not force:
        return 0
    checks = [
        {"campaign_id": cid or random.choice(campaign_ids), "passed": 1, "affiliate_disclosed": 1, "notes": "Compliant — #ad included"},
        {"campaign_id": cid or random.choice(campaign_ids), "passed": 1, "affiliate_disclosed": 1, "notes": "Meets all platform guidelines"},
    ]
    for c in checks:
        await session.execute(ComplianceCheck.__table__.insert().values(id=str(uuid.uuid4()), **c))
    return len(checks)


async def _seed_audit_log(session, force=False):
    if await _count(session, AuditLogEntry) > 0 and not force:
        return 0
    logs = [
        {"action": "campaign.created", "actor": "system", "target": f"campaign_{uuid.uuid4().hex[:8]}", "details": {"product_title": "Sample Product", "status": "active"}},
        {"action": "pipeline.completed", "actor": "autonomous_pipeline", "target": f"pipeline_{uuid.uuid4().hex[:8]}", "details": {"hooks": 10, "videos": 3}},
        {"action": "product.analyzed", "actor": "product_agent", "target": f"prod_{uuid.uuid4().hex[:8]}", "details": {"category": "elektronik", "rating": 4.5}},
    ]
    for l in logs:
        await session.execute(AuditLogEntry.__table__.insert().values(id=str(uuid.uuid4()), **l))
    return len(logs)


async def _seed_alert_rules(session, campaign_ids, cid, force=False):
    if await _count(session, AlertRule) > 0 and not force:
        return 0
    rules = [
        {"name": "Low CTR Alert", "metric": "ctr", "condition": "lt", "threshold": 1.0, "campaign_id": cid or random.choice(campaign_ids), "enabled": 1, "cooldown_minutes": 60},
        {"name": "Daily Budget Alert", "metric": "spend", "condition": "gt", "threshold": 500000, "campaign_id": cid or random.choice(campaign_ids), "enabled": 1, "cooldown_minutes": 1440},
        {"name": "Viral Detection", "metric": "engagement", "condition": "gt", "threshold": 10.0, "campaign_id": "", "enabled": 1, "cooldown_minutes": 30},
    ]
    for r in rules:
        await session.execute(AlertRule.__table__.insert().values(id=str(uuid.uuid4()), **r))
    return len(rules)


async def _seed_performance_alerts(session, campaign_ids, cid, force=False):
    if await _count(session, PerformanceAlert) > 0 and not force:
        return 0
    alerts = [
        {"campaign_id": cid or random.choice(campaign_ids), "rule_id": str(uuid.uuid4()), "metric_value": 0.8, "severity": "warning", "message": "CTR turun di bawah 1%", "acknowledged": 0},
        {"campaign_id": cid or random.choice(campaign_ids), "rule_id": str(uuid.uuid4()), "metric_value": 12.5, "severity": "info", "message": "Engagement spike detected!", "acknowledged": 0},
    ]
    for a in alerts:
        await session.execute(PerformanceAlert.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(alerts)


async def _seed_revenue_data_points(session, campaign_ids, cid, force=False):
    if await _count(session, RevenueDataPoint) > 0 and not force:
        return 0
    points = []
    for i in range(14):
        points.append({
            "campaign_id": cid or random.choice(campaign_ids),
            "date": _ts(14 - i)[:10],
            "revenue": round(random.uniform(50000, 500000), 0),
            "expenses": round(random.uniform(10000, 100000), 0),
            "source": random.choice(["shopee", "tokopedia", "tiktok"]),
        })
    for p in points:
        await session.execute(RevenueDataPoint.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(points)


async def _seed_revenue_forecasts(session, force=False):
    if await _count(session, RevenueForecast) > 0 and not force:
        return 0
    forecasts = [
        {"period": "2026-07", "predicted_revenue": round(random.uniform(10000000, 50000000), 0), "confidence": 0.75, "assumptions": {"growth_rate": 0.15, "new_campaigns": 5}},
        {"period": "2026-08", "predicted_revenue": round(random.uniform(15000000, 60000000), 0), "confidence": 0.60, "assumptions": {"growth_rate": 0.20, "new_campaigns": 8}},
    ]
    for f in forecasts:
        await session.execute(RevenueForecast.__table__.insert().values(id=str(uuid.uuid4()), **f))
    return len(forecasts)


async def _seed_voice_profiles(session, force=False):
    if await _count(session, VoiceProfile) > 0 and not force:
        return 0
    # VoiceProfile doesn't exist in models? Skip if error
    return 0


async def _seed_webhook_configs(session, force=False):
    if await _count(session, WebhookConfig) > 0 and not force:
        return 0
    hooks = [
        {"name": "Discord Alerts", "url": "https://discord.com/api/webhooks/titan", "enabled": 1, "events": ["campaign.created", "viral.detected"]},
        {"name": "Slack Notifications", "url": "https://hooks.slack.com/services/titan", "enabled": 1, "events": ["pipeline.complete", "pipeline.failed"]},
    ]
    for h in hooks:
        await session.execute(WebhookConfig.__table__.insert().values(id=str(uuid.uuid4()), **h))
    return len(hooks)


async def _seed_telegram_configs(session, force=False):
    if await _count(session, TelegramConfig) > 0 and not force:
        return 0
    configs = [
        {"chat_id": "-1001234567890", "enabled": 1, "notify_on": ["campaign_created", "viral_detected", "daily_report"]},
    ]
    for c in configs:
        await session.execute(TelegramConfig.__table__.insert().values(id=str(uuid.uuid4()), **c))
    return len(configs)


async def _seed_affiliate_accounts(session, force=False):
    if await _count(session, AffiliateAccount) > 0 and not force:
        return 0
    accounts = [
        {"platform": "shopee", "account_id": "aff_shopee_001", "status": "active", "earnings": round(random.uniform(500000, 5000000), 0), "metadata": {"tier": "gold"}},
        {"platform": "tokopedia", "account_id": "aff_tokped_001", "status": "active", "earnings": round(random.uniform(300000, 3000000), 0), "metadata": {"tier": "silver"}},
    ]
    for a in accounts:
        await session.execute(AffiliateAccount.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(accounts)


async def _seed_brand_mentions(session, force=False):
    if await _count(session, BrandMention) > 0 and not force:
        return 0
    mentions = [
        {"brand": "TitanStore", "platform": "tiktok", "content": "Produk TitanStore bikin glowing! #skincare", "sentiment": "positive", "reach": random.randint(1000, 10000)},
        {"brand": "TitanStore", "platform": "instagram", "content": "Review TitanStore — overall bagus", "sentiment": "positive", "reach": random.randint(500, 5000)},
        {"brand": "TitanStore", "platform": "twitter", "content": "pengiriman titanstore lambat banget", "sentiment": "negative", "reach": random.randint(100, 1000)},
    ]
    for m in mentions:
        await session.execute(BrandMention.__table__.insert().values(id=str(uuid.uuid4()), **m))
    return len(mentions)


async def _seed_influencer_profiles(session, force=False):
    if await _count(session, InfluencerProfile) > 0 and not force:
        return 0
    profiles = [
        {"name": "BeautyBySari", "platform": "tiktok", "followers": 50000, "niche": "kecantikan", "engagement_rate": 5.2, "reach": 15000, "notes": "High engagement, good for skincare"},
        {"name": "TechReviewID", "platform": "instagram", "followers": 35000, "niche": "elektronik", "engagement_rate": 3.8, "reach": 8000, "notes": "Tech specialist"},
    ]
    for p in profiles:
        await session.execute(InfluencerProfile.__table__.insert().values(id=str(uuid.uuid4()), **p))
    return len(profiles)


async def _seed_competitor_watches(session, force=False):
    if await _count(session, CompetitorWatch) > 0 and not force:
        return 0
    watches = [
        {"competitor_name": "Toko Sejahtera", "platform": "shopee", "metric": "price", "current_value": 150000, "alert_threshold": 120000},
        {"competitor_name": "BeautyHunt", "platform": "tiktok", "metric": "followers", "current_value": 250000, "alert_threshold": 300000},
    ]
    for w in watches:
        await session.execute(CompetitorWatch.__table__.insert().values(id=str(uuid.uuid4()), **w))
    return len(watches)


async def _seed_content_ideas(session, force=False):
    if await _count(session, ContentIdea) > 0 and not force:
        return 0
    ideas = [
        {"content_type": "video", "topic": "Review skincare viral 2026", "category": "kecantikan", "estimated_engagement": 8.5, "difficulty": "mudah", "source": "trend_analysis"},
        {"topic": "Perbandingan gadget under 500rb", "category": "elektronik", "estimated_engagement": 6.0, "difficulty": "sedang", "source": "competitor_gap"},
    ]
    for i in ideas:
        await session.execute(ContentIdea.__table__.insert().values(id=str(uuid.uuid4()), **i))
    return len(ideas)


async def _seed_pricing_analyses(session, product_ids, pid, force=False):
    if await _count(session, PricingAnalysis) > 0 and not force:
        return 0
    analyses = [
        {"product_id": pid or random.choice(product_ids), "market_avg_price": 170000, "competitor_min": 120000, "competitor_max": 220000, "demand_score": 85, "supply_score": 45, "recommended_price": 165000, "strategy": "competitive"},
        {"product_id": random.choice(product_ids), "market_avg_price": 500000, "competitor_min": 350000, "competitor_max": 750000, "demand_score": 70, "supply_score": 60, "recommended_price": 480000, "strategy": "premium"},
    ]
    for a in analyses:
        await session.execute(PricingAnalysis.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(analyses)


async def _seed_budget_allocations(session, campaign_ids, cid, force=False):
    if await _count(session, BudgetAllocation) > 0 and not force:
        return 0
    allocs = [
        {"campaign_id": cid or random.choice(campaign_ids), "total_budget": 1000000, "allocated": 750000, "spent": 450000, "period": "2026-07", "roi": round(random.uniform(1.5, 4.0), 2)},
        {"campaign_id": cid or random.choice(campaign_ids), "total_budget": 2000000, "allocated": 1500000, "spent": 1200000, "period": "2026-07", "roi": round(random.uniform(2.0, 5.0), 2)},
    ]
    for a in allocs:
        await session.execute(BudgetAllocation.__table__.insert().values(id=str(uuid.uuid4()), **a))
    return len(allocs)


async def _seed_batch_jobs(session, force=False):
    if await _count(session, BatchJob) > 0 and not force:
        return 0
    jobs = [
        {"job_type": "video_generation", "total_items": 10, "processed": 8, "successful": 7, "failed": 1, "status": "running", "config": {"model": "wan2.7-i2v", "resolution": "720p"}, "created_at_iso": _ts(0)},
        {"job_type": "content_remix", "total_items": 5, "processed": 5, "successful": 5, "failed": 0, "status": "completed", "config": {"platforms": ["tiktok", "instagram"]}, "created_at_iso": _ts(-1)},
    ]
    for j in jobs:
        await session.execute(BatchJob.__table__.insert().values(id=str(uuid.uuid4()), **j))
    return len(jobs)


async def _seed_auto_reports(session, force=False):
    if await _count(session, AutoReport) > 0 and not force:
        return 0
    reports = [
        {"report_type": "weekly", "config": {"channels": ["telegram", "discord"], "include": ["revenue", "campaigns", "top_products"]}, "last_generated": _ts(-1), "schedule_cron": "0 9 * * 1"},
        {"report_type": "daily", "config": {"channels": ["telegram"], "include": ["revenue", "alerts"]}, "last_generated": _ts(0), "schedule_cron": "0 8 * * *"},
    ]
    for r in reports:
        await session.execute(AutoReport.__table__.insert().values(id=str(uuid.uuid4()), **r))
    return len(reports)


async def _seed_pipeline_runs(session, product_ids, force=False):
    if await _count(session, PipelineRun) > 0 and not force:
        return 0
    runs = []
    for i in range(3):
        runs.append({
            "pipeline_id": f"pipe-{uuid.uuid4().hex[:12]}",
            "product_url": "https://shopee.co.id/product/test",
            "status": random.choice(["complete", "failed", "running"]),
            "features_used": ["product_agent", "review_agent", "content_agent"],
            "started_at_iso": _ts(i),
            "hooks_count": random.randint(5, 15),
            "scripts_count": random.randint(3, 8),
            "video_count": random.randint(1, 4),
        })
    for r in runs:
        await session.execute(PipelineRun.__table__.insert().values(id=str(uuid.uuid4()), **r))
    return len(runs)


async def _seed_smart_schedule_slots(session, force=False):
    if await _count(session, SmartScheduleSlot) > 0 and not force:
        return 0
    slots = []
    for platform in ["tiktok", "instagram", "facebook"]:
        for hour in [7, 12, 18, 19, 20, 21]:
            slots.append({
                "platform": platform,
                "hour": hour,
                "day_of_week": random.randint(1, 7),
            })
    for s in slots[:12]:
        await session.execute(SmartScheduleSlot.__table__.insert().values(id=str(uuid.uuid4()), **s))
    return len(slots[:12])


async def _seed_cross_platform_metrics(session, campaign_ids, cid, force=False):
    if await _count(session, CrossPlatformMetric) > 0 and not force:
        return 0
    metrics = [
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "tiktok", "views": random.randint(5000, 50000), "engagement": round(random.uniform(2.0, 8.0), 2), "period": "2026-07"},
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "instagram", "views": random.randint(3000, 30000), "engagement": round(random.uniform(1.5, 5.0), 2), "period": "2026-07"},
        {"campaign_id": cid or random.choice(campaign_ids), "platform": "facebook", "views": random.randint(2000, 20000), "engagement": round(random.uniform(1.0, 4.0), 2), "period": "2026-07"},
    ]
    for m in metrics:
        await session.execute(CrossPlatformMetric.__table__.insert().values(id=str(uuid.uuid4()), **m))
    return len(metrics)


# ── Main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    logging.basicConfig(level=logging.INFO)
    results = asyncio.run(seed_all(force=force))
    print("\n📊 SEED RESULTS:")
    total = 0
    for table, count in results.items():
        emoji = "✅" if isinstance(count, int) and count > 0 else "ℹ️" if isinstance(count, int) else "❌"
        print(f"  {emoji} {table}: {count}")
        if isinstance(count, int):
            total += count
    print(f"\n{'='*40}")
    print(f"📦 Total rows seeded: {total}")
    print(f"📋 Tables with data: {sum(1 for v in results.values() if isinstance(v, int) and v > 0)}/{len(results)}")
