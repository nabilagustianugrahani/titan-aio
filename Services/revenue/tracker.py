"""Revenue Tracker — tracks affiliate clicks, conversions, and commissions."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class AffiliateClick(BaseModel):
    click_id: str = ""
    link_id: str
    platform: str
    source: str = ""
    timestamp: str = ""
    ip_hash: str = ""


class Conversion(BaseModel):
    conversion_id: str = ""
    link_id: str
    platform: str
    product_name: str = ""
    sale_amount: float = 0.0
    commission_rate: float = 0.0
    commission_earned: float = 0.0
    timestamp: str = ""


class RevenueSummary(BaseModel):
    total_revenue: float = 0.0
    total_commission: float = 0.0
    total_clicks: int = 0
    total_conversions: int = 0
    conversion_rate: float = 0.0
    avg_commission: float = 0.0
    top_products: list[dict] = []
    daily_revenue: list[dict] = []


class RevenueTracker:
    def __init__(self):
        self.clicks: list[AffiliateClick] = []
        self.conversions: list[Conversion] = []

    async def record_click(self, link_id: str, platform: str, source: str = "", ip: str = "") -> AffiliateClick:
        click_id = hashlib.md5(f"{link_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        ip_hash = hashlib.md5(ip.encode()).hexdigest()[:8] if ip else ""
        click = AffiliateClick(
            click_id=click_id,
            link_id=link_id,
            platform=platform,
            source=source,
            timestamp=datetime.now().isoformat(),
            ip_hash=ip_hash,
        )
        self.clicks.append(click)
        return click

    async def record_conversion(
        self,
        link_id: str,
        platform: str,
        product_name: str = "",
        sale_amount: float = 0.0,
        commission_rate: float = 0.0,
    ) -> Conversion:
        commission = round(sale_amount * commission_rate / 100, 2)
        conv_id = hashlib.md5(f"conv:{link_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        conv = Conversion(
            conversion_id=conv_id,
            link_id=link_id,
            platform=platform,
            product_name=product_name,
            sale_amount=sale_amount,
            commission_rate=commission_rate,
            commission_earned=commission,
            timestamp=datetime.now().isoformat(),
        )
        self.conversions.append(conv)
        return conv

    async def get_summary(self, days: int = 30) -> RevenueSummary:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent_clicks = [c for c in self.clicks if c.timestamp >= cutoff]
        recent_convs = [c for c in self.conversions if c.timestamp >= cutoff]

        total_revenue = sum(c.sale_amount for c in recent_convs)
        total_commission = sum(c.commission_earned for c in recent_convs)

        # Group by product
        product_rev: dict[str, float] = {}
        for c in recent_convs:
            product_rev[c.product_name] = product_rev.get(c.product_name, 0) + c.commission_earned
        top_products = sorted(
            [{"name": k, "revenue": v} for k, v in product_rev.items()],
            key=lambda x: x["revenue"],
            reverse=True,
        )[:10]

        # Daily revenue
        daily: dict[str, float] = {}
        for c in recent_convs:
            day = c.timestamp[:10]
            daily[day] = daily.get(day, 0) + c.commission_earned
        daily_revenue = [{"date": k, "revenue": v} for k, v in sorted(daily.items())]

        return RevenueSummary(
            total_revenue=total_revenue,
            total_commission=total_commission,
            total_clicks=len(recent_clicks),
            total_conversions=len(recent_convs),
            conversion_rate=round(len(recent_convs) / max(1, len(recent_clicks)) * 100, 2),
            avg_commission=round(total_commission / max(1, len(recent_convs)), 2),
            top_products=top_products,
            daily_revenue=daily_revenue,
        )

    async def get_clicks(self, link_id: str = "", platform: str = "", limit: int = 100) -> list[AffiliateClick]:
        result = self.clicks
        if link_id:
            result = [c for c in result if c.link_id == link_id]
        if platform:
            result = [c for c in result if c.platform == platform]
        return result[-limit:]

    async def get_conversions(self, platform: str = "", limit: int = 100) -> list[Conversion]:
        result = self.conversions
        if platform:
            result = [c for c in result if c.platform == platform]
        return result[-limit:]

    async def get_stats(self) -> dict:
        return {
            "total_clicks": len(self.clicks),
            "total_conversions": len(self.conversions),
            "total_commission": round(sum(c.commission_earned for c in self.conversions), 2),
        }
