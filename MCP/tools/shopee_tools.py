"""MCP tools for Shopee API — search, browse, compare, and get affiliate links."""

from __future__ import annotations

from MCP.server import mcp

_client = None


def _get_client():
    global _client
    if _client is None:
        from Services.api.shopee_client import ShopeeClient

        _client = ShopeeClient()
    return _client


@mcp.tool()
async def shopee_search_products(
    query: str,
    page: int = 1,
    limit: int = 20,
    sort: str = "relevancy",
    min_price: float = 0,
    max_price: float = 0,
) -> dict:
    """Search for products on Shopee Indonesia.

    Returns product listings with prices, ratings, sales counts, and shop info.

    Args:
        query: Search keyword (e.g. "earphone bluetooth", "case iPhone 15").
        page: Page number (1-indexed).
        limit: Results per page (max 60).
        sort: Sort order — "relevancy", "sales", "price_asc", "price_desc", "ctime".
        min_price: Minimum price filter in IDR.
        max_price: Maximum price filter in IDR.

    Returns:
        dict with query, total_results, products list, page, has_more.
    """
    client = _get_client()
    result = await client.search(
        query=query,
        page=page,
        limit=limit,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
    )
    return result.model_dump()


@mcp.tool()
async def shopee_get_product(url: str) -> dict:
    """Get detailed product information from a Shopee product URL.

    Extracts shop_id and item_id from the URL, then fetches full product
    details including variants, stock, and shop info.

    Args:
        url: Full Shopee product URL (e.g. "https://shopee.co.id/Product-Name-i.123.456").

    Returns:
        dict with product details (product_id, name, price, rating, sold, etc.)
        or {"error": "Product not found"}.
    """
    client = _get_client()
    result = await client.get_product(product_url=url)
    return result.model_dump() if result else {"error": "Product not found"}


@mcp.tool()
async def shopee_get_product_by_id(shop_id: str, item_id: str) -> dict:
    """Get product details using Shopee shop_id and item_id directly.

    Args:
        shop_id: Shopee shop identifier (numeric string).
        item_id: Shopee item identifier (numeric string).

    Returns:
        dict with product details or {"error": "Product not found"}.
    """
    client = _get_client()
    result = await client.get_product_by_id(shop_id=shop_id, item_id=item_id)
    return result.model_dump() if result else {"error": "Product not found"}


@mcp.tool()
async def shopee_get_trending(category: str = "", limit: int = 20) -> dict:
    """Get trending/best-selling products from Shopee.

    Defaults to overall best-sellers. Optionally filter by category keyword.

    Args:
        category: Optional category keyword filter (e.g. "earphone", "fashion").
        limit: Number of results (max 20).

    Returns:
        dict with query, total_results, products list.
    """
    client = _get_client()
    result = await client.get_trending(category=category, limit=limit)
    return result.model_dump()


@mcp.tool()
async def shopee_find_high_commission(keyword: str = "", limit: int = 10) -> list[dict]:
    """Find high-commission affiliate products on Shopee.

    Searches for popular products with strong sales volume and assigns
    estimated commission rates. Ideal for affiliate campaign selection.

    Args:
        keyword: Search keyword. Defaults to "terlaris" (best-selling).
        limit: Max products to return (max 10).

    Returns:
        list of product dicts with estimated commission_rate field.
    """
    client = _get_client()
    products = await client.get_high_commission(keyword=keyword, limit=limit)
    return [p.model_dump() for p in products]


@mcp.tool()
async def shopee_price_compare(keyword: str, limit: int = 20) -> dict:
    """Compare prices for a product keyword on Shopee.

    Searches and returns results sorted by price (lowest first) for
    easy price comparison.

    Args:
        keyword: Product keyword to compare (e.g. "TWS earphone Bluetooth").
        limit: Number of results (max 20).

    Returns:
        dict with query, total_results, products sorted by ascending price.
    """
    client = _get_client()
    result = await client.price_compare(keyword=keyword, limit=limit)
    return result.model_dump()


@mcp.tool()
async def shopee_browse_category(
    category_id: str, limit: int = 20, sort: str = "sales"
) -> dict:
    """Browse products by Shopee category ID.

    Args:
        category_id: Shopee numeric category ID (e.g. "11043" for phones).
        limit: Results per page (max 60).
        sort: Sort order — "sales", "price_asc", "price_desc", "ctime".

    Returns:
        dict with query, total_results, products list.
    """
    client = _get_client()
    result = await client.search_by_category(
        category_id=category_id, limit=limit, sort=sort
    )
    return result.model_dump()


@mcp.tool()
async def shopee_generate_affiliate_url(
    product_url: str, affiliate_id: str = ""
) -> dict:
    """Generate an affiliate tracking URL for a Shopee product.

    Appends affiliate parameters to the product URL for commission tracking.

    Args:
        product_url: Original Shopee product URL.
        affiliate_id: Your Shopee affiliate/partner ID for tracking.

    Returns:
        dict with original_url, affiliate_url, deep_link.
    """
    client = _get_client()
    affiliate_url = client.generate_affiliate_url(product_url, affiliate_id)
    deep_link = client.generate_deep_link(product_url, affiliate_id)
    return {
        "original_url": product_url,
        "affiliate_url": affiliate_url,
        "deep_link": deep_link,
    }


@mcp.tool()
async def shopee_get_product_variants(product_url: str) -> dict:
    """Get product variant data (size, color, options) for a Shopee product.

    Returns variant information including stock levels and pricing per variant.

    Args:
        product_url: Full Shopee product URL.

    Returns:
        dict with product_url and variants list (id, name, price, stock, sold).
    """
    client = _get_client()
    variants = await client.get_product_variants(product_url=product_url)
    return {"product_url": product_url, "variants": variants}


@mcp.tool()
async def shopee_get_shop_products(
    shop_id: str, page: int = 1, limit: int = 20
) -> dict:
    """Get all products from a specific Shopee shop.

    Useful for competitor shop analysis or finding products from a trusted seller.

    Args:
        shop_id: Shopee shop identifier (numeric string).
        page: Page number (1-indexed).
        limit: Results per page (max 60).

    Returns:
        dict with shop_id, products list.
    """
    client = _get_client()
    products = await client.get_shop_products(
        shop_id=shop_id, page=page, limit=limit
    )
    return {
        "shop_id": shop_id,
        "products": [p.model_dump() for p in products],
    }
