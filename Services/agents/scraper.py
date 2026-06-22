"""Scrape Agent — autonomous product discovery & data extraction.

Uses HF Space BrowserUse for scraping (zero RAM on VPS).
Fallback: ScrapingBee cloud browser → simulated data.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import httpx


class ScrapeAgent:
    """Autonomous product scraper — finds products without manual URLs.

    Fallback chain:
    1. HF Space BrowserUse (primary) → AI-powered browser scraping
    2. ScrapingBee cloud browser (fallback)
    3. Simulated data (zero deps fallback)
    """

    HF_SPACE_URL = os.environ.get("HF_SCRAPER_URL", "https://hf.space/titan/browser_scraper")

    def __init__(self, use_reach: bool = False):
        self.use_reach = use_reach

    async def search_products(
        self,
        keyword: str,
        platform: str = "shopee",
        max_results: int = 10,
    ) -> list[dict]:
        """Search products by keyword on e-commerce platforms.

        Args:
            keyword: Search term (e.g., "power bank 20000mah")
            platform: Target platform ('shopee', 'tokopedia', or 'all')
            max_results: Max products to return

        Returns:
            List of products with title, price, rating, url, sales
        """
        platforms = ["shopee", "tokopedia"] if platform == "all" else [platform]
        all_results = []

        for p in platforms:
            # 1. Try HF Space BrowserUse (primary)
            results = await self._scrape_with_hf_space(p, keyword, max_results // len(platforms))
            if results:
                all_results.extend(results)
            else:
                # 2. Fallback to ScrapingBee
                results = await self._scrape_with_scrapingbee(p, keyword, max_results // len(platforms))
                if results:
                    all_results.extend(results)
                else:
                    # 3. Fallback to simulated data
                    results = self._simulate_search(p, keyword, max_results // len(platforms))
                    all_results.extend(results)

        return all_results[:max_results]

    async def get_product_details(self, url: str) -> dict:
        """Extract detailed product info from a product URL."""
        # 1. Try HF Space BrowserUse (primary)
        result = await self._scrape_details_with_hf_space(url)
        if result and result.get("title") != "Unknown":
            return result
        # 2. Fallback to ScrapingBee
        result = await self._scrape_details_with_scrapingbee(url)
        if result and result.get("title") != "Unknown":
            return result
        # 3. Fallback to simulated data
        return self._simulate_details(url)

    async def get_reviews(self, url: str, max_reviews: int = 20) -> list[dict]:
        """Scrape reviews from a product page."""
        # TODO: Add HF Space review scraping
        return self._simulate_reviews(max_reviews)

    async def discover_trending(self, category: str = "") -> list[dict]:
        """Discover trending products from social media + e-commerce."""
        trends = []

        # Try Agent-Reach for social discovery
        if self.use_reach:
            try:
                from Services.agents.trend import TrendAgent
                trend = TrendAgent()
                # Use social search directly
                social = await trend._search_social(
                    query=f"{category} viral produk" if category else "produk viral terbaru"
                )
                trends.extend(social)
            except Exception:
                pass

        # Also search e-commerce directly
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

        return trends or self._simulate_trends(category)

    # -- HF Space BrowserUse (primary) ---------------------------

    async def _scrape_with_hf_space(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Scrape products via HF Space BrowserUse API."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.HF_SPACE_URL}/api/search",
                    json={"keyword": keyword, "platform": platform, "max_results": limit},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return data.get("products", [])
        except Exception:
            return []

    async def _scrape_details_with_hf_space(self, url: str) -> dict:
        """Get product details via HF Space BrowserUse API."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.HF_SPACE_URL}/api/details",
                    json={"url": url},
                )
                if resp.status_code != 200:
                    return {"title": "Unknown"}
                return resp.json()
        except Exception:
            return {"title": "Unknown"}

    # -- ScrapingBee (cloud browser, zero RAM) -------------------

    async def _scrape_with_scrapingbee(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Scrape products using ScrapingBee cloud browser."""
        from Services.browser.cloud_browser import CloudBrowser

        urls = {
            "shopee": f"https://shopee.co.id/search?keyword={keyword}&sortBy=sales",
            "tokopedia": f"https://www.tokopedia.com/search?q={keyword}&st=product&ob=5",
        }
        url = urls.get(platform)
        if not url:
            return []

        browser = CloudBrowser()
        try:
            result = await browser.navigate(url, extra_params={"wait": "5000"})
            if not result.success or not result.html:
                return []
            return self._parse_products_from_html(result.html, platform, keyword, limit)
        except Exception:
            return []
        finally:
            await browser.close()

    def _parse_products_from_html(self, html: str, platform: str, keyword: str, limit: int) -> list[dict]:
        """Parse product data from HTML response."""
        import re

        products = []

        # Try to extract product data from various patterns
        # Pattern 1: JSON data in script tags
        json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if json_matches:
            try:
                import json
                data = json.loads(json_matches[0])
                # Extract products from state
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
            # Look for product cards with various selectors
            product_patterns = [
                r'data-sqe="item"[^>]*>(.*?)</div>',
                r'class="[^"]*product[^"]*"[^>]*>(.*?)</div>',
                r'data-testid="divProductWrapper"[^>]*>(.*?)</div>',
            ]
            for pattern in product_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    for match in matches[:limit]:
                        # Extract title
                        title_match = re.search(r'class="[^"]*name[^"]*"[^>]*>([^<]+)', match)
                        title = title_match.group(1).strip() if title_match else keyword.title()

                        # Extract price
                        price_match = re.search(r'(?:Rp|IDR)\s*([\d.,]+)', match)
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

    async def _scrape_details_with_scrapingbee(self, url: str) -> dict:
        """Scrape product details using ScrapingBee cloud browser."""
        from Services.browser.cloud_browser import CloudBrowser

        browser = CloudBrowser()
        try:
            result = await browser.navigate(url, extra_params={"wait": "5000"})
            if not result.success or not result.html:
                return {"title": "Unknown"}
            html = result.html
            # Extract title
            title_m = re.search(r'<title[^>]*>([^<]+)', html)
            title = title_m.group(1).strip() if title_m else "Unknown"
            # Extract price
            price_m = re.search(r'(?:Rp|IDR)\s*([\d.,]+)', html)
            price = self._parse_price(price_m.group(0)) if price_m else 0
            # Extract rating
            rating_m = re.search(r'rating[^>]*>([\d.]+)', html)
            rating = float(rating_m.group(1)) if rating_m else None
            # Extract sales
            sales_m = re.search(r'(\d[\d.,]*)\s*(?:terjual|sold|sales)', html, re.I)
            sales = self._parse_sales(sales_m.group(1)) if sales_m else 0
            return {
                "title": title, "price": price, "rating": rating,
                "sales": sales, "url": url, "source": "scrapingbee",
            }
        except Exception:
            return {"title": "Unknown"}
        finally:
            await browser.close()

    # -- Scrapling (real content fetching) ----------------------

    async def _scrape_with_scrapling(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Scrape products using Scrapling AsyncFetcher."""
        try:
            from scrapling import AsyncFetcher
        except ImportError:
            return self._simulate_search(platform, keyword, limit)

        urls = {
            "shopee": f"https://shopee.co.id/search?keyword={keyword}",
            "tokopedia": f"https://www.tokopedia.com/search?q={keyword}",
        }
        url = urls.get(platform)
        if not url:
            return []

        try:
            fetcher = AsyncFetcher()
            resp = await fetcher.get(url)
            if resp is None or resp.status != 200:
                return self._simulate_search(platform, keyword, limit)

            # Parse HTML with Scrapling's built-in parser
            root = resp.css
            if root is None:
                return self._simulate_search(platform, keyword, limit)

            products = []
            items = root.css("div[data-sqe='item'], div[class*='product__'], a[data-track='click'], div[class*='card'])")
            if not items:
                return self._simulate_search(platform, keyword, limit)

            for item in items[:limit]:
                el_title = item.css("div[class*='name'], div[class*='title'], span[class*='name']")
                el_price = item.css("span[class*='price'], div[class*='price']")
                el_rating = item.css("div[class*='rating'], span[class*='rating']")
                el_link = item.css("a[href]")

                products.append({
                    "title": el_title[0].text_content().strip() if el_title else keyword.title(),
                    "price": self._parse_price(el_price[0].text_content() if el_price else "0"),
                    "rating": float(str(el_rating[0].text_content())[:3]) if el_rating else None,
                    "url": el_link[0].attrib.get("href", "") if el_link else url,
                    "platform": platform,
                    "source": "scrapling",
                })

            return products if products else self._simulate_search(platform, keyword, limit)

        except Exception:
            return self._simulate_search(platform, keyword, limit)

    async def _scrape_details(self, url: str) -> dict:
        """Scrape product details page."""
        try:
            from scrapling import AsyncFetcher
            fetcher = AsyncFetcher()
            resp = await fetcher.get(url)
            if resp is None:
                return self._simulate_details(url)
            root = resp.css
            if root is None:
                return self._simulate_details(url)

            el_title = root.css("h1, div[class*='title'], span[class*='name']")
            el_price = root.css("div[class*='price'], span[class*='price']")
            el_rating = root.css("div[class*='rating'], span[class*='rating']")
            el_sales = root.css("div[class*='sale'], span[class*='sale'], div[class*='terjual']")
            el_desc = root.css("div[class*='description'], div[class*='desc'], p[class*='desc']")

            result = {
                "title": el_title[0].text_content() if el_title else "Unknown",
                "price": self._parse_price(el_price[0].text_content() if el_price else "0"),
                "rating": float(el_rating[0].text_content()[:3]) if el_rating else None,
                "sales": self._parse_sales(el_sales[0].text_content() if el_sales else "0"),
                "description": el_desc[0].text_content()[:500] if el_desc else "",
                "url": url,
                "source": "scrapling",
            }

            await fetcher.close()
            return result
        except Exception as e:
            return {**self._simulate_details(url), "error": str(e)}

    async def _scrape_reviews(self, url: str, max_reviews: int) -> list[dict]:
        """Scrape product reviews."""
        try:
            from scrapling import AsyncFetcher
            fetcher = AsyncFetcher()
            resp = await fetcher.get(url)
            if resp is None:
                return self._simulate_reviews(max_reviews)
            root = resp.css
            if root is None:
                return self._simulate_reviews(max_reviews)

            review_elements = root.css("div[class*='review'], div[class*='rating'], li[class*='review']")
            reviews = []
            for r in review_elements[:max_reviews]:
                text = r.css("span[class*='content'], div[class*='text'], p")
                stars = r.css("img[class*='star'], div[class*='star']")

                reviews.append({
                    "text": text[0].text_content() if text else "",
                    "rating": len(stars) if stars else None,
                    "source": "scrapling",
                })

            return reviews if reviews else self._simulate_reviews(max_reviews)
        except Exception:
            return self._simulate_reviews(max_reviews)

    # -- Fallback: simulated data (zero deps) -----------------

    def _simulate_search(self, platform: str, keyword: str, limit: int) -> list[dict]:
        """Fallback simulated search results. Using simulated data — install scraping deps for real data."""
        import logging
        logging.getLogger("titan.scraper").warning(
            "Using simulated search data for '%s' — install httpx+lxml for real scraping", keyword
        )
        import random
        products = [
            {"title": f"{keyword} Premium Original - Terlaris", "price": round(random.uniform(15000, 500000), -3), "rating": round(random.uniform(3.5, 5), 1), "sales": random.randint(100, 5000), "platform": platform, "source": "simulated"},
            {"title": f"{keyword} Termurah Se-Indonesia", "price": round(random.uniform(10000, 300000), -3), "rating": round(random.uniform(3.0, 4.5), 1), "sales": random.randint(50, 2000), "platform": platform, "source": "simulated"},
            {"title": f"{keyword} Kualitas Premium - Garansi Resmi", "price": round(random.uniform(200000, 800000), -3), "rating": round(random.uniform(4.0, 5.0), 1), "sales": random.randint(200, 10000), "platform": platform, "source": "simulated"},
        ]
        for p in products:
            p["url"] = f"https://{platform}.co.id/products/{keyword.replace(' ', '-')}-{random.randint(100,999)}"
        return products[:limit]

    def _simulate_details(self, url: str) -> dict:
        import logging
        logging.getLogger("titan.scraper").warning("Using simulated product details — install scraping deps for real data")
        import random
        return {
            "title": "Produk Premium Original",
            "price": round(random.uniform(25000, 500000), -3),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "sales": random.randint(100, 5000),
            "description": "Produk original kualitas terbaik. Garansi resmi 1 tahun.",
            "url": url,
            "source": "simulated",
        }

    def _simulate_reviews(self, count: int) -> list[dict]:
        texts = [
            "Produk sangat bagus, sesuai deskripsi",
            "Kualitas ok, pengiriman cepat",
            "Barang original, recommended",
            "Lumayan untuk harganya",
            "Pengiriman lama, barang gepok",
            "Kualitas kurang sesuai ekspektasi",
            "Mantap! seller respon cepat",
        ]
        import random
        return [{"text": random.choice(texts), "rating": random.choice([4, 5, 3, 4, 5, 2, 5]), "source": "simulated"} for _ in range(min(count, 15))]

    def _simulate_trends(self, category: str) -> list[dict]:
        return [
            {"source": "twitter", "text": f"{category} lagi viral di Twitter!", "engagement": 1500, "simulated": True},
            {"source": "youtube", "text": f"Review {category} — 100k views", "engagement": 100000, "simulated": True},
            {"source": "shopee", "text": f"{category} best seller", "price": 150000, "simulated": True},
        ]

    @staticmethod
    def _parse_price(text: str) -> float:
        nums = re.findall(r'[\d.]+', text.replace("Rp", "").replace(".", "").strip())
        return float(nums[0]) if nums else 0.0

    @staticmethod
    def _parse_sales(text: str) -> int:
        nums = re.findall(r'\d+', text)
        return int(nums[0]) if nums else 0
