"""MCP tools for product scraping and discovery."""
from __future__ import annotations

from Services.agents.scraper import ScrapeAgent


async def discover_products(keyword: str = "", category: str = "", platform: str = "shopee", max_results: int = 10) -> dict:
    """Search for products by keyword on e-commerce platforms."""
    scraper = ScrapeAgent()
    query = keyword or category
    results = await scraper.search_products(
        keyword=query,
        platform=platform,
        max_results=max_results,
    )
    return {
        "query": query,
        "platform": platform,
        "total": len(results),
        "products": results,
    }


async def discover_trending_products(category: str = "") -> list[dict]:
    """Discover trending products from social media + e-commerce data."""
    scraper = ScrapeAgent()
    return await scraper.discover_trending(category=category)


async def get_product_details_data(product_url: str) -> dict:
    """Get detailed product information from a product URL."""
    scraper = ScrapeAgent()
    return await scraper.get_product_details(url=product_url)


async def find_high_commission(
    keyword: str = "",
    category: str = "umum",
    platform: str = "shopee",
    max_results: int = 10,
) -> dict:
    """Find products with highest affiliate commission potential."""
    from Services.agents.commission_hunter import CommissionHunterAgent

    agent = CommissionHunterAgent()
    return await agent(
        keyword=keyword,
        category=category,
        platform=platform,
        max_results=max_results,
    )
