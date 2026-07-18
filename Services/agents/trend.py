"""Trend Agent — detects market trends from DB + real web search."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from Database.models import Metric, Product
from Database.repository import Repository
from Services.agents.base import AgentContext, BaseAgent
from Services.llm import analyze_competitors_llm, llm_call

logger = logging.getLogger("titan.trend")


class TrendAgent(BaseAgent):
    """Detects trending products and market opportunities.

    Combines DB product/metric analysis with real web search
    for trend data, analyzed via LLM.
    """

    async def execute(
        self, ctx: AgentContext, category: str = "", query: str = "",
        use_social: bool = False, **kwargs: Any,
    ) -> dict:
        # ── DB analysis ──
        db_result = await self._analyze_db(ctx, category)

        # ── Web trend search (always runs, replaces old social listening) ──
        search_query = query or category
        web_data: list[dict] = []
        if search_query:
            web_data = await self._search_trending_products(search_query)

        # ── LLM analysis of real web data ──
        llm_analysis: dict = {}
        competitor_analysis: dict = {}
        if web_data:
            llm_analysis = await self._llm_analyze_trends(web_data, search_query)
            competitor_analysis = await analyze_competitors_llm(
                competitor_data=json.dumps(
                    [{"source": w.get("source", ""), "content_preview": w.get("content", "")[:500]}
                     for w in web_data[:3]],
                    indent=2,
                ),
                product_name=search_query,
                category=category,
            )

        # ── Merge LLM insights into result ──
        trend_score = db_result["trend_score"]
        adjustment = llm_analysis.get("trend_score_adjustment", 0)
        if isinstance(adjustment, (int, float)):
            trend_score = min(max(trend_score + adjustment, 0), 10.0)

        return {
            **db_result,
            "trend_score": round(trend_score, 1),
            "web_data": web_data,
            "llm_analysis": llm_analysis,
            "competitor_analysis": competitor_analysis,
            "detected_at": datetime.utcnow().isoformat(),
        }

    async def _analyze_db(self, ctx: AgentContext, category: str) -> dict:
        """Analyze products and metrics from database."""
        repo = Repository(ctx.session, Product)
        metric_repo = Repository(ctx.session, Metric)

        if category:
            products = await repo.find(category=category)
        else:
            products = await repo.list_all(limit=100)

        product_count = len(products)
        if product_count == 0:
            return self._empty(category)

        avg_rating = sum(p.rating or 0 for p in products) / product_count
        total_sales = sum(p.total_sales or 0 for p in products)
        avg_price = sum(p.price for p in products) / product_count

        high_rated = sum(1 for p in products if (p.rating or 0) >= 4.0)
        quality_ratio = high_rated / product_count

        # Metrics
        all_metrics: list = []
        for p in products:
            m = await metric_repo.find(campaign_id=p.id)
            all_metrics.extend(m)

        total_views = sum(m.views for m in all_metrics)
        total_clicks = sum(m.clicks for m in all_metrics)
        total_revenue = sum(m.revenue for m in all_metrics)

        # Score (0-10)
        density = min(product_count / 10.0, 3.0)
        sales = min(total_sales / 1000.0, 3.0)
        quality = quality_ratio * 2.0
        engagement = min((total_views + total_clicks) / 5000.0, 2.0)
        trend_score = round(min(density + sales + quality + engagement, 10.0), 1)

        # Direction
        sorted_by_usage = sorted(products, key=lambda p: p.usage_count, reverse=True)
        top_half = sorted_by_usage[: product_count // 2 or 1]
        bot_half = sorted_by_usage[product_count // 2 or 1 :]
        top_sales = sum(p.total_sales or 0 for p in top_half) / len(top_half)
        bot_sales = sum(p.total_sales or 0 for p in bot_half) / len(bot_half)

        if top_sales > bot_sales * 1.2:
            direction = "up"
        elif top_sales < bot_sales * 0.8:
            direction = "down"
        else:
            direction = "stable"

        # Velocity
        if trend_score >= 8:
            velocity = "viral"
        elif trend_score >= 5:
            velocity = "fast"
        elif trend_score >= 2.5:
            velocity = "moderate"
        else:
            velocity = "slow"

        top_products = [
            {"product_id": p.id, "title": p.title[:80], "price": p.price,
             "rating": p.rating, "sales": p.total_sales}
            for p in sorted_by_usage[:5]
        ]

        return {
            "category": category,
            "trend_score": trend_score,
            "trend_direction": direction,
            "velocity": velocity,
            "product_count": product_count,
            "avg_rating": round(avg_rating, 2),
            "total_sales": total_sales,
            "avg_price": round(avg_price, 0),
            "engagement": {"views": total_views, "clicks": total_clicks, "revenue": total_revenue},
            "top_products": top_products,
        }

    async def _search_trending_products(self, query: str) -> list[dict]:
        """Search the web for real trending product data via ScrapingBee or direct fetch."""
        if not query:
            return []
        api_key = os.environ.get("SCRAPINGBEE_API_KEY", "")
        if api_key:
            return await self._scrape_via_scrapingbee(query, api_key)
        return await self._fetch_via_httpx(query)

    async def _scrape_via_scrapingbee(self, query: str, api_key: str) -> list[dict]:
        """Search trending products via ScrapingBee API."""
        encoded = query.replace(" ", "+")
        search_url = (
            f"https://www.google.com/search?q={encoded}+produk+terlaris+2026&hl=id"
        )
        api_url = "https://app.scrapingbee.com/api/v1"
        params = {
            "api_key": api_key,
            "url": search_url,
            "render_js": "false",
            "premium_proxy": "true",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(api_url, params=params)
                resp.raise_for_status()
                return [{"source": "scrapingbee", "query": query, "content": resp.text[:6000]}]
        except Exception as e:
            logger.warning("ScrapingBee search failed: %s", e)
            return await self._fetch_via_httpx(query)

    async def _fetch_via_httpx(self, query: str) -> list[dict]:
        """Fallback: direct HTTP fetch of search results."""
        results: list[dict] = []
        encoded = query.replace(" ", "+")
        search_urls = [
            f"https://www.google.com/search?q={encoded}+trending+products+2026&hl=en",
        ]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for url in search_urls:
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        results.append({
                            "source": url,
                            "query": query,
                            "content": resp.text[:6000],
                        })
                except Exception as e:
                    logger.debug("Failed to fetch %s: %s", url, e)
        return results

    async def _llm_analyze_trends(self, web_data: list[dict], category: str) -> dict:
        """Use LLM to extract trend insights from real web data."""
        web_text = "\n\n".join(
            f"[{item.get('source', 'web')}]\n{item.get('content', '')[:2000]}"
            for item in web_data
        )[:6000]

        system_prompt = """Kamu adalah analis tren e-commerce Indonesia.
