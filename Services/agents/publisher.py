"""Publisher Agent -- formats content for platforms."""

from __future__ import annotations

from typing import Any

from Services.agents.base import BaseAgent, AgentContext


class PublisherAgent(BaseAgent):
    """Formats and prepares content for distribution."""

    _PLATFORMS = ["tiktok", "instagram", "youtube_shorts", "facebook", "shopee_feed"]

    async def execute(
        self, ctx: AgentContext, caption: str = "", **kwargs: Any
    ) -> dict:
        platforms = []
        for p in self._PLATFORMS:
            text = caption if caption else "Cek produk ini! Link di bio!"
            platforms.append(
                {
                    "platform": p,
                    "caption": f"{text}\n\nLink di bio!",
                    "hashtags": ["#fyp", "#recommended", "#produkoriginal"],
                }
            )
        return {"platforms": platforms}
