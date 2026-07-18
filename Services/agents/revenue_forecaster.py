import hashlib
from datetime import datetime, timedelta

from pydantic import BaseModel


class RevenueDataPoint(BaseModel):
    date: str
    campaign_id: str = ""
    platform: str = ""
    revenue: float = 0.0
    ad_spend: float = 0.0
    clicks: int = 0
    conversions: int = 0


class RevenueForecast(BaseModel):
    forecast_id: str = ""
    period: str = ""  # 7d/30d/90d
    predicted_revenue: float = 0.0
    predicted_roi: float = 0.0
    confidence: float = 0.0
    trend: str = "stable"  # growing/stable/declining
    daily_average: float = 0.0
    best_day: str = ""
    worst_day: str = ""
    recommendations: list[str] = []


class RevenueForecaster:
    def __init__(self):
        self.history: list[RevenueDataPoint] = []

    async def record_revenue(
        self,
        revenue: float,
        ad_spend: float = 0.0,
        campaign_id: str = "",
        platform: str = "",
        clicks: int = 0,
        conversions: int = 0,
    ) -> RevenueDataPoint:
        point = RevenueDataPoint(
            date=datetime.now().strftime("%Y-%m-%d"),
            campaign_id=campaign_id,
            platform=platform,
            revenue=revenue,
            ad_spend=ad_spend,
            clicks=clicks,
            conversions=conversions,
        )
        self.history.append(point)
        return point

    async def forecast(self, period: str = "30d") -> RevenueForecast:
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)

        if not self.history:
            return RevenueForecast(
                period=period,
                predicted_revenue=0,
                trend="stable",
                recommendations=["No historical data. Start recording revenue."],
            )

        recent = self.history[-30:] if len(self.history) >= 30 else self.history

        daily_revenue: dict[str, float] = {}
        for p in recent:
            daily_revenue[p.date] = daily_revenue.get(p.date, 0) + p.revenue

        values = list(daily_revenue.values()) if daily_revenue else [0]
        avg = sum(values) / len(values)

        # Simple linear trend: compare first half avg to second half avg
        if len(values) >= 2:
            mid = len(values) // 2
            first_half = sum(values[:mid]) / max(1, mid)
            second_half = sum(values[mid:]) / max(1, len(values) - mid)
            if second_half > first_half * 1.1:
                trend = "growing"
            elif second_half < first_half * 0.9:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        multiplier = {"growing": 1.15, "stable": 1.0, "declining": 0.85}[trend]
        predicted = round(avg * days * multiplier, 2)

        total_spend = sum(p.ad_spend for p in recent)
        total_rev = sum(p.revenue for p in recent)
        roi = round((total_rev - total_spend) / max(1, total_spend) * 100, 1)

        best_day = max(daily_revenue, key=daily_revenue.get) if daily_revenue else ""
        worst_day = (
            min(daily_revenue, key=daily_revenue.get) if daily_revenue else ""
        )

        recommendations: list[str] = []
        if trend == "declining":
            recommendations.append(
                "Revenue declining -- review underperforming campaigns",
            )
            recommendations.append("Consider pausing low-ROI campaigns")
        elif trend == "growing":
            recommendations.append("Revenue growing -- scale winning campaigns")
            recommendations.append("Increase ad budget for top performers")
        if roi < 50:
            recommendations.append(
                f"ROI at {roi}% -- optimize targeting or creative",
            )

        return RevenueForecast(
            forecast_id=hashlib.md5(
                f"{period}:{datetime.now().isoformat()}".encode(),
            ).hexdigest()[:10],
            period=period,
            predicted_revenue=predicted,
            predicted_roi=roi,
            confidence=min(1.0, 0.5 + len(recent) / 60),
            trend=trend,
            daily_average=round(avg, 2),
            best_day=best_day,
            worst_day=worst_day,
            recommendations=recommendations,
        )

    async def detect_trend(self, window: int = 14) -> dict:
        """Detect revenue trend over a given window of days."""
        cutoff = (datetime.now() - timedelta(days=window)).strftime("%Y-%m-%d")
        points = [p for p in self.history if p.date >= cutoff]

        if len(points) < 2:
            return {"trend": "insufficient_data", "window_days": window, "data_points": len(points)}

        daily: dict[str, float] = {}
        for p in points:
            daily[p.date] = daily.get(p.date, 0) + p.revenue

        values = sorted(daily.items())
        mid = len(values) // 2
        first_avg = sum(v for _, v in values[:mid]) / max(1, mid)
        second_avg = sum(v for _, v in values[mid:]) / max(1, len(values) - mid)

        if second_avg > first_avg * 1.1:
            trend = "growing"
            pct = round((second_avg - first_avg) / max(0.01, first_avg) * 100, 1)
        elif second_avg < first_avg * 0.9:
            trend = "declining"
            pct = round((second_avg - first_avg) / max(0.01, first_avg) * 100, 1)
        else:
            trend = "stable"
            pct = round((second_avg - first_avg) / max(0.01, first_avg) * 100, 1)

        return {
            "trend": trend,
            "change_pct": pct,
            "window_days": window,
            "first_half_avg": round(first_avg, 2),
            "second_half_avg": round(second_avg, 2),
            "data_points": len(points),
        }

    async def forecast_break_even(self) -> dict:
        """Forecast when cumulative revenue will break even against cumulative ad spend."""
        total_spend = sum(p.ad_spend for p in self.history)
        total_revenue = sum(p.revenue for p in self.history)

        if total_spend <= 0:
            return {"status": "no_spend", "total_spend": 0, "total_revenue": total_revenue}

        if total_revenue >= total_spend:
            return {
                "status": "already_breakeven",
                "total_spend": round(total_spend, 2),
                "total_revenue": round(total_revenue, 2),
                "surplus": round(total_revenue - total_spend, 2),
            }

        deficit = total_spend - total_revenue

        # Estimate daily profit rate from recent data
        recent_30 = self.history[-30:] if len(self.history) >= 30 else self.history
        daily_rev = {}
        daily_spend = {}
        for p in recent_30:
            daily_rev[p.date] = daily_rev.get(p.date, 0) + p.revenue
            daily_spend[p.date] = daily_spend.get(p.date, 0) + p.ad_spend

        days_tracked = max(1, len(daily_rev))
        avg_daily_profit = (sum(daily_rev.values()) - sum(daily_spend.values())) / days_tracked

        if avg_daily_profit <= 0:
            return {
                "status": "not_breakeven_likely",
                "total_spend": round(total_spend, 2),
                "total_revenue": round(total_revenue, 2),
                "deficit": round(deficit, 2),
                "avg_daily_profit": round(avg_daily_profit, 2),
                "message": "Negative daily profit -- break even unlikely without changes",
            }

        days_to_breakeven = int(deficit / avg_daily_profit) + 1
        breakeven_date = (datetime.now() + timedelta(days=days_to_breakeven)).strftime("%Y-%m-%d")

        return {
            "status": "projected_breakeven",
            "total_spend": round(total_spend, 2),
            "total_revenue": round(total_revenue, 2),
            "deficit": round(deficit, 2),
            "avg_daily_profit": round(avg_daily_profit, 2),
            "days_to_breakeven": days_to_breakeven,
            "projected_date": breakeven_date,
        }

    async def get_history(self, days: int = 30) -> list[RevenueDataPoint]:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [p for p in self.history if p.date >= cutoff]

    async def get_platform_breakdown(self) -> dict:
        breakdown: dict[str, dict] = {}
        for p in self.history:
            if p.platform not in breakdown:
                breakdown[p.platform] = {"revenue": 0.0, "ad_spend": 0.0, "count": 0}
            breakdown[p.platform]["revenue"] += p.revenue
            breakdown[p.platform]["ad_spend"] += p.ad_spend
            breakdown[p.platform]["count"] += 1
        for platform in breakdown:
            b = breakdown[platform]
            b["revenue"] = round(b["revenue"], 2)
            b["ad_spend"] = round(b["ad_spend"], 2)
            b["roi"] = round(
                (b["revenue"] - b["ad_spend"]) / max(1, b["ad_spend"]) * 100, 1,
            )
        return breakdown

    async def get_campaign_breakdown(self) -> dict:
        breakdown: dict[str, dict] = {}
        for p in self.history:
            cid = p.campaign_id or "unknown"
            if cid not in breakdown:
                breakdown[cid] = {"revenue": 0.0, "ad_spend": 0.0, "clicks": 0, "conversions": 0, "count": 0}
            breakdown[cid]["revenue"] += p.revenue
            breakdown[cid]["ad_spend"] += p.ad_spend
            breakdown[cid]["clicks"] += p.clicks
            breakdown[cid]["conversions"] += p.conversions
            breakdown[cid]["count"] += 1
        for cid in breakdown:
            b = breakdown[cid]
            b["revenue"] = round(b["revenue"], 2)
            b["ad_spend"] = round(b["ad_spend"], 2)
            b["roi"] = round(
                (b["revenue"] - b["ad_spend"]) / max(1, b["ad_spend"]) * 100, 1,
            )
            b["ctr"] = round(b["clicks"] / max(1, b["count"]) * 100, 1)
            b["conversion_rate"] = round(b["conversions"] / max(1, b["clicks"]) * 100, 1)
        return breakdown

    async def generate_report(self) -> dict:
        """Generate a comprehensive revenue report."""
        stats = await self.get_stats()
        platform = await self.get_platform_breakdown()
        campaigns = await self.get_campaign_breakdown()
        trend_7 = await self.detect_trend(7)
        trend_30 = await self.detect_trend(30)
        forecast_7 = await self.forecast("7d")
        forecast_30 = await self.forecast("30d")
        forecast_90 = await self.forecast("90d")
        breakeven = await self.forecast_break_even()

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": stats,
            "platforms": platform,
            "campaigns": campaigns,
            "trends": {"7_day": trend_7, "30_day": trend_30},
            "forecasts": {
                "7_day": forecast_7.model_dump(),
                "30_day": forecast_30.model_dump(),
                "90_day": forecast_90.model_dump(),
            },
            "break_even": breakeven,
        }

    async def get_stats(self) -> dict:
        total_rev = sum(p.revenue for p in self.history)
        total_spend = sum(p.ad_spend for p in self.history)
        total_clicks = sum(p.clicks for p in self.history)
        total_conversions = sum(p.conversions for p in self.history)
        unique_campaigns = len({p.campaign_id for p in self.history if p.campaign_id})
        unique_platforms = len({p.platform for p in self.history if p.platform})
        return {
            "total_revenue": round(total_rev, 2),
            "total_ad_spend": round(total_spend, 2),
            "net_profit": round(total_rev - total_spend, 2),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "unique_campaigns": unique_campaigns,
            "unique_platforms": unique_platforms,
            "data_points": len(self.history),
        }
