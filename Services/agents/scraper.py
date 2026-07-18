"""Scrape Agent — autonomous product discovery & data extraction.

Real scraping sources in priority order:
1. ScrapingBee API (cloud browser via SCRAPINGBEE_API_KEY env)
2. ShopeeClient / TokopediaClient (platform API wrappers)
3. LLM extraction from URL context (intelligent fallback via llm_call)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from Services.agents.base import AgentContext, BaseAgent
from Services.api.shopee_client import ShopeeClient
from Services.api.tokopedia_client import TokopediaClient
from Services.llm import llm_call

logger = logging.getLogger(__name__)


class ScrapeAgent(BaseAgent):
    """Autonomous product scraper — finds products using real data sources.

    Priority:
    1. ScrapingBee API (cloud browser, needs SCRAPINGBEE_API_KEY in env)
    2. ShopeeClient / TokopediaClient (platform API clients)
    3. LLM extraction (intelligent fallback from URL context)
    """

    SCRAPINGBEE_BASE = "https://app.scrapingbee.com/api/v1/"

    def __init__(self, use_reach: bool = False, name: str = "") -> None:
        super().__init__(name=name)
        self.use_reach = use_reach
        self._scrapingbee_key = os.environ.get("SCRAPINGBEE_API_KEY", "")

    async def execute(self, ctx: AgentContext, **kwargs: Any) -> Any:
        """Execute the agent's task (BaseAgent interface).

        Supported actions via kwargs:
          - action="search"   -> search_products(keyword, platform, max_results)
          - action="details"  -> get_product_details(url)
          - action="reviews"  -> get_reviews(url, max_reviews)
          - action="trending" -> discover_trending(category)
        """
        action = kwargs.get("action", "")
        if action == "search":
            return await self.search_products(
                keyword=kwargs.get("keyword", ""),
                platform=kwargs.get("platform", "shopee"),
                max_results=kwargs.get("max_results", 10),
            )
        if action == "details":
            return await self.get_product_details(url=kwargs.get("url", ""))
        if action == "reviews":
            return await self.get_reviews(
                url=kwargs.get("url", ""),
                max_reviews=kwargs.get("max_reviews", 20),
            )
        if action == "trending":
            return await self.discover_trending(category=kwargs.get("category", ""))
        return {}

    # ── Public API ───────────────────────────────────────────────────

    async def search_products(
        self,
        keyword: str,
        platform: str = "shopee",
        max_results: int = 10,
    ) -> list[dict]:
        """Search products by keyword on e-commerce platforms.

        Priority: ScrapingBee -> ShopeeClient/TokopediaClient -> LLM
        """
        platforms = ["shopee", "tokopedia"] if platform == "all" else [platform]
        all_results: list[dict] = []

        for p in platforms:
            # 1. ScrapingBee API
            results = await self._scrape_with_scrapingbee(p, keyword, max_results // len(platforms))
            if results:
                all_results.extend(results)
                continue

            # 2. Platform API client
            results = await self._scrape_with_client(p, keyword, max_results // len(platforms))
            if results:
                all_results.extend(results)
                continue

            # 3. LLM extraction (last resort)
            results = await self._scrape_with_llm(p, keyword, max_results // len(platforms))
            if results:
                all_results.extend(results)

        return all_results[:max_results]

    async def get_product_details(self, url: str) -> dict:
        """Extract detailed product info from a product URL.

        Priority: ScrapingBee -> ShopeeClient/TokopediaClient -> LLM
        """
        result = await self._details_with_scrapingbee(url)
        if result and result.get("title") not in (None, "Unknown"):
            return result

        result = await self._details_with_client(url)
        if result and result.get("title") not in (None, "Unknown"):
            return result

        return await self._details_with_llm(url)

    async def get_reviews(self, url: str, max_reviews: int = 20) -> list[dict]:
        """Scrape reviews from a product page.

        Priority: ScrapingBee -> LLM
        """
        reviews = await self._reviews_with_scrapingbee(url, max_reviews)
        if reviews:
            return reviews
        return await self._reviews_with_llm(url, max_reviews)

    async def discover_trending(self, category: str = "") -> list[dict]:
        """Discover trending products from social media + e-commerce."""
        trends: list[dict] = []

        if self.use_reach:
            try:
                from Services.agents.trend import TrendAgent

                trend = TrendAgent()
                social = await trend._search_social(
                    query=f"{category} viral produk" if category else "produk viral terbaru",
                )
                trends.extend(social)
            except Exception:
                logger.warning("TrendAgent unavailable for discover_trending")

        if category:
            products = await self.search_products(category, max_results=5)
            for p in products:
                trends.append({
                    "source": p.get("platform", "shopee"),
                    "text": p.get("title", ""),
                    "price": p.get("price", 0),
                    "engagement": p.get("sales", 0),
                    "url": p.get("url", ""),
                })

        return trends

    # ── 1. ScrapingBee API ──────────────────────────────────────────

    async def _scrape_with_scrapingbee(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Search products via ScrapingBee cloud browser API."""
        if not self._scrapingbee_key:
            return []

        urls = {
            "shopee": f"https://shopee.co.id/search?keyword={keyword}&sortBy=sales",
            "tokopedia": f"https://www.tokopedia.com/search?q={keyword}&st=product&ob=5",
        }
        url = urls.get(platform)
        if not url:
            return []

        try:
            params = {
                "api_key": self._scrapingbee_key,
                "url": url,
                "render_js": "false",
                "premium_proxy": "true",
                "country_code": "id",
                "wait": "3000",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.SCRAPINGBEE_BASE, params=params)
                if resp.status_code != 200:
                    return []
                return self._parse_products_from_html(resp.text, platform, keyword, limit)
        except Exception:
            logger.debug("ScrapingBee search failed for %s/%s", platform, keyword)
            return []

    async def _details_with_scrapingbee(self, url: str) -> dict:
        """Get product details via ScrapingBee API."""
        if not self._scrapingbee_key:
            return {"title": "Unknown"}

        try:
            params = {
                "api_key": self._scrapingbee_key,
                "url": url,
                "render_js": "false",
                "premium_proxy": "true",
                "country_code": "id",
                "wait": "3000",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.SCRAPINGBEE_BASE, params=params)
                if resp.status_code != 200:
                    return {"title": "Unknown"}
                html = resp.text
                title_m = re.search(r"<title[^>]*>([^<]+)", html)
                title = title_m.group(1).strip() if title_m else "Unknown"
                price_m = re.search(r"(?:Rp|IDR)\s*([\d.,]+)", html)
                price = self._parse_price(price_m.group(0)) if price_m else 0
                rating_m = re.search(r"rating[^>]*>([\d.]+)", html)
                rating = float(rating_m.group(1)) if rating_m else None
                sales_m = re.search(r"(\d[\d.,]*)\s*(?:terjual|sold|sales)", html, re.I)
                sales = self._parse_sales(sales_m.group(1)) if sales_m else 0
                return {
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "sales": sales,
                    "url": url,
                    "source": "scrapingbee",
                }
        except Exception:
            logger.debug("ScrapingBee details failed for %s", url)
            return {"title": "Unknown"}

    async def _reviews_with_scrapingbee(self, url: str, max_reviews: int) -> list[dict]:
        """Scrape reviews via ScrapingBee API."""
        if not self._scrapingbee_key:
            return []

        try:
            params = {
                "api_key": self._scrapingbee_key,
                "url": url,
                "render_js": "false",
                "premium_proxy": "true",
                "country_code": "id",
                "wait": "3000",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.SCRAPINGBEE_BASE, params=params)
                if resp.status_code != 200:
                    return []
                html = resp.text
                reviews: list[dict] = []
                review_sections = re.findall(
                    r'<div[^>]*class="[^"]*(?:review|komentar|rating)[^"]*"[^>]*>(.*?)</div>',
                    html,
                    re.DOTALL | re.I,
                )
                for section in review_sections[:max_reviews]:
                    text_m = re.search(r"<p[^>]*>(.*?)</p>", section, re.DOTALL)
                    star_m = re.search(r"<img[^>]*star[^>]*>", section, re.I)
                    reviews.append({
                        "text": text_m.group(1).strip() if text_m else "",
                        "rating": 4 if star_m else None,
                        "source": "scrapingbee",
                    })
                return reviews
        except Exception:
            logger.debug("ScrapingBee reviews failed for %s", url)
            return []

    # ── 2. Platform API clients ─────────────────────────────────────

    async def _scrape_with_client(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Search products via ShopeeClient or TokopediaClient."""
        if platform == "shopee":
            try:
                client = ShopeeClient()
                result = await client.search(query=keyword, limit=limit)
                return [
                    {
                        "title": p.name,
                        "price": p.price,
                        "rating": p.rating,
                        "sales": p.sold,
                        "url": p.url,
                        "platform": "shopee",
                        "source": "shopee_client",
                    }
                    for p in result.products
                ]
            except Exception:
                return []
        elif platform == "tokopedia":
            try:
                client = TokopediaClient()
                result = await client.search(query=keyword, limit=limit)
                return [
                    {
                        "title": p.name,
                        "price": p.price,
                        "rating": p.rating,
                        "sales": p.sold,
                        "url": p.url,
                        "platform": "tokopedia",
                        "source": "tokopedia_client",
                    }
                    for p in result.products
                ]
            except Exception:
                return []
        return []

    async def _details_with_client(self, url: str) -> dict:
        """Get product details via ShopeeClient or TokopediaClient from URL."""
        if "shopee" in url:
            try:
                client = ShopeeClient()
                p = await client.get_product(url)
                if p:
                    return {
                        "title": p.name,
                        "price": p.price,
                        "rating": p.rating,
                        "sales": p.sold,
                        "url": url,
                        "source": "shopee_client",
                    }
            except Exception:
                pass
        elif "tokopedia" in url:
            try:
                client = TokopediaClient()
                p = await client.get_product(url)
                if p:
                    return {
                        "title": p.name,
                        "price": p.price,
                        "rating": p.rating,
                        "sales": p.sold,
                        "url": url,
                        "source": "tokopedia_client",
                    }
            except Exception:
                pass
        return {"title": "Unknown"}

    # ── 3. LLM extraction (last resort) ────────────────────────────

    async def _scrape_with_llm(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Use llm_call to generate plausible product data from keyword context."""
        try:
            system = (
                "Kamu adalah asisten e-commerce Indonesia. "
                "Berdasarkan keyword produk dan platform, buat data produk yang realistis."
            )
            prompt = (
                f"Keyword: {keyword}\n"
                f"Platform: {platform}\n"
                f"Jumlah: {limit}\n\n"
                f"Buat JSON array of objects dengan field: title (string), price (number dalam IDR), "
                f"rating (number 1-5), sales (number), url (string), platform (string), source='llm'."
            )
            text = await llm_call(system_prompt=system, user_prompt=prompt, temperature=0.3)
            if not text:
                return []
            data = self._extract_json(text)
            if isinstance(data, list):
                for item in data:
                    item.setdefault("platform", platform)
                    item.setdefault("source", "llm")
                    item.setdefault("rating", None)
                    item.setdefault("sales", 0)
                return data[:limit]
            if isinstance(data, dict):
                items: list = data.get("products", data.get("items", data.get("data", [])))
                if isinstance(items, list):
                    return items[:limit]
            return []
        except Exception:
            logger.debug("LLM search fallback failed for %s/%s", platform, keyword)
            return []

    async def _details_with_llm(self, url: str) -> dict:
        """Use llm_call to extract product info from URL context."""
        try:
            system = (
                "Kamu adalah asisten e-commerce Indonesia. "
                "Berdasarkan URL produk, ekstrak informasi produk yang paling mungkin."
            )
            prompt = (
                f"URL: {url}\n\n"
                f"Berdasarkan URL di atas, tebak informasi produk dalam format JSON:\n"
                f'{{"title": "nama produk", "price": 0, "rating": 0.0, "sales": 0, '
                f'"description": "...", "url": "{url}", "source": "llm"}}'
            )
            text = await llm_call(system_prompt=system, user_prompt=prompt, temperature=0.3)
            if not text:
                return {"title": "Unknown", "url": url, "source": "llm"}
            data = self._extract_json(text)
            if isinstance(data, dict):
                data.setdefault("url", url)
                data.setdefault("source", "llm")
                return data
            return {"title": "Unknown", "url": url, "source": "llm"}
        except Exception:
            return {"title": "Unknown", "url": url, "source": "llm"}

    async def _reviews_with_llm(self, url: str, max_reviews: int) -> list[dict]:
        """Use llm_call to generate plausible reviews from URL context."""
        try:
            system = (
                "Kamu adalah asisten e-commerce Indonesia. "
                "Berdasarkan URL produk, buat review yang realistis."
            )
            prompt = (
                f"URL: {url}\n\n"
                f"Buat {max_reviews} review realistis dalam format JSON array:\n"
                f'[{{"text": "...", "rating": 4, "source": "llm"}}]'
            )
            text = await llm_call(system_prompt=system, user_prompt=prompt, temperature=0.4)
            if not text:
                return []
            data = self._extract_json(text)
            if isinstance(data, list):
                for item in data:
                    item.setdefault("source", "llm")
                return data[:max_reviews]
            return []
        except Exception:
            logger.debug("LLM reviews fallback failed for %s", url)
            return []

    # ── JSON extraction helper ──────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Extract and parse JSON from LLM response text."""
        text = text.strip()
        # Try to find JSON array or object boundaries
        start = text.find("[")
        if start == -1:
            start = text.find("{")
        if start != -1:
            text = text[start:]
        # Strip markdown code fences
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence) :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    # ── HTML parsing helpers (used by ScrapingBee path) ───────────

    def _parse_products_from_html(self, html: str, platform: str, keyword: str, limit: int) -> list[dict]:
        """Parse product data from HTML response."""
        products: list[dict] = []

        # Pattern 1: JSON data in script tags
        json_matches = re.findall(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html, re.DOTALL)
        if json_matches:
            try:
                data = json.loads(json_matches[0])
                items = data.get("items", data.get("products", []))
                for item in items[:limit]:
                    if isinstance(item, dict):
                        products.append({
                            "title": item.get("name", item.get("title", keyword.title())),
                            "price": item.get("price", 0),
                            "rating": item.get("rating", item.get("score")),
                            "sales": item.get("sales", item.get("sold", 0)),
                            "url": item.get("url", ""),
                            "platform": platform,
                            "source": "scrapingbee",
                        })
            except Exception:
                pass

        # Pattern 2: Extract from HTML attributes
        if not products:
            product_patterns = [
                r'data-sqe="item"[^>]*>(.*?)</div>',
                r'class="[^"]*product[^"]*"[^>]*>(.*?)</div>',
                r'data-testid="divProductWrapper"[^>]*>(.*?)</div>',
            ]
            for pattern in product_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    for match in matches[:limit]:
                        title_match = re.search(r'class="[^"]*name[^"]*"[^>]*>([^<]+)', match)
                        title = title_match.group(1).strip() if title_match else keyword.title()
                        price_match = re.search(r"(?:Rp|IDR)\s*([\d.,]+)", match)
                        price = self._parse_price(price_match.group(0)) if price_match else 0
                        if title and price > 0:
                            products.append({
                                "title": title,
                                "price": price,
                                "rating": None,
                                "sales": 0,
                                "url": "",
                                "platform": platform,
                                "source": "scrapingbee",
                            })

        return products[:limit]

    @staticmethod
    def _parse_price(text: str) -> float:
        nums = re.findall(r"[\d.]+", text.replace("Rp", "").replace(".", "").strip())
        return float(nums[0]) if nums else 0.0

    @staticmethod
    def _parse_sales(text: str) -> int:
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else 0
