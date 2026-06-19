"""MCP tools for new agents: Asset, Affiliate, Campaign Builder, Discovery."""
from __future__ import annotations

from Services.agents.asset import AssetAgent
from Services.agents.affiliate import AffiliateAgent
from Services.agents.campaign_builder import CampaignBuilder


async def collect_product_assets(product_id: str, image_urls: list[str] | None = None) -> dict:
    """Download and prepare product assets for campaign creatives."""
    agent = AssetAgent()
    return await agent(product_id=product_id, image_urls=image_urls or [])


async def generate_affiliate_links(product_url: str = "", product_id: str = "", platform: str = "shopee") -> dict:
    """Generate affiliate tracking links for Shopee/Tokopedia."""
    agent = AffiliateAgent()
    return await agent(product_url=product_url, product_id=product_id, platform=platform)


async def build_campaign_package(product: dict = None, reviews: dict = None, hooks: list = None, scripts: list = None, thumbnail: str = "", images: list = None, video: str = "", captions: dict = None, affiliate_links: dict = None, publishing: dict = None) -> dict:
    """Build complete campaign package from all components."""
    agent = CampaignBuilder()
    return await agent(
        product=product or {},
        reviews=reviews or {},
        hooks=hooks or [],
        scripts=scripts or [],
        thumbnail=thumbnail,
        images=images or [],
        video=video,
        captions=captions or {},
        affiliate_links=affiliate_links or {},
        publishing=publishing or {},
    )


async def discover_products(keyword: str = "", category: str = "", platform: str = "") -> dict:
    """Search/discover products for affiliate campaigns."""
    from MCP.tools.search_product import search_product
    from MCP.schemas import SearchProductInput

    result = await search_product(SearchProductInput(
        query=keyword or category,
        platform=platform or None,
        limit=5,
    ))
    return {
        "query": keyword or category,
        "results": [r.model_dump() for r in result.results],
        "total": result.total,
    }
