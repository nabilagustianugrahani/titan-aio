"""Generate UGC scripts from hooks."""

from __future__ import annotations

import random
from MCP.schemas import (
    GenerateScriptInput,
    GenerateScriptOutput,
    Script,
    ScriptStructure,
)


async def generate_script(input_data: GenerateScriptInput) -> GenerateScriptOutput:
    """Generate full UGC scripts from hooks."""
    scripts = []
    for i, hook in enumerate(input_data.hooks[: input_data.count]):
        s = Script(
            title=f"Variasi {i+1}: {hook.hook[:40]}...",
            duration_seconds=random.choice([15, 30, 45, 60]),
            structure=ScriptStructure(
                hook=hook.hook,
                problem=f"Masalah: objection ke-{(i % max(len(input_data.offer_strategy.objections_to_address), 1)) + 1}",
                solution=f"Solusi: {input_data.offer_strategy.value_proposition}",
                social_proof=input_data.offer_strategy.positioning_statement,
                cta=input_data.offer_strategy.recommended_cta,
            ),
            full_script=_generate_full_script(hook, input_data.offer_strategy),
        )
        scripts.append(s)

    return GenerateScriptOutput(product_id=input_data.product_id, scripts=scripts)


def _generate_full_script(hook, offer_strategy) -> str:
    obj = (
        offer_strategy.objections_to_address[0]
        if offer_strategy.objections_to_address
        else "produk yang gak sesuai ekspektasi"
    )
    lines = [
        "[HOOK]",
        hook.hook,
        "",
        "[PROBLEM]",
        f"Kita semua tahu masalahnya -- {obj}.",
        "",
        "[SOLUTION]",
        f"Tapi sekarang ada solusinya. {offer_strategy.value_proposition}.",
        "",
        "[SOCIAL PROOF]",
        f"{offer_strategy.positioning_statement}. Udah banyak yang buktiin.",
        "",
        "[CTA]",
        offer_strategy.recommended_cta,
        "",
        "Klik link di bio!",
    ]
    return "\n".join(lines)
