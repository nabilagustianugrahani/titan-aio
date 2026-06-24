"""Scene Builder — drag-and-drop video scene composition (MVP).

Like Higgsfield's scene builder but simpler:
1. Add scenes (video clip + text overlay + voiceover)
2. Arrange order
3. Export final video via FFmpeg

Usage:
    from Services.ugc.scene_builder import SceneBuilder
    builder = SceneBuilder()
    scene = builder.add_scene(video_path="clip.mp4", text="Wow!", duration=5)
    builder.arrange(order=[0, 1, 2])
    result = await builder.export("final.mp4")
"""

from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import gradio as gr


@dataclass
class SceneClip:
    """Single scene in the sequence."""
    id: str
    video_path: str = ""
    text_overlay: str = ""
    voiceover_path: str = ""
    duration_sec: int = 5
    order: int = 0


@dataclass
class SceneExportResult:
    video_path: str = ""
    scene_count: int = 0
    total_duration: float = 0
    success: bool = False
    error: str = ""


class SceneBuilder:
    """Compose video scenes into a final video."""

    WORK_DIR = Path("/tmp/titan-scenes")
    OUTPUT_DIR = Path("/tmp/titan-scenes/output")

    def __init__(self):
        self.WORK_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.scenes: dict[str, SceneClip] = {}

    def add_scene(
        self,
        video_path: str = "",
        text_overlay: str = "",
        voiceover_path: str = "",
        duration_sec: int = 5,
    ) -> SceneClip:
        """Add a scene to the builder."""
        scene = SceneClip(
            id=uuid.uuid4().hex[:8],
            video_path=video_path,
            text_overlay=text_overlay,
            voiceover_path=voiceover_path,
            duration_sec=duration_sec,
            order=len(self.scenes),
        )
        self.scenes[scene.id] = scene
        return scene

    def remove_scene(self, scene_id: str):
        """Remove scene by ID."""
        self.scenes.pop(scene_id, None)

    def arrange(self, order: list[str]):
        """Reorder scenes by list of scene IDs."""
        for i, sid in enumerate(order):
            if sid in self.scenes:
                self.scenes[sid].order = i

    def get_scenes_sorted(self) -> list[SceneClip]:
        """Get scenes in display order."""
        return sorted(self.scenes.values(), key=lambda s: s.order)

    def list_scenes(self) -> list[dict]:
        """List scenes as dicts (for Gradio display)."""
        return [
            {
                "id": s.id,
                "text": s.text_overlay[:50],
                "duration": s.duration_sec,
                "order": s.order,
            }
            for s in self.get_scenes_sorted()
        ]

    async def export(self, output_name: str = "") -> SceneExportResult:
        """Export all scenes to final video using FFmpeg."""
        scenes = self.get_scenes_sorted()
        if not scenes:
            return SceneExportResult(
                scene_count=0, success=False, error="No scenes to export",
            )

        if not output_name:
            output_name = f"scene-{uuid.uuid4().hex[:8]}.mp4"

        output_path = str(self.OUTPUT_DIR / output_name)

        try:
            concat_file = self.WORK_DIR / "concat.txt"
            with open(concat_file, "w") as f:
                for scene in scenes:
                    if scene.video_path and Path(scene.video_path).exists():
                        f.write(f"file '{scene.video_path}'\n")
                        if scene.duration_sec:
                            f.write(f"duration {scene.duration_sec}\n")
                        if scene.text_overlay:
                            f.write(f"file '{scene.video_path}'\n")

            if not concat_file.stat().st_size:
                return SceneExportResult(
                    scene_count=len(scenes),
                    success=False, error="No valid video files",
                )

            # Use FFmpeg to concatenate
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return SceneExportResult(
                    scene_count=len(scenes),
                    success=False,
                    error=f"FFmpeg error: {result.stderr[:300]}",
                )

            total_duration = sum(s.duration_sec for s in scenes)
            return SceneExportResult(
                video_path=output_path,
                scene_count=len(scenes),
                total_duration=float(total_duration),
                success=True,
            )

        except subprocess.TimeoutExpired:
            return SceneExportResult(
                scene_count=len(scenes),
                success=False, error="FFmpeg timeout (300s)",
            )
        except Exception as e:
            return SceneExportResult(
                scene_count=len(scenes),
                success=False, error=str(e),
            )


# ── Gradio UI ─────────────────────────────────────────────────────

# If FFmpeg not available, create placeholder
_ffmpeg_available = False
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    _ffmpeg_available = True
except Exception:
    pass


def create_ui() -> gr.Blocks:
    """Create Gradio scene builder UI."""
    builder = SceneBuilder()

    with gr.Blocks(title="Scene Builder", theme=gr.themes.Soft()) as ui:
        gr.Markdown("# 🎬 Scene Builder")
        gr.Markdown("Compose video scenes like Higgsfield.ai — totally free")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Add Scene")
                scene_video = gr.Video(label="Video Clip (optional)")
                scene_text = gr.Textbox(label="Text Overlay", placeholder="Wow! Check this out...")
                scene_duration = gr.Slider(2, 30, value=5, step=1, label="Duration (sec)")
                add_btn = gr.Button("➕ Add Scene", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("### Timeline")
                scene_list = gr.JSON(label="Scenes")

                with gr.Row():
                    export_btn = gr.Button("🎬 Export Video", variant="primary", size="sm")
                    clear_btn = gr.Button("🗑️ Clear All", size="sm")

                output_video = gr.Video(label="Final Video")

        add_btn.click(
            fn=lambda v, t, d: (builder.add_scene(
                video_path=v if v else "",
                text_overlay=t,
                duration_sec=int(d),
            ).id, builder.list_scenes()),
            inputs=[scene_video, scene_text, scene_duration],
            outputs=[gr.Text(visible=False), scene_list],
        )

        clear_btn.click(
            fn=lambda: (builder.scenes.clear(), []),
            outputs=[scene_list],
        )

        async def do_export():
            result = await builder.export()
            return result.video_path if result.success else f"❌ {result.error}"

        export_btn.click(
            fn=do_export,
            outputs=output_video,
        )

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(server_port=7860)
