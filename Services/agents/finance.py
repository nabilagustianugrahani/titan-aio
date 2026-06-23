"""Finance Agent — tracks revenue, commission, ROI with DB persistence."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from Database.models import Campaign, Metric, RevenueDataPoint
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class FinanceAgent(BaseAgent):
    """Tracks financial performance across campaigns.

    Actions:
      record   — log a revenue data point for a campaign
      summary  — aggregate revenue/profit/ROI across campaigns
      forecast — simple trend-based forecast from recent data
    """

    async def execute(self, ctx: AgentContext, action: str = "record", **kwargs: Any) -> dict:
        if action == "record":
            return await self._record(ctx, **kwargs)
        if action == "summary":
            return await self._summary(ctx, **kwargs)
        if action == "forecast":
            return await self._forecast(ctx, **kwargs)
        return {"error": f"Unknown action: {action}"}

    # ── record ──────────────────────────────────────────────────────
    async def _record(
        self,
        ctx: AgentContext,
        campaign_id: str = "",
        revenue: float = 0.0,
        ad_spend: float = 0.0,
        clicks: int = 0,
        conversions: int = 0,
        platform: str = "",
        **_: Any,
    ) -> dict:
        repo = Repository(ctx.session, RevenueDataPoint)
        net_profit = revenue - ad_spend
        point = await repo.create(
            campaign_id=campaign_id,
            platform=platform,
            revenue=revenue,
            ad_spend=ad_spend,
            clicks=clicks,
            conversions=conversions,
            net_profit=net_profit,
        )

        # Update campaign totals
        camp_repo = Repository(ctx.session, Campaign)
        camps = await camp_repo.find(id=campaign_id)
        if camps:
            c = camps[0]
            await camp_repo.update(
                c.id,
                total_revenue=c.total_revenue + revenue,
                total_spent=c.total_spent + ad_spend,
            )

        await ctx.session.commit()
        return {
            "recorded": True,
            "data_point_id": point.id,
            "campaign_id": campaign_id,
            "revenue": revenue,
            "ad_spend": ad_spend,
            "net_profit": net_profit,
            "roi": round((revenue - ad_spend) / max(ad_spend, 1), 2),
        }

    # ── summary ─────────────────────────────────────────────────────
    async def _summary(
        self,
        ctx: AgentContext,
        campaign_id: str = "",
        days: int = 30,
        **_: Any,
    ) -> dict:
        repo = Repository(ctx.session, RevenueDataPoint)
        since = datetime.utcnow() - timedelta(days=days)

        if campaign_id:
            all_pts = await repo.find(campaign_id=campaign_id)
            pts = [p for p in all_pts if p.created_at and p.created_at >= since]
        else:
            all_pts = await repo.list_all(limit=1000)
            pts = [p for p in all_pts if p.created_at and p.created_at >= since]

        total_revenue = sum(p.revenue for p in pts)
        total_spend = sum(p.ad_spend for p in pts)
        total_clicks = sum(p.clicks for p in pts)
        total_conversions = sum(p.conversions for p in pts)

        return {
            "period_days": days,
            "data_points": len(pts),
            "total_revenue": round(total_revenue, 2),
            "total_ad_spend": round(total_spend, 2),
            "net_profit": round(total_revenue - total_spend, 2),
            "roi": round((total_revenue - total_spend) / max(total_spend, 1), 2),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "avg_ctr": round(total_clicks / max(total_conversions, 1) * 100, 2),
            "avg_commission": round(total_revenue * 0.05, 2),
        }

    # ── forecast ────────────────────────────────────────────────────
    async def _forecast(
        self,
        ctx: AgentContext,
        campaign_id: str = "",
        days_ahead: int = 7,
        **_: Any,
    ) -> dict:
        repo = Repository(ctx.session, RevenueDataPoint)
        since_30 = datetime.utcnow() - timedelta(days=30)

        all_pts = await repo.list_all(limit=1000)
        pts = [p for p in all_pts if p.created_at and p.created_at >= since_30]
        if campaign_id:
            pts = [p for p in pts if p.campaign_id == campaign_id]

        if len(pts) < 2:
            return {
                "forecast": [],
                "note": "Insufficient data (need ≥2 data points)",
            }

        # Sort by created_at
        pts.sort(key=lambda p: p.created_at or datetime.min)

        # Daily revenue aggregation
        daily_rev: dict[str, float] = {}
        for p in pts:
            day = (p.created_at or datetime.utcnow()).strftime("%Y-%m-%d")
            daily_rev[day] = daily_rev.get(day, 0) + p.revenue

        values = list(daily_rev.values())
        avg_daily = sum(values) / len(values)
        trend = (values[-1] - values[0]) / max(len(values), 1)  # slope

        forecast = []
        base = avg_daily
        for i in range(1, days_ahead + 1):
            predicted = max(0, base + trend * i)
            forecast.append({
                "day": i,
                "predicted_revenue": round(predicted, 2),
                "predicted_profit": round(predicted * 0.85, 2),  # ~15% margin
            })

        return {
            "days_ahead": days_ahead,
            "avg_daily_revenue": round(avg_daily, 2),
            "trend_per_day": round(trend, 2),
            "forecast": forecast,
            "confidence": "low" if len(pts) < 7 else "medium" if len(pts) < 14 else "high",
        }
