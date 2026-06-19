"""Finance Agent -- tracks revenue, commission, ROI."""

from __future__ import annotations

from typing import Any

from Services.agents.base import BaseAgent, AgentContext


class FinanceAgent(BaseAgent):
    """Tracks financial performance across campaigns."""

    async def execute(
        self,
        ctx: AgentContext,
        campaign_id: str = "",
        revenue: float = 0.0,
        ad_spend: float = 0.0,
        **kwargs: Any,
    ) -> dict:
        return {
            "campaign_id": campaign_id,
            "financials": {
                "total_revenue": revenue,
                "total_commission": revenue * 0.05,
                "ad_spend": ad_spend,
                "net_profit": revenue - ad_spend,
                "roi": (revenue - ad_spend) / max(ad_spend, 1),
            },
        }
