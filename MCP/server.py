"""FastMCP server for TITAN AIO."""

from __future__ import annotations

from fastmcp import FastMCP

from MCP.schemas import (
    AnalyzeProductInput,
    AnalyzeReviewsInput,
    AnalyzeCompetitorsInput,
    GenerateOfferInput,
    GenerateHooksInput,
    GenerateScriptInput,
    GenerateThumbnailInput,
    GenerateImageInput,
    GenerateVideoInput,
    GenerateAvatarInput,
    CreateAffiliatePackageInput,
    SaveCampaignInput,
    LoadCampaignInput,
    GetMetricsInput,
    GetRecommendationsInput,
    SearchProductInput,
    AnalyzeProductOutput,
    AnalyzeReviewsOutput,
    AnalyzeCompetitorsOutput,
    GenerateOfferOutput,
)
from MCP.tools.health import health
from MCP.tools.search_product import search_product
from MCP.tools.analyze_product import analyze_product
from MCP.tools.analyze_reviews import analyze_reviews
from MCP.tools.analyze_competitors import analyze_competitors
from MCP.tools.generate_offer import generate_offer
from MCP.tools.generate_hooks import generate_hooks
from MCP.tools.generate_script import generate_script
from MCP.tools.generate_thumbnail import generate_thumbnail
from MCP.tools.generate_image import generate_image
from MCP.tools.generate_video import generate_video
from MCP.tools.generate_avatar import generate_avatar
from MCP.tools.create_affiliate_package import create_affiliate_package
from MCP.tools.save_campaign import save_campaign
from MCP.tools.load_campaign import load_campaign
from MCP.tools.get_metrics import get_metrics
from MCP.tools.get_recommendations import get_recommendations
from MCP.tools.notion_tools import (
    notion_save_campaign,
    notion_save_knowledge,
    notion_create_task,
    notion_query_campaigns,
)
from MCP.tools.trend_tools import analyze_trend, analyze_competitor, evaluate_campaign_finance, decide_growth_action, store_winning_hook
from MCP.tools.memory_tools import memory_store_hook, memory_find_similar_hooks, memory_store_product_knowledge, memory_find_similar_products
from MCP.tools.publisher_tools import prepare_platform_content, track_campaign_metrics
from MCP.tools.publisher_v2_tools import (
    upload_to_social,
    upload_to_all,
    login_to_platform,
    prepare_and_upload,
)
from MCP.tools.video_avatar_tools import (
    generate_product_video,
    generate_spokesperson_avatar,
    generate_lora_model,
)
from MCP.tools.new_agent_tools import (
    collect_product_assets,
    generate_affiliate_links,
    build_campaign_package,
    discover_products,
)
from MCP.tools.scraper_tools import (
    discover_products as scraper_discover_products,
    discover_trending_products,
    get_product_details_data,
    find_high_commission,
)
from MCP.tools.graph_tools import run_graph_campaign
from MCP.tools.dashboard_tools import (
    dashboard_push_campaign,
    dashboard_push_knowledge,
    dashboard_list_active_campaigns,
    dashboard_list_pending_tasks,
    dashboard_query_knowledge,
)
from MCP.tools.batch_variant_tools import (
    generate_batch_variants,
    analyze_batch_performance,
)
from MCP.tools.lip_sync_tools import (
    generate_lip_sync_video,
    install_lip_sync_engine,
)
from MCP.tools.google_flow_tools import (
    generate_flow_video,
    login_google_flow,
)
from MCP.tools.autonomous_pipeline_tools import (
    run_autonomous_pipeline,
)
from MCP.tools.cloud_browser_tools import (
    cloud_navigate_url,
    cloud_screenshot_url,
)
from MCP.tools.remix_tools import remix_content as _remix_content
from MCP.tools.viral_tools import predict_virality as _predict_virality
from MCP.tools.voice_tools import (
    create_voice_profile as _create_voice_profile,
    generate_voice as _generate_voice,
    list_voice_profiles as _list_voice_profiles,
    get_voice_profile as _get_voice_profile,
    update_voice_profile as _update_voice_profile,
    delete_voice_profile as _delete_voice_profile,
    generate_batch_voices as _generate_batch_voices,
    generate_voice_variations as _generate_voice_variations,
    get_voice_history as _get_voice_history,
    get_voice_style_presets as _get_voice_style_presets,
    validate_voice_profile as _validate_voice_profile,
)
from MCP.tools.ab_tools import (
    create_ab_test as _create_ab_test,
    update_ab_test as _update_ab_test,
    get_ab_results as _get_ab_results,
    list_ab_tests as _list_ab_tests,
    promote_ab_winner as _promote_ab_winner,
    delete_ab_test as _delete_ab_test,
    calculate_sample_size as _calculate_sample_size,
)
from MCP.tools.trend_monitor_tools import monitor_trends as _monitor_trends
from MCP.tools.thumbnail_tools import generate_thumbnails as _generate_thumbnails
from MCP.tools.affiliate_optimizer_tools import optimize_affiliate as _optimize_affiliate
from MCP.tools.seo_tools import seo_optimize as _seo_optimize
from MCP.tools.sentiment_tools import monitor_sentiment as _monitor_sentiment
from MCP.tools.pipeline_tools import get_pipeline_health as _get_pipeline_health
from MCP.tools.content_calendar_tools import schedule_content_post, get_content_calendar, find_best_posting_times, cancel_scheduled_post, reschedule_post, get_calendar_stats
from MCP.tools.webhook_tools import register_webhook_alert, send_webhook_alert, list_webhook_alerts, get_alert_history, delete_webhook_alert
from MCP.tools.infra_tools import check_api_rate_limit, acquire_api_slot, get_api_rate_usage, reset_api_rate_limit, cache_get, cache_set, cache_stats
from MCP.tools.audit_tools import log_audit_event, query_audit_log, get_audit_stats
from MCP.tools.compliance_tools import check_content_compliance, create_niche_campaign
from MCP.tools.ml_scorer_tools import ml_score_content, ml_batch_score
from MCP.tools.cross_platform_tools import record_platform_metrics, generate_cross_platform_report, get_platform_comparison
from MCP.tools.versioning_tools import create_content_version, get_content_versions, revert_content_version, compare_content_versions, update_version_score
from MCP.tools.batch_processor_tools import create_batch_job, run_batch_job, get_batch_status, pause_batch_job, list_batch_jobs, get_batch_stats
from MCP.tools.dynamic_pricing_tools import analyze_product_pricing, bulk_price_analysis, get_pricing_recommendations, get_pricing_stats
from MCP.tools.telegram_tools import configure_telegram_bot, send_telegram_notification, handle_telegram_command, get_telegram_stats
from MCP.tools.revenue_tools import record_revenue, forecast_revenue, get_revenue_breakdown, get_revenue_stats
from MCP.tools.advanced_tools import (
    generate_auto_report, record_report_data, set_total_budget, register_campaign_budget, optimize_budget, get_budget_summary,
    get_optimal_posting_times, suggest_posting_schedule, record_engagement_data,
    create_alert_rule, record_performance_metric, get_performance_alerts, acknowledge_alert,
    generate_content_ideas, get_saved_ideas,
    add_competitor_watch, check_competitor_metrics, list_competitor_watches,
    add_brand_to_watch, record_brand_mention, get_brand_mentions, get_sentiment_summary,
    find_influencers, add_affiliate_account, record_account_earnings, list_affiliate_accounts, get_earnings_summary,
)
from MCP.tools.websocket_tools import ws_broadcast_metric, ws_broadcast_alert, ws_broadcast_pipeline, ws_get_connections
from MCP.tools.shopee_tools import shopee_search_products, shopee_get_product, shopee_get_trending, shopee_find_high_commission
from MCP.tools.social_api_tools import tiktok_trending, tiktok_search, tiktok_analyze, tiktok_creator, social_search, social_trending, social_brand_mentions
from MCP.tools.ecommerce_tools import search_products, get_product_details, get_trending_products, compare_products, find_affiliate_products
from MCP.tools.shopee_tools import shopee_search_products, shopee_get_product, shopee_get_trending, shopee_find_high_commission
from MCP.tools.social_api_tools import tiktok_trending, tiktok_search, tiktok_analyze, tiktok_creator, social_search, social_trending, social_brand_mentions
from MCP.tools.ecommerce_tools import search_products, get_product_details, get_trending_products, compare_products, find_affiliate_products
from MCP.tools.shopee_tools import shopee_search_products, shopee_get_product, shopee_get_trending, shopee_find_high_commission
from MCP.tools.social_api_tools import tiktok_trending, tiktok_search, tiktok_analyze, tiktok_creator, social_search, social_trending, social_brand_mentions
from MCP.tools.ecommerce_tools import search_products, get_product_details, get_trending_products, compare_products, find_affiliate_products
from MCP.tools.shopee_tools import shopee_search_products, shopee_get_product, shopee_get_trending, shopee_find_high_commission
from MCP.tools.social_api_tools import tiktok_trending, tiktok_search, tiktok_analyze, tiktok_creator, social_search, social_trending, social_brand_mentions
from MCP.tools.ecommerce_tools import search_products, get_product_details, get_trending_products, compare_products, find_affiliate_products

