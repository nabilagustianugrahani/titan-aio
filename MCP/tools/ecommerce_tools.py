"""MCP tools for E-commerce APIs — Shopee + Tokopedia."""

from __future__ import annotations

from MCP.server import mcp

_shopee = None
_tokopedia = None


def _get_shopee():
    global _shopee
    if _shopee is None:
        from Services.api.shopee_client import ShopeeClient

        _shopee = ShopeeClient()
    return _shopee


def _get_tokopedia():
    global _tokopedia
    if _tokopedia is None:
        from Services.api.tokopedia_client import TokopediaClient

        _tokopedia = TokopediaClient()
    return _tokopedia


@mcp.tool()
async def search_products(
    query: str,
    platform: str = "shopee",
    page: int = 1,
    limit: int = 20,
    sort: str = "relevancy",
) -> dict:
    """Search for products across e-commerce platforms (Shopee/Tokopedia).

    Args:
        query: Search keyword
        platform: 'shopee' or 'tokopedia'
        page: Page number
        limit: Results per page (max 50)
        sort: Sort order — relevancy, price_asc, price_desc, sold, newest, rating
    """
    if platform == "tokopedia":
        client = _get_tokopedia()
        result = await client.search(query=query, page=page, limit=limit, sort=sort)
    else:
        client = _get_shopee()
        result = await client.search(query=query, page=page, limit=limit, sort=sort)
    return result.model_dump()


@mcp.tool()
async def get_product_details(url: str) -> dict:
    """Get detailed product info from a Shopee or Tokopedia URL.

    Args:
        url: Full product URL from Shopee or Tokopedia
    """
    if "tokopedia" in url:
        client = _get_tokopedia()
        result = await client.get_product(product_url=url)
    else:
        client = _get_shopee()
        result = await client.get_product(product_url=url)
    return result.model_dump() if result else {"error": "Product not found"}


@mcp.tool()
async def get_trending_products(
    platform: str = "shopee",
    category: str = "",
    limit: int = 20,
) -> dict:
    """Get trending/bestselling products from an e-commerce platform.

    Args:
        platform: 'shopee' or 'tokopedia'
        category: Optional category filter (e.g. 'elektronik', 'fashion')
        limit: Number of results
    """
    if platform == "tokopedia":
        client = _get_tokopedia()
        result = await client.get_trending(category=category, limit=limit)
    else:
        client = _get_shopee()
        result = await client.get_trending(category=category, limit=limit)
    return result.model_dump()


@mcp.tool()
async def compare_products(url_a: str, url_b: str) -> dict:
    """Compare two products from Shopee/Tokopedia side by side.

    Args:
        url_a: First product URL
        url_b: Second product URL
    """
    product_a = await get_product_details(url=url_a)
    product_b = await get_product_details(url=url_b)

    price_a = product_a.get("price", 0)
    price_b = product_b.get("price", 0)
    rating_a = product_a.get("rating", 0)
    rating_b = product_b.get("rating", 0)
    sold_a = product_a.get("sold", 0)
    sold_b = product_b.get("sold", 0)

    comparison = {
        "product_a": product_a,
        "product_b": product_b,
        "price_diff": abs(price_a - price_b),
        "cheaper": "A" if price_a < price_b else ("B" if price_b < price_a else "same"),
        "higher_rated": "A" if rating_a > rating_b else ("B" if rating_b > rating_a else "same"),
        "better_seller": "A" if sold_a > sold_b else ("B" if sold_b > sold_a else "same"),
    }
    return comparison


@mcp.tool()
async def find_affiliate_products(
    keyword: str, platform: str = "shopee", limit: int = 10
) -> list[dict]:
    """Find products suitable for affiliate marketing (high sales, good ratings).

    Args:
        keyword: Search term
        platform: 'shopee' or 'tokopedia'
        limit: Number of results
    """
    if platform == "tokopedia":
        client = _get_tokopedia()
        result = await client.search(query=keyword, sort="sold", limit=limit)
        products = [p.model_dump() for p in result.products]
    else:
        client = _get_shopee()
        result = await client.get_high_commission(keyword=keyword, limit=limit)
        if isinstance(result, list):
            products = [p.model_dump() if hasattr(p, "model_dump") else p for p in result]
        elif hasattr(result, "products"):
            products = [p.model_dump() for p in result.products]
        else:
            products = result if isinstance(result, list) else []
    return products
