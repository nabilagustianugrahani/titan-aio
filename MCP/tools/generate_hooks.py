"""Generate attention-grabbing hooks."""

from __future__ import annotations

import random
from MCP.schemas import GenerateHooksInput, GenerateHooksOutput, Hook


_HOOK_TEMPLATES = [
    ("Kamu gak akan percaya sama produk ini sebelum lihat...", "curiosity"),
    ("STOP! Jangan beli sebelum nonton ini...", "problem"),
    ("Dari 3.2/5 jadi 4.8/5 cuma pakai ini...", "social_proof"),
    ("Ini dia rahasia yang gak pernah dikasih tau toko...", "how_to"),
    ("Harga segini? Serius? Coba cek dulu...", "comparison"),
    ("Gue udah nyoba 5 produk, ini yang paling worth it...", "testimonial"),
    ("Dalam 24 jam, produk ini ludes terjual...", "scarcity"),
    ("Jangan scrolling dulu, ini penting buat kamu...", "curiosity"),
    ("Udah 10.000 orang beralih ke produk ini...", "social_proof"),
    ("Rahasia kecil yang bikin produk ini beda...", "how_to"),
    ("Aku gak nyangka kualitasnya sebagus ini...", "testimonial"),
    ("Yang suka belanja online wajib nonton ini...", "problem"),
]


async def generate_hooks(input_data: GenerateHooksInput) -> GenerateHooksOutput:
    """Generate attention-grabbing hooks."""
    templates = _HOOK_TEMPLATES.copy()
    random.shuffle(templates)

    hooks = []
    for hook_text, hook_type in templates[: input_data.count]:
        ctr = random.choices(["high", "medium", "low"], weights=[0.3, 0.5, 0.2])[0]
        hooks.append(Hook(hook=hook_text, type=hook_type, predicted_ctr=ctr))

    return GenerateHooksOutput(product_id=input_data.product_id, hooks=hooks)
