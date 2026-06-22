"""Affiliate Optimizer — auto-switch to higher commission products."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime

from pydantic import BaseModel, Field


# ── Models ───────────────────────────────────────────────────────

class AffiliateProduct(BaseModel):
    product_id: str = ""
    name: str
    platform: str = "shopee"
    commission_rate: float = 0.0
    price: float = 0.0
    earnings_per_click: float = 0.0
    conversion_rate: float = 0.0
    trend: str = "stable"
    category: str = ""


class ProductSwitch(BaseModel):
    from_product: str
    to_product: str
    reason: str
    expected_improvement: float
    confidence: float


class AffiliateOptimization(BaseModel):
    current_products: list[AffiliateProduct]
    recommended_switches: list[ProductSwitch]
    projected_revenue_increase: float
    total_commission_rate: float
    optimization_score: int = Field(ge=0, le=100)
    recommendations: list[str]


# ── Commission Data (simulated marketplace) ──────────────────────

COMMISSION_RATES = {
    "electronics": {"min": 3.0, "max": 12.0, "avg_conversion": 0.04},
    "fashion": {"min": 5.0, "max": 20.0, "avg_conversion": 0.06},
    "beauty": {"min": 8.0, "max": 25.0, "avg_conversion": 0.07},
    "food": {"min": 2.0, "max": 10.0, "avg_conversion": 0.05},
    "health": {"min": 10.0, "max": 30.0, "avg_conversion": 0.03},
    "home": {"min": 4.0, "max": 15.0, "avg_conversion": 0.04},
    "general": {"min": 3.0, "max": 15.0, "avg_conversion": 0.05},
}


# ── Engine ───────────────────────────────────────────────────────

async def optimize_affiliate(
    current_products: list[AffiliateProduct] | None = None,
    niche: str = "general",
    budget: float = 0.0,
) -> AffiliateOptimization:
    """Optimize affiliate strategy — find higher commission products."""
    if not current_products:
        # Generate sample products for analysis
        current_products = [
            AffiliateProduct(
                product_id=hashlib.md5(f"prod_{i}".encode()).hexdigest()[:8],
                name=f"Product {i+1}",
                platform=random.choice(["shopee", "tokopedia"]),
                commission_rate=random.uniform(3, 12),
                price=random.uniform(50000, 500000),
                earnings_per_click=random.uniform(0.5, 5.0),
                conversion_rate=random.uniform(0.02, 0.08),
                trend=random.choice(["rising", "stable", "declining"]),
                category=niche,
            )
            for i in range(5)
        ]

    # Analyze commission landscape
    niche_data = COMMISSION_RATES.get(niche, COMMISSION_RATES["general"])
    recommendations = []
    switches = []
    total_commission = 0.0

    for product in current_products:
        total_commission += product.commission_rate

        # Check if there's room for improvement
        if product.commission_rate < niche_data["max"] * 0.7:
            potential_rate = random.uniform(
                product.commission_rate * 1.3,
                min(niche_data["max"], product.commission_rate * 2),
            )
            improvement = round(potential_rate - product.commission_rate, 2)

            if improvement > 2.0:
                switches.append(ProductSwitch(
                    from_product=product.name,
                    to_product=f"Higher-commission alternative in {product.category or niche}",
                    reason=f"Current commission {product.commission_rate:.1f}% vs potential {potential_rate:.1f}%",
                    expected_improvement=improvement,
                    confidence=round(random.uniform(0.6, 0.9), 2),
                ))

        # Check trend
        if product.trend == "declining":
            recommendations.append(f"⚠️ {product.name} is declining — consider switching to a rising product")
        elif product.trend == "rising":
            recommendations.append(f"✅ {product.name} is trending — scale this product")

    avg_commission = total_commission / len(current_products) if current_products else 0
    projected_increase = sum(s.expected_improvement for s in switches)
    optimization_score = min(100, int(avg_commission * 5 + len(switches) * 10))

    recommendations.extend([
        f"Average commission rate: {avg_commission:.1f}%",
        f"Found {len(switches)} potential upgrades",
        f"Niche benchmark: {niche_data['min']}-{niche_data['max']}% commission",
    ])

    return AffiliateOptimization(
        current_products=current_products,
        recommended_switches=switches,
        projected_revenue_increase=round(projected_increase, 2),
        total_commission_rate=round(avg_commission, 2),
        optimization_score=optimization_score,
        recommendations=recommendations,
    )
