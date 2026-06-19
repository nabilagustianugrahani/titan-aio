"""Offer Agent -- determines best positioning."""

from __future__ import annotations

from typing import Any

from MCP.schemas import (
    AnalyzeCompetitorsOutput,
    AnalyzeProductOutput,
    AnalyzeReviewsOutput,
    GenerateOfferOutput,
)
from Services.agents.base import BaseAgent, AgentContext


class OfferAgent(BaseAgent):
    """Determines the best angle and positioning."""

    async def execute(
        self,
        ctx: AgentContext,
        product: AnalyzeProductOutput,
        reviews: AnalyzeReviewsOutput | None = None,
        competitors: AnalyzeCompetitorsOutput | None = None,
        **kwargs: Any,
    ) -> GenerateOfferOutput:
        benefits = ["Kualitas terjamin", "Harga terjangkau"]
        objections = ["Takut barang tidak original"]

        if reviews:
            for b in reviews.benefits:
                benefits.append(b.point)
            for o in reviews.objections:
                objections.append(o.point)

        await ctx.session.commit()
        return GenerateOfferOutput(
            product_id=product.product_id,
            primary_angle="Social Proof + Scarcity",
            value_proposition=f"Produk terbaik dengan harga Rp {product.price:,.0f}",
            positioning_statement=f"{product.title} -- solusi #1 untuk Anda",
            target_audience="Pria & Wanita 18-45 tahun",
            emotional_triggers=["FOMO", "Social Proof", "Trust"],
            key_benefits_to_highlight=benefits[:5],
            objections_to_address=objections[:3],
            recommended_cta="Beli Sekarang -- Stok Terbatas!",
        )
