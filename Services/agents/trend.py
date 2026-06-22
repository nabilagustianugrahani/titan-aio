"""Trend Agent — detects market trends from DB + optional social listening."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from Database.models import Product, Metric
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext

logger = logging.getLogger("titan.trend")


class TrendAgent(BaseAgent):
    """Detects trending products and market opportunities.

    Combines DB product/metric analysis with optional social listening
    via Agent-Reach CLI (Twitter, Reddit, YouTube).
    """

    async def execute(
        self, ctx: AgentContext, category: str = "", query: str = "",
        use_social: bool = False, **kwargs: Any,
    ) -> dict:
        # ── DB analysis ──
        db_result = await self._analyze_db(ctx, category)

        # ── Social listening (optional) ──
        social_signals: list[dict] = []
        if use_social:
            social_signals = await self._search_social(query or category)

        # ── Boost score from social signals ──
        social_boost = min(len(social_signals) * 0.3, 2.0)
        trend_score = min(db_result["trend_score"] + social_boost, 10.0)

        return {
            **db_result,
            "trend_score": round(trend_score, 1),
            "social_signals": social_signals,
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
            "detected_at": datetime.utcnow().isoformat(),
        }

    async def _search_social(self, query: str) -> list[dict]:
        """Search social platforms via Agent-Reach CLI (fallback to simulated)."""
        try:
            return await self._agent_reach_search(query)
        except Exception as e:
            logger.debug("Agent-Reach not available: %s — using simulated data", e)
            return self._simulate_social(query)

    async def _agent_reach_search(self, query: str) -> list[dict]:
        """Call Agent-Reach CLI for social listening."""
        sources = ["twitter", "reddit", "youtube"]
        results: list[dict] = []

        for source in sources:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "agent-reach", "skill", source, query, "--json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
                if proc.returncode == 0:
                    data = json.loads(stdout.decode())
                    items = data if isinstance(data, list) else data.get("results", [])
                    for item in items[:10]:
                        results.append({
                            "source": source,
                            "text": item.get("text", item.get("title", ""))[:200],
                            "url": item.get("url", ""),
                            "engagement": item.get("engagement", item.get("likes", 0)),
                        })
            except (asyncio.TimeoutError, FileNotFoundError, json.JSONDecodeError):
                continue

        if not results:
            raise RuntimeError("No results from Agent-Reach")
        return results

    def _simulate_social(self, query: str) -> list[dict]:
        """Simulated social data when Agent-Reach not installed."""
        return [
            {"source": "twitter", "text": f"Trending: {query} banyak dibicarakan", "engagement": 1240, "simulated": True},
            {"source": "reddit", "text": f"Review {query} di subreddit Indonesia", "engagement": 456, "simulated": True},
            {"source": "youtube", "text": f"Review {query} — 50k views", "engagement": 50000, "simulated": True},
        ]

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
            "social_signals": [],
            "detected_at": datetime.utcnow().isoformat(),
        }
