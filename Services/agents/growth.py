"""Growth Agent -- scales winners, kills losers."""

from __future__ import annotations

from typing import Any

from Services.agents.base import BaseAgent, AgentContext


class GrowthAgent(BaseAgent):
    """Automates campaign scaling and termination."""

    async def execute(
        self, ctx: AgentContext, roi: float = 0.0, **kwargs: Any
    ) -> dict:
        action = "maintain"
        if roi > 2.0:
            action = "scale"
        elif roi < 0.5:
            action = "kill"

        return {
            "actions": [
                {
                    "action": action,
                    "rationale": f"ROI is {roi:.2f}",
                    "budget_change": 0.5 if action == "scale" else -1.0 if action == "kill" else 0.0,
                }
            ],
            "recommendations": ["Increase ad spend on winning platforms."],
        }