Analisis data dari web dan ekstrak insight tren produk.
Gunakan Bahasa Indonesia.
Output JSON:
{
  "trend_score_adjustment": 0.0,
  "trend_direction": "up/down/stable",
  "velocity": "viral/fast/moderate/slow",
  "trending_products": [{"name": "...", "reason": "..."}],
  "market_insights": "...",
  "recommended_angles": ["..."]
}"""

        user_prompt = f"Kategori: {category}\nData Web:\n{web_text}\n\nAnalisis tren:"

        result_text = await llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
        )
        if not result_text:
            return {}

        try:
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if 0 <= start < end:
                return json.loads(result_text[start:end])
        except json.JSONDecodeError:
            logger.warning("LLM trend analysis JSON parse failed")
        return {}

    @staticmethod
    def _empty(category: str) -> dict:
        return {
            "category": category,
            "trend_score": 0.0,
            "trend_direction": "stable",
            "velocity": "slow",
            "product_count": 0,
            "avg_rating": 0.0,
            "total_sales": 0,
            "avg_price": 0.0,
            "engagement": {"views": 0, "clicks": 0, "revenue": 0.0},
            "top_products": [],
            "web_data": [],
            "llm_analysis": {},
            "competitor_analysis": {},
            "detected_at": datetime.utcnow().isoformat(),
        }
