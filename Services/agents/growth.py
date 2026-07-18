"""Growth Agent — scales winners, kills losers with DB persistence."""

from __future__ import annotations

from typing import Any

from Database.models import BudgetAllocation, Campaign, FailedCampaign, Metric
from Database.repository import Repository
from Services.agents.base import AgentContext, BaseAgent


class GrowthAgent(BaseAgent):
    """Automates campaign scaling and termination based on performance metrics.

    Actions:
      evaluate  — assess a campaign and recommend scale/maintain/kill
      allocate  — compute budget allocation across platforms
      retire    — archive a failed campaign
    """

    # Thresholds (configurable via kwargs)
    SCALE_ROI = 2.0
    KILL_ROI = 0.3
    KILL_MIN_SPEND = 50_000  # IDR — only kill if enough data

    async def execute(self, ctx: AgentContext, action: str = "evaluate", **kwargs: Any) -> dict:
        if action == "evaluate":
            return await self._evaluate(ctx, **kwargs)
        if action == "allocate":
            return await self._allocate(ctx, **kwargs)
        if action == "retire":
            return await self._retire(ctx, **kwargs)
        return {"error": f"Unknown action: {action}"}

    # ── evaluate ────────────────────────────────────────────────────
    async def _evaluate(self, ctx: AgentContext, campaign_id: str = "", roi: float = 0.0, **kwargs: Any) -> dict:
        # Direct ROI evaluation (no DB lookup)
        if not campaign_id:
            action, budget_delta, rationale = self._decide_simple(roi)
            return {
                "campaign_id": "",
                "action": action,
                "roi": roi,
                "ctr": 0.0,
                "conversion_rate": 0.0,
                "budget_change_pct": round(budget_delta * 100, 1),
                "rationale": rationale,
            }

        camp_repo = Repository(ctx.session, Campaign)
        camps = await camp_repo.find(id=campaign_id)
        if not camps:
            return {"error": f"Campaign {campaign_id} not found"}

        camp = camps[0]
        roi = self._calc_roi(camp.total_revenue, camp.total_spent)

        # Fetch latest metrics
        metric_repo = Repository(ctx.session, Metric)
        metrics = await metric_repo.find(campaign_id=campaign_id)
        latest = metrics[-1] if metrics else None

        ctr = latest.ctr if latest else 0.0
        conv_rate = latest.conversion_rate if latest else 0.0

        # Decision logic
        action, budget_delta, rationale = self._decide(roi, ctr, conv_rate, camp.total_spent)

        # Persist recommendation as BudgetAllocation
        alloc_repo = Repository(ctx.session, BudgetAllocation)
        recommended = max(0, (camp.budget or 100_000) * (1 + budget_delta))
        await alloc_repo.create(
            campaign_id=campaign_id,
            platform=camp.platform or "tiktok",
            current_budget=camp.budget or 0,
            recommended_budget=round(recommended, 0),
            roi=roi,
            priority=1 if action == "scale" else 3 if action == "kill" else 2,
            reason=rationale,
        )

        await ctx.session.commit()
        return {
            "campaign_id": campaign_id,
            "action": action,
            "roi": roi,
            "ctr": ctr,
            "conversion_rate": conv_rate,
            "budget_change_pct": round(budget_delta * 100, 1),
            "rationale": rationale,
        }

    # ── allocate ────────────────────────────────────────────────────
    async def _allocate(
        self,
        ctx: AgentContext,
        total_budget: float = 100_000,
        **kwargs: Any,
    ) -> dict:
        camp_repo = Repository(ctx.session, Campaign)
        active = await camp_repo.find(status="active")
        if not active:
            active = await camp_repo.find(status="published")
        if not active:
            return {"allocations": [], "note": "No active campaigns"}

        # Score each campaign
        scored = []
        for c in active:
            roi = self._calc_roi(c.total_revenue, c.total_spent)
            score = max(0.1, roi)  # floor at 0.1 so every campaign gets something
            scored.append((c, roi, score))

        total_score = sum(s for _, _, s in scored)

        alloc_repo = Repository(ctx.session, BudgetAllocation)
        allocations = []
        for c, roi, score in scored:
            share = score / total_score
            amount = round(total_budget * share, 0)
            await alloc_repo.create(
                campaign_id=c.id,
                platform=c.platform or "tiktok",
                current_budget=c.budget or 0,
                recommended_budget=amount,
                roi=roi,
                priority=1 if roi > self.SCALE_ROI else 3 if roi < self.KILL_ROI else 2,
                reason=f"ROI {roi:.2f}, share {share:.1%}",
            )
            allocations.append({
                "campaign_id": c.id,
                "platform": c.platform,
                "roi": roi,
                "budget_share_pct": round(share * 100, 1),
                "recommended_budget": amount,
            })

        await ctx.session.commit()
        return {"total_budget": total_budget, "allocations": allocations}

    # ── retire ──────────────────────────────────────────────────────
    async def _retire(self, ctx: AgentContext, campaign_id: str = "", reason: str = "", **kwargs: Any) -> dict:
        camp_repo = Repository(ctx.session, Campaign)
        camps = await camp_repo.find(id=campaign_id)
        if not camps:
            return {"error": f"Campaign {campaign_id} not found"}

        camp = camps[0]
        failed_repo = Repository(ctx.session, FailedCampaign)
        await failed_repo.create(
            campaign_id=campaign_id,
            product_id=camp.product_id,
            reason=reason or "ROI below threshold",
            metrics_snapshot={
                "revenue": camp.total_revenue,
                "spent": camp.total_spent,
                "roi": self._calc_roi(camp.total_revenue, camp.total_spent),
            },
        )
        await camp_repo.update(camp.id, status="retired")
        await ctx.session.commit()
        return {"retired": True, "campaign_id": campaign_id, "reason": reason}

    def _decide_simple(self, roi: float) -> tuple[str, float, str]:
        """Simple ROI-only decision (no DB)."""
        if roi > self.SCALE_ROI:
            return "scale", 0.5, f"ROI {roi:.2f} exceeds scale threshold ({self.SCALE_ROI})"
        if roi <= self.KILL_ROI:
            return "kill", -1.0, f"ROI {roi:.2f} below kill threshold ({self.KILL_ROI})"
        return "maintain", 0.0, f"ROI {roi:.2f} within normal range"

    # ── helpers ─────────────────────────────────────────────────────
    def _calc_roi(self, revenue: float, spend: float) -> float:
        if spend <= 0:
            return 0.0
        return round((revenue - spend) / spend, 2)

    def _decide(self, roi: float, ctr: float, conv_rate: float, total_spent: float) -> tuple[str, float, str]:
        if roi > self.SCALE_ROI:
            return "scale", 0.5, f"ROI {roi:.2f} exceeds scale threshold ({self.SCALE_ROI})"
        if roi < self.KILL_ROI and total_spent >= self.KILL_MIN_SPEND:
            return "kill", -1.0, f"ROI {roi:.2f} below kill threshold ({self.KILL_ROI}) after Rp {total_spent:,.0f} spent"
        if roi < self.KILL_ROI:
            return "monitor", 0.0, f"ROI {roi:.2f} low but spend Rp {total_spent:,.0f} insufficient for kill decision"
        return "maintain", 0.0, f"ROI {roi:.2f} within normal range"
