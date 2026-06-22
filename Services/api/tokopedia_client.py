"""Tokopedia API Client — product data from Tokopedia Indonesia."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel


class TokopediaProduct(BaseModel):
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
    wholesale_price: float = 0.0


class TokopediaSearchResult(BaseModel):
    query: str
    total_results: int = 0
    products: list[TokopediaProduct] = []
    page: int = 1
    has_more: bool = False


class TokopediaClient:
    """Tokopedia Indonesia product data client."""

    SEARCH_URL = "https://gql.tokopedia.com/graphql/SearchProductQueryV4"
    PRODUCT_URL = "https://gql.tokopedia.com/graphql/ProductQuery"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": "https://www.tokopedia.com",
                    "Referer": "https://www.tokopedia.com/",
                },
            )
        return self._client

    def _extract_product_id(self, url: str) -> str:
        """Extract product ID from Tokopedia URL."""
        match = re.search(r"/(\d+)", url.split("?")[0])
        return match.group(1) if match else ""

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        sort: str = "relevancy",
        min_price: float = 0,
        max_price: float = 0,
    ) -> TokopediaSearchResult:
        """Search for products on Tokopedia."""
        client = await self._get_client()

        sort_map: dict[str, str] = {
            "relevancy": "relevancy",
            "price_asc": "2",
            "price_desc": "3",
            "newest": "9",
            "sold": "5",
            "rating": "6",
        }
        ob = sort_map.get(sort, sort)

        params_str = f"device=desktop&navsource=home&ob={ob}&page={page}&q={query}&rows={limit}&safe_search=false&source=search"
        if min_price > 0:
            params_str += f"&pmin={int(min_price)}"
        if max_price > 0:
            params_str += f"&pmax={int(max_price)}"

        payload = {
            "operationName": "SearchProductQueryV4",
            "variables": {"params": params_str},
            "query": (
                "query SearchProductQueryV4($params:String!){"
                "ace_search_product_v4(params:$params){"
                "header{totalData totalDataText}"
                "data{id name price{text textIdr textOriginal currency}{"
                "imageUrl url}"
                "labelGroups{text type}"
                "shop{id name city url}"
                "}}}"
            ),
        }

        try:
            resp = await client.post(self.SEARCH_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

            search_data = data.get("data", {}).get("ace_search_product_v4", {})
            products_data = search_data.get("data", [])
            total = search_data.get("header", {}).get("totalData", 0)

            products: list[TokopediaProduct] = []
            for item in products_data:
                price_info = item.get("price", {})
                price_text = price_info.get("textIdr", price_info.get("text", "0"))
                price_val = _parse_idr(price_text)

                shop_info = item.get("shop", {})
                labels = item.get("labelGroups", [])
                sold_count = _extract_sold(labels)
                rating_val = _extract_rating(labels)

                product_url = item.get("url", "")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www.tokopedia.com{product_url}"

                products.append(
                    TokopediaProduct(
                        product_id=item.get("id", ""),
                        name=item.get("name", ""),
                        price=price_val,
                        currency="IDR",
                        rating=rating_val,
                        sold=sold_count,
                        stock=0,
                        category="",
                        shop_name=shop_info.get("name", ""),
                        shop_id=shop_info.get("id", ""),
                        image=item.get("imageUrl", ""),
                        url=product_url,
                    )
                )

            return TokopediaSearchResult(
                query=query,
                total_results=total,
                products=products,
                page=page,
                has_more=len(products) == limit,
            )
        except Exception:
            return TokopediaSearchResult(
                query=query, total_results=0, products=[], page=page
            )

    async def get_product(self, product_url: str) -> TokopediaProduct | None:
        """Get detailed product info from a Tokopedia URL."""
        product_id = self._extract_product_id(product_url)
        if not product_id:
            return None

        client = await self._get_client()
        payload = {
            "operationName": "ProductQuery",
            "variables": {"id": product_id, "src": "pd"},
            "query": (
                "query ProductQuery($id:String!,$src:String!){"
                "data:getProductInfo(id:$id,src:$src){"
                "id name description url"
                "price{text textIdr textOriginal currency}"
                "imageUrl images{url}"
                "shop{id name url city isOfficial}"
                "stats{countView countReview countTalk countFavorite}"
                "category{id name}"
                "variant{id name option{id name price}}"
                "newFlag warranty"
                "}}"
            ),
        }

        try:
            resp = await client.post(self.PRODUCT_URL, json=payload)
            resp.raise_for_status()
            raw = resp.json().get("data", {}).get("getProductInfo", {})
            if not raw:
                return None

            price_info = raw.get("price", {})
            price_val = _parse_idr(
                price_info.get("textIdr", price_info.get("text", "0"))
            )
            shop = raw.get("shop", {})
            stats = raw.get("stats", {})
            category = raw.get("category", {})

            return TokopediaProduct(
                product_id=raw.get("id", product_id),
                name=raw.get("name", ""),
                price=price_val,
                currency="IDR",
                rating=0,
                sold=stats.get("countTalk", 0),
                stock=0,
                category=category.get("name", ""),
                shop_name=shop.get("name", ""),
                shop_id=shop.get("id", ""),
                image=raw.get("imageUrl", ""),
                url=raw.get("url", product_url),
            )
        except Exception:
            return None

    async def get_trending(
        self, category: str = "", limit: int = 20
    ) -> TokopediaSearchResult:
        """Get trending products."""
        query = category if category else "terlaris"
        return await self.search(query=query, sort="sold", limit=limit)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _parse_idr(text: str) -> float:
    """Parse IDR price string like 'Rp123.000' to 123000.0."""
    if not text:
        return 0.0
    cleaned = text.replace("Rp", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _extract_sold(labels: list[dict]) -> int:
    """Extract sold count from labelGroups."""
    for label in labels:
        if label.get("type") == "product_count_text":
            text = label.get("text", "")
            match = re.search(r"([\d.]+)", text.replace(".", ""))
            if match:
                try:
                    return int(match.group(1).replace(".", ""))
                except ValueError:
                    pass
    for label in labels:
        text = label.get("text", "")
        if "terjual" in text.lower():
            match = re.search(r"([\d.]+)", text.replace(".", ""))
            if match:
                try:
                    return int(match.group(1).replace(".", ""))
                except ValueError:
                    pass
    return 0


def _extract_rating(labels: list[dict]) -> float:
    """Extract rating from labelGroups."""
    for label in labels:
        text = label.get("text", "")
        if label.get("type") == "rating":
            try:
                return float(text)
            except (ValueError, TypeError):
                pass
    for label in labels:
        text = label.get("text", "")
        if re.match(r"^\d+(\.\d+)?$", text):
            try:
                val = float(text)
                if 0 < val <= 5:
                    return val
            except ValueError:
                pass
    return 0.0
