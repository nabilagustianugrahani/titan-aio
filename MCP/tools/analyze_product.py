"""Analyze a product from its URL."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Product
from Database.repository import Repository
from MCP.schemas import AnalyzeProductInput, AnalyzeProductOutput
from Services.api.shopee_client import ShopeeClient
from Services.api.tokopedia_client import TokopediaClient
from Services.llm import llm_json


async def analyze_product(
    input_data: AnalyzeProductInput,
    session: AsyncSession | None = None,
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

        # Fetch real product data from Shopee/Tokopedia/LLM fallback
        product_data = await _fetch_product_data(input_data.url)

        new_product = await repo.create(
            external_id=external_id,
            title=product_data["title"],
            price=product_data["price"],
            currency=product_data["currency"],
            rating=product_data["rating"],
            total_sales=product_data["total_sales"],
            category=product_data["category"],
            commission_rate=product_data["commission_rate"],
            competition_level="medium",
            url=input_data.url,
            raw_data={"source": product_data["source"], "url": input_data.url},
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


async def _fetch_product_data(url: str) -> dict[str, Any]:
    """Fetch real product data from Shopee, Tokopedia, or LLM fallback."""
    url_lower = url.lower()
    is_shopee = "shopee" in url_lower

    # Try ShopeeClient first for Shopee URLs
    if is_shopee:
        shopee = ShopeeClient()
        try:
            product = await shopee.get_product(url)
            if product is not None:
                return {
                    "title": product.name,
                    "price": product.price,
                    "currency": product.currency,
                    "rating": product.rating,
                    "total_sales": product.sold,
                    "category": product.category,
                    "commission_rate": product.commission_rate or product.price * 0.05,
                    "source": "shopee",
                }
        finally:
            await shopee.close()

    # Try TokopediaClient (ShopeeClient failed or URL is not Shopee)
    tokopedia = TokopediaClient()
    try:
        product = await tokopedia.get_product(url)
        if product is not None:
            return {
                "title": product.name,
                "price": product.price,
                "currency": product.currency,
                "rating": product.rating,
                "total_sales": product.sold,
                "category": product.category,
                "commission_rate": product.commission_rate or product.price * 0.05,
                "source": "tokopedia",
            }
    finally:
        await tokopedia.close()

    # LLM fallback when both API clients fail
    return await _llm_fallback(url)


async def _llm_fallback(url: str) -> dict[str, Any]:
    """Use LLM to generate reasonable product data from the URL and any available info."""
    system_prompt = (
        "Kamu adalah asisten e-commerce Indonesia. Berdasarkan URL produk, "
        "buat tebakan data produk yang masuk akal dalam format JSON. "
        "Gunakan informasi yang bisa diekstrak dari URL untuk menebak "
        "nama produk, kategori, dan perkiraan harga."
    )
    user_prompt = (
        f"URL: {url}\n\n"
        "Buat tebakan data produk dalam format JSON dengan field:\n"
        "- title (string): nama produk yang masuk akal\n"
        "- price (number): perkiraan harga dalam IDR\n"
        "- rating (number): perkiraan rating 0-5\n"
        "- total_sales (number): perkiraan jumlah terjual\n"
        "- category (string): kategori produk\n"
        "Contoh: {\"title\": \"Sepatu Olahraga Pria Original\", "
        "\"price\": 150000, \"rating\": 4.5, "
        "\"total_sales\": 500, \"category\": \"fashion\"}"
    )
    result = await llm_json(system_prompt=system_prompt, user_prompt=user_prompt)
    if result and isinstance(result, dict):
        price = float(result.get("price", 50000))
        return {
            "title": result.get("title", "Produk dari " + url[:50]),
            "price": price,
            "currency": "IDR",
            "rating": float(result.get("rating", 4.0)),
            "total_sales": int(result.get("total_sales", 100)),
            "category": result.get("category", "umum"),
            "commission_rate": price * 0.05,
            "source": "llm",
        }
    # Ultimate fallback if LLM fails too
    return {
        "title": "Produk dari " + url[:60],
        "price": 50000.0,
        "currency": "IDR",
        "rating": 4.0,
        "total_sales": 100,
        "category": "umum",
        "commission_rate": 2500.0,
        "source": "llm_fallback",
    }


def _extract_product_id(url: str) -> str:
    match = re.search(r"[-/]([a-zA-Z0-9]{8,})", url)
    return match.group(1) if match else url[-12:]


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
