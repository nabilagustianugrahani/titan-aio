"""Search for affiliate products."""

from __future__ import annotations


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Database.connection import get_session
from Database.models import Product
from MCP.schemas import SearchProductInput, SearchProductItem, SearchProductOutput


async def search_product(
    input_data: SearchProductInput,
    session: AsyncSession | None = None,
) -> SearchProductOutput:
    """Search for products by query string."""
    if session is None:
        async for s in get_session():
            session = s
            break

    stmt = select(Product).where(Product.title.ilike(f"%{input_data.query}%"))
    if input_data.platform:
        stmt = stmt.where(Product.category.ilike(f"%{input_data.platform}%"))
    stmt = stmt.limit(input_data.limit)

    result = await session.execute(stmt)
    products = result.scalars().all()

    items = [
        SearchProductItem(
            external_id=p.external_id,
            title=p.title,
            price=p.price,
            currency=p.currency,
            rating=p.rating,
            total_sales=p.total_sales,
            url=p.url,
            platform="shopee",
        )
        for p in products
    ]
    return SearchProductOutput(results=items, total=len(items))
