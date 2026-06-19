"""Creative Agent — plans visual direction, storyboards, and shot lists."""

from __future__ import annotations

import random
from typing import Any

from MCP.schemas import GenerateThumbnailOutput, ThumbnailConcept
from Services.agents.base import BaseAgent, AgentContext

# Concept templates by product category
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

# Storyboard templates
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


class CreativeAgent(BaseAgent):
    """Generates storyboards, thumbnails, and creative variations."""

    async def execute(
        self, ctx: AgentContext, product_id: str = "", **kwargs: Any
    ) -> dict:
        category = kwargs.get("category", "umum")
        title = kwargs.get("title", "Product")

        # ── Thumbnail concepts ──
        concepts = _CATEGORY_CONCEPTS.get(category, _CATEGORY_CONCEPTS["umum"])
        selected = random.sample(concepts, min(2, len(concepts)))

        thumbnails = []
        for c in selected:
            # Dynamic text overlay based on product
            overlay = _pick_overlay(category)
            thumbnails.append(ThumbnailConcept(
                concept=c["concept"],
                description=c["description"],
                text_overlay=overlay,
                style=c["style"],
            ))

        thumbnail_output = GenerateThumbnailOutput(
            product_id=product_id,
            thumbnail=thumbnails[0] if thumbnails else ThumbnailConcept(),
        )

        # ── Storyboard ──
        duration = kwargs.get("duration_seconds", 30)
        if duration <= 15:
            template = _STORYBOARD_TEMPLATES["short"]
        elif duration <= 30:
            template = _STORYBOARD_TEMPLATES["medium"]
        else:
            template = _STORYBOARD_TEMPLATES["long"]

        storyboard = {
            "script_title": f"Creative for {title[:40]}",
            "frames": template,
        }

        # ── Shot list ──
        shot_list = {
            "script_title": storyboard["script_title"],
            "shots": [
                {
                    "shot": f"Shot {i+1}: {frame['visual']}",
                    "camera_angle": _shot_camera(frame),
                    "duration": _parse_duration(frame["time"]),
                }
                for i, frame in enumerate(template)
            ],
        }

        # ── Creative variations ──
        variations = [
            {"variant": "A", "style": "bold", "rationale": "High contrast, urgency-driven"},
            {"variant": "B", "style": "lifestyle", "rationale": "Authentic, relatable feel"},
            {"variant": "C", "style": "minimal", "rationale": "Clean, premium perception"},
        ]

        await ctx.session.commit()

        return {
            "thumbnail": thumbnail_output,
            "thumbnail_concepts": [
                {"concept": t.concept, "description": t.description, "text_overlay": t.text_overlay, "style": t.style}
                for t in thumbnails
            ],
            "storyboards": [storyboard],
            "shot_lists": [shot_list],
            "creative_variations": variations,
        }


def _pick_overlay(category: str) -> str:
    overlays = {
        "elektronik": ["SPESIFIKASI TERBAIK!", "DISKON 50%!", "BEST SELLER!", "TECH REVIEW"],
        "kecantikan": ["GLOW UP!", "SEBELUM vs SESUDAH", "RUTIN KULIT CANTIK", "HASIL NYATA"],
        "fashion": ["OOTD VIRAL!", "STYLE UPDATE!", "KAIN PREMIUM", "LOOK BOOK"],
        "umum": ["DISKON 50%!", "BEST SELLER!", "REVIEW JUJUR", "WAJIB BELI!"],
    }
    return random.choice(overlays.get(category, overlays["umum"]))


def _shot_camera(frame: dict) -> str:
    vis = frame.get("visual", "").lower()
    if "hook" in vis or "close" in vis:
        return "close-up"
    if "cta" in vis or "wide" in vis:
        return "wide"
    return "medium"


def _parse_duration(time_range: str) -> int:
    """Parse '0:05-0:12' → 7 seconds."""
    try:
        parts = time_range.split("-")
        def to_sec(t):
            parts = t.strip().split(":")
            return int(parts[0]) * 60 + int(parts[1])
        return to_sec(parts[1]) - to_sec(parts[0])
    except Exception:
        return 5
