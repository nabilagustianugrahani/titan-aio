"""Product Agent — analyzes product data with 3-score system."""
from __future__ import annotations

import random
import re
from typing import Any

from Database.models import Product
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class ProductAgent(BaseAgent):
    """Analyzes products with 3-score system: product, affiliate, competition."""

    async def execute(self, ctx: AgentContext, url: str = "", **kwargs: Any) -> dict:
        external_id = self._extract_id(url or "")
        repo = Repository(ctx.session, Product)
        existing = await repo.find(external_id=external_id)

        if existing:
            p = existing[0]
            await repo.update(p.id, usage_count=p.usage_count + 1)
        else:
            p = await repo.create(
                external_id=external_id,
                title=self._sim_title(url or ""),
                price=self._sim_price(),
                rating=self._sim_rating(),
                total_sales=self._sim_sales(),
                url=url or "",
            )

        await ctx.session.commit()
        return self._score_product(p)

    def _score_product(self, p: Product) -> dict:
        # Product score — quality based on rating and sales
        rating_score = min((p.rating or 4.0) / 5.0 * 40, 40)  # max 40
        sales_score = min((p.total_sales or 100) / 10000 * 30, 30)  # max 30
        price_score = min((p.price or 50000) / 500000 * 30, 30) if (p.price or 0) > 10000 else 15  # max 30
        product_score = min(round(rating_score + sales_score + price_score), 100)

        # Affiliate score — commission potential
        base_commission = (p.price or 50000) * 0.05
        commission_score = min(base_commission / 25000 * 40, 40)  # max 40
        price_range_score = 30 if 20000 < (p.price or 0) < 500000 else 15  # sweet spot
        demand_score = min((p.total_sales or 100) / 5000 * 30, 30)  # max 30
        affiliate_score = min(round(commission_score + price_range_score + demand_score), 100)

        # Competition score — lower = more competition (inverted)
        comp_map = {"low": 85, "medium": 60, "high": 35}
        base_score = comp_map.get(p.competition_level or "medium", 60)
        sales_density = min((p.total_sales or 100) / 1000 * 15, 15)  # more sales = more competition
        competition_score = max(round(base_score - sales_density), 0)

        return {
            "product_id": p.id,
            "title": p.title,
            "price": p.price,
            "currency": p.currency,
            "rating": p.rating,
            "total_sales": p.total_sales,
            "category": p.category,
            "url": p.url,
            "product_score": product_score,
            "affiliate_score": affiliate_score,
            "competition_score": competition_score,
            "scores": {
                "product": product_score,
                "affiliate": affiliate_score,
                "competition": competition_score,
                "overall": round((product_score + affiliate_score + (100 - competition_score)) / 3),
            },
        }

    @staticmethod
    def _extract_id(url: str) -> str:
        m = re.search(r"[-/]([a-zA-Z0-9]{8,})", url)
        return m.group(1) if m else url[-12:]

    @staticmethod
    def _sim_title(url: str) -> str:
        return "Produk Premium Original - Terlaris"

    @staticmethod
    def _sim_price() -> float:
        return round(random.uniform(15000, 500000), -3)

    @staticmethod
    def _sim_rating() -> float:
        return round(random.uniform(3.5, 5.0), 1)

    @staticmethod
    def _sim_sales() -> int:
        return random.randint(50, 10000)
