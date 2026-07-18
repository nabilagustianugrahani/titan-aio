"""ViMax Adapter — multi-shot video generation.

ViMax is an agentic video generation framework (github.com/HKUDS/ViMax).
It chains multiple AI-generated shots into coherent short films with
storyboarding, character consistency, and voice sync.

Usage:
    from Services.video.vimax_adapter import ViMaxEngine
    engine = ViMaxEngine()
    result = await engine.generate(script="...", style="ugc")
"""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path


class ViMaxEngine:
    """Multi-shot video engine using ViMax.

    Falls back to single-shot generation if ViMax is not installed.
    """

    VIMAX_DIR = Path("/opt/ViMax")

    def __init__(self, use_vimax: bool = False):
        self.use_vimax = use_vimax and self.VIMAX_DIR.exists()
        self.output_dir = Path("/tmp/titan-videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        script: str,
        hook: str = "",
        style: str = "ugc",
        duration: int = 30,
    ) -> dict:
        """Generate a multi-shot video from script.

        If ViMax is available, uses multi-shot pipeline.
        Otherwise falls back to single-shot Wan 2.2 via video_worker.
        """
        if self.use_vimax:
            return await self._generate_vimax(script, hook, style, duration)
        return await self._fallback(script, hook, duration)

    async def _generate_vimax(self, script: str, hook: str, style: str, duration: int) -> dict:
        """Generate using ViMax multi-shot pipeline."""
        output_name = f"vimax-{uuid.uuid4().hex[:12]}"
        output_path = self.output_dir / f"{output_name}.mp4"

        # Write input config
        config = {
            "idea": hook or script[:100],
            "script": script,
            "style": style,
            "duration": duration,
            "output": str(output_path),
            "shots": self._parse_shots(script),
        }
        config_path = self.output_dir / f"{output_name}.json"
        config_path.write_text(json.dumps(config, indent=2))

        try:
            # Call ViMax CLI (conceptual — actual command depends on ViMax version)
            result = subprocess.run(
                ["python", "-m", "vimax.pipeline", "--config", str(config_path)],
                cwd=str(self.VIMAX_DIR),
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode == 0 and output_path.exists():
                return {
                    "path": str(output_path),
                    "duration": duration,
                    "model": "vimax",
                    "multi_shot": True,
                    "shots": len(config["shots"]),
                }
            return {"error": result.stderr[:500], "model": "vimax"}
        except FileNotFoundError:
            return {"error": "ViMax not installed", "model": "vimax"}
        except subprocess.TimeoutExpired:
            return {"error": "ViMax timed out", "model": "vimax"}

    async def _fallback(self, script: str, hook: str, duration: int) -> dict:
        """Fallback to DashScope Wan 2.7 I2V (cloud, no GPU needed)."""
        try:
            from Services.generation.dashscope_video import generate_video
            # Generate a placeholder product image for I2V
            image_url = await self._generate_placeholder_image(hook or script[:100])
            video_url = await generate_video(
                image_url=image_url,
                prompt=script or hook,
                duration=min(duration, 15),
            )
            if video_url:
                return {
                    "path": video_url,
                    "duration": duration,
                    "model": "wan2.7-i2v",
                    "multi_shot": False,
                }
            return {"error": "DashScope returned no video URL", "model": "wan2.7-i2v"}
        except Exception as e:
            return {"error": str(e), "model": "wan2.7-i2v"}

    async def _generate_placeholder_image(self, prompt: str) -> str:
        """Generate a placeholder product image for I2V input."""
        try:
            from Services.generation.dashscope_image import generate_image
            url = await generate_image(prompt=prompt)
            if url:
                return url
        except Exception:
            pass
        # Fallback: use a solid color placeholder hosted image
        return "https://placehold.co/1280x720/1a1a2e/ffffff?text=Product+Review"

    @staticmethod
    def _parse_shots(script: str) -> list[dict]:
        """Parse script into shots (scene breakdown)."""
        scenes = script.split("\n\n")
        shots = []
        for i, scene in enumerate(scenes[:8]):  # max 8 shots
            shots.append({
                "shot_id": i + 1,
                "description": scene.strip()[:100],
                "style": "closeup" if i == 0 else "wide" if i == len(scenes) - 1 else "medium",
                "duration_sec": 4,
            })
        return shots if shots else [{"shot_id": 1, "description": script[:100], "style": "medium", "duration_sec": 4}]

    @staticmethod
    def is_available() -> bool:
        """Check if ViMax is installed."""
        return ViMaxEngine.VIMAX_DIR.exists()
