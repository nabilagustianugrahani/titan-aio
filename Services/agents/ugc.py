"""UGC Agent -- generates hooks, scripts, testimonials."""

from __future__ import annotations

import random
from typing import Any

from Database.models import WinningHook
from Database.repository import Repository
from MCP.schemas import (
    GenerateHooksOutput,
    GenerateScriptOutput,
    Hook,
    Script,
    ScriptStructure,
)
from Services.agents.base import BaseAgent, AgentContext

_HOOKS = [
    ("Kamu gak akan percaya sama produk ini sebelum lihat...", "curiosity"),
    ("STOP! Jangan beli sebelum nonton ini...", "problem"),
    ("Dari 3.2/5 jadi 4.8/5 cuma pakai ini...", "social_proof"),
    ("Harga segini? Serius?", "comparison"),
    ("Gue udah nyoba 5 produk, ini yang paling worth it...", "testimonial"),
    ("Dalam 24 jam, produk ini ludes terjual...", "scarcity"),
    ("Jangan scrolling dulu, ini penting buat kamu...", "curiosity"),
    ("Udah 10.000 orang beralih ke produk ini...", "social_proof"),
    ("Aku gak nyangka kualitasnya sebagus ini...", "testimonial"),
    ("Yang suka belanja online wajib nonton ini...", "problem"),
]


class UGCAgent(BaseAgent):
    """Generates UGC content -- hooks, scripts, testimonials."""

    async def execute(
        self,
        ctx: AgentContext,
        product_id: str,
        offer_strategy: Any = None,
        **kwargs: Any,
    ) -> dict:
        random.shuffle(_HOOKS)
        hooks_list = []
        for text, htype in _HOOKS[:10]:
            ctr = random.choices(["high", "medium", "low"], weights=[0.3, 0.5, 0.2])[0]
            hooks_list.append(
                Hook(hook=text, type=htype, predicted_ctr=ctr)
            )

        scripts_list = []
        for i, h in enumerate(hooks_list[:10]):
            scripts_list.append(
                Script(
                    title=f"Variasi {i+1}: {h.hook[:30]}...",
                    duration_seconds=random.choice([15, 30, 45]),
                    structure=ScriptStructure(
                        hook=h.hook,
                        problem="Problem umum...",
                        solution="Solusi...",
                        cta="Beli sekarang!",
                    ),
                    full_script=f"[HOOK]\n{h.hook}\n[CTA]\nBeli sekarang!\nLink di bio!",
                )
            )

        # Store first hook as winning hook candidate
        repo = Repository(ctx.session, WinningHook)
        for hook in hooks_list[:3]:
            await repo.create(
                campaign_id=product_id,
                hook_text=hook.hook,
                hook_type=hook.type,
            )
        await ctx.session.commit()

        return {
            "hooks": GenerateHooksOutput(product_id=product_id, hooks=hooks_list),
            "scripts": GenerateScriptOutput(product_id=product_id, scripts=scripts_list),
        }
