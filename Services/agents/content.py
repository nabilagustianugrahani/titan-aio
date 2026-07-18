"""Content Agent — unified UGC + Creative generation."""

from __future__ import annotations

import random
from typing import Any

from Database.models import WinningHook
from Database.repository import Repository
from MCP.schemas import (
    GenerateHooksOutput,
    GenerateScriptOutput,
    GenerateThumbnailOutput,
    Hook,
    Script,
    ScriptStructure,
    ThumbnailConcept,
)
from Services.agents.base import AgentContext, BaseAgent

# ── Hook templates ──────────────────────────────────────────────

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

# ── Creative concepts by category ───────────────────────────────

_CATEGORY_CONCEPTS = {
    "elektronik": [
        {"concept": "Tech Showcase", "description": "Product rotating on dark background with specs overlay", "style": "bold"},
        {"concept": "Unboxing", "description": "Hands opening package, product reveal moment", "style": "lifestyle"},
        {"concept": "Side by Side", "description": "Before/after or competitor comparison split screen", "style": "comparison"},
    ],
    "kecantikan": [
        {"concept": "Glow Up", "description": "Split face transformation with product in hand", "style": "lifestyle"},
        {"concept": "Texture Close-up", "description": "Macro shot of product texture/consistency", "style": "minimal"},
        {"concept": "Routine", "description": "Step-by-step application process", "style": "lifestyle"},
    ],
    "fashion": [
        {"concept": "OOTD", "description": "Full outfit styled with product as hero piece", "style": "lifestyle"},
        {"concept": "Detail Shot", "description": "Close-up of fabric, stitching, quality markers", "style": "minimal"},
        {"concept": "Flat Lay", "description": "Arranged items on clean surface, top-down angle", "style": "minimal"},
    ],
    "umum": [
        {"concept": "Bold Text + Product", "description": "Product shot with bold text overlay", "style": "bold"},
        {"concept": "Before After", "description": "Split screen comparison showing transformation", "style": "comparison"},
        {"concept": "Lifestyle", "description": "Product in real-life usage context", "style": "lifestyle"},
        {"concept": "Minimal", "description": "Clean white background, product only", "style": "minimal"},
    ],
}

_OVERLAYS = {
    "elektronik": ["SPESIFIKASI TERBAIK!", "DISKON 50%!", "BEST SELLER!", "TECH REVIEW"],
    "kecantikan": ["GLOW UP!", "SEBELUM vs SESUDAH", "RUTIN KULIT CANTIK", "HASIL NYATA"],
    "fashion": ["OOTD VIRAL!", "STYLE UPDATE!", "KAIN PREMIUM", "LOOK BOOK"],
    "umum": ["DISKON 50%!", "BEST SELLER!", "REVIEW JUJUR", "WAJIB BELI!"],
}

_STORYBOARD_TEMPLATES = {
    "short": [  # 15s
        {"time": "0:00-0:03", "visual": "Hook — bold text + product close-up", "audio": "Trending sound"},
        {"time": "0:03-0:08", "visual": "Product demo / transformation", "audio": "Voiceover narration"},
        {"time": "0:08-0:12", "visual": "Social proof / testimonial", "audio": "Upbeat music"},
        {"time": "0:12-0:15", "visual": "CTA — link in bio text", "audio": "Call to action voiceover"},
    ],
    "medium": [  # 30s
        {"time": "0:00-0:05", "visual": "Hook — problem statement", "audio": "Trending sound"},
        {"time": "0:05-0:12", "visual": "Product introduction + features", "audio": "Voiceover narration"},
        {"time": "0:12-0:20", "visual": "Demo / transformation / testimonial", "audio": "Background music"},
        {"time": "0:20-0:27", "visual": "Results / social proof", "audio": "Testimonial audio"},
        {"time": "0:27-0:30", "visual": "CTA — limited time offer", "audio": "Urgency voiceover"},
    ],
    "long": [  # 45s
        {"time": "0:00-0:05", "visual": "Hook — curiosity gap", "audio": "Trending sound"},
        {"time": "0:05-0:12", "visual": "Problem setup", "audio": "Relatable narration"},
        {"time": "0:12-0:20", "visual": "Product reveal + features", "audio": "Voiceover"},
        {"time": "0:20-0:30", "visual": "Full demo / before-after", "audio": "Background music"},
        {"time": "0:30-0:40", "visual": "Social proof + comparison", "audio": "Testimonial"},
        {"time": "0:40-0:45", "visual": "CTA + urgency", "audio": "Final push"},
    ],
}


