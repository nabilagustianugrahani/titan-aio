"""Analyze product reviews."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Product, Review
from Database.repository import Repository
from MCP.schemas import AnalyzeReviewsInput, AnalyzeReviewsOutput, PainPoint, ReviewSentiment
from Services.llm import analyze_reviews_llm

logger = logging.getLogger(__name__)


async def analyze_reviews(
    input_data: AnalyzeReviewsInput,
    session: AsyncSession | None = None,
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
            reviews = await _scrape_and_store_reviews(
                session=session,
                product_id=input_data.product_id,
                max_reviews=input_data.max_reviews,
            )

        pain_points, objections, benefits, complaints = _stub_extractions()

        return AnalyzeReviewsOutput(
            product_id=input_data.product_id,
            total_reviews_analyzed=len(reviews),
            average_rating=_average_rating(reviews),
            pain_points=pain_points,
            objections=objections,
            benefits=benefits,
            complaints=complaints,
            sentiment_summary=_calculate_sentiment(reviews),
        )
    finally:
        if own_session:
            await session.close()


async def _scrape_and_store_reviews(
    session: AsyncSession,
    product_id: str,
    max_reviews: int,
) -> list[Review]:
    """Scrape real reviews and store in DB; fall back to LLM analysis.

    Priority:
    1. ShopeeClient.get_reviews(product_id) — if the method exists on the client
    2. ScrapeAgent.get_reviews(url) — existing browser/API scraper
    3. analyze_reviews_llm() — LLM-generated analysis from product info
    """
    reviews: list[Review] = []

    # 1. Try ShopeeClient.get_reviews if available
    scraped = await _try_shopee_reviews(product_id, max_reviews)

    # 2. Fallback to ScrapeAgent if we have a product URL
    if not scraped:
        product_url = await _get_product_field(session, product_id, "url")
        if product_url:
            scraped = await _try_scrape_agent_reviews(product_url, max_reviews)

    # Store scraped reviews in DB
    if scraped:
        repo = Repository(session, Review)
        for r in scraped[:max_reviews]:
            review = await repo.create(
                product_id=product_id,
                text=r.get("text", ""),
                rating=r.get("rating"),
                sentiment=r.get("sentiment", _infer_sentiment(r.get("rating"))),
            )
            reviews.append(review)
        return reviews

    # 3. Fallback: LLM analysis with whatever product info we have
    product_name = await _get_product_field(session, product_id, "title")
    llm_result = await analyze_reviews_llm(
        reviews_text="",
        product_name=product_name or product_id,
    )
    if llm_result:
        repo = Repository(session, Review)
        review = await repo.create(
            product_id=product_id,
            text=llm_result.get("summary", "LLM-generated analysis"),
            rating=_infer_rating_from_sentiment(llm_result.get("sentiment", {})),
            sentiment="neutral",
            pain_points=llm_result.get("pain_points", []),
        )
        reviews.append(review)

    return reviews


async def _try_shopee_reviews(product_id: str, max_reviews: int) -> list[dict]:
    """Attempt to scrape reviews using ShopeeClient.get_reviews if available."""
    try:
        from Services.api.shopee_client import ShopeeClient

        client = ShopeeClient()
        if hasattr(client, "get_reviews"):
            result = await client.get_reviews(product_id)
            if result and isinstance(result, list):
                return result
    except Exception:
        logger.debug("ShopeeClient.get_reviews not available", exc_info=True)
    return []


async def _try_scrape_agent_reviews(url: str, max_reviews: int) -> list[dict]:
    """Attempt to scrape reviews using the existing ScrapeAgent."""
    try:
        from Services.agents.scraper import ScrapeAgent

        agent = ScrapeAgent()
        result = await agent.get_reviews(url, max_reviews)
        if result and isinstance(result, list):
            return result
    except Exception:
        logger.debug("ScrapeAgent.get_reviews failed", exc_info=True)
    return []


async def _get_product_field(session: AsyncSession, product_id: str, field: str) -> str | None:
    """Get a field from the Product table by external_id."""
    try:
        product_repo = Repository(session, Product)
        products = await product_repo.find(external_id=product_id)
        if products:
            return getattr(products[0], field, None)
    except Exception:
        logger.debug("Failed to get product %s for %s", field, product_id, exc_info=True)
    return None


def _infer_sentiment(rating: float | None) -> str:
    """Infer sentiment label from a numeric rating."""
    if rating is None:
        return "neutral"
    if rating >= 4.0:
        return "positive"
    if rating <= 2.0:
        return "negative"
    return "neutral"


def _infer_rating_from_sentiment(sentiment: dict) -> float:
    """Derive a representative numeric rating from a sentiment distribution."""
    pos = sentiment.get("positive", 0)
    neg = sentiment.get("negative", 0)
    if pos > 0.6:
        return 4.5
    if neg > 0.4:
        return 2.0
    return 3.0


# TODO: Replace with real NLP extraction from review text.
# These stubs return generic Indonesian e-commerce patterns.
_STUB_PAIN_POINTS: list[dict] = [
    {"point": "Pengiriman lambat", "frequency": 0.3, "quotes": ["pengiriman lama banget", "pengiriman agak lambat"]},
    {"point": "Kualitas tidak sesuai", "frequency": 0.2, "quotes": ["kualitas kurang sesuai", "kualitas ok tapi"]},
]
_STUB_OBJECTIONS: list[dict] = [
    {"point": "Harga terlalu mahal", "frequency": 0.15, "quotes": ["harganya terlalu mahal"]},
    {"point": "Ukuran tidak sesuai", "frequency": 0.1, "quotes": ["saya kira lebih besar"]},
]
_STUB_BENEFITS: list[dict] = [
    {"point": "Kualitas bagus", "frequency": 0.4, "quotes": ["produk sangat bagus", "kualitas ok"]},
    {"point": "Sesuai deskripsi", "frequency": 0.3, "quotes": ["sesuai deskripsi", "barang sesuai gambar"]},
]
_STUB_COMPLAINTS: list[dict] = [
    {"point": "Cepat rusak", "frequency": 0.1, "quotes": ["cepat rusak setelah 3 hari"]},
    {"point": "Warna tidak sesuai", "frequency": 0.1, "quotes": ["warna tidak sesuai foto"]},
]


def _stub_extractions() -> tuple[list[PainPoint], list[PainPoint], list[PainPoint], list[PainPoint]]:
    """Return static analysis stubs — replace with real NLP extraction."""
    def _make(items: list[dict]) -> list[PainPoint]:
        return [PainPoint(point=i["point"], frequency=i["frequency"], top_quotes=i["quotes"]) for i in items]
    return (
        _make(_STUB_PAIN_POINTS),
        _make(_STUB_OBJECTIONS),
        _make(_STUB_BENEFITS),
        _make(_STUB_COMPLAINTS),
    )


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
