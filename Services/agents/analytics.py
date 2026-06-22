"""Analytics Agent — tracks campaign performance from DB metrics."""

from __future__ import annotations

from typing import Any


from Database.models import Metric, Campaign, WinningHook
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext


class AnalyticsAgent(BaseAgent):
    """Tracks views, CTR, conversions, and revenue from DB metrics."""

    async def execute(
        self, ctx: AgentContext, campaign_id: str = "", **kwargs: Any
    ) -> dict:
        if not campaign_id:
            return self._empty(campaign_id)

        # ── Aggregate metrics for this campaign ──
        repo = Repository(ctx.session, Metric)
        metrics = await repo.find(campaign_id=campaign_id)

        if not metrics:
            return self._empty(campaign_id)

        total_views = sum(m.views for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        total_revenue = sum(m.revenue for m in metrics)

        ctr = total_clicks / total_views if total_views > 0 else 0.0
        conversion_rate = total_conversions / total_clicks if total_clicks > 0 else 0.0

        # ── Group by platform ──
        by_platform: dict[str, dict] = {}
        for m in metrics:
            p = m.platform or "unknown"
            if p not in by_platform:
                by_platform[p] = {"views": 0, "clicks": 0, "conversions": 0, "revenue": 0.0}
            by_platform[p]["views"] += m.views
            by_platform[p]["clicks"] += m.clicks
            by_platform[p]["conversions"] += m.conversions
            by_platform[p]["revenue"] += m.revenue

        # Compute per-platform CTR
        for pdata in by_platform.values():
            pdata["ctr"] = pdata["clicks"] / pdata["views"] if pdata["views"] > 0 else 0.0

        # ── Get campaign spend for ROI ──
        campaign_repo = Repository(ctx.session, Campaign)
        campaigns = await campaign_repo.find(id=campaign_id)
        total_spent = campaigns[0].total_spent if campaigns else 0.0
        roi = ((total_revenue - total_spent) / total_spent) if total_spent > 0 else 0.0

        # ── Top winning hooks for this campaign ──
        hook_repo = Repository(ctx.session, WinningHook)
        hooks = await hook_repo.find(campaign_id=campaign_id)
        top_hooks = sorted(
            [{"text": h.hook_text, "type": h.hook_type, "ctr": h.ctr or 0.0} for h in hooks],
            key=lambda x: x["ctr"],
            reverse=True,
        )[:5]

        return {
            "campaign_id": campaign_id,
            "metrics": {
                "views": total_views,
                "clicks": total_clicks,
                "ctr": round(ctr, 4),
                "conversions": total_conversions,
                "conversion_rate": round(conversion_rate, 4),
                "revenue": round(total_revenue, 2),
            },
            "financials": {
                "total_spent": round(total_spent, 2),
                "total_revenue": round(total_revenue, 2),
                "roi": round(roi, 4),
            },
            "by_platform": by_platform,
            "top_hooks": top_hooks,
            "periods_tracked": len(metrics),
        }

    @staticmethod
    def _empty(campaign_id: str) -> dict:
        return {
            "campaign_id": campaign_id,
            "metrics": {
                "views": 0, "clicks": 0, "ctr": 0.0,
                "conversions": 0, "conversion_rate": 0.0, "revenue": 0.0,
            },
            "financials": {"total_spent": 0.0, "total_revenue": 0.0, "roi": 0.0},
            "by_platform": {},
            "top_hooks": [],
            "periods_tracked": 0,
        }