mcp = FastMCP(
    "TITAN AIO",
)


@mcp.tool()
async def health_check() -> dict:
    """Check if the TITAN AIO system is healthy."""
    result = await health()
    return result.model_dump()


@mcp.tool()
async def search_products(query: str, platform: str = "", limit: int = 10) -> dict:
    """Search for affiliate products. Returns matching products."""
    input_data = SearchProductInput(
        query=query, platform=platform or None, limit=limit
    )
    result = await search_product(input_data)
    return result.model_dump()


@mcp.tool()
async def analyze_product_url(url: str) -> dict:
    """Analyze a product from its Shopee/Tokopedia URL. Returns product intelligence."""
    input_data = AnalyzeProductInput(url=url)
    result = await analyze_product(input_data)
    return result.model_dump()


@mcp.tool()
async def analyze_product_reviews(
    product_id: str, max_reviews: int = 100
) -> dict:
    """Analyze reviews for a product. Returns pain points, objections, benefits."""
    input_data = AnalyzeReviewsInput(
        product_id=product_id, max_reviews=max_reviews
    )
    result = await analyze_reviews(input_data)
    return result.model_dump()


@mcp.tool()
async def analyze_competitors_for_category(
    category: str, limit: int = 10
) -> dict:
    """Analyze competitor ads and hooks for a category."""
    input_data = AnalyzeCompetitorsInput(category=category, limit=limit)
    result = await analyze_competitors(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_offer_strategy(
    product_id: str,
    product_analysis: dict,
    review_analysis: dict | None = None,
    competitor_analysis: dict | None = None,
) -> dict:
    """Generate optimal offer strategy from analyses."""
    input_data = GenerateOfferInput(
        product_id=product_id,
        product_analysis=AnalyzeProductOutput(**product_analysis),
        review_analysis=(
            AnalyzeReviewsOutput(**review_analysis) if review_analysis else None
        ),
        competitor_analysis=(
            AnalyzeCompetitorsOutput(**competitor_analysis)
            if competitor_analysis
            else None
        ),
    )
    result = await generate_offer(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_hooks_for_product(
    product_id: str, offer_strategy: dict, count: int = 10
) -> dict:
    """Generate attention-grabbing hooks for a product."""
    input_data = GenerateHooksInput(
        product_id=product_id,
        offer_strategy=GenerateOfferOutput(**offer_strategy),
        count=count,
    )
    result = await generate_hooks(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_ugc_scripts(
    product_id: str,
    hooks: list[dict],
    offer_strategy: dict,
    count: int = 10,
) -> dict:
    """Generate full UGC scripts from hooks."""
    from MCP.schemas import Hook

    input_data = GenerateScriptInput(
        product_id=product_id,
        hooks=[Hook(**h) for h in hooks],
        offer_strategy=GenerateOfferOutput(**offer_strategy),
        count=count,
    )
    result = await generate_script(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_thumbnail_concept(
    product_id: str, style: str = "bold"
) -> dict:
    """Generate a thumbnail concept for a product."""
    input_data = GenerateThumbnailInput(product_id=product_id, style=style)
    result = await generate_thumbnail(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_product_image(
    prompt: str, model: str = "flux-schnell"
) -> dict:
    """Generate a product image using FLUX."""
    input_data = GenerateImageInput(prompt=prompt, model=model)
    result = await generate_image(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_video_from_script(
    script: str, model: str = "wan-2-2"
) -> dict:
    """Generate a video from script using Wan 2.2 or Hunyuan."""
    input_data = GenerateVideoInput(script=script, model=model)
    result = await generate_video(input_data)
    return result.model_dump()


@mcp.tool()
async def generate_ai_avatar(
    persona_name: str, style: str = "realistic"
) -> dict:
    """Generate an AI spokesperson avatar."""
    input_data = GenerateAvatarInput(
        persona_name=persona_name, style=style
    )
    result = await generate_avatar(input_data)
    return result.model_dump()


@mcp.tool()
async def create_full_affiliate_package(
    url: str, include_video: bool = False, include_avatar: bool = False
) -> dict:
    """Create a complete affiliate package from a product URL. One-shot pipeline."""
    input_data = CreateAffiliatePackageInput(
        url=url, include_video=include_video, include_avatar=include_avatar
    )
    result = await create_affiliate_package(input_data)
    return result.model_dump()


@mcp.tool()
async def save_campaign_data(
    product_id: str, name: str, platform: str = "", budget: float = 0.0
) -> dict:
    """Save a campaign to the database."""
    input_data = SaveCampaignInput(
        product_id=product_id,
        name=name,
        platform=platform or None,
        budget=budget if budget > 0 else None,
    )
    result = await save_campaign(input_data)
    return result.model_dump()


@mcp.tool()
async def load_campaign_data(campaign_id: str) -> dict:
    """Load a campaign from the database."""
    input_data = LoadCampaignInput(campaign_id=campaign_id)
    result = await load_campaign(input_data)
    return result.model_dump()


@mcp.tool()
async def get_campaign_metrics(campaign_id: str) -> dict:
    """Get metrics for a campaign."""
    input_data = GetMetricsInput(campaign_id=campaign_id)
    result = await get_metrics(input_data)
    return result.model_dump()


@mcp.tool()
async def get_campaign_recommendations(
    category: str = "", limit: int = 5
) -> dict:
    """Get campaign recommendations from historical data."""
    input_data = GetRecommendationsInput(
        category=category or None, limit=limit
    )
    result = await get_recommendations(input_data)
    return result.model_dump()


@mcp.tool()
async def notion_save_campaign_data(
    campaign_id: str,
    name: str,
    product_title: str,
    revenue: float = 0.0,
    status: str = "Active",
) -> dict:
    """Save campaign data to a Notion database for tracking."""
    return await notion_save_campaign(
        campaign_id=campaign_id,
        name=name,
        product_title=product_title,
        revenue=revenue,
        status=status,
    )


@mcp.tool()
async def notion_save_knowledge_entry(
    category: str,
    pattern: str,
    confidence: float,
    actionable_advice: str = "",
) -> dict:
    """Save a knowledge/insight entry to your Notion knowledge base."""
    return await notion_save_knowledge(
        category=category,
        pattern=pattern,
        confidence=confidence,
        actionable_advice=actionable_advice,
    )


@mcp.tool()
async def notion_create_task_item(
    title: str, status: str = "Not started", priority: str = "Medium"
) -> dict:
    """Create a task in your Notion tasks database."""
    return await notion_create_task(
        title=title, status=status, priority=priority
    )


@mcp.tool()
async def notion_list_campaigns(
    status_filter: str = "", limit: int = 20
) -> list[dict]:
    """List campaigns from your Notion campaigns database."""
    return await notion_query_campaigns(
        status_filter=status_filter or None, limit=limit
    )


@mcp.tool()
async def analyze_market_trend(category: str = "") -> dict:
    """Analyze market trends for a product category."""
    return await analyze_trend(category=category)


@mcp.tool()
async def analyze_market_competitors(category: str = "umum") -> dict:
    """Analyze competitor landscape and winning hooks."""
    return await analyze_competitor(category=category)


@mcp.tool()
async def evaluate_campaign_finances(campaign_id: str, revenue: float, ad_spend: float) -> dict:
    """Evaluate campaign financial performance."""
    return await evaluate_campaign_finance(campaign_id=campaign_id, revenue=revenue, ad_spend=ad_spend)


@mcp.tool()
async def decide_campaign_growth(roi: float) -> dict:
    """Get growth recommendation (scale/kill/maintain) based on ROI."""
    return await decide_growth_action(roi=roi)


@mcp.tool()
async def memory_save_hook(hook_text: str, hook_type: str = "curiosity", campaign_id: str = "") -> dict:
    """Save a winning hook to vector memory."""
    return await memory_store_hook(hook_text=hook_text, hook_type=hook_type, campaign_id=campaign_id)


@mcp.tool()
async def memory_search_hooks(query: str, top_k: int = 5) -> list[dict]:
    """Search for similar hooks using semantic search."""
    return await memory_find_similar_hooks(query=query, top_k=top_k)


@mcp.tool()
async def memory_save_product_knowledge(product_id: str, knowledge: str) -> dict:
    """Store product intelligence in knowledge base."""
    return await memory_store_product_knowledge(product_id=product_id, knowledge=knowledge)


@mcp.tool()
async def track_campaign_performance(campaign_id: str) -> dict:
    """Get campaign performance metrics."""
    return await track_campaign_metrics(campaign_id=campaign_id)


@mcp.tool()
async def prepare_social_content(caption: str = "") -> list[dict]:
    """Format content for all social platforms."""
    return await prepare_platform_content(caption=caption)


@mcp.tool()
async def generate_product_video_tool(product_id: str, script_text: str, model: str = "wan-2-2") -> dict:
    """Generate a short-form product video using AI models (Wan 2.2 / Hunyuan)."""
    return await generate_product_video(product_id=product_id, script_text=script_text, model=model)


@mcp.tool()
async def generate_spokesperson_avatar_tool(name: str = "AI Spokesperson", style: str = "realistic") -> dict:
    """Generate a consistent AI spokesperson avatar for UGC content."""
    return await generate_spokesperson_avatar(name=name, style=style)


@mcp.tool()
async def generate_product_lora(product_id: str, image_urls: list[str]) -> dict:
    """Train a product-specific LoRA model. Enforces usage-threshold policy."""
    return await generate_lora_model(product_id=product_id, image_urls=image_urls)


@mcp.tool()
async def dashboard_push_campaign_result(product_id: str, title: str, price: float, campaign_id: str = "", url: str = "") -> dict:
    """Push a campaign result to the Notion dashboard."""
    return await dashboard_push_campaign(product_id=product_id, title=title, price=price, campaign_id=campaign_id, url=url)


@mcp.tool()
async def dashboard_save_knowledge(category: str, pattern: str, confidence: float = 0.5, advice: str = "") -> dict:
    """Save a knowledge/insight entry to the Notion dashboard knowledge base."""
    return await dashboard_push_knowledge(category=category, pattern=pattern, confidence=confidence, advice=advice)


@mcp.tool()
async def dashboard_get_active_campaigns(limit: int = 10) -> list[dict]:
    """Get active campaigns from your Notion dashboard."""
    return await dashboard_list_active_campaigns(limit=limit)


@mcp.tool()
async def dashboard_get_pending_tasks(limit: int = 10) -> list[dict]:
    """Get pending tasks from your Notion dashboard."""
    return await dashboard_list_pending_tasks(limit=limit)


@mcp.tool()
async def dashboard_search_knowledge(category: str = "", limit: int = 10) -> list[dict]:
    """Search the Notion knowledge base by category."""
    return await dashboard_query_knowledge(category=category, limit=limit)


@mcp.tool()
async def collect_product_assets_tool(product_id: str, image_urls: list[str] | None = None) -> dict:
    """Download and prepare product assets (images) for campaign creatives."""
    return await collect_product_assets(product_id=product_id, image_urls=image_urls)


@mcp.tool()
async def generate_affiliate_links_tool(product_url: str = "", product_id: str = "", platform: str = "shopee") -> dict:
    """Generate affiliate tracking links for Shopee or Tokopedia."""
    return await generate_affiliate_links(product_url=product_url, product_id=product_id, platform=platform)


@mcp.tool()
async def build_campaign_package_tool(
    product: dict | None = None,
    reviews: dict | None = None,
    hooks: list | None = None,
    scripts: list | None = None,
    thumbnail: str = "",
    images: list | None = None,
    video: str = "",
    captions: dict | None = None,
    affiliate_links: dict | None = None,
    publishing: dict | None = None,
) -> dict:
    """Build a complete campaign package from all components (product, reviews, hooks, scripts, media, captions, links, publishing)."""
    return await build_campaign_package(
        product=product,
        reviews=reviews,
        hooks=hooks,
        scripts=scripts,
        thumbnail=thumbnail,
        images=images,
        video=video,
        captions=captions,
        affiliate_links=affiliate_links,
        publishing=publishing,
    )


@mcp.tool()
async def discover_products_tool(keyword: str = "", category: str = "", platform: str = "") -> dict:
    """Search and discover products for affiliate campaigns by keyword or category."""
    return await discover_products(keyword=keyword, category=category, platform=platform)


@mcp.tool()
async def upload_video_to_social(platform: str, video_path: str, caption: str, hashtags: str = "") -> dict:
    """Upload a video to TikTok, Instagram, or Facebook. Requires prior login."""
    return await upload_to_social(platform=platform, video_path=video_path, caption=caption, hashtags=hashtags)


@mcp.tool()
async def upload_video_to_all(video_path: str, caption: str, hashtags: str = "", platforms: str = "") -> dict:
    """Upload video to ALL platforms in parallel (TikTok, Instagram, Facebook).

    Args:
        video_path: Path to video file.
        caption: Caption text.
        hashtags: Space-separated hashtags.
        platforms: Comma-separated platform names. Empty = all.
    """
    return await upload_to_all(video_path=video_path, caption=caption, hashtags=hashtags, platforms=platforms)


@mcp.tool()
async def login_to_social_platform(platform: str) -> dict:
    """Login to a social platform (TikTok/Instagram/Facebook). Only needed once — session saved."""
    return await login_to_platform(platform=platform)


@mcp.tool()
async def auto_generate_and_upload(product_url: str, platform: str = "tiktok") -> dict:
    """One-shot: analyze product → generate video → upload to platform."""
    return await prepare_and_upload(product_url=product_url, platform=platform)


@mcp.tool()
async def search_products_auto(keyword: str, platform: str = "shopee", max_results: int = 10) -> list[dict]:
    """Search for products by keyword. No URL needed. Auto-scrapes Shopee/Tokopedia."""
    return await scraper_discover_products(keyword=keyword, platform=platform, max_results=max_results)


@mcp.tool()
async def discover_trending(category: str = "") -> list[dict]:
    """Find trending products from social media + e-commerce data."""
    return await discover_trending_products(category=category)


@mcp.tool()
async def get_product_details(product_url: str) -> dict:
    """Get detailed product information from a product URL."""
    return await get_product_details_data(product_url=product_url)


@mcp.tool()
async def run_campaign_graph(url: str) -> dict:
    """Run a complete affiliate campaign using LangGraph workflow. Step-by-step AI orchestration."""
    return await run_graph_campaign(url=url)


# ── Batch A/B Variant Tools ──────────────────────────────────────


@mcp.tool()
async def generate_ab_variants(
    product_url: str,
    product_title: str = "",
    num_variants: int = 3,
    platforms: list[str] | None = None,
    duration_seconds: int = 30,
) -> dict:
    """Generate multiple A/B variants for a product. Each variant gets unique hook, script, style, and thumbnail.

    Use for A/B testing across platforms. Returns batch with variant IDs for tracking.
    """
    from MCP.tools.batch_variant_tools import BatchVariantInput
    input_data = BatchVariantInput(
        product_url=product_url,
        product_title=product_title,
        num_variants=num_variants,
        platforms=platforms or ["tiktok"],
        duration_seconds=duration_seconds,
    )
    result = await generate_batch_variants(input_data)
    return result.model_dump()


@mcp.tool()
async def analyze_ab_results(batch_id: str) -> dict:
    """Analyze A/B test results and recommend the winning variant.

    Returns best variant, optimization recommendations, and budget scaling suggestions.
    """
    from MCP.tools.batch_variant_tools import AnalyzeBatchInput
    input_data = AnalyzeBatchInput(batch_id=batch_id)
    result = await analyze_batch_performance(input_data)
    return result.model_dump()


# ── Lip Sync Tools ──────────────────────────────────────────────


@mcp.tool()
async def create_lip_sync_video(
    audio_path: str,
    face_image: str | None = None,
    face_video: str | None = None,
    engine: str = "auto",
) -> dict:
    """Generate lip sync video from audio + face image/video.

    Engines: wav2lip (high quality), sadtalker (head movement), wan_native (fallback).
    Auto-detects best available engine.
    """
    from MCP.tools.lip_sync_tools import LipSyncInput
    input_data = LipSyncInput(
        audio_path=audio_path,
        face_image=face_image,
        face_video=face_video,
        engine=engine,
    )
    result = await generate_lip_sync_video(input_data)
    return result.model_dump()


@mcp.tool()
async def setup_lip_sync(engine: str = "wav2lip") -> dict:
    """Install a lip sync engine (Wav2Lip or SadTalker).

    Downloads models and sets up the environment. Requires git, python3, pip.
    """
    from MCP.tools.lip_sync_tools import InstallLipSyncInput
    input_data = InstallLipSyncInput(engine=engine)
    result = await install_lip_sync_engine(input_data)
    return result.model_dump()


# ── Google Flow (VideoFX) Tools ──────────────────────────────────


@mcp.tool()
async def generate_video_with_flow(
    prompt: str,
    style: str = "cinematic",
    duration: str = "5s",
    aspect_ratio: str = "16:9",
) -> dict:
    """Generate a video using Google Flow (VideoFX).

    High-quality AI video generation via labs.google/flow.
    Free tier: 50 credits/day. Login required first.
    """
    from MCP.tools.google_flow_tools import FlowGenerateInput
    input_data = FlowGenerateInput(
        prompt=prompt,
        style=style,
        duration=duration,
        aspect_ratio=aspect_ratio,
    )
    result = await generate_flow_video(input_data)
    return result.model_dump()


@mcp.tool()
async def login_google_flow_tool() -> dict:
    """Login to Google Flow (interactive, handles 2FA).

    Run this once to save session cookies.
    Subsequent generate calls will reuse the session.
    """
    result = await login_google_flow()
    return result.model_dump()


# ── Autonomous Pipeline ──────────────────────────────────────────


@mcp.tool()
async def run_full_pipeline(
    product_url: str,
    platforms: list[str] | None = None,
    num_variants: int = 3,
    include_lip_sync: bool = False,
    auto_publish: bool = True,
) -> dict:
    """Run the FULL autonomous pipeline — one URL to published campaign.

    Product URL → Analysis → Content → Video (Google Flow) →
    Post-production → Publish (6 platforms) → Track

    All 18 agents integrated. Fully autonomous.
    """
    from MCP.tools.autonomous_pipeline_tools import AutonomousPipelineInput
    input_data = AutonomousPipelineInput(
        product_url=product_url,
        platforms=platforms or ["tiktok", "instagram", "facebook"],
        num_variants=num_variants,
        include_lip_sync=include_lip_sync,
        auto_publish=auto_publish,
    )
    result = await run_autonomous_pipeline(input_data)
    return result.model_dump()


# ── Cloud Browser (Zero RAM) ────────────────────────────────────


@mcp.tool()
async def cloud_browser_navigate(url: str) -> dict:
    """Navigate to URL using cloud browser (BrowserCat → ScrapingBee).

    Zero RAM on VPS. Cloud-based browser automation.
    Free: 1,000 req/mo (BrowserCat) + 1,000 req/mo (ScrapingBee).
    """
    from MCP.tools.cloud_browser_tools import CloudNavigateInput
    input_data = CloudNavigateInput(url=url)
    result = await cloud_navigate_url(input_data)
    return result.model_dump()


@mcp.tool()
async def cloud_browser_screenshot(url: str) -> dict:
    """Take screenshot of URL using cloud browser.

    Zero RAM on VPS. Cloud-based browser automation.
    """
    from MCP.tools.cloud_browser_tools import CloudScreenshotInput
    input_data = CloudScreenshotInput(url=url)
    result = await cloud_screenshot_url(input_data)
    return result.model_dump()


@mcp.tool()
async def store_winning_hook_tool(hook_text: str, hook_type: str = "curiosity", campaign_id: str = "") -> dict:
    """Store a winning hook for future reference."""
    return await store_winning_hook(hook_text=hook_text, hook_type=hook_type, campaign_id=campaign_id)


@mcp.tool()
async def find_high_commission_products(keyword: str, category: str = "umum", platform: str = "shopee", max_results: int = 5) -> dict:
    """Find products with highest commission rates for a keyword."""
    return await find_high_commission(keyword=keyword, category=category, platform=platform, max_results=max_results)


@mcp.tool()
async def search_similar_products(query: str, top_k: int = 5) -> list[dict]:
    """Search for similar products in the knowledge base."""
    return await memory_find_similar_products(query=query, top_k=top_k)


# ── Multilingual Tools ───────────────────────────────────────


@mcp.tool()
async def translate_to_languages(
    content: str,
    source_language: str = "id",
    target_languages: str = "en,es,pt,ja,ko",
    platform: str = "tiktok",
    niche: str = "general",
    optimize_emojis: bool = True,
) -> dict:
    """Translate and culturally adapt content to multiple languages.

    Handles: Indonesian, English, Spanish, Portuguese, Japanese, Korean,
    Thai, Vietnamese, Hindi, Arabic, Turkish. Platform-specific formatting,
    CTA localization, trending hashtags, emoji optimization.

    Args:
        content: Source content (Indonesian recommended as source).
        source_language: Source language code.
        target_languages: Comma-separated language codes. E.g. "en,es,pt,ja,ko"
        platform: tiktok, instagram, facebook, twitter, youtube.
        niche: general, electronics, fashion, beauty, food.
        optimize_emojis: Culturally optimize emoji usage.

    Returns: MultilingualPackage with per-language variants.
    """
    from MCP.tools.multilingual_tools import translate_content as _tc
    return await _tc(
        content=content,
        source_language=source_language,
        target_languages=target_languages,
        platform=platform,
        niche=niche,
        optimize_emojis=optimize_emojis,
    )


@mcp.tool()
async def translate_single(
    content: str,
    source_language: str = "id",
    target_language: str = "en",
    platform: str = "tiktok",
    niche: str = "general",
) -> dict:
    """Translate content to a single target language with cultural adaptation.

    Returns translated content, localized CTA, trending hashtags, char count/limit.
    """
    from MCP.tools.multilingual_tools import translate_single_language as _ts
    return await _ts(
        content=content,
        source_language=source_language,
        target_language=target_language,
        platform=platform,
        niche=niche,
    )


@mcp.tool()
async def localize_cta_text(
    cta_text: str,
    source_language: str = "id",
    target_language: str = "en",
    platform: str = "tiktok",
) -> dict:
    """Localize a call-to-action for a target language and platform.

    E.g. "Link di bio!" (id) → "Link in bio!" (en) → "¡Enlace en bio!" (es)
    """
    from MCP.tools.multilingual_tools import localize_cta as _lc
    return await _lc(
        cta_text=cta_text,
        source_language=source_language,
        target_language=target_language,
        platform=platform,
    )


@mcp.tool()
async def get_language_hashtags(
    language: str = "en",
    niche: str = "general",
    count: int = 5,
) -> dict:
    """Get culturally trending hashtags for a language and niche."""
    from MCP.tools.multilingual_tools import get_trending_hashtags as _ht
    return await _ht(language=language, niche=niche, count=count)


@mcp.tool()
async def get_char_limits(platform: str = "tiktok", language: str = "") -> dict:
    """Get character limits for a platform across languages."""
    from MCP.tools.multilingual_tools import get_platform_char_limits as _cl
    return await _cl(platform=platform, language=language)


@mcp.tool()
async def list_supported_languages() -> dict:
    """Get all 11 supported languages for multilingual content."""
    from MCP.tools.multilingual_tools import get_supported_languages as _sl
    return await _sl()


@mcp.tool()
async def batch_translate_platforms(
    content: str,
    source_language: str = "id",
    platforms: str = "tiktok,instagram,facebook",
    niche: str = "general",
) -> dict:
    """Translate content for multiple platforms with per-platform formatting.

    Each platform gets language variants with correct char limits and CTAs.
    """
    from MCP.tools.multilingual_tools import batch_translate_for_platforms as _bp
    return await _bp(
        content=content,
        source_language=source_language,
        platforms=platforms,
        niche=niche,
    )


# ── A/B Stats Engine ────────────────────────────────────────────────


@mcp.tool()
async def create_ab_test_tool(
    test_name: str,
    variants: str,
    niche: str = "general",
    platform: str = "tiktok",
) -> dict:
    """Create an A/B test with multiple content variants.

    Args:
        test_name: Name for the test.
        variants: Comma-separated variant descriptions.
        niche: Product/content niche.
        platform: Target platform.

    Returns: Test ID, variant IDs, and status.
    """
    return await _create_ab_test(
        test_name=test_name,
        variants=variants,
        niche=niche,
        platform=platform,
    )


@mcp.tool()
async def update_ab_test_tool(
    test_id: str,
    variant_id: str,
    impressions: int = 0,
    clicks: int = 0,
    conversions: int = 0,
) -> dict:
    """Update A/B test metrics for a variant. Metrics accumulate across calls.

    Args:
        test_id: The A/B test ID.
        variant_id: The variant ID to update.
        impressions: New impressions to add.
        clicks: New clicks to add.
        conversions: New conversions to add.

    Returns: Updated test state with significance results.
    """
    return await _update_ab_test(
        test_id=test_id,
        variant_id=variant_id,
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
    )


@mcp.tool()
async def get_ab_results_tool(test_id: str) -> dict:
    """Get A/B test results with statistical significance.

    Returns winner, confidence level, lift, and recommendations.
    """
    return await _get_ab_results(test_id=test_id)


@mcp.tool()
async def list_ab_tests_tool(status_filter: str = "") -> list[dict]:
    """List all A/B tests with optional status filter (running/significant/inconclusive)."""
    return await _list_ab_tests(status_filter=status_filter)


@mcp.tool()
async def promote_ab_winner_tool(test_id: str) -> dict:
    """Promote the winning variant and retire losers from an A/B test."""
    return await _promote_ab_winner(test_id=test_id)


@mcp.tool()
async def delete_ab_test_tool(test_id: str) -> dict:
    """Delete an A/B test."""
    return await _delete_ab_test(test_id=test_id)


@mcp.tool()
async def calculate_ab_sample_size(
    baseline_rate: float,
    mde: float = 0.1,
    power: float = 0.8,
) -> dict:
    """Calculate required sample size per variant for an A/B test.

    Args:
        baseline_rate: Current conversion/click rate (0-1).
        mde: Minimum detectable effect as fraction of baseline.
        power: Statistical power (default 0.8 = 80%).

    Returns: Minimum and recommended sample sizes.
    """
    return await _calculate_sample_size(
        baseline_rate=baseline_rate,
        mde=mde,
        power=power,
    )


# ── Voice Cloning Tools ────────────────────────────────────────


@mcp.tool()
async def create_voice_profile_tool(
    name: str,
    style: str = "enthusiastic",
    languages: str = "id,en",
    avatar_id: str = "",
) -> dict:
    """Create a voice profile for consistent AI narration.

    Styles: enthusiastic, calm, professional, funny.
    Languages: comma-separated codes (id=Indonesian, en=English).
    """
    return await _create_voice_profile(
        name=name, style=style, languages=languages, avatar_id=avatar_id,
    )


@mcp.tool()
async def generate_voice_narration(
    text: str,
    profile_id: str,
    emotion: str = "neutral",
    speed: float = 1.0,
    output_format: str = "mp3",
    avatar_id: str = "",
) -> dict:
    """Generate voice narration using a cloned voice profile.

    Returns TTS parameters (pitch, speed, energy, prosody, emphasis).
    Emotions: neutral, excited, serious, funny, sad.
    """
    return await _generate_voice(
        text=text, profile_id=profile_id, emotion=emotion,
        speed=speed, output_format=output_format, avatar_id=avatar_id,
    )


@mcp.tool()
async def list_all_voice_profiles(avatar_id: str = "") -> dict:
    """List all voice profiles, optionally filtered by avatar."""
    return await _list_voice_profiles(avatar_id=avatar_id)


@mcp.tool()
async def get_voice_profile_detail(profile_id: str) -> dict:
    """Get a voice profile and its usage statistics."""
    return await _get_voice_profile(profile_id=profile_id)


@mcp.tool()
async def update_voice_profile_tool(
    profile_id: str,
    name: str = "",
    style: str = "",
    languages: str = "",
) -> dict:
    """Update an existing voice profile."""
    return await _update_voice_profile(
        profile_id=profile_id, name=name, style=style, languages=languages,
    )


@mcp.tool()
async def delete_voice_profile_tool(profile_id: str) -> dict:
    """Delete a voice profile."""
    return await _delete_voice_profile(profile_id=profile_id)


@mcp.tool()
async def generate_batch_voice_narration(
    texts: list[str],
    profile_id: str,
    emotion: str = "neutral",
    speed: float = 1.0,
    output_format: str = "mp3",
) -> dict:
    """Generate voice narration for multiple texts at once.

    Useful for batch video production or multi-script campaigns.
    """
    return await _generate_batch_voices(
        texts=texts, profile_id=profile_id, emotion=emotion,
        speed=speed, output_format=output_format,
    )


@mcp.tool()
async def generate_voice_ab_variations(
    text: str,
    profile_id: str,
    emotions: str = "neutral,excited,serious",
    speeds: str = "1.0,1.1",
    output_format: str = "mp3",
) -> dict:
    """Generate multiple voice variations for A/B testing.

    Returns all combinations of emotions x speeds.
    """
    return await _generate_voice_variations(
        text=text, profile_id=profile_id, emotions=emotions,
        speeds=speeds, output_format=output_format,
    )


@mcp.tool()
async def get_voice_generation_history(limit: int = 50) -> dict:
    """Get recent voice generation history."""
    return await _get_voice_history(limit=limit)


@mcp.tool()
async def get_available_voice_styles() -> dict:
    """Get available voice style presets and their characteristics."""
    return await _get_voice_style_presets()


@mcp.tool()
async def validate_voice_profile_health(profile_id: str) -> dict:
    """Validate a voice profile and check for issues."""
    return await _validate_voice_profile(profile_id=profile_id)


# ── Viral Prediction Tool ──────────────────────────────────────────


@mcp.tool()
async def predict_content_virality(
    hook: str,
    script: str = "",
    platform: str = "tiktok",
    niche: str = "general",
) -> dict:
    """Score content virality before publishing.

    Analyzes 22 features (hook strength, emotional impact, curiosity gap,
    power words, CTA placement, story arc, etc.) and returns a 0-100 score
    with predicted reach, engagement rate, best posting time, per-platform
    scores, and actionable optimization tips.
    """
    from MCP.tools.viral_tools import PredictViralityInput
    input_data = PredictViralityInput(
        hook=hook, script=script, platform=platform, niche=niche,
    )
    result = await _predict_virality(
        hook=input_data.hook,
        script=input_data.script,
        platform=input_data.platform,
        niche=input_data.niche,
    )
    return result.model_dump()


# ── Content Remix Engine ────────────────────────────────────────────


@mcp.tool()
async def remix_content(
    content: str,
    content_type: str = "script",
    niche: str = "general",
    target_platforms: str = "tiktok,instagram,youtube,twitter,facebook",
) -> dict:
    """Transform one winning content piece into 10+ platform-specific formats.

    Generates adapted variants for TikTok, Instagram, YouTube, Twitter,
    Facebook, Blog, Newsletter, and Podcast. Each variant is scored for
    viral potential and includes platform-appropriate hashtags and CTAs.

    Args:
        content: Source content (script, hook, or video concept).
        content_type: "script", "hook", or "video_concept".
        niche: Content niche for hashtag targeting.
        target_platforms: Comma-separated platform list.

    Returns: RemixPackage with all variants, scores, and best variant index.
    """
    platforms = [p.strip() for p in target_platforms.split(",") if p.strip()]
    result = await _remix_content(
        content=content,
        content_type=content_type,
        niche=niche,
        target_platforms=platforms,
    )
    return result.model_dump()


# ── Trend Monitor ───────────────────────────────────────────────


@mcp.tool()
async def get_trend_alerts(
    platform: str = "tiktok",
    niche: str = "general",
    limit: int = 10,
) -> dict:
    """Get real-time trend alerts with velocity scores and urgency levels."""
    input_data = {"platform": platform, "niche": niche, "limit": limit}
    return await _monitor_trends(**input_data)


# ── Thumbnail Generator ─────────────────────────────────────────


@mcp.tool()
async def auto_generate_thumbnails(
    product_name: str,
    niche: str = "general",
    content_type: str = "product_review",
    num_variants: int = 3,
) -> dict:
    """Generate AI-optimized thumbnail variants with CTR predictions."""
    input_data = {"product_name": product_name, "niche": niche, "content_type": content_type, "num_variants": num_variants}
    return await _generate_thumbnails(**input_data)


# ── Affiliate Optimizer ─────────────────────────────────────────


@mcp.tool()
async def optimize_affiliate_strategy(
    current_products: str = "",
    niche: str = "general",
    budget: float = 0.0,
) -> dict:
    """Find higher commission products and optimize affiliate strategy."""
    from Services.agents.affiliate_optimizer import AffiliateProduct
    products = None
    if current_products.strip():
        products = [AffiliateProduct(product_id=pid.strip(), name=f"Product {pid.strip()}") for pid in current_products.split(",") if pid.strip()]
    return await _optimize_affiliate(current_products=products, niche=niche, budget=budget)


# ── SEO Engine ──────────────────────────────────────────────────


@mcp.tool()
async def optimize_content_seo(
    title: str,
    description: str = "",
    niche: str = "general",
    platform: str = "youtube",
) -> dict:
    """Optimize content for search rankings with keyword research."""
    return await _seo_optimize(title=title, description=description, niche=niche, platform=platform)


# ── Sentiment Monitor ──────────────────────────────────────────


@mcp.tool()
async def track_brand_sentiment(
    brand_name: str,
    platforms: str = "tiktok,instagram,twitter",
    niche: str = "general",
) -> dict:
    """Monitor brand sentiment across platforms. Detect crises and suggest pivots."""
    return await _monitor_sentiment(brand_name=brand_name, platforms=platforms, niche=niche)


# ── Self-Healing Pipeline ──────────────────────────────────────


@mcp.tool()
async def get_self_healing_status(pipeline_id: str = "") -> dict:
    """Check self-healing pipeline status, failures, and recoveries."""
    return await _get_pipeline_health(pipeline_id=pipeline_id)


# ── Content Calendar ─────────────────────────────────────────────


@mcp.tool()
async def schedule_content_post_tool(platform: str, content: str, scheduled_time: str, hashtags: str = "", campaign_id: str = "") -> dict:
    """Schedule a content post for a specific platform and time."""
    return await schedule_content_post(platform=platform, content=content, scheduled_time=scheduled_time, hashtags=hashtags, campaign_id=campaign_id)


@mcp.tool()
async def get_content_calendar_tool(platform: str = "", days: int = 7) -> list[dict]:
    """Get scheduled posts for the next N days."""
    return await get_content_calendar(platform=platform, days=days)


@mcp.tool()
async def find_best_posting_times_tool(platform: str = "tiktok", count: int = 5) -> list[dict]:
    """Find optimal posting times for a platform based on engagement data."""
    return await find_best_posting_times(platform=platform, count=count)


@mcp.tool()
async def cancel_scheduled_post_tool(post_id: str) -> dict:
    """Cancel a scheduled post."""
    return await cancel_scheduled_post(post_id=post_id)


@mcp.tool()
async def reschedule_post_tool(post_id: str, new_time: str) -> dict:
    """Reschedule a post to a new time."""
    return await reschedule_post(post_id=post_id, new_time=new_time)


@mcp.tool()
async def get_calendar_stats_tool() -> dict:
    """Get calendar statistics — total posts, by status, by platform."""
    return await get_calendar_stats()


# ── Webhook Alerts ──────────────────────────────────────────────


@mcp.tool()
async def register_webhook_tool(name: str, url: str, platform: str = "discord", events: str = "") -> dict:
    """Register a webhook for notifications (Discord/Slack/Telegram)."""
    return await register_webhook_alert(name=name, url=url, platform=platform, events=events)


@mcp.tool()
async def send_alert_tool(event_type: str, title: str, message: str, severity: str = "info") -> dict:
    """Send an alert to all matching webhooks."""
    return await send_webhook_alert(event_type=event_type, title=title, message=message, severity=severity)


@mcp.tool()
async def list_webhooks_tool() -> list[dict]:
    """List all registered webhooks."""
    return await list_webhook_alerts()


@mcp.tool()
async def get_alert_history_tool(limit: int = 20) -> list[dict]:
    """Get recent alert history."""
    return await get_alert_history(limit=limit)


# ── API Rate Limiter & Cache ────────────────────────────────────


@mcp.tool()
async def check_rate_limit(provider: str) -> dict:
    """Check if an API provider has available rate limit capacity."""
    return await check_api_rate_limit(provider=provider)


@mcp.tool()
async def acquire_rate_slot(provider: str) -> dict:
    """Acquire a rate limit slot before making an API call."""
    return await acquire_api_slot(provider=provider)


@mcp.tool()
async def get_rate_usage() -> dict:
    """Get rate limit usage for all providers."""
    return await get_api_rate_usage()


@mcp.tool()
async def get_cache(content_type: str, key_params: str) -> dict | None:
    """Get cached content by type and key parameters."""
    return await cache_get(content_type=content_type, key_params=key_params)


@mcp.tool()
async def set_cache(content_type: str, key_params: str, content: str) -> dict:
    """Store content in cache."""
    return await cache_set(content_type=content_type, key_params=key_params, content=content)


@mcp.tool()
async def get_cache_stats() -> dict:
    """Get cache statistics."""
    return await cache_stats()


# ── Audit Logger ────────────────────────────────────────────────


@mcp.tool()
async def log_audit(action: str, actor: str = "system", target: str = "", details: str = "") -> dict:
    """Log an audit event for tracking."""
    return await log_audit_event(action=action, actor=actor, target=target, details=details)


@mcp.tool()
async def query_audit(action: str = "", actor: str = "", limit: int = 50) -> list[dict]:
    """Query audit log entries."""
    return await query_audit_log(action=action, actor=actor, limit=limit)


# ── Compliance Checker ──────────────────────────────────────────


@mcp.tool()
async def check_compliance(content: str, platform: str = "tiktok", has_affiliate: bool = True) -> dict:
    """Check content for platform compliance (char limits, disclosures, banned words)."""
    return await check_content_compliance(content=content, platform=platform, has_affiliate=has_affiliate)


@mcp.tool()
async def create_niche_campaign_tool(niche: str, name: str, platforms: str = "tiktok,instagram", budget: float = 0.0) -> dict:
    """Create a multi-niche campaign manager entry."""
    return await create_niche_campaign(niche=niche, name=name, platforms=platforms, budget=budget)


# ── ML Content Scorer ──────────────────────────────────────────


@mcp.tool()
async def ml_score(content: str, platform: str = "tiktok", niche: str = "general") -> dict:
    """ML-based content scoring with feature breakdown, risk factors, and improvement suggestions."""
    return await ml_score_content(content=content, platform=platform, niche=niche)


# ── Cross-Platform Analytics ────────────────────────────────────


@mcp.tool()
async def record_metrics(platform: str, impressions: int = 0, reach: int = 0, engagement: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0, ad_spend: float = 0.0) -> dict:
    """Record metrics for a platform."""
    return await record_platform_metrics(platform=platform, impressions=impressions, reach=reach, engagement=engagement, clicks=clicks, conversions=conversions, revenue=revenue, ad_spend=ad_spend)


@mcp.tool()
async def get_cross_platform_report(campaign_id: str = "") -> dict:
    """Generate unified cross-platform analytics report."""
    return await generate_cross_platform_report(campaign_id=campaign_id)


# ── Content Versioning ──────────────────────────────────────────


@mcp.tool()
async def save_content_version(content_type: str, content_id: str, content: str, author: str = "system", notes: str = "") -> dict:
    """Create a new version of content."""
    return await create_content_version(content_type=content_type, content_id=content_id, content=content, author=author, notes=notes)


@mcp.tool()
async def get_version_history(content_type: str, content_id: str) -> list[dict]:
    """Get all versions of a content piece."""
    return await get_content_versions(content_type=content_type, content_id=content_id)


@mcp.tool()
async def revert_to_version(content_type: str, content_id: str, version_id: str) -> dict:
    """Revert content to a specific version."""
    return await revert_content_version(content_type=content_type, content_id=content_id, version_id=version_id)


# ── Batch Processor ─────────────────────────────────────────────


@mcp.tool()
async def create_batch(items: str, concurrency: int = 3, delay: float = 1.0) -> dict:
    """Create a batch processing job."""
    return await create_batch_job(items=items, concurrency=concurrency, delay=delay)


@mcp.tool()
async def run_batch(job_id: str) -> dict:
    """Run a batch processing job."""
    return await run_batch_job(job_id=job_id)


@mcp.tool()
async def get_batch_status_tool(job_id: str) -> dict:
    """Get batch job status and progress."""
    return await get_batch_status(job_id=job_id)


@mcp.tool()
async def list_batches(status: str = "") -> list[dict]:
    """List all batch jobs."""
    return await list_batch_jobs(status=status)


# ── Dynamic Pricing ─────────────────────────────────────────────


@mcp.tool()
async def analyze_pricing(product_id: str, base_price: float, commission_rate: float, market_avg: float = 0.0, competitor_avg: float = 0.0, demand_score: float = 0.5, supply_score: float = 0.5) -> dict:
    """Analyze optimal pricing for a product."""
    return await analyze_product_pricing(product_id=product_id, base_price=base_price, commission_rate=commission_rate, market_avg=market_avg, competitor_avg=competitor_avg, demand_score=demand_score, supply_score=supply_score)


@mcp.tool()
async def get_pricing_recommendations_tool() -> list[dict]:
    """Get pricing recommendations for all analyzed products."""
    return await get_pricing_recommendations()


# ── Telegram Bot ────────────────────────────────────────────────


@mcp.tool()
async def setup_telegram_bot(bot_token: str, chat_ids: str = "") -> dict:
    """Configure Telegram bot for notifications."""
    return await configure_telegram_bot(bot_token=bot_token, chat_ids=chat_ids)


@mcp.tool()
async def send_telegram_alert(title: str, message: str, severity: str = "info") -> dict:
    """Send notification to Telegram."""
    return await send_telegram_notification(title=title, message=message, severity=severity)


@mcp.tool()
async def telegram_command(command: str, chat_id: str = "default") -> dict:
    """Handle a Telegram bot command."""
    return await handle_telegram_command(command=command, chat_id=chat_id)


# ── Revenue Forecasting ─────────────────────────────────────────


@mcp.tool()
async def record_revenue_data(revenue: float, ad_spend: float = 0.0, campaign_id: str = "", platform: str = "", clicks: int = 0, conversions: int = 0) -> dict:
    """Record revenue data for forecasting."""
    return await record_revenue(revenue=revenue, ad_spend=ad_spend, campaign_id=campaign_id, platform=platform, clicks=clicks, conversions=conversions)


@mcp.tool()
async def forecast_revenue_data(period: str = "30d") -> dict:
    """Forecast revenue for 7d/30d/90d."""
    return await forecast_revenue(period=period)


@mcp.tool()
async def get_revenue_breakdown_data() -> dict:
    """Get revenue breakdown by platform."""
    return await get_revenue_breakdown()


@mcp.tool()
async def get_revenue_stats_data() -> dict:
    """Get overall revenue statistics."""
    return await get_revenue_stats()


# ── Auto Reports ────────────────────────────────────────────────


@mcp.tool()
async def generate_report(report_type: str = "weekly") -> dict:
    """Generate an automatic performance report."""
    return await generate_auto_report(report_type=report_type)


@mcp.tool()
async def report_data(category: str, data: str) -> dict:
    """Record data for report generation."""
    return await record_report_data(category=category, data=data)


# ── Budget Optimizer ────────────────────────────────────────────


@mcp.tool()
async def set_budget(budget: float) -> dict:
    """Set total advertising budget."""
    return await set_total_budget(budget=budget)


@mcp.tool()
async def register_campaign_for_budget(campaign_id: str, platform: str, current_budget: float = 0.0, roi: float = 0.0) -> dict:
    """Register a campaign for budget optimization."""
    return await register_campaign_budget(campaign_id=campaign_id, platform=platform, current_budget=current_budget, roi=roi)


@mcp.tool()
async def optimize_budget_allocation() -> list[dict]:
    """Auto-allocate budget for maximum ROI."""
    return await optimize_budget()


@mcp.tool()
async def budget_summary() -> dict:
    """Get budget allocation summary."""
    return await get_budget_summary()


# ── Smart Scheduler ─────────────────────────────────────────────


@mcp.tool()
async def optimal_times(platform: str = "tiktok", count: int = 5) -> list[dict]:
    """Get ML-optimized posting times."""
    return await get_optimal_posting_times(platform=platform, count=count)


@mcp.tool()
async def suggest_schedule(platform: str = "tiktok", posts_per_day: int = 2) -> list[dict]:
    """Suggest daily posting schedule."""
    return await suggest_posting_schedule(platform=platform, posts_per_day=posts_per_day)


@mcp.tool()
async def log_engagement(platform: str, hour: int, day_of_week: str, engagement_rate: float) -> dict:
    """Record engagement data for scheduling optimization."""
    return await record_engagement_data(platform=platform, hour=hour, day_of_week=day_of_week, engagement_rate=engagement_rate)


# ── Performance Alerts ──────────────────────────────────────────


@mcp.tool()
async def create_alert(name: str, metric: str, condition: str, threshold: float, platform: str = "") -> dict:
    """Create a performance alert rule."""
    return await create_alert_rule(name=name, metric=metric, condition=condition, threshold=threshold, platform=platform)


@mcp.tool()
async def log_metric(metric: str, value: float, platform: str = "", campaign_id: str = "") -> dict:
    """Record a performance metric."""
    return await record_performance_metric(metric=metric, value=value, platform=platform, campaign_id=campaign_id)


@mcp.tool()
async def active_alerts(limit: int = 20) -> list[dict]:
    """Get unacknowledged performance alerts."""
    return await get_performance_alerts(limit=limit)


@mcp.tool()
async def ack_alert(alert_id: str) -> dict:
    """Acknowledge a performance alert."""
    return await acknowledge_alert(alert_id=alert_id)


# ── Content Ideas ───────────────────────────────────────────────


@mcp.tool()
async def ideas(niche: str = "general", platform: str = "tiktok", count: int = 5) -> list[dict]:
    """Generate AI content ideas for a niche."""
    return await generate_content_ideas(niche=niche, platform=platform, count=count)


# ── Competitor Monitor ──────────────────────────────────────────


@mcp.tool()
async def watch_competitor(name: str, platform: str, url: str = "") -> dict:
    """Add a competitor to monitor."""
    return await add_competitor_watch(name=name, platform=platform, url=url)


@mcp.tool()
async def check_competitor(watch_id: str) -> dict:
    """Check competitor metrics."""
    return await check_competitor_metrics(watch_id=watch_id)


@mcp.tool()
async def list_competitors(platform: str = "") -> list[dict]:
    """List monitored competitors."""
    return await list_competitor_watches(platform=platform)


# ── Social Listener ─────────────────────────────────────────────


@mcp.tool()
async def watch_brand(brand: str) -> dict:
    """Add brand to social listening."""
    return await add_brand_to_watch(brand=brand)


@mcp.tool()
async def log_mention(brand: str, platform: str, text: str = "", sentiment: str = "neutral", author: str = "") -> dict:
    """Record a brand mention."""
    return await record_brand_mention(brand=brand, platform=platform, text=text, sentiment=sentiment, author=author)


@mcp.tool()
async def brand_mentions(brand: str = "", platform: str = "", sentiment: str = "") -> list[dict]:
    """Get brand mentions."""
    return await get_brand_mentions(brand=brand, platform=platform, sentiment=sentiment)


@mcp.tool()
async def brand_sentiment(brand: str = "") -> dict:
    """Get sentiment summary for a brand."""
    return await get_sentiment_summary(brand=brand)


# ── Influencer Finder ───────────────────────────────────────────


@mcp.tool()
async def find_influencers_tool(niche: str = "general", platform: str = "tiktok", min_followers: int = 0, max_followers: int = 999999999, count: int = 5) -> list[dict]:
    """Find influencers in a niche."""
    return await find_influencers(niche=niche, platform=platform, min_followers=min_followers, max_followers=max_followers, count=count)


# ── Multi-Account Manager ──────────────────────────────────────


@mcp.tool()
async def add_account(name: str, platform: str, commission_rate: float = 0.0) -> dict:
    """Add an affiliate account."""
    return await add_affiliate_account(name=name, platform=platform, commission_rate=commission_rate)


@mcp.tool()
async def log_earnings(account_id: str, earnings: float, clicks: int = 0, conversions: int = 0) -> dict:
    """Record account earnings."""
    return await record_account_earnings(account_id=account_id, earnings=earnings, clicks=clicks, conversions=conversions)


@mcp.tool()
async def list_accounts(platform: str = "") -> list[dict]:
    """List affiliate accounts."""
    return await list_affiliate_accounts(platform=platform)


@mcp.tool()
async def earnings_summary() -> dict:
    """Get total earnings across all accounts."""
    return await get_earnings_summary()


# ── WebSocket Dashboard ─────────────────────────────────────────


@mcp.tool()
async def ws_broadcast_metric_tool(metric_type: str, data: str) -> dict:
    """Broadcast a metric update to all connected WebSocket clients."""
    return await ws_broadcast_metric(metric_type=metric_type, data=data)


@mcp.tool()
async def ws_broadcast_alert_tool(severity: str, title: str, message: str) -> dict:
    """Broadcast an alert to all connected WebSocket clients."""
    return await ws_broadcast_alert(severity=severity, title=title, message=message)


@mcp.tool()
async def ws_broadcast_pipeline_tool(pipeline_id: str, status: str, phase: str = "", progress: float = 0.0) -> dict:
    """Broadcast pipeline status to all connected WebSocket clients."""
    return await ws_broadcast_pipeline(pipeline_id=pipeline_id, status=status, phase=phase, progress=progress)


@mcp.tool()
async def ws_connections() -> dict:
    """Get WebSocket connection count and buffer status."""
    return await ws_get_connections()


# ── E-commerce APIs (Real Shopee + Tokopedia) ───────────────────


@mcp.tool()
async def shopee_search(query: str, page: int = 1, limit: int = 20, sort: str = "relevancy") -> dict:
    """Search products on Shopee Indonesia. Real API call."""
    result = await shopee_search_products(query=query, page=page, limit=limit, sort=sort)
    return result.model_dump() if hasattr(result, "model_dump") else result


@mcp.tool()
async def shopee_product(url: str) -> dict:
    """Get product details from a Shopee URL."""
    result = await shopee_get_product(url=url)
    return result.model_dump() if hasattr(result, "model_dump") else result


@mcp.tool()
async def shopee_trending(category: str = "", limit: int = 20) -> dict:
    """Get trending products from Shopee."""
    result = await shopee_get_trending(category=category, limit=limit)
    return result.model_dump() if hasattr(result, "model_dump") else result


@mcp.tool()
async def shopee_high_commission(keyword: str = "", limit: int = 10) -> list[dict]:
    """Find high-commission affiliate products on Shopee."""
    return await shopee_find_high_commission(keyword=keyword, limit=limit)


@mcp.tool()
async def ecommerce_search(query: str, platform: str = "shopee", page: int = 1, limit: int = 20, sort: str = "relevancy") -> dict:
    """Search products across Shopee or Tokopedia."""
    return await search_products(query=query, platform=platform, page=page, limit=limit, sort=sort)


@mcp.tool()
async def ecommerce_product_details(url: str) -> dict:
    """Get product details from any Shopee or Tokopedia URL."""
    return await get_product_details(url=url)


@mcp.tool()
async def ecommerce_trending(platform: str = "shopee", category: str = "", limit: int = 20) -> dict:
    """Get trending products from Shopee or Tokopedia."""
    return await get_trending_products(platform=platform, category=category, limit=limit)


@mcp.tool()
async def ecommerce_compare(url_a: str, url_b: str) -> dict:
    """Compare two products side by side."""
    return await compare_products(url_a=url_a, url_b=url_b)


@mcp.tool()
async def ecommerce_find_affiliates(keyword: str, platform: str = "shopee", limit: int = 10) -> list[dict]:
    """Find affiliate-ready products across platforms."""
    return await find_affiliate_products(keyword=keyword, platform=platform, limit=limit)


# ── Social Media APIs (Real TikTok + Social) ────────────────────


@mcp.tool()
async def tiktok_trending_hashtags(category: str = "", limit: int = 20) -> list[dict]:
    """Get trending hashtags from TikTok."""
    return await tiktok_trending(category=category, limit=limit)


@mcp.tool()
async def tiktok_search_videos(query: str, count: int = 20) -> list[dict]:
    """Search for videos on TikTok."""
    return await tiktok_search(query=query, count=count)


@mcp.tool()
async def tiktok_analyze_video(video_url: str) -> dict:
    """Analyze engagement metrics for a TikTok video."""
    return await tiktok_analyze(video_url=video_url)


@mcp.tool()
async def tiktok_get_creator(username: str) -> dict:
    """Get TikTok creator profile information."""
    return await tiktok_creator(username=username)


@mcp.tool()
async def social_search_all(query: str, platforms: str = "tiktok", limit: int = 10) -> list[dict]:
    """Search across social media platforms."""
    return await social_search(query=query, platforms=platforms, limit=limit)


@mcp.tool()
async def social_get_trending(platforms: str = "tiktok", category: str = "", limit: int = 20) -> list[dict]:
    """Get trending topics across social platforms."""
    return await social_trending(platforms=platforms, category=category, limit=limit)


@mcp.tool()
async def social_find_brand(brand: str, platforms: str = "tiktok", limit: int = 50) -> list[dict]:
    """Find brand mentions across social platforms."""
    return await social_brand_mentions(brand=brand, platforms=platforms, limit=limit)
