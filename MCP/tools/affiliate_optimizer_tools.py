"""MCP tools for Affiliate Optimizer."""

from __future__ import annotations

from MCP.server import mcp
from Services.agents.affiliate_optimizer import AffiliateProduct, optimize_affiliate


@mcp.tool()
async def optimize_affiliate(
    current_products: str = "",
    niche: str = "general",
    budget: float = 0.0,
) -> dict:
    """Optimize affiliate strategy. Find higher commission products and auto-switch.

    Args:
        current_products: Comma-separated product IDs (empty = analyze niche defaults)
        niche: Product niche for commission benchmarking
        budget: Optional ad spend budget for optimization
    """
    products = None
    if current_products.strip():
        products = [
            AffiliateProduct(product_id=pid.strip(), name=f"Product {pid.strip()}")
            for pid in current_products.split(",")
            if pid.strip()
        ]
    result = await optimize_affiliate(
        current_products=products,
        niche=niche,
        budget=budget,
    )
    return result.model_dump()