class ContentAgent(BaseAgent):
    """Generates all campaign content: hooks, scripts, thumbnails, storyboards."""

    async def execute(
        self, ctx: AgentContext, product_id: str = "", **kwargs: Any,
    ) -> dict:
        category = kwargs.get("category", "umum")
        title = kwargs.get("title", "Product")
        offer_strategy = kwargs.get("offer_strategy")
        duration = kwargs.get("duration_seconds", 30)

        # ── Text content (hooks + scripts) ──
        hooks, scripts = self._generate_text(product_id, offer_strategy)

        # ── Visual content (thumbnails + storyboards) ──
        thumbnails, storyboards, shot_lists, variations = self._generate_visual(
            product_id, category, title, duration,
        )

        # ── Store winning hooks ──
        repo = Repository(ctx.session, WinningHook)
        for hook in hooks[:3]:
            await repo.create(
                campaign_id=product_id,
                hook_text=hook.hook,
                hook_type=hook.type,
            )
        await ctx.session.commit()

        result = {
            # UGC output
            "hooks": GenerateHooksOutput(product_id=product_id, hooks=hooks),
            "scripts": GenerateScriptOutput(product_id=product_id, scripts=scripts),
            # Creative output
            "thumbnail": GenerateThumbnailOutput(
                product_id=product_id,
                thumbnail=thumbnails[0] if thumbnails else ThumbnailConcept(),
            ),
            "thumbnail_concepts": [
                {"concept": t.concept, "description": t.description,
                 "text_overlay": t.text_overlay, "style": t.style}
                for t in thumbnails
            ],
            "storyboards": storyboards,
            "shot_lists": shot_lists,
            "creative_variations": variations,
        }
        self.publish(ctx, "content.generated", {"product_id": product_id, "hooks": len(hooks)})
        return result

    def _generate_text(self, product_id: str, offer_strategy: Any) -> tuple[list[Hook], list[Script]]:
        """Generate hooks and scripts."""
        random.shuffle(_HOOKS)
        hooks = [
            Hook(hook=text, type=htype,
                 predicted_ctr=random.choices(["high", "medium", "low"], weights=[0.3, 0.5, 0.2])[0])
            for text, htype in _HOOKS[:10]
        ]

        scripts = []
        for i, h in enumerate(hooks):
            scripts.append(Script(
                title=f"Variasi {i+1}: {h.hook[:30]}...",
                duration_seconds=random.choice([15, 30, 45]),
                structure=ScriptStructure(
                    hook=h.hook, problem="Problem umum...",
                    solution="Solusi...", cta="Beli sekarang!",
                ),
                full_script=f"[HOOK]\n{h.hook}\n[CTA]\nBeli sekarang!\nLink di bio!",
            ))

        return hooks, scripts

    def _generate_visual(self, product_id: str, category: str, title: str, duration: int):
        """Generate thumbnails, storyboards, shot lists, variations."""
        # Thumbnails
        concepts = _CATEGORY_CONCEPTS.get(category, _CATEGORY_CONCEPTS["umum"])
        selected = random.sample(concepts, min(2, len(concepts)))
        thumbnails = [
            ThumbnailConcept(
                concept=c["concept"], description=c["description"],
                text_overlay=random.choice(_OVERLAYS.get(category, _OVERLAYS["umum"])),
                style=c["style"],
            )
            for c in selected
        ]

        # Storyboard
        if duration <= 15:
            template = _STORYBOARD_TEMPLATES["short"]
        elif duration <= 30:
            template = _STORYBOARD_TEMPLATES["medium"]
        else:
            template = _STORYBOARD_TEMPLATES["long"]

        storyboard = {"script_title": f"Creative for {title[:40]}", "frames": template}

        # Shot list
        shot_list = {
            "script_title": storyboard["script_title"],
            "shots": [
                {"shot": f"Shot {i+1}: {f['visual']}",
                 "camera_angle": _shot_camera(f),
                 "duration": _parse_duration(f["time"])}
                for i, f in enumerate(template)
            ],
        }

        # Variations
        variations = [
            {"variant": "A", "style": "bold", "rationale": "High contrast, urgency-driven"},
            {"variant": "B", "style": "lifestyle", "rationale": "Authentic, relatable feel"},
            {"variant": "C", "style": "minimal", "rationale": "Clean, premium perception"},
        ]

        return thumbnails, [storyboard], [shot_list], variations


def _shot_camera(frame: dict) -> str:
    vis = frame.get("visual", "").lower()
    if "hook" in vis or "close" in vis:
        return "close-up"
    if "cta" in vis or "wide" in vis:
        return "wide"
    return "medium"


def _parse_duration(time_range: str) -> int:
    try:
        parts = time_range.split("-")
        def to_sec(t):
            p = t.strip().split(":")
            return int(p[0]) * 60 + int(p[1])
        return to_sec(parts[1]) - to_sec(parts[0])
    except Exception:
        return 5
