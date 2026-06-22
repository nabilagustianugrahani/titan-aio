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
