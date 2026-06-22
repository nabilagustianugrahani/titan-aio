"""Dynamic Pricing — auto-adjust commission strategies based on market data."""

from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
import hashlib


class PricePoint(BaseModel):
    product_id: str
    base_price: float
    commission_rate: float
    market_avg: float = 0.0
    competitor_avg: float = 0.0
    demand_score: float = 0.5  # 0-1
    supply_score: float = 0.5  # 0-1
    recommended_price: float = 0.0
    recommended_commission: float = 0.0
    strategy: str = ""  # undercut/match/premium/volume


class DynamicPricingEngine:
    def __init__(self):
        self.price_history: dict[str, list[PricePoint]] = {}
        self.strategies = {
            "undercut": {"price_factor": 0.95, "commission_boost": 2.0, "desc": "Price 5% below market, boost commission"},
            "match": {"price_factor": 1.0, "commission_boost": 0.0, "desc": "Match market price exactly"},
            "premium": {"price_factor": 1.10, "commission_boost": -1.0, "desc": "Price 10% above market, reduce commission"},
            "volume": {"price_factor": 0.90, "commission_boost": 3.0, "desc": "Price 10% below, maximize volume"},
        }

    async def analyze_price(self, product_id: str, base_price: float, commission_rate: float, market_avg: float = 0.0, competitor_avg: float = 0.0, demand_score: float = 0.5, supply_score: float = 0.5) -> PricePoint:
        effective_market = market_avg or base_price
        effective_competitor = competitor_avg or effective_market

        if demand_score > 0.7 and supply_score < 0.3:
            strategy = "premium"
        elif demand_score < 0.3:
            strategy = "volume"
        elif base_price > effective_competitor * 1.1:
            strategy = "undercut"
        else:
            strategy = "match"

        s = self.strategies[strategy]
        rec_price = round(base_price * s["price_factor"], 0)
        rec_commission = round(commission_rate + s["commission_boost"], 1)

        point = PricePoint(
            product_id=product_id, base_price=base_price, commission_rate=commission_rate,
            market_avg=effective_market, competitor_avg=effective_competitor,
            demand_score=demand_score, supply_score=supply_score,
            recommended_price=rec_price, recommended_commission=max(0, rec_commission),
            strategy=strategy,
        )

        if product_id not in self.price_history:
            self.price_history[product_id] = []
        self.price_history[product_id].append(point)
        return point

    async def get_product_history(self, product_id: str) -> list[PricePoint]:
        return self.price_history.get(product_id, [])

    async def bulk_analyze(self, products: list[dict]) -> list[PricePoint]:
        results = []
        for p in products:
            point = await self.analyze_price(
                product_id=p.get("product_id", ""), base_price=p.get("base_price", 0),
                commission_rate=p.get("commission_rate", 0), market_avg=p.get("market_avg", 0),
                competitor_avg=p.get("competitor_avg", 0), demand_score=p.get("demand_score", 0.5),
                supply_score=p.get("supply_score", 0.5),
            )
            results.append(point)
        return results

    async def get_recommendations(self) -> list[dict]:
        recs = []
        for pid, history in self.price_history.items():
            if history:
                latest = history[-1]
                recs.append({
                    "product_id": pid, "strategy": latest.strategy,
                    "current_price": latest.base_price, "recommended_price": latest.recommended_price,
                    "current_commission": latest.commission_rate, "recommended_commission": latest.recommended_commission,
                    "reason": self.strategies[latest.strategy]["desc"],
                })
        return recs

    async def get_stats(self) -> dict:
        total_products = len(self.price_history)
        strategies = {}
        for history in self.price_history.values():
            if history:
                s = history[-1].strategy
                strategies[s] = strategies.get(s, 0) + 1
        return {"total_products": total_products, "strategies": strategies}
