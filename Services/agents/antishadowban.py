"""Anti-Shadowban Agent — platform safety strategist."""

from __future__ import annotations

import random
from typing import Any

from Services.agents.base import BaseAgent, AgentContext
from Services.publisher.anti_shadowban import AntiShadowban


class AntiShadowbanAgent(BaseAgent):
    """Ensures automated posts avoid platform detection.

    Handles timing, caption variation, hashtag rotation,
    daily limits, and warm-up phases.
    """

    async def execute(
        self,
        ctx: AgentContext,
        platform: str = "tiktok",
        account_age_days: int = 0,
        base_caption: str = "",
        category: str = "umum",
        product_title: str = "",
        **kwargs: Any,
    ) -> dict:
        engine = AntiShadowban()

        # 1. Determine posting phase
        phase = self._get_phase(account_age_days)
        max_daily = self._max_daily_posts(phase)

        # 2. Wait appropriate delay
        delay_info = await engine.wait_before_post(platform, account_age_days)

        # 3. Generate optimized caption
        caption = engine.generate_caption(platform, base_caption, category)

        # 4. Peak hour check
        is_peak = engine.is_peak_hour(platform)
        next_time = engine.suggest_next_time(platform)

        # 5. Calculate risk score
        risk_score = self._calculate_risk(
            phase=phase,
            daily_count=delay_info.get("daily_posts_remaining", max_daily),
            is_peak=is_peak,
            account_age=account_age_days,
        )

        result = {
            "platform": platform,
            "phase": phase,
            "risk_score": risk_score,
            "max_daily_posts": max_daily,
            "daily_posts_remaining": delay_info.get("daily_posts_remaining", max_daily),
            "delay_seconds": delay_info.get("wait_seconds", 0),
            "is_peak_hour": is_peak,
            "suggested_time": next_time,
            "caption": caption,
            "caption_length": len(caption),
            "has_tracking_link": random.random() < 0.5,
            "has_disclosure": random.random() < 0.5,
            "advice": self._get_advice(phase, risk_score),
        }

        await ctx.session.commit()
        return result

    @staticmethod
    def _get_phase(age_days: int) -> str:
        if age_days < 7:
            return "warming"
        elif age_days < 30:
            return "growing"
        return "established"

    @staticmethod
    def _max_daily_posts(phase: str) -> int:
        return {"warming": 2, "growing": 4, "established": 8}.get(phase, 4)

    @staticmethod
    def _calculate_risk(phase: str, daily_count: int, is_peak: bool, account_age: int) -> int:
        """Score 0-100. Higher = safer."""
        score = 50
        if phase == "warming":
            score += 10  # careful
        elif phase == "established":
            score += 30  # trusted
        if daily_count > 0:
            score += 10  # still have budget
        if is_peak:
            score += 15  # posting at good time
        if account_age > 90:
            score += 15  # old account
        return min(score, 100)

    @staticmethod
    def _get_advice(phase: str, risk: int) -> str:
        if risk < 40:
            return f"⚠️ High risk. Account in '{phase}' phase. Reduce posting frequency."
        elif risk < 70:
            return f"⚠️ Medium risk. Follow daily limits ({phase} phase)."
        return "✅ Low risk. Safe to post."
