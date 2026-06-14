"""Product Agent -- analyzes product data from affiliate URLs."""

from __future__ import annotations

import re
from typing import Any

from Database.models import Product
from Database.repository import Repository
from MCP.schemas import AnalyzeProductOutput
from Services.agents.base import BaseAgent, AgentContext


class ProductAgent(BaseAgent):
    """Analyzes products from Shopee/Tokopedia URLs."""

    async def execute(
        self, ctx: AgentContext, url: str, **kwargs: Any
    ) -> AnalyzeProductOutput:
        external_id = self._extract_id(url)
        repo = Repository(ctx.session, Product)
        existing = await repo.find(external_id=external_id)

        if existing:
            p = existing[0]
            await repo.update(p.id, usage_count=p.usage_count + 1)
            await ctx.session.commit()
            return AnalyzeProductOutput(
                product_id=p.id,
                title=p.title,
                price=p.price,
                currency=p.currency,
                rating=p.rating,
                total_sales=p.total_sales,
                category=p.category,
                commission_estimate=p.commission_rate,
                competition_level=p.competition_level,
                product_score=0.0,
                url=p.url,
            )

        product = await repo.create(
            external_id=external_id,
            title=self._sim_title(url),
            price=self._sim_price(),
            rating=self._sim_rating(),
            total_sales=self._sim_sales(),
            url=url,
        )
        await ctx.session.commit()
        return AnalyzeProductOutput(
            product_id=product.id,
            title=product.title,
            price=product.price,
            currency="IDR",
            rating=product.rating,
            total_sales=product.total_sales,
            category=product.category,
            commission_estimate=product.price * 0.05,
            competition_level="medium",
            product_score=0.0,
            url=product.url,
        )

    @staticmethod
    def _extract_id(url: str) -> str:
        m = re.search(r"[-/]([a-zA-Z0-9]{8,})", url)
        return m.group(1) if m else url[-12:]

    @staticmethod
    def _sim_title(url: str) -> str:
        return "Produk Premium Original - Terlaris"

    @staticmethod
    def _sim_price() -> float:
        import random
        return round(random.uniform(15000, 500000), -3)

    @staticmethod
    def _sim_rating() -> float:
        import random
        return round(random.uniform(3.5, 5.0), 1)

    @staticmethod
    def _sim_sales() -> int:
        import random
        return random.randint(50, 10000)
