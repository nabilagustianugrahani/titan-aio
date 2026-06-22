"""Cross-Platform Analytics — unified metrics across all social platforms."""

from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime


class PlatformMetrics(BaseModel):
    platform: str
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    engagement_rate: float = 0.0
    ctr: float = 0.0
    conversion_rate: float = 0.0
    cost_per_click: float = 0.0
    roi: float = 0.0


class CrossPlatformReport(BaseModel):
    report_id: str = ""
    campaign_id: str = ""
    platforms: list[PlatformMetrics]
    total_impressions: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_revenue: float = 0.0
    avg_engagement_rate: float = 0.0
    avg_ctr: float = 0.0
    best_platform: str = ""
    worst_platform: str = ""
    total_roi: float = 0.0
    recommendations: list[str] = []


class CrossPlatformAnalytics:
    def __init__(self):
        self.reports: dict[str, CrossPlatformReport] = {}
        self.platform_data: dict[str, list[PlatformMetrics]] = {}

    async def record_metrics(self, platform: str, impressions: int = 0, reach: int = 0, engagement: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0, ad_spend: float = 0.0) -> PlatformMetrics:
        er = round(engagement / max(1, impressions) * 100, 2) if impressions > 0 else 0
        ctr = round(clicks / max(1, impressions) * 100, 2) if impressions > 0 else 0
        cr = round(conversions / max(1, clicks) * 100, 2) if clicks > 0 else 0
        cpc = round(ad_spend / max(1, clicks), 2) if clicks > 0 else 0
        roi = round((revenue - ad_spend) / max(1, ad_spend) * 100, 1) if ad_spend > 0 else 0
        metrics = PlatformMetrics(
            platform=platform, impressions=impressions, reach=reach, engagement=engagement,
            clicks=clicks, conversions=conversions, revenue=revenue,
            engagement_rate=er, ctr=ctr, conversion_rate=cr, cost_per_click=cpc, roi=roi,
        )
        if platform not in self.platform_data:
            self.platform_data[platform] = []
        self.platform_data[platform].append(metrics)
        return metrics

    async def generate_report(self, campaign_id: str = "") -> CrossPlatformReport:
        import hashlib
        report_id = hashlib.md5(f"{campaign_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:10]
        all_metrics = []
        for platform, metrics_list in self.platform_data.items():
            if metrics_list:
                latest = metrics_list[-1]
                all_metrics.append(latest)
        total_imp = sum(m.impressions for m in all_metrics)
        total_reach = sum(m.reach for m in all_metrics)
        total_eng = sum(m.engagement for m in all_metrics)
        total_clicks = sum(m.clicks for m in all_metrics)
        total_conv = sum(m.conversions for m in all_metrics)
        total_rev = sum(m.revenue for m in all_metrics)
        avg_er = round(total_eng / max(1, total_imp) * 100, 2)
        avg_ctr = round(total_clicks / max(1, total_imp) * 100, 2)
        best = max(all_metrics, key=lambda m: m.roi).platform if all_metrics else ""
        worst = min(all_metrics, key=lambda m: m.roi).platform if all_metrics else ""
        total_spend = sum(m.cost_per_click * m.clicks for m in all_metrics)
        total_roi = round((total_rev - total_spend) / max(1, total_spend) * 100, 1)

        recommendations = []
        if all_metrics:
            best_m = max(all_metrics, key=lambda m: m.engagement_rate)
            worst_m = min(all_metrics, key=lambda m: m.engagement_rate)
            if best_m.platform != worst_m.platform:
                recommendations.append(f"Scale {best_m.platform} (highest engagement: {best_m.engagement_rate}%)")
                recommendations.append(f"Review {worst_m.platform} strategy (lowest engagement: {worst_m.engagement_rate}%)")
            if avg_ctr < 1.0:
                recommendations.append("CTR below 1% — improve hooks and CTAs")
            if total_roi < 0:
                recommendations.append("Negative ROI — reduce ad spend or improve conversion")

        report = CrossPlatformReport(
            report_id=report_id, campaign_id=campaign_id, platforms=all_metrics,
            total_impressions=total_imp, total_reach=total_reach, total_engagement=total_eng,
            total_clicks=total_clicks, total_conversions=total_conv, total_revenue=total_rev,
            avg_engagement_rate=avg_er, avg_ctr=avg_ctr, best_platform=best, worst_platform=worst,
            total_roi=total_roi, recommendations=recommendations,
        )
        self.reports[report_id] = report
        return report

    async def get_comparison(self) -> dict:
        comparison = {}
        for platform, metrics_list in self.platform_data.items():
            if metrics_list:
                latest = metrics_list[-1]
                comparison[platform] = {
                    "engagement_rate": latest.engagement_rate,
                    "ctr": latest.ctr,
                    "conversion_rate": latest.conversion_rate,
                    "roi": latest.roi,
                    "revenue": latest.revenue,
                }
        return comparison
