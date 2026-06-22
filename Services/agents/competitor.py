"""Competitor Agent — analyzes competitor ads, hooks, and creative patterns."""

from __future__ import annotations

from typing import Any

from MCP.schemas import AnalyzeCompetitorsOutput, CompetitorHook
from Database.models import Product, WinningHook
from Database.repository import Repository
from Services.agents.base import BaseAgent, AgentContext

# Keywords that signal common angles in Indonesian e-commerce
_ANGLE_KEYWORDS = {
    "harga": "harga murah",
    "murah": "harga murah",
    "diskon": "diskon/promo",
    "promo": "diskon/promo",
    "sale": "diskon/promo",
    "garansi": "garansi resmi",
    "resmi": "garansi resmi",
    "original": "produk original",
    "ori": "produk original",
    "best seller": "social proof",
    "terlaris": "social proof",
    "review": "social proof",
    "testimoni": "testimoni",
    "pengalaman": "testimoni",
    "gratis": "gratis ongkir",
    "ongkir": "gratis ongkir",
    "cashback": "cashback",
    "bonus": "bonus/hadiah",
    "hadiah": "bonus/hadiah",
    "kualitas": "kualitas premium",
    "premium": "kualitas premium",
    "korea": "tren import",
    "japan": "tren import",
}

# Common creative patterns
_CREATIVE_PATTERNS = [
    "product shot white bg",
    "before-after transformation",
    "unboxing video",
    "lifestyle in-use shot",
    "split screen comparison",
    "talking head review",
    "close-up detail shot",
    "flat lay arrangement",
]


class CompetitorAgent(BaseAgent):
    """Analyzes competitor ads, hooks, and creatives from DB data."""

    async def execute(
        self, ctx: AgentContext, category: str = "umum", **kwargs: Any
    ) -> AnalyzeCompetitorsOutput:
        repo = Repository(ctx.session, Product)
        hook_repo = Repository(ctx.session, WinningHook)

        # ── Get competitor products in category ──
        if category:
            competitors = await repo.find(category=category)
        else:
            competitors = await repo.list_all(limit=50)

        competitors_analyzed = len(competitors)

        # ── Extract angle keywords from product titles ──
        angle_counts: dict[str, int] = {}
        for p in competitors:
            title_lower = (p.title or "").lower()
            for keyword, angle in _ANGLE_KEYWORDS.items():
                if keyword in title_lower:
                    angle_counts[angle] = angle_counts.get(angle, 0) + 1

        # Sort angles by frequency
        common_angles = sorted(angle_counts.keys(), key=lambda a: angle_counts[a], reverse=True)[:10]

        # ── Get winning hooks from DB ──
        all_hooks: list[WinningHook] = []
        product_ids = [p.id for p in competitors[:20]]
        for pid in product_ids:
            hooks = await hook_repo.find(campaign_id=pid)
            all_hooks.extend(hooks)

        # Also get hooks by category match
        all_win_hooks = await hook_repo.list_all(limit=100)
        category_hooks = [
            h for h in all_win_hooks
            if any(
                keyword in (h.hook_text or "").lower()
                for keyword in category.lower().split()
            )
        ]
        all_hooks.extend(category_hooks)

        # Deduplicate by hook_text
        seen_hooks: set[str] = set()
        unique_hooks: list[WinningHook] = []
        for h in all_hooks:
            if h.hook_text not in seen_hooks:
                seen_hooks.add(h.hook_text)
                unique_hooks.append(h)

        # Sort by CTR
        unique_hooks.sort(key=lambda h: h.ctr or 0, reverse=True)

        winning_hooks = [
            CompetitorHook(
                hook=h.hook_text,
                source="campaign_data",
                engagement_est=_estimate_engagement(h.ctr),
            )
            for h in unique_hooks[:10]
        ]

        # ── Identify creative patterns ──
        # Check product titles for pattern signals
        detected_patterns: list[str] = []
        for p in competitors:
            title = (p.title or "").lower()
            if "unboxing" in title:
                detected_patterns.append("unboxing video")
            if "before" in title and "after" in title:
                detected_patterns.append("before-after transformation")
            if "review" in title:
                detected_patterns.append("talking head review")

        creative_patterns = list(dict.fromkeys(detected_patterns))[:5] or _CREATIVE_PATTERNS[:3]

        # ── Gap analysis ──
        all_possible_angles = set(_ANGLE_KEYWORDS.values())
        used_angles = set(common_angles)
        gap_angles = all_possible_angles - used_angles

        gaps = []
        if "testimoni" in gap_angles:
            gaps.append("Belum ada testimonial pengguna nyata")
        if "tren import" in gap_angles:
            gaps.append("Belum ada angle tren import Korea/Jepang")
        if len(gaps) == 0:
            gaps = ["Sudah cukup kompetitif — coba diferensiasi via visual/branding"]

        # ── Differentiation recommendation ──
        if "testimoni" in gap_angles:
            differentiation = "Fokus storytelling pengguna nyata + testimoni video."
        elif "tren import" in gap_angles:
            differentiation = "Manfaatkan tren import Korea/Jepang untuk reach lebih luas."
        else:
            differentiation = "Tingkatkan kualitas visual dan konsistensi branding."

        return AnalyzeCompetitorsOutput(
            category=category,
            competitors_analyzed=competitors_analyzed,
            winning_hooks=winning_hooks,
            common_angles=common_angles[:5],
            creative_patterns=creative_patterns,
            gaps_identified=gaps,
            recommended_differentiation=differentiation,
        )


def _estimate_engagement(ctr: float | None) -> str:
    if ctr is None:
        return "unknown"
    if ctr >= 0.05:
        return "high"
    if ctr >= 0.02:
        return "medium"
    return "low"
