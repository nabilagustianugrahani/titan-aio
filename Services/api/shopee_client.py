"""Shopee API Client — real product data from Shopee Indonesia."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
from pydantic import BaseModel, Field


class ShopeeProduct(BaseModel):
    product_id: str
    name: str
    price: float
    currency: str = "IDR"
    rating: float = 0.0
    sold: int = 0
    stock: int = 0
    category: str = ""
    shop_name: str = ""
    shop_id: str = ""
    image: str = ""
    url: str = ""
    commission_rate: float = 0.0
    affiliate_url: str = ""


class ShopeeSearchResult(BaseModel):
    query: str
    total_results: int = 0
    products: list[ShopeeProduct] = []
    page: int = 1
    has_more: bool = False


class ShopeeClient:
    """Real Shopee Indonesia API client.

    Uses Shopee's internal API endpoints for product search and details.
    No official API key needed — uses public web endpoints.
    """

    BASE_URL = "https://shopee.co.id/api/v4"
    SEARCH_URL = "https://shopee.co.id/api/v4/search/search_items"
    PRODUCT_URL = "https://shopee.co.id/api/v4/item/get"
    ITEM_SEARCH_URL = "https://shopee.co.id/api/v4/search/search_items"

    # Rate limiting: max 30 requests per 60 seconds
    _MAX_REQUESTS = 30
    _RATE_WINDOW_SECONDS = 60.0

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._request_timestamps: list[float] = []
        self._last_cookie_refresh: float = 0.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json",
                    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
                    "Referer": "https://shopee.co.id/",
                    "X-Requested-With": "XMLHttpRequest",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                },
            )
        await self._refresh_cookies_if_needed()
        return self._client

    async def _refresh_cookies_if_needed(self) -> None:
        """Refresh cookies periodically to maintain session validity."""
        if self._client is None or self._client.is_closed:
            return
        now = time.time()
        if now - self._last_cookie_refresh < 300:
            return
        try:
            resp = await self._client.get(
                "https://shopee.co.id/",
                headers={"Accept": "text/html"},
                follow_redirects=True,
            )
            self._last_cookie_refresh = now
        except Exception:
            pass

    async def _rate_limit(self) -> None:
        """Enforce rate limiting: max _MAX_REQUESTS per _RATE_WINDOW_SECONDS."""
        now = time.time()
        cutoff = now - self._RATE_WINDOW_SECONDS
        self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]
        if len(self._request_timestamps) >= self._MAX_REQUESTS:
            oldest = self._request_timestamps[0]
            wait_time = self._RATE_WINDOW_SECONDS - (now - oldest) + 0.1
            if wait_time > 0:
                await self._async_sleep(wait_time)
        self._request_timestamps.append(time.time())

    @staticmethod
    async def _async_sleep(seconds: float) -> None:
        """Async sleep without importing asyncio at module level."""
        import asyncio
        await asyncio.sleep(seconds)

    def _parse_product_url(self, url: str) -> tuple[str, str]:
        """Extract shop_id and item_id from Shopee URL.

        Supports formats:
        - https://shopee.co.id/Product-Name-i.shopid.itemid
        - https://shopee.co.id/product-name-i.shopid.itemid
        - https://shopee.co.id/api/v4/item/get?shopid=X&itemid=Y
        """
        # Standard URL pattern: -i.{shopid}.{itemid}
        match = re.search(r"-i\.(\d+)\.(\d+)", url)
        if match:
            return match.group(1), match.group(2)

        # API URL pattern with query params
        shop_match = re.search(r"shopid=(\d+)", url)
        item_match = re.search(r"itemid=(\d+)", url)
        if shop_match and item_match:
            return shop_match.group(1), item_match.group(1)

        # Fallback: extract all numeric segments
        path_part = url.split("?")[0]
        nums = re.findall(r"\d+", path_part.split("/")[-1])
        if len(nums) >= 2:
            return nums[-2], nums[-1]
        return "", ""

    @staticmethod
    def _normalize_price(raw_price: int | float) -> float:
        """Convert Shopee internal price (IDR with 100000 multiplier) to actual IDR."""
        if raw_price > 1_000_000_000:
            return raw_price / 100_000
        if raw_price > 100_000_000:
            return raw_price / 100_000
        return float(raw_price)

    @staticmethod
    def _build_image_url(image_key: str) -> str:
        """Build full Shopee CDN image URL from image key."""
        if not image_key:
            return ""
        if image_key.startswith("http"):
            return image_key
        return f"https://cf.shopee.co.id/file/{image_key}"

    @staticmethod
    def _build_product_url(shop_id: int | str, item_id: int | str, slug: str = "") -> str:
        """Build canonical Shopee product URL."""
        slug_part = slug if slug else "product"
        return f"https://shopee.co.id/{slug_part}-i.{shop_id}.{item_id}"

    def _item_to_product(self, item_data: dict, slug: str = "") -> ShopeeProduct:
        """Convert raw Shopee API item dict to ShopeeProduct model."""
        shop_id = item_data.get("shopid", "")
        item_id = item_data.get("itemid", "")
        raw_price = item_data.get("price", 0)
        rating_info = item_data.get("item_rating", {})

        return ShopeeProduct(
            product_id=str(item_id),
            name=item_data.get("name", ""),
            price=self._normalize_price(raw_price),
            currency="IDR",
            rating=rating_info.get("rating_star", 0.0),
            sold=item_data.get("historical_sold", 0) or item_data.get("sold", 0),
            stock=item_data.get("stock", 0),
            category=item_data.get("category_name", "")
            or item_data.get("catname", "")
            or "",
            shop_name=item_data.get("shop_name", "")
            or item_data.get("shop_info", {}).get("name", "")
            or "",
            shop_id=str(shop_id),
            image=self._build_image_url(item_data.get("image", "")),
            url=self._build_product_url(shop_id, item_id, slug),
        )

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        sort: str = "relevancy",
        min_price: float = 0,
        max_price: float = 0,
    ) -> ShopeeSearchResult:
        """Search for products on Shopee.

        Args:
            query: Search keyword (e.g. "earphone bluetooth", "case iPhone 15").
            page: Page number (1-indexed).
            limit: Results per page (max 60).
            sort: Sort order — "relevancy", "sales", "price_asc", "price_desc", "ctime" (newest).
            min_price: Minimum price filter (IDR).
            max_price: Maximum price filter (IDR).

        Returns:
            ShopeeSearchResult with matched products.
        """
        await self._rate_limit()
        client = await self._get_client()

        limit = min(limit, 60)
        offset = (page - 1) * limit

        params: dict = {
            "by": "relevancy",
            "keyword": query,
            "limit": limit,
            "newest": offset,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2,
        }

        sort_map = {
            "sales": ("sales", "desc"),
            "price_asc": ("price", "asc"),
            "price_desc": ("price", "desc"),
            "ctime": ("ctime", "desc"),
            "rating": ("rating", "desc"),
        }
        if sort in sort_map:
            sort_field, sort_order = sort_map[sort]
            params["by"] = sort_field
            params["order"] = sort_order

        if min_price > 0:
            params["min_price"] = int(min_price)
        if max_price > 0:
            params["max_price"] = int(max_price)

        try:
            resp = await client.get(self.SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            products: list[ShopeeProduct] = []
            for item in items:
                item_data = item.get("item_basic", item)
                try:
                    product = self._item_to_product(item_data)
                    products.append(product)
                except Exception:
                    continue

            total = data.get("total_count", 0)

            return ShopeeSearchResult(
                query=query,
                total_results=total,
                products=products,
                page=page,
                has_more=len(products) == limit and (offset + limit) < total,
            )
        except httpx.HTTPStatusError:
            return ShopeeSearchResult(query=query, total_results=0, products=[])
        except httpx.RequestError:
            return ShopeeSearchResult(query=query, total_results=0, products=[])
        except Exception:
            return ShopeeSearchResult(query=query, total_results=0, products=[])

    async def get_product(self, product_url: str) -> ShopeeProduct | None:
        """Get detailed product info from a Shopee URL.

        Args:
            product_url: Full Shopee product URL containing shop_id and item_id.

        Returns:
            ShopeeProduct with full details, or None if not found.
        """
        await self._rate_limit()
        client = await self._get_client()
        shop_id, item_id = self._parse_product_url(product_url)

        if not shop_id or not item_id:
            return None

        params = {"itemid": item_id, "shopid": shop_id}

        try:
            resp = await client.get(self.PRODUCT_URL, params=params)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            item = data.get("item", data)

            if not item or not item.get("itemid"):
                return None

            return self._item_to_product(item)
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError:
            return None
        except Exception:
            return None

    async def get_product_by_id(
        self, shop_id: str | int, item_id: str | int
    ) -> ShopeeProduct | None:
        """Get product details using raw shop_id and item_id.

        Args:
            shop_id: Shopee shop identifier.
            item_id: Shopee item identifier.

        Returns:
            ShopeeProduct with full details, or None if not found.
        """
        url = self._build_product_url(shop_id, item_id)
        return await self.get_product(url)

    async def get_trending(
        self, category: str = "", limit: int = 20
    ) -> ShopeeSearchResult:
        """Get trending/best-selling products.

        Args:
            category: Optional category filter (searched as keyword).
            limit: Number of results.

        Returns:
            ShopeeSearchResult with trending products.
        """
        query = category if category else "terlaris"
        return await self.search(query=query, sort="sales", limit=limit)

    async def get_high_commission(
        self, keyword: str = "", limit: int = 10
    ) -> list[ShopeeProduct]:
        """Search for high-commission affiliate products.

        Finds popular products with strong sales volume, suitable for
        affiliate promotion. Assigns estimated commission rates.

        Args:
            keyword: Search keyword. Defaults to "terlaris" (best-selling).
            limit: Max products to return.

        Returns:
            List of ShopeeProduct with estimated commission rates.
        """
        result = await self.search(
            query=keyword or "terlaris", sort="sales", limit=limit
        )
        for product in result.products:
            if not product.commission_rate:
                product.commission_rate = self._estimate_commission_rate(product)
        return result.products

    async def search_by_category(
        self, category_id: int | str, limit: int = 20, sort: str = "sales"
    ) -> ShopeeSearchResult:
        """Browse products by Shopee category ID.

        Args:
            category_id: Shopee numeric category ID.
            limit: Number of results.

        Returns:
            ShopeeSearchResult with category products.
        """
        await self._rate_limit()
        client = await self._get_client()

        limit = min(limit, 60)
        params: dict = {
            "catid": category_id,
            "limit": limit,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "version": 2,
        }

        sort_map = {
            "sales": ("sales", "desc"),
            "price_asc": ("price", "asc"),
            "price_desc": ("price", "desc"),
            "ctime": ("ctime", "desc"),
        }
        if sort in sort_map:
            sort_field, sort_order = sort_map[sort]
            params["by"] = sort_field
            params["order"] = sort_order

        try:
            resp = await client.get(self.SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            products: list[ShopeeProduct] = []
            for item in items:
                item_data = item.get("item_basic", item)
                try:
                    product = self._item_to_product(item_data)
                    products.append(product)
                except Exception:
                    continue

            total = data.get("total_count", 0)
            return ShopeeSearchResult(
                query=f"category:{category_id}",
                total_results=total,
                products=products,
                page=1,
                has_more=len(products) == limit,
            )
        except Exception:
            return ShopeeSearchResult(
                query=f"category:{category_id}", total_results=0, products=[]
            )

    async def price_compare(
        self, keyword: str, limit: int = 20
    ) -> ShopeeSearchResult:
        """Search and sort by price ascending for comparison.

        Args:
            keyword: Product keyword to compare.
            limit: Number of results.

        Returns:
            ShopeeSearchResult sorted by price (lowest first).
        """
        return await self.search(query=keyword, sort="price_asc", limit=limit)

    def generate_affiliate_url(
        self, product_url: str, affiliate_id: str = ""
    ) -> str:
        """Generate affiliate tracking URL for Shopee product.

        Uses Shopee's affiliate parameter format.

        Args:
            product_url: Original Shopee product URL.
            affiliate_id: Your Shopee affiliate/partner ID.

        Returns:
            URL with affiliate tracking parameters appended.
        """
        shop_id, item_id = self._parse_product_url(product_url)
        base_url = self._build_product_url(shop_id, item_id)

        if affiliate_id:
            return f"{base_url}?af_id={affiliate_id}&utm_source=affiliate&utm_medium={affiliate_id}"

        return base_url

    def generate_deep_link(
        self, product_url: str, campaign: str = ""
    ) -> str:
        """Generate a Shopee deep link for mobile app promotion.

        Args:
            product_url: Original Shopee product URL.
            campaign: Campaign identifier for tracking.

        Returns:
            Deep link URL for mobile sharing.
        """
        shop_id, item_id = self._parse_product_url(product_url)
        base_url = f"https://shopee.co.id/universal-link/i.{shop_id}.{item_id}"
        if campaign:
            return f"{base_url}?af_id={campaign}"
        return base_url

    @staticmethod
    def _estimate_commission_rate(product: ShopeeProduct) -> float:
        """Estimate Shopee affiliate commission rate based on product signals.

        Higher-rated products with more sales typically get better rates.
        """
        base_rate = 5.0
        if product.sold > 10_000:
            base_rate = 8.0
        elif product.sold > 1_000:
            base_rate = 6.5
        elif product.sold > 100:
            base_rate = 5.5

        if product.rating >= 4.8:
            base_rate += 1.0
        elif product.rating >= 4.5:
            base_rate += 0.5

        return round(base_rate, 1)

    async def get_product_variants(self, product_url: str) -> list[dict]:
        """Get product variant data (size, color, etc.) for a product.

        Returns:
            List of variant dicts with id, name, price, stock, sold fields.
        """
        await self._rate_limit()
        client = await self._get_client()
        shop_id, item_id = self._parse_product_url(product_url)

        if not shop_id or not item_id:
            return []

        params = {"itemid": item_id, "shopid": shop_id}

        try:
            resp = await client.get(self.PRODUCT_URL, params=params)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            item = data.get("item", data)

            tiers = item.get("tier_variations", [])
            if not tiers:
                return []

            variants: list[dict] = []
            stocks = item.get("stocks", [])
            for stock_entry in stocks:
                variant = {
                    "variant_id": stock_entry.get("itemid", ""),
                    "name": stock_entry.get("name", ""),
                    "price": self._normalize_price(stock_entry.get("price", 0)),
                    "stock": stock_entry.get("stock", 0),
                    "sold": stock_entry.get("sold", 0),
                    "extinfo": stock_entry.get("extinfo", {}),
                }
                variants.append(variant)

            return variants
        except Exception:
            return []

    async def get_shop_products(
        self, shop_id: str | int, page: int = 1, limit: int = 20
    ) -> list[ShopeeProduct]:
        """Get all products from a specific Shopee shop.

        Args:
            shop_id: Shopee shop identifier.
            page: Page number (1-indexed).
            limit: Results per page.

        Returns:
            List of ShopeeProduct from the shop.
        """
        await self._rate_limit()
        client = await self._get_client()

        limit = min(limit, 60)
        offset = (page - 1) * limit

        params = {
            "shopid": shop_id,
            "limit": limit,
            "newest": offset,
            "order": "desc",
        }

        try:
            resp = await client.get(
                "https://shopee.co.id/api/v4/shop/search_items", params=params
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            products: list[ShopeeProduct] = []
            for item in items:
                item_data = item.get("item_basic", item)
                try:
                    product = self._item_to_product(item_data)
                    products.append(product)
                except Exception:
                    continue

            return products
        except Exception:
            return []

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ShopeeClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
