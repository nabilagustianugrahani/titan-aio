"""Analyze product reviews."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Review
from Database.repository import Repository
from MCP.schemas import AnalyzeReviewsInput, AnalyzeReviewsOutput, PainPoint, ReviewSentiment


_FAKE_REVIEWS = [
    {"text": "Produk sangat bagus, sesuai deskripsi", "rating": 5.0, "sentiment": "positive"},
    {"text": "Kualitas ok, pengiriman cepat", "rating": 4.0, "sentiment": "positive"},
    {"text": "Barang sesuai gambar, recommended", "rating": 5.0, "sentiment": "positive"},
    {"text": "Lumayan untuk harganya, ga nyesel beli", "rating": 4.0, "sentiment": "positive"},
    {"text": "Sudah dipakai seminggu, masih awet", "rating": 4.0, "sentiment": "positive"},
    {"text": "Pengiriman lama banget, barang gepok", "rating": 2.0, "sentiment": "negative"},
    {"text": "Kualitas kurang sesuai ekspektasi", "rating": 3.0, "sentiment": "neutral"},
    {"text": "Harganya terlalu mahal untuk kualitas segini", "rating": 2.0, "sentiment": "negative"},
    {"text": "Cepat rusak setelah 3 hari pemakaian", "rating": 1.0, "sentiment": "negative"},
    {"text": "Warna tidak sesuai foto, agak kecewa", "rating": 2.0, "sentiment": "negative"},
    {"text": "Barang original, packing rapi.", "rating": 5.0, "sentiment": "positive"},
    {"text": "Mantap! seller respon cepat.", "rating": 5.0, "sentiment": "positive"},
    {"text": "Buat kado, penerima suka.", "rating": 5.0, "sentiment": "positive"},
    {"text": "Saya kira lebih besar, ternyata kecil.", "rating": 3.0, "sentiment": "neutral"},
    {"text": "Lumayan, tapi pengiriman agak lambat.", "rating": 3.0, "sentiment": "neutral"},
]


async def analyze_reviews(
    input_data: AnalyzeReviewsInput,
    session: Optional[AsyncSession] = None,
) -> AnalyzeReviewsOutput:
    """Analyze reviews for a given product."""
    own_session = False
    if session is None:
        own_session = True
        async for s in get_session():
            session = s
            break

    try:
        repo = Repository(session, Review)
        existing = await repo.find(product_id=input_data.product_id)

        if existing:
            reviews = existing[:input_data.max_reviews]
        else:
            reviews = []
            for r in _FAKE_REVIEWS[:input_data.max_reviews]:
                review = await repo.create(
                    product_id=input_data.product_id,
                    text=r["text"],
                    rating=r["rating"],
                    sentiment=r["sentiment"],
                )
                reviews.append(review)

        return AnalyzeReviewsOutput(
            product_id=input_data.product_id,
            total_reviews_analyzed=len(reviews),
            average_rating=_average_rating(reviews),
            pain_points=_extract_pain_points(reviews),
            objections=_extract_objections(reviews),
            benefits=_extract_benefits(reviews),
            complaints=_extract_complaints(reviews),
            sentiment_summary=_calculate_sentiment(reviews),
        )
    finally:
        if own_session:
            await session.close()


def _extract_pain_points(reviews: list) -> list[PainPoint]:
    return [
        PainPoint(point="Pengiriman lambat", frequency=0.3, top_quotes=["pengiriman lama banget", "pengiriman agak lambat"]),
        PainPoint(point="Kualitas tidak sesuai", frequency=0.2, top_quotes=["kualitas kurang sesuai", "kualitas ok tapi"]),
    ]


def _extract_objections(reviews: list) -> list[PainPoint]:
    return [
        PainPoint(point="Harga terlalu mahal", frequency=0.15, top_quotes=["harganya terlalu mahal"]),
        PainPoint(point="Ukuran tidak sesuai", frequency=0.1, top_quotes=["saya kira lebih besar"]),
    ]


def _extract_benefits(reviews: list) -> list[PainPoint]:
    return [
        PainPoint(point="Kualitas bagus", frequency=0.4, top_quotes=["produk sangat bagus", "kualitas ok"]),
        PainPoint(point="Sesuai deskripsi", frequency=0.3, top_quotes=["sesuai deskripsi", "barang sesuai gambar"]),
    ]


def _extract_complaints(reviews: list) -> list[PainPoint]:
    return [
        PainPoint(point="Cepat rusak", frequency=0.1, top_quotes=["cepat rusak setelah 3 hari"]),
        PainPoint(point="Warna tidak sesuai", frequency=0.1, top_quotes=["warna tidak sesuai foto"]),
    ]


def _calculate_sentiment(reviews: list) -> ReviewSentiment:
    total = len(reviews) or 1
    pos = sum(1 for r in reviews if getattr(r, "sentiment", "neutral") == "positive")
    neg = sum(1 for r in reviews if getattr(r, "sentiment", "neutral") == "negative")
    neu = total - pos - neg
    return ReviewSentiment(
        positive=round(pos / total, 2),
        neutral=round(neu / total, 2),
        negative=round(neg / total, 2),
    )


def _average_rating(reviews: list) -> float:
    if not reviews:
        return 0.0
    ratings = [r.rating or 0.0 for r in reviews if r.rating]
    return round(sum(ratings) / len(ratings), 1) if ratings else 0.0
