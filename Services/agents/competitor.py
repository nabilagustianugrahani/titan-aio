"""Competitor Agent -- analyzes competitor ads and hooks."""

from __future__ import annotations

from typing import Any

from MCP.schemas import AnalyzeCompetitorsOutput, CompetitorHook
from Services.agents.base import BaseAgent, AgentContext


class CompetitorAgent(BaseAgent):
    """Analyzes competitor ads, hooks, and creatives."""

    async def execute(
        self, ctx: AgentContext, category: str = "umum", **kwargs: Any
    ) -> AnalyzeCompetitorsOutput:
        return AnalyzeCompetitorsOutput(
            category=category,
            competitors_analyzed=5,
            winning_hooks=[
                CompetitorHook(
                    hook="Harga termurah se-Indonesia!",
                    source="shopee",
                    engagement_est="high",
                ),
                CompetitorHook(
                    hook="Garansi resmi 1 tahun!",
                    source="tokopedia",
                    engagement_est="high",
                ),
            ],
            common_angles=["harga murah", "garansi resmi", "diskon terbatas"],
            creative_patterns=["product shot white bg", "before-after"],
            gaps_identified=["Belum ada testimonial pengguna", "Video UGC masih jarang"],
            recommended_differentiation="Fokus storytelling pengguna nyata.",
        )
