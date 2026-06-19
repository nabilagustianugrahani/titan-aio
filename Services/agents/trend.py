"""Trend Agent — detects market trends from DB product + metric data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select, func

from Database.models import Product, Metric
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class TrendAgent(BaseAgent):
    """Detects trending products and market opportunities from DB data."""

    async def execute(
        self, ctx: AgentContext, category: str = "", **kwargs: Any
    ) -> dict:
        repo = Repository(ctx.session, Product)
        metric_repo = Repository(ctx.session, Metric)

        # ── Products in this category ──
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

        # High-rated products ratio
        high_rated = sum(1 for p in products if (p.rating or 0) >= 4.0)
        quality_ratio = high_rated / product_count

        # ── Metrics for these products ──
        product_ids = [p.id for p in products]
        all_metrics: list = []
        for pid in product_ids:
            m = await metric_repo.find(campaign_id=pid)
            all_metrics.extend(m)

        total_views = sum(m.views for m in all_metrics)
        total_clicks = sum(m.clicks for m in all_metrics)
        total_revenue = sum(m.revenue for m in all_metrics)

        # ── Compute trend score (0-10) ──
        # Factor 1: product density (more products = more interest)
        density_score = min(product_count / 10.0, 3.0)  # max 3

        # Factor 2: sales velocity
        sales_score = min(total_sales / 1000.0, 3.0)  # max 3

        # Factor 3: quality signal
        quality_score = quality_ratio * 2.0  # max 2

        # Factor 4: engagement (views + clicks)
        engagement_score = min((total_views + total_clicks) / 5000.0, 2.0)  # max 2

        trend_score = round(
            density_score + sales_score + quality_score + engagement_score, 1
        )
        trend_score = min(trend_score, 10.0)

        # ── Trend direction ──
        # Compare high usage_count products (recent) vs low (older)
        sorted_by_usage = sorted(products, key=lambda p: p.usage_count, reverse=True)
        top_half = sorted_by_usage[: product_count // 2 or 1]
        bottom_half = sorted_by_usage[product_count // 2 or 1 :]
        top_avg_sales = sum(p.total_sales or 0 for p in top_half) / len(top_half)
        bot_avg_sales = sum(p.total_sales or 0 for p in bottom_half) / len(bottom_half)

        if top_avg_sales > bot_avg_sales * 1.2:
            direction = "up"
        elif top_avg_sales < bot_avg_sales * 0.8:
            direction = "down"
        else:
            direction = "stable"

        # ── Velocity ──
        if trend_score >= 8:
            velocity = "viral"
        elif trend_score >= 5:
            velocity = "fast"
        elif trend_score >= 2.5:
            velocity = "moderate"
        else:
            velocity = "slow"

        # ── Top products ──
        top_products = [
            {
                "product_id": p.id,
                "title": p.title[:80],
                "price": p.price,
                "rating": p.rating,
                "sales": p.total_sales,
            }
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
            "detected_at": datetime.utcnow().isoformat(),
        }
