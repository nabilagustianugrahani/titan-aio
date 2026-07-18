"""TITAN AIO — HTML Video Generator (HyperFrames-inspired).

Generates promotional videos from HTML+CSS templates.
Renders via Playwright headless browser → FFmpeg encoding.

Pattern inspired by HeyGen HyperFrames: write HTML, render video.

Usage:
    from Services.video.html_video import HTMLVideoGenerator
    gen = HTMLVideoGenerator()
    result = await gen.generate(product_name="Skincare Serum", price=165000)

    # Returns HTML preview string if ffmpeg/playwright unavailable
    html = await gen.render_preview(product_name="Skincare Serum", price=165000)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# ── Default content generator ──────────────────────────────────

REASONS_POOL = [
    "Kualitas Premium — Bahan terbaik di kelasnya",
    "Harga Terjangkau — Setara brand mahal dengan harga hemat",
    "Viral di TikTok — Udah dipakai 10.000+ orang",
    "Garansi 100% Uang Kembali — Bebas resiko",
    "Gratis Ongkir — Se-Indonesia",
    "Sudah BPOM / SNI — Aman dan terpercaya",
    "Cocok untuk Pemula — Mudah digunakan",
    "Hasil Maksimal — Terbukti secara klinis",
]

HOOK_DESCRIPTIONS = {
    "curiosity": "Kenapa produk ini viral? Yuk kita bedah!",
    "testimonial": "Udah 5 produk dicoba, ini yang paling WORTH IT!",
    "problem": "Masalah kamu bisa selesai dengan produk ini",
    "social_proof": "10.000+ orang udah buktikan sendiri!",
    "scarcity": "STOK TERBATAS! Buruan sebelum habis!",
    "comparison": "Bandingin sama yang lain, ini jauh lebih unggul!",
}


class HTMLVideoGenerator:
    """Generate promotional videos from HTML templates."""

    def __init__(self, output_dir: str = "/tmp/titan-video-html"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg = shutil.which("ffmpeg")
        self._playwright = False
        try:
            from playwright.async_api import async_playwright
            self._playwright_import = async_playwright
            self._playwright = True
        except ImportError:
            pass

    def is_available(self) -> dict:
        """Check if video rendering dependencies are available."""
        return {
            "ffmpeg": self._ffmpeg is not None,
            "playwright": self._playwright,
            "html_preview": True,  # Always available
        }

    async def _generate_content(
        self,
        product_name: str,
        price: float = 0,
        category: str = "umum",
        hook_text: str = "",
        hook_type: str = "curiosity",
        rating: float = 4.5,
        sales: int = 5000,
        num_reasons: int = 4,
    ) -> dict:
        """Generate content for the video template."""

        # Format price
        price_int = int(price)
        price_formatted = f"{price_int:,}".replace(",", ".")
        final_price = f"Rp {price_formatted}"
        original_price = f"Rp {price_int * 3 // 2:,}".replace(",", ".")

        # Generate hook if not provided
        if not hook_text:
            hook_text = f"Cuma Rp {price_formatted}? Kualitasnya BIKIN MELOTOT!"

        # Pick reasons
        reasons = REASONS_POOL[:num_reasons]

        # Short name
        name_short = product_name[:30] if len(product_name) > 30 else product_name

        hook_desc = HOOK_DESCRIPTIONS.get(hook_type, HOOK_DESCRIPTIONS["curiosity"])

        return {
            "product_name": product_name,
            "product_name_short": name_short,
            "price": price_formatted,
            "final_price": final_price,
            "original_price": original_price,
            "tagline": f"Cuma {final_price} — Kualitas setara brand mahal!",
            "hook": hook_text,
            "hook_description": hook_desc,
            "rating": f"{rating:.1f}",
            "sales": f"{sales:,}".replace(",", "."),
            "reasons": reasons,
        }

    async def render_html(
        self,
        template_name: str = "product_promo.html",
        **content_kwargs,
    ) -> str:
        """Render the HTML template with content.

        Returns the full HTML string.
        """
        template_path = TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        content = await self._generate_content(**content_kwargs)

        # Simple string replacement templating (no Jinja2 dependency)
        html = template_path.read_text(encoding="utf-8")

        for key, value in content.items():
            placeholder = "{{ " + key + " }}"
            if isinstance(value, list):
                # Render bullet list
                bullets = "\n".join(
                    f'<div class="bullet-item">{item}</div>'
                    for item in value
                )
                html = html.replace(
                    "{% for reason in reasons %}\n    <div class=\"bullet-item\">{{ reason }}</div>\n    {% endfor %}",
                    bullets,
                )
            elif isinstance(value, str):
                html = html.replace(placeholder, value)

        return html

    async def render_preview(
        self,
        template_name: str = "product_promo.html",
        output_name: str = "",
        **content_kwargs,
    ) -> str:
        """Render and save the HTML preview.

        Returns the path to the saved HTML file.
        """
        html = await self.render_html(template_name, **content_kwargs)

        name = content_kwargs.get("product_name", "product")
        slug = name.lower().replace(" ", "-")[:30]
        output_name = output_name or f"{slug}-preview.html"
        output_path = self.output_dir / output_name

        output_path.write_text(html, encoding="utf-8")
        logger.info(f"📄 HTML preview saved: {output_path}")
        return str(output_path)

    async def render_video(
        self,
        template_name: str = "product_promo.html",
        output_name: str = "",
        fps: int = 30,
        **content_kwargs,
    ) -> dict:
        """Render the template and encode to MP4 video.

        Requires ffmpeg and playwright installed.
        Returns dict with status and path/error.
        """
        deps = self.is_available()
        if not deps["ffmpeg"]:
            return {"status": "error", "error": "ffmpeg not installed"}
        if not deps["playwright"]:
            return {"status": "error", "error": "playwright not installed"}

        html = await self.render_html(template_name, **content_kwargs)

        name = content_kwargs.get("product_name", "product")
        slug = name.lower().replace(" ", "-")[:30]
        output_name = output_name or f"{slug}-promo.mp4"
        output_path = self.output_dir / output_name

        html_path = self.output_dir / f"{slug}-temp.html"
        html_path.write_text(html, encoding="utf-8")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    viewport={"width": 1080, "height": 1920},
                    device_scale_factor=1,
                )
                await page.goto(f"file://{html_path}", wait_until="networkidle")

                # Get each slide's duration from data-duration attributes
                durations = await page.evaluate("""
                    Array.from(document.querySelectorAll('.slide')).map(el => ({
                        duration: parseInt(el.dataset.duration) || 5,
                    }))
                """)

                sum(d["duration"] * fps for d in durations)
                temp_dir = Path(tempfile.mkdtemp())

                # Capture each slide as frames
                frame_idx = 0
                for i, slide_dur in enumerate(durations):
                    seconds = slide_dur["duration"]
                    total_slide_frames = seconds * fps

                    # Navigate to the slide
                    slides = await page.query_selector_all(".slide")
                    if slides and i < len(slides):
                        await slides[i].scroll_into_view_if_needed()

                    for f in range(total_slide_frames):
                        frame_path = temp_dir / f"frame_{frame_idx:06d}.png"
                        await page.screenshot(path=str(frame_path))
                        frame_idx += 1

                await browser.close()

            # Encode frames to video
            ffmpeg_cmd = [
                self._ffmpeg,
                "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%06d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",
                "-crf", "23",
                str(output_path),
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # Cleanup frames
            for f in temp_dir.glob("*.png"):
                f.unlink()
            temp_dir.rmdir()
            html_path.unlink()

            file_size = output_path.stat().st_size
            return {
                "status": "success",
                "path": str(output_path),
                "size_mb": round(file_size / (1024 * 1024), 1),
                "duration_seconds": sum(d["duration"] for d in durations),
                "slides": len(durations),
                "fps": fps,
            }

        except Exception as e:
            logger.error(f"Video rendering failed: {e}")
            return {"status": "error", "error": str(e)}

    async def batch_render(
        self,
        variants: list[dict],
        template_name: str = "product_promo.html",
    ) -> list[dict]:
        """Render multiple video variants for A/B testing.

        Each variant dict should have the same keys as generate() kwargs.
        """
        results = []
        for i, variant in enumerate(variants):
            name = variant.get("product_name", f"variant_{i}")
            result = await self.render_video(
                template_name=template_name,
                output_name=f"{name.lower().replace(' ', '-')[:30]}.mp4",
                **variant,
            )
            result["variant_index"] = i
            result["variant_name"] = name
            results.append(result)
        return results
