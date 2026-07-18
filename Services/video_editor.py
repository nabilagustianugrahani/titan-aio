"""TITAN AIO — Video Editor
FFmpeg-based: captions, voiceover, product overlay, CTA.
Runs anywhere FFmpeg is installed.
"""

from __future__ import annotations

import os
import subprocess
import textwrap
import uuid
from pathlib import Path


class VideoEditor:
    """Generate affiliate UGC videos with FFmpeg.

    Features:
    - Hook text overlay (attention-grabbing first 3 seconds)
    - Product image inset
    - Testimonial / social proof overlay
    - CTA button at end
    - Optional TTS voiceover (via edge-tts or gTTS)
    """

    def __init__(self, output_dir: str = "/tmp/titan-videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_ugc_video(
        self,
        hook: str,
        script_text: str,
        cta: str = "",
        product_image: str | None = None,
        bg_video: str | None = None,
        duration: int = 30,
        output_name: str | None = None,
    ) -> dict:
        """Generate a complete UGC-style short video.

        Args:
            hook: Attention hook (first 3 seconds)
            script_text: Full script content
            cta: Call to action at end
            product_image: Path/URL to product image overlay
            bg_video: Background video (or None = generate colored background)
            duration: Target duration in seconds
            output_name: Custom output filename

        Returns:
            dict with path, duration, size

        """
        output = output_name or f"ugc-{uuid.uuid4().hex[:12]}.mp4"
        output_path = self.output_dir / output

        # If no bg video, create a gradient background
        bg_path = bg_video or self._create_gradient_bg(duration, output_path.with_suffix(".bg.mp4"))

        # Build complex FFmpeg filter graph
        filters = self._build_ugc_filters(
            hook=hook,
            script=script_text,
            cta=cta,
            bg_path=bg_path,
            product_image=product_image,
            duration=duration,
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", bg_path,
            "-vf", filters,
            "-c:a", "copy" if not bg_video else "aac",
            "-t", str(duration),
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return {"error": result.stderr[:500], "cmd": " ".join(cmd[:6])}

            size = output_path.stat().st_size if output_path.exists() else 0
            return {
                "path": str(output_path),
                "duration": duration,
                "size_bytes": size,
                "size_mb": round(size / 1_048_576, 2),
                "url": f"https://storage.titan-aio.local/videos/{output}",
            }
        except FileNotFoundError:
            return {"error": "FFmpeg not installed. Install with: apt install ffmpeg"}
        except subprocess.TimeoutExpired:
            return {"error": "Video generation timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _build_ugc_filters(
        self,
        hook: str,
        script: str,
        cta: str,
        bg_path: str,
        product_image: str | None = None,
        duration: int = 30,
    ) -> str:
        """Build FFmpeg drawtext filter graph for UGC video.

        Creates:
        - Hook in large bold text (0-4s)
        - Script scroll (4-25s)
        - Product image overlay (4-25s)
        - CTA button (25-30s)
        """
        filters = []

        # 1. Hook overlay — large text centered, first 4 seconds
        hook_safe = self._escape_ffmpeg(hook[:80])
        filters.append(
            f"drawtext=text='{hook_safe}'"
            f":fontsize=36:fontcolor=white:box=1:boxcolor=black@0.6"
            f":boxborderw=20:x=(w-text_w)/2:y=(h-text_h)/2"
            f":enable='between(t,0,3.5)'"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        )

        # 2. Script body — scrolling text
        script_safe = self._escape_ffmpeg(script[:200])
        lines = textwrap.wrap(script_safe, width=35)
        script_text_escaped = "\\n".join(lines[:6])
        filters.append(
            f"drawtext=text='{script_text_escaped}'"
            f":fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5"
            f":boxborderw=15:x=30:y=h-120"
            f":enable='between(t,3.5,27)'"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )

        # 3. Product image overlay
        if product_image and os.path.exists(product_image):
            # Overlay product image in top-right corner
            filters.append(
                f"movie={self._escape_ffmpeg(product_image)}"
                f":loop=0:setpts=PTS-STARTPTS"
                f"[product];[in][product]"
                f"overlay=W-w-20:20:enable='between(t,3.5,28)'[out]",
            )

        # 4. CTA overlay — bottom centered, last 5 seconds
        if cta:
            cta_safe = self._escape_ffmpeg(cta[:60])
            filters.append(
                f"drawtext=text='{cta_safe}'"
                f":fontsize=42:fontcolor=#FFD700:box=1:boxcolor=black@0.7"
                f":boxborderw=25:x=(w-text_w)/2:y=(h-text_h)/2"
                f":enable='between(t,25,{duration})'"
                f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            )

        return ",".join(filters)

    def _create_gradient_bg(self, duration: int, output_path: str) -> str:
        """Create a gradient background video with FFmpeg."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=#1a1a2e:s=1080x1920:d={duration}:r=30",
            "-vf",
            "drawbox=x=0:y=0:w=1080:h=1920:color=#16213e@0.5:t=fill,"
            "drawtext=text='':fontsize=10",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return output_path

    @staticmethod
    def add_voiceover(video_path: str, text: str, lang: str = "id") -> dict:
        """Generate TTS voiceover using edge-tts or gTTS and overlay on video."""
        try:
            import edge_tts
        except ImportError:
            return {"error": "edge-tts not installed. pip install edge-tts"}

        audio_path = video_path.replace(".mp4", ".aac")
        output_path = video_path.replace(".mp4", "_voiced.mp4")

        async def _tts():
            communicate = edge_tts.Communicate(text, "id-ID-ArdiNeural" if lang == "id" else "en-US-JennyNeural")
            await communicate.save(audio_path)

        import asyncio
        asyncio.run(_tts())

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {"path": output_path}

    @staticmethod
    def _escape_ffmpeg(text: str) -> str:
        """Escape text for FFmpeg drawtext filter."""
        return (text
                .replace("'", "'\\\\''")
                .replace(":", "\\\\:")
                .replace("'", "\\\\'")
                .replace("%", "\\\\%")
                .replace("\n", " ")
                .replace('"', '"'))

    @staticmethod
    def check_ffmpeg() -> bool:
        """Check if FFmpeg is installed."""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
