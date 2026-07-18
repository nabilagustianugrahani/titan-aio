"""Budget Optimizer — auto-allocate ad spend across campaigns for maximum ROI."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BudgetAllocation(BaseModel):
    campaign_id: str
    platform: str
    current_budget: float = 0.0
    recommended_budget: float = 0.0
    roi: float = 0.0
    priority: str = "medium"  # low/medium/high
    reason: str = ""


class BudgetOptimizer:
    def __init__(self):
        self.allocations: dict[str, BudgetAllocation] = {}
        self.total_budget: float = 0.0
        self.history: list[dict] = []

    async def set_total_budget(self, budget: float):
        self.total_budget = budget

    async def register_campaign(self, campaign_id: str, platform: str, current_budget: float = 0.0, roi: float = 0.0) -> BudgetAllocation:
        priority = "high" if roi > 100 else ("medium" if roi > 30 else "low")
        reason = f"ROI: {roi}%" + (" — scale aggressively" if roi > 100 else " — optimize" if roi < 30 else " — maintain")
        alloc = BudgetAllocation(campaign_id=campaign_id, platform=platform, current_budget=current_budget, roi=roi, priority=priority, reason=reason)
        self.allocations[campaign_id] = alloc
        return alloc

    async def optimize(self) -> list[BudgetAllocation]:
        if not self.allocations:
            return []
        total_roi = sum(max(0.1, a.roi) for a in self.allocations.values())
        for alloc in self.allocations.values():
            roi_weight = max(0.1, alloc.roi) / total_roi
            alloc.recommended_budget = round(self.total_budget * roi_weight, 2)
        self.history.append({"timestamp": datetime.now().isoformat(), "total_budget": self.total_budget, "allocations": len(self.allocations)})
        return list(self.allocations.values())

    async def get_allocations(self) -> list[BudgetAllocation]:
        return list(self.allocations.values())

    async def get_summary(self) -> dict:
        total_current = sum(a.current_budget for a in self.allocations.values())
        total_recommended = sum(a.recommended_budget for a in self.allocations.values())
        return {"total_budget": self.total_budget, "total_current_spend": total_current, "total_recommended": total_recommended, "campaigns": len(self.allocations)}

    async def get_stats(self) -> dict:
        return {"total_budget": self.total_budget, "campaigns": len(self.allocations), "optimizations_run": len(self.history)}
