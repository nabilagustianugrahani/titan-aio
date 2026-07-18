"""Knowledge Agent — synthesizes campaign history into reusable intelligence."""

from __future__ import annotations

from typing import Any

from Database.models import (
    Campaign,
    Product,
    WinningHook,
)
from Database.repository import Repository
from Services.agents.base import AgentContext, BaseAgent


class KnowledgeAgent(BaseAgent):
    """Synthesizes campaign history into category playbooks and patterns."""

    async def execute(self, ctx: AgentContext, **kwargs: Any) -> dict:
        campaign_repo = Repository(ctx.session, Campaign)
        hook_repo = Repository(ctx.session, WinningHook)
        product_repo = Repository(ctx.session, Product)

        # ── Gather data ──
        all_campaigns = await campaign_repo.list_all(limit=200)
        all_hooks = await hook_repo.list_all(limit=500)

        # ── Build category → campaigns mapping ──
        cat_campaigns: dict[str, list] = {}
        for c in all_campaigns:
            # Look up product to get category
            products = await product_repo.find(id=c.product_id)
            cat = products[0].category if products and products[0].category else "umum"
            cat_campaigns.setdefault(cat, []).append(c)

        # ── Build category → hooks mapping ──
        cat_hooks: dict[str, list[WinningHook]] = {}
        for h in all_hooks:
            products = await product_repo.find(id=h.campaign_id)
            cat = products[0].category if products and products[0].category else "umum"
            cat_hooks.setdefault(cat, []).append(h)

        # ── Generate knowledge entries ──
        entries = []
        for cat, campaigns in cat_campaigns.items():
            hooks = cat_hooks.get(cat, [])
            if not hooks:
                continue

            # Best hook by CTR
            best_hook = max(hooks, key=lambda h: h.ctr or 0)

            # Hook type distribution
            type_counts: dict[str, int] = {}
            for h in hooks:
                type_counts[h.hook_type] = type_counts.get(h.hook_type, 0) + 1
            best_type = max(type_counts, key=type_counts.get) if type_counts else "unknown"

            confidence = min(len(hooks) / 10.0, 1.0)  # More hooks = higher confidence

            entries.append({
                "category": cat,
                "pattern": f"Best hook type: {best_type} ({len(hooks)} hooks analyzed)",
                "confidence": round(confidence, 2),
                "evidence": [h.campaign_id for h in hooks[:5]],
                "actionable_advice": f"Use {best_type} hooks for {cat}. Top hook: \"{best_hook.hook_text[:60]}\"",
            })

        # ── Generate category playbooks ──
        playbooks = []
        for cat, campaigns in cat_campaigns.items():
            hooks = cat_hooks.get(cat, [])

            # Determine best angle from hook types
            type_counts = {}
            for h in hooks:
                type_counts[h.hook_type] = type_counts.get(h.hook_type, 0) + 1
            winning_angle = max(type_counts, key=type_counts.get) if type_counts else "curiosity"

            # Top hooks by CTR
            top_hooks = sorted(hooks, key=lambda h: h.ctr or 0, reverse=True)[:5]
            hook_texts = [h.hook_text for h in top_hooks]

            # Best platform from campaigns
            platform_counts: dict[str, int] = {}
            for c in campaigns:
                if c.platform:
                    platform_counts[c.platform] = platform_counts.get(c.platform, 0) + 1
            best_platform = max(platform_counts, key=platform_counts.get) if platform_counts else "tiktok"

            playbooks.append({
                "category": cat,
                "winning_angle": winning_angle,
                "top_hooks": hook_texts,
                "best_platform": best_platform,
                "best_posting_time": "18:00-21:00 WIB",
                "campaigns_analyzed": len(campaigns),
            })

        return {
            "knowledge_entries": entries,
            "category_playbooks": playbooks,
            "total_campaigns_analyzed": len(all_campaigns),
            "total_hooks_analyzed": len(all_hooks),
        }
