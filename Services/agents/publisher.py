"""Publisher Agent — formats content per-platform with anti-shadowban."""

from __future__ import annotations

from typing import Any

from Services.agents.base import AgentContext, BaseAgent
from Services.publisher.anti_shadowban import AntiShadowban

# Platform-specific character limits
_PLATFORM_LIMITS = {
    "tiktok": 300,
    "instagram": 2200,
    "facebook": 63206,
}

# Platform-specific CTA styles
_PLATFORM_CTA = {
    "tiktok": "Link di bio! 👆",
    "instagram": "Link di bio! 🔗",
    "facebook": "Order sekarang! Link di komentar.",
}

# Platform-specific first comment for affiliate links
_FIRST_COMMENT = {
    "tiktok": True,
    "instagram": True,
    "facebook": True,
}


class PublisherAgent(BaseAgent):
    """Formats and prepares content for multi-platform distribution."""

    _PLATFORMS = ["tiktok", "instagram", "facebook"]

    async def execute(
        self, ctx: AgentContext, caption: str = "", **kwargs: Any,
    ) -> dict:
        engine = AntiShadowban()
        category = kwargs.get("category", "umum")

        base_text = caption or "Cek produk ini! Link di bio!"
        platforms = []

        for platform in self._PLATFORMS:
            # Platform-optimized caption with rotated hashtags
            formatted = engine.generate_caption(platform, base_text, category)

            # Truncate to platform limit
            limit = _PLATFORM_LIMITS.get(platform, 500)
            if len(formatted) > limit:
                formatted = formatted[: limit - 3] + "..."

            # Timing
            is_peak = engine.is_peak_hour(platform)
            next_time = engine.suggest_next_time(platform)

            # Hashtags — extract from formatted caption
            hashtags = [word for word in formatted.split() if word.startswith("#")]

            # CTA
            cta = _PLATFORM_CTA.get(platform, "Link di bio!")

            # First comment flag
            first_comment = _FIRST_COMMENT.get(platform, False)

            platforms.append({
                "platform": platform,
                "caption": formatted,
                "hashtags": hashtags,
                "cta": cta,
                "scheduled_time": next_time,
                "is_peak_hour": is_peak,
                "first_comment": first_comment,
                "max_chars": limit,
            })

        return {"platforms": platforms}
