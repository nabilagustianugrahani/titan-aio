"""MCP tools module."""

from __future__ import annotations

from MCP.instance import mcp

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from Services.agents.dynamic_pricing import DynamicPricingEngine
        _engine = DynamicPricingEngine()
    return _engine


@mcp.tool()
async def analyze_product_pricing(product_id: str, base_price: float, commission_rate: float, market_avg: float = 0.0, competitor_avg: float = 0.0, demand_score: float = 0.5, supply_score: float = 0.5) -> dict:
    """Analyze optimal pricing for a product. Returns recommended price, commission, and strategy."""
    engine = _get_engine()
    result = await engine.analyze_price(product_id=product_id, base_price=base_price, commission_rate=commission_rate, market_avg=market_avg, competitor_avg=competitor_avg, demand_score=demand_score, supply_score=supply_score)
    return result.model_dump()


@mcp.tool()
async def bulk_price_analysis(products: str) -> list[dict]:
    """Analyze pricing for multiple products at once. Products as JSON array."""
    import json
    engine = _get_engine()
    product_list = json.loads(products) if isinstance(products, str) else products
    results = await engine.bulk_analyze(products=product_list)
    return [r.model_dump() for r in results]


@mcp.tool()
async def get_pricing_recommendations() -> list[dict]:
    """Get pricing recommendations for all analyzed products."""
    engine = _get_engine()
    return await engine.get_recommendations()


@mcp.tool()
async def get_pricing_stats() -> dict:
    """Get dynamic pricing statistics."""
    engine = _get_engine()
    return await engine.get_stats()
