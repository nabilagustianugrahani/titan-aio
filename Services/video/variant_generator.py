"""
Batch Variant Generator — one product → N campaign variants for A/B testing.

Competitor gap: Arcads excels at batch variant generation.
This module generates structured A/B variants with tracking IDs.

Usage:
    from Services.video.variant_generator import VariantGenerator
    gen = VariantGenerator()
    variants = await gen.generate(product_url="...", num_variants=3)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional



@dataclass
class Variant:
    """Single A/B test variant."""
    variant_id: str
    label: str  # "A", "B", "C"
    hook: str
    script: str
    style: str
    thumbnail_concept: str
    video_path: Optional[str] = None
    platform: str = "tiktok"
    metrics: dict = field(default_factory=dict)  # views, clicks, ctr, revenue


@dataclass
class VariantBatch:
    """Batch of variants for a single product."""
    batch_id: str
    product_id: str
    product_title: str
    product_url: str
    variants: list[Variant]
    status: str = "created"  # created → generating → published → optimizing


class VariantGenerator:
    """Generate multiple A/B variants for a product."""

    STYLES = [
        {"label": "A", "style": "bold", "rationale": "High contrast, urgency-driven. Best for cold traffic."},
        {"label": "B", "style": "lifestyle", "rationale": "Authentic, relatable feel. Best for warm audiences."},
        {"label": "C", "style": "minimal", "rationale": "Clean, premium perception. Best for retargeting."},
        {"label": "D", "style": "humor", "rationale": "Entertaining, shareable. Best for viral potential."},
    ]

    HOOK_ANGLES = [
        "problem",
        "curiosity",
        "social_proof",
        "comparison",
        "testimonial",
        "scarcity",
        "transformation",
        "urgency",
    ]

    async def generate(
        self,
        product_url: str,
        product_title: str = "",
        product_id: str = "",
        num_variants: int = 3,
        platforms: Optional[list[str]] = None,
        duration_seconds: int = 30,
    ) -> VariantBatch:
        """Generate N variants for a product.

        Each variant gets:
        - Unique hook angle
        - Different script style
        - Different thumbnail concept
        - Platform-specific formatting
        """
        batch_id = uuid.uuid4().hex[:12]
        product_id = product_id or f"prod-{uuid.uuid4().hex[:8]}"

        if platforms is None:
            platforms = ["tiktok"]

        variants = []
        selected_styles = self.STYLES[:num_variants]

        for style_config in selected_styles:
            variant_id = f"var-{batch_id}-{style_config['label']}"

            # Generate hook based on style
            hook = self._generate_hook(
                style=style_config["style"],
                product_title=product_title,
                angle=self.HOOK_ANGLES[len(variants) % len(self.HOOK_ANGLES)],
            )

            # Generate script based on style
            script = self._generate_script(
                hook=hook,
                style=style_config["style"],
                duration_seconds=duration_seconds,
                product_title=product_title,
            )

            # Generate thumbnail concept
            thumbnail = self._generate_thumbnail_concept(
                style=style_config["style"],
                product_title=product_title,
            )

            variant = Variant(
                variant_id=variant_id,
                label=style_config["label"],
                hook=hook,
                script=script,
                style=style_config["style"],
                thumbnail_concept=thumbnail,
                platform=platforms[0] if platforms else "tiktok",
            )
            variants.append(variant)

        batch = VariantBatch(
            batch_id=batch_id,
            product_id=product_id,
            product_title=product_title,
            product_url=product_url,
            variants=variants,
        )

        return batch

    def _generate_hook(self, style: str, product_title: str, angle: str) -> str:
        """Generate a hook based on style and angle."""
        hooks = {
            "bold": {
                "problem": f"STOP! Jangan beli {product_title} sebelum nonton ini...",
                "curiosity": f"Kamu gak akan percaya sama {product_title} ini...",
                "social_proof": f"Udah 10.000+ orang pakai {product_title}, kamu kapan?",
                "comparison": f"Review jujur {product_title} vs kompetitor!",
                "testimonial": f"Gue udah nyoba {product_title}, ini hasilnya...",
                "scarcity": f"Stok tinggal sedikit! {product_title} diskon gede!",
                "transformation": f"Dari skeptic jadi fanboy {product_title}!",
                "urgency": f"HARI INI AJA! {product_title} diskon 50%!",
            },
            "lifestyle": {
                "problem": f"Selama ini salah pakai produk...直到 nemu {product_title}",
                "curiosity": f"Daily routine gue sekarang beda banget karena {product_title}",
                "social_proof": f"Temennya pada iri lihat results {product_title} gue",
                "comparison": f"Upgrade from {product_title} lama ke baru, beda jauh!",
                "testimonial": f"3 bulan pakai {product_title}, ini honest review",
                "scarcity": f"Flash sale {product_title} cuma 2 jam lagi!",
                "transformation": "Morning routine gue sekarang简单 dan efektif",
                "urgency": f"Last chance! {product_title} diskon ends tonight",
            },
            "minimal": {
                "problem": f"{product_title} — the one product I actually use",
                "curiosity": f"What makes {product_title} different? Let me show you",
                "social_proof": f"Everyone's been asking about my {product_title}",
                "comparison": f"{product_title}: worth the hype or not?",
                "testimonial": f"My honest {product_title} review after 30 days",
                "scarcity": f"{product_title} is almost sold out everywhere",
                "transformation": f"Before vs After using {product_title}",
                "urgency": f"Don't sleep on {product_title} — sale ends soon",
            },
            "humor": {
                "problem": f"POV: kamu belum tau {product_title} exist",
                "curiosity": f"Kenapa sih semua orang ribet soal {product_title}?",
                "social_proof": f"Gue: *pakai {product_title}*\nTeman: WAH BISA?",
                "comparison": f"Expectation vs Reality {product_title} (plot twist!)",
                "testimonial": f"Cerita gua sama {product_title}... dramatic banget",
                "scarcity": f"Ketahuan beli {product_title} lagi... sorry not sorry",
                "transformation": f"Gua sebelum vs sesudah {product_title} 😂",
                "urgency": f"BUKAN clickbait! {product_title} beneran diskon!",
            },
        }
        return hooks.get(style, hooks["bold"]).get(angle, f"Review jujur {product_title}")

    def _generate_script(
        self, hook: str, style: str, duration_seconds: int, product_title: str
    ) -> str:
        """Generate script based on style and duration."""
        if duration_seconds <= 15:
            return (
                f"[HOOK - 3s] {hook}\n"
                f"[DEMO - 7s] *show product close-up*\n"
                f"[CTA - 5s] Link di bio! Beli sekarang!"
            )
        elif duration_seconds <= 30:
            return (
                f"[HOOK - 5s] {hook}\n"
                f"[PROBLEM - 5s] Masalah umum yang sering terjadi...\n"
                f"[SOLUTION - 10s] {product_title} solusinya! *demo product*\n"
                f"[SOCIAL PROOF - 5s] Udah banyak yang buktiin\n"
                f"[CTA - 5s] Link di bio! Diskon terbatas!"
            )
        else:
            return (
                f"[HOOK - 5s] {hook}\n"
                f"[PROBLEM - 8s] Jujur, gue juga dulu skeptis...\n"
                f"[INTRO - 5s] Tapi pas coba {product_title}...\n"
                f"[DEMO - 12s] *show product in action*\n"
                f"[RESULTS - 8s] Hasilnya gak pernah bohong\n"
                f"[SOCIAL PROOF - 5s] Banyak yang sudah buktiin\n"
                f"[CTA - 7s] Link di bio! Jangan sampe kehabisan!"
            )

    def _generate_thumbnail_concept(self, style: str, product_title: str) -> str:
        """Generate thumbnail concept based on style."""
        concepts = {
            "bold": f"BOLD TEXT: 'WOW!' + {product_title} close-up, high contrast red/yellow",
            "lifestyle": f"Person using {product_title} in natural setting, warm tones",
            "minimal": f"Clean white background, {product_title} centered, minimal text",
            "humor": f"Fun reaction face + {product_title} + emoji overlay, bright colors",
        }
        return concepts.get(style, concepts["bold"])


class VariantPublisher:
    """Publish variant batches across platforms with A/B tracking."""

    async def publish_batch(
        self,
        batch: VariantBatch,
        platforms: Optional[list[str]] = None,
    ) -> dict:
        """Publish all variants in a batch.

        Returns tracking dict with variant IDs → platform post IDs.
        """
        if platforms is None:
            platforms = ["tiktok"]

        tracking = {}
        for variant in batch.variants:
            for platform in platforms:
                post_id = f"{platform}-{variant.variant_id}"
                tracking[variant.variant_id] = {
                    "platform": platform,
                    "post_id": post_id,
                    "status": "published",
                    "url": f"https://{platform}.com/@username/video/{post_id}",
                }
                variant.metrics["post_id"] = post_id

        batch.status = "published"
        return tracking


class VariantOptimizer:
    """Optimize based on A/B test results."""

    async def analyze_batch(self, batch: VariantBatch) -> dict:
        """Analyze variant performance and recommend winner."""
        if not batch.variants:
            return {"error": "No variants to analyze"}

        best_variant = max(
            batch.variants,
            key=lambda v: v.metrics.get("ctr", 0) + v.metrics.get("conversion_rate", 0),
        )

        analysis = {
            "batch_id": batch.batch_id,
            "total_variants": len(batch.variants),
            "best_variant": {
                "id": best_variant.variant_id,
                "label": best_variant.label,
                "style": best_variant.style,
                "hook": best_variant.hook,
                "metrics": best_variant.metrics,
            },
            "recommendations": self._generate_recommendations(batch),
            "scale_budget": self._suggest_budget_scaling(batch),
        }
        return analysis

    def _generate_recommendations(self, batch: VariantBatch) -> list[str]:
        """Generate optimization recommendations."""
        recs = []
        for v in batch.variants:
            ctr = v.metrics.get("ctr", 0)
            if ctr < 0.02:
                recs.append(f"Variant {v.label} ({v.style}): Low CTR ({ctr:.1%}). Consider new hook.")
            elif ctr > 0.05:
                recs.append(f"Variant {v.label} ({v.style}): High CTR ({ctr:.1%}). Scale budget!")
        return recs

    def _suggest_budget_scaling(self, batch: VariantBatch) -> dict:
        """Suggest budget allocation based on performance."""
        total = sum(v.metrics.get("spend", 0) for v in batch.variants) or 100
        allocation = {}
        for v in batch.variants:
            score = v.metrics.get("ctr", 0.01) * 0.6 + v.metrics.get("conversion_rate", 0.01) * 0.4
            allocation[v.variant_id] = {
                "label": v.label,
                "style": v.style,
                "budget_pct": round(score / max(sum(
                    vv.metrics.get("ctr", 0.01) * 0.6 + vv.metrics.get("conversion_rate", 0.01) * 0.4
                    for vv in batch.variants
                ), 0.01) * 100, 1),
            }
        return allocation
