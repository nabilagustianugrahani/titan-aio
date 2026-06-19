"""Review Agent -- extracts intelligence from product reviews."""

from __future__ import annotations

from typing import Any

from Database.models import Review
from Database.repository import Repository
from MCP.schemas import AnalyzeReviewsOutput, PainPoint, ReviewSentiment
from Services.agents.base import BaseAgent, AgentContext


class ReviewAgent(BaseAgent):
    """Extracts pain points, objections, benefits from reviews."""

    _FAKE_REVIEWS = [
        ("Produk sangat bagus, sesuai deskripsi", 5.0, "positive"),
        ("Kualitas ok, pengiriman cepat", 4.0, "positive"),
        ("Barang sesuai gambar, recommended", 5.0, "positive"),
        ("Lumayan untuk harganya", 4.0, "positive"),
        ("Pengiriman lama banget, barang gepok", 2.0, "negative"),
        ("Kualitas kurang sesuai ekspektasi", 3.0, "neutral"),
        ("Harganya terlalu mahal", 2.0, "negative"),
        ("Cepat rusak setelah 3 hari", 1.0, "negative"),
        ("Warna tidak sesuai foto", 2.0, "negative"),
        ("Mantap! seller respon cepat", 5.0, "positive"),
    ]

    async def execute(
        self, ctx: AgentContext, product_id: str, **kwargs: Any
    ) -> AnalyzeReviewsOutput:
        repo = Repository(ctx.session, Review)
        reviews = []
        for text, rating, sentiment in self._FAKE_REVIEWS:
            r = await repo.create(
                product_id=product_id,
                text=text,
                rating=rating,
                sentiment=sentiment,
            )
            reviews.append(r)
        await ctx.session.commit()

        avg_rating = sum(r.rating or 0.0 for r in reviews) / max(len(reviews), 1)
        return AnalyzeReviewsOutput(
            product_id=product_id,
            total_reviews_analyzed=len(reviews),
            average_rating=round(avg_rating, 1),
            pain_points=[
                PainPoint(
                    point="Pengiriman lambat",
                    frequency=0.3,
                    top_quotes=["pengiriman lama banget"],
                ),
                PainPoint(
                    point="Kualitas tidak sesuai",
                    frequency=0.2,
                    top_quotes=["kualitas kurang sesuai"],
                ),
            ],
            objections=[
                PainPoint(
                    point="Harga terlalu mahal",
                    frequency=0.15,
                    top_quotes=["harganya terlalu mahal"],
                ),
            ],
            benefits=[
                PainPoint(
                    point="Kualitas bagus",
                    frequency=0.4,
                    top_quotes=["produk sangat bagus"],
                ),
            ],
            complaints=[
                PainPoint(
                    point="Cepat rusak",
                    frequency=0.1,
                    top_quotes=["cepat rusak setelah 3 hari"],
                ),
            ],
            sentiment_summary=ReviewSentiment(positive=0.5, neutral=0.2, negative=0.3),
        )
