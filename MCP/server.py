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
from MCP.tools.trend_tools import analyze_trend, analyze_competitor, store_winning_hook, evaluate_campaign_finance, decide_growth_action
from MCP.tools.memory_tools import memory_store_hook, memory_find_similar_hooks, memory_store_product_knowledge, memory_find_similar_products
from MCP.tools.publisher_tools import prepare_platform_content, track_campaign_metrics

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
