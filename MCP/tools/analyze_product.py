"""Analyze a product from its URL."""

from __future__ import annotations

import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Product
from Database.repository import Repository
from MCP.schemas import AnalyzeProductInput, AnalyzeProductOutput


async def analyze_product(
    input_data: AnalyzeProductInput,
    session: Optional[AsyncSession] = None,
) -> AnalyzeProductOutput:
    """Analyze a product from its Shopee/Tokopedia URL."""
    own_session = False
    if session is None:
        own_session = True
        async for s in get_session():
            session = s
            break

    try:
        repo = Repository(session, Product)
        external_id = _extract_product_id(input_data.url)
        existing = await repo.find(external_id=external_id)

        if existing:
            p = existing[0]
            return AnalyzeProductOutput(
                product_id=p.id,
                title=p.title,
                price=p.price,
                currency=p.currency,
                rating=p.rating or 0.0,
                total_sales=p.total_sales,
                category=p.category,
                commission_estimate=p.commission_rate,
                competition_level=p.competition_level,
                product_score=_calculate_score(p),
                url=p.url,
            )

        new_product = await repo.create(
            external_id=external_id,
            title=_simulate_title(input_data.url),
            price=_simulate_price(),
            currency="IDR",
            rating=_simulate_rating(),
            total_sales=_simulate_sales(),
            category=_simulate_category(),
            commission_rate=_simulate_price() * 0.05,
            competition_level="medium",
            url=input_data.url,
            raw_data={"source": "simulated", "url": input_data.url},
        )

        return AnalyzeProductOutput(
            product_id=new_product.id,
            title=new_product.title,
            price=new_product.price,
            currency="IDR",
            rating=new_product.rating,
            total_sales=new_product.total_sales,
            category=new_product.category,
            commission_estimate=new_product.commission_rate,
            competition_level="medium",
            product_score=_calculate_score(new_product),
            url=input_data.url,
        )
    finally:
        if own_session:
            await session.close()


def _extract_product_id(url: str) -> str:
    match = re.search(r"[-/]([a-zA-Z0-9]{8,})", url)
    return match.group(1) if match else url[-12:]


def _simulate_title(url: str) -> str:
    if "shopee" in url.lower():
        return "Produk Shopee Terlaris 2024 - Original Premium"
    return "Produk Tokopedia Terbaik - Garansi Resmi"


def _simulate_price() -> float:
    import random
    return round(random.uniform(15000, 500000), -3)


def _simulate_rating() -> float:
    import random
    return round(random.uniform(3.5, 5.0), 1)


def _simulate_sales() -> int:
    import random
    return random.randint(50, 10000)


def _simulate_category() -> str:
    return "elektronik"


def _calculate_score(product: Product) -> float:
    score = 0.0
    if product.rating and product.rating > 4.0:
        score += 3.0
    elif product.rating and product.rating > 3.0:
        score += 1.5
    if product.total_sales and product.total_sales > 1000:
        score += 3.0
    elif product.total_sales and product.total_sales > 100:
        score += 1.5
    if product.price and product.price > 100000:
        score += 2.0
    if product.competition_level == "low":
        score += 2.0
    return min(score, 10.0)
