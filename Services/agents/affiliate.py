"""Affiliate Agent — generates affiliate links for Shopee/Tokopedia campaigns."""
from __future__ import annotations

from typing import Any

from Services.agents.base import BaseAgent, AgentContext


class AffiliateAgent(BaseAgent):
    """Generate affiliate links for Shopee, Tokopedia, TikTok Shop."""

    async def execute(self, ctx: AgentContext, product_url: str = "", product_id: str = "", platform: str = "shopee", **kwargs: Any) -> dict:
        links = {
            "shopee": {"base": "https://shopee.co.id", "tracking_param": "af_id="},
            "tokopedia": {"base": "https://tokopedia.com", "tracking_param": "af_id="},
            "tiktokshop": {"base": "https://shop.tiktok.com", "tracking_param": "af_id="},
        }

        platforms = [platform] if platform != "all" else ["shopee", "tokopedia", "tiktokshop"]
        result = {}
        for p in platforms:
            info = links.get(p, {})
            base = info.get("base", "")
            param = info.get("tracking_param", "")

            if product_url:
                sep = "&" if "?" in product_url else "?"
                affiliate_url = f"{product_url}{sep}{param}titan_aio"
            else:
                affiliate_url = f"{base}/product/{product_id}?{param}titan_aio"

            result[p] = {
                "url": affiliate_url,
                "platform": p,
                "tracking_id": "titan_aio",
            }

        await ctx.session.commit()
        return {
            "affiliate_links": result,
            "primary_platform": platform,
            "disclosure_note": "This link contains affiliate commission tracking.",
        }
