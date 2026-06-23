"""
Multi-Shot Video Engine — ViMax-inspired, zero external deps.

ViMax concept: split script → plan shots → generate per-shot → assemble.
We already have all the pieces (LLM, FLUX, Wan 2.7 I2V, FFmpeg).
This just orchestrates them in a multi-shot pipeline.

No API key needed beyond what we already have.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path


class ShotPlanner:
    """Plan a storyboard from a script — split into shots/scenes."""

    @staticmethod
    def plan(script: str, hook: str = "", duration: int = 30) -> list[dict]:
        """Split script into timed shots with visual direction.

        Returns list of shots: {id, description, visual_style, duration, hook}
        """
        # Split script into paragraphs (each = potential shot)
        paragraphs = [p.strip() for p in script.replace("\n", " ").split(".") if p.strip()]

        if not paragraphs:
            paragraphs = [script[:200]]

        # Distribute duration across shots
        num_shots = min(len(paragraphs), 6)
        shot_duration = max(duration // max(num_shots, 1), 3)

        styles = ["closeup", "product_shot", "demo", "testimonial", "lifestyle", "cta"]
        shots = []

        for i in range(num_shots):
            paragraph = paragraphs[i] if i < len(paragraphs) else paragraphs[-1]
            is_first = i == 0
            is_last = i == num_shots - 1

            shots.append({
                "id": i + 1,
                "hook": hook if is_first else "",
                "text": paragraph[:150],
                "visual_style": styles[i % len(styles)],
                "duration_sec": shot_duration if not is_last else max(shot_duration, 5),
                "is_intro": is_first,
                "is_cta": is_last,
                "camera": "close-up" if is_first else "wide" if is_last else "medium",
                "text_overlay": hook if is_first else paragraph[:80],
            })

        return shots


class MultiShotAssembler:
    """Assemble multiple shots into a final video using FFmpeg."""

    def __init__(self, output_dir: str = "/tmp/titan-videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble(self, shot_videos: list[str], output_name: str = "") -> dict:
        """Concatenate multiple video clips into one final video."""
        if not shot_videos:
            return {"error": "No shots to assemble"}

        output = output_name or f"multi-{uuid.uuid4().hex[:12]}.mp4"
        output_path = self.output_dir / output

        # Create concat file
        concat_path = self.output_dir / f"concat-{uuid.uuid4().hex[:8]}.txt"
        with open(concat_path, "w") as f:
            for v in shot_videos:
                if Path(v).exists():
                    f.write(f"file '{v}'\n")

        # Concatenate with FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            concat_path.unlink(missing_ok=True)

            if result.returncode == 0 and output_path.exists():
                return {
                    "path": str(output_path),
                    "shots": len(shot_videos),
                    "size_mb": round(output_path.stat().st_size / 1_048_576, 2),
                }
            return {"error": result.stderr[:300]}
        except Exception as e:
            concat_path.unlink(missing_ok=True)
            return {"error": str(e)}

    def add_transitions(self, video_path: str, transition: str = "fade") -> str:
        """Add transitions between shots."""
        output = video_path.replace(".mp4", f"-{transition}.mp4")
        if transition == "fade":
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", "fade=t=in:st=0:d=0.5,fade=t=out:st=28:d=1",
                "-c:a", "copy", output,
            ]
        elif transition == "crossfade":
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", "fade=t=in:st=0:d=1,fade=t=out:st=28:d=1.5",
                "-c:a", "copy", output,
            ]
        else:
            return video_path

        subprocess.run(cmd, capture_output=True, timeout=60)
        return output if Path(output).exists() else video_path
