"""Multi-niche campaign manager for running parallel affiliate campaigns."""

from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel


class NicheCampaign(BaseModel):
    campaign_id: str = ""
    niche: str
    name: str
    status: str = "active"
    products: list[str] = []
    budget: float = 0.0
    daily_post_limit: int = 3
    platforms: list[str] = ["tiktok", "instagram"]
    created_at: str = ""


class MultiNicheManager:
    """In-memory multi-niche campaign orchestrator."""

    def __init__(self) -> None:
        self.campaigns: dict[str, NicheCampaign] = {}

    async def create_campaign(
        self,
        niche: str,
        name: str,
        platforms: list[str] | None = None,
        budget: float = 0.0,
        daily_post_limit: int = 3,
    ) -> NicheCampaign:
        cid = hashlib.md5(f"{niche}:{name}".encode()).hexdigest()[:10]
        campaign = NicheCampaign(
            campaign_id=cid,
            niche=niche,
            name=name,
            platforms=platforms or ["tiktok", "instagram"],
            budget=budget,
            daily_post_limit=daily_post_limit,
            created_at=datetime.now().isoformat(),
        )
        self.campaigns[cid] = campaign
        return campaign

    async def add_product(self, campaign_id: str, product_id: str) -> bool:
        if campaign_id in self.campaigns:
            if product_id not in self.campaigns[campaign_id].products:
                self.campaigns[campaign_id].products.append(product_id)
            return True
        return False

    async def remove_product(self, campaign_id: str, product_id: str) -> bool:
        if campaign_id in self.campaigns:
            try:
                self.campaigns[campaign_id].products.remove(product_id)
                return True
            except ValueError:
                return False
        return False

    async def list_campaigns(
        self,
        niche: str = "",
        status: str = "",
    ) -> list[NicheCampaign]:
        result = list(self.campaigns.values())
        if niche:
            result = [c for c in result if c.niche == niche]
        if status:
            result = [c for c in result if c.status == status]
        return result

    async def get_campaign(self, campaign_id: str) -> NicheCampaign | None:
        return self.campaigns.get(campaign_id)

    async def get_niche_summary(self) -> dict:
        summary: dict[str, dict] = {}
        for c in self.campaigns.values():
            if c.niche not in summary:
                summary[c.niche] = {
                    "campaigns": 0,
                    "total_products": 0,
                    "total_budget": 0.0,
                }
            summary[c.niche]["campaigns"] += 1
            summary[c.niche]["total_products"] += len(c.products)
            summary[c.niche]["total_budget"] += c.budget
        return summary

    async def pause_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self.campaigns:
            self.campaigns[campaign_id].status = "paused"
            return True
        return False

    async def resume_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self.campaigns:
            self.campaigns[campaign_id].status = "active"
            return True
        return False

    async def delete_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self.campaigns:
            del self.campaigns[campaign_id]
            return True
        return False
