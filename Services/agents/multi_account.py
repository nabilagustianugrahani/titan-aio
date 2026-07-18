"""Multi-account management for multiple affiliate accounts."""

import hashlib
from datetime import datetime

from pydantic import BaseModel


class AffiliateAccount(BaseModel):
    account_id: str = ""
    name: str
    platform: str
    status: str = "active"
    commission_rate: float = 0.0
    total_earnings: float = 0.0
    total_clicks: int = 0
    total_conversions: int = 0
    created_at: str = ""


class MultiAccountManager:
    def __init__(self):
        self.accounts: dict[str, AffiliateAccount] = {}

    async def add_account(
        self,
        name: str,
        platform: str,
        commission_rate: float = 0.0,
    ) -> AffiliateAccount:
        aid = hashlib.md5(f"{name}:{platform}".encode()).hexdigest()[:10]
        account = AffiliateAccount(
            account_id=aid,
            name=name,
            platform=platform,
            commission_rate=commission_rate,
            created_at=datetime.now().isoformat(),
        )
        self.accounts[aid] = account
        return account

    async def record_earnings(
        self,
        account_id: str,
        earnings: float,
        clicks: int = 0,
        conversions: int = 0,
    ) -> bool:
        if account_id in self.accounts:
            acc = self.accounts[account_id]
            acc.total_earnings += earnings
            acc.total_clicks += clicks
            acc.total_conversions += conversions
            return True
        return False

    async def list_accounts(self, platform: str = "", status: str = "") -> list[AffiliateAccount]:
        accounts = list(self.accounts.values())
        if platform:
            accounts = [a for a in accounts if a.platform == platform]
        if status:
            accounts = [a for a in accounts if a.status == status]
        return accounts

    async def pause_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            self.accounts[account_id].status = "paused"
            return True
        return False

    async def resume_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            self.accounts[account_id].status = "active"
            return True
        return False

    async def delete_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            del self.accounts[account_id]
            return True
        return False

    async def get_account(self, account_id: str) -> AffiliateAccount | None:
        return self.accounts.get(account_id)

    async def get_total_earnings(self) -> dict:
        total = sum(a.total_earnings for a in self.accounts.values())
        total_clicks = sum(a.total_clicks for a in self.accounts.values())
        total_conversions = sum(a.total_conversions for a in self.accounts.values())
        by_platform: dict[str, float] = {}
        for a in self.accounts.values():
            if a.platform not in by_platform:
                by_platform[a.platform] = 0
            by_platform[a.platform] += a.total_earnings
        return {
            "total_earnings": round(total, 2),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "conversion_rate": round(
                total_conversions / max(1, total_clicks) * 100, 2,
            ),
            "by_platform": by_platform,
            "account_count": len(self.accounts),
        }

    async def get_account_performance(self, account_id: str) -> dict | None:
        if account_id not in self.accounts:
            return None
        acc = self.accounts[account_id]
        earnings_per_click = (
            round(acc.total_earnings / max(1, acc.total_clicks), 4)
        )
        return {
            "account_id": acc.account_id,
            "name": acc.name,
            "platform": acc.platform,
            "total_earnings": acc.total_earnings,
            "total_clicks": acc.total_clicks,
            "total_conversions": acc.total_conversions,
            "commission_rate": acc.commission_rate,
            "earnings_per_click": earnings_per_click,
            "conversion_rate": round(
                acc.total_conversions / max(1, acc.total_clicks) * 100, 2,
            ),
        }
