"""Video Agent — generates short-form videos via Kaggle worker dispatch."""

from __future__ import annotations

import logging
from typing import Any

from Services.agents.base import BaseAgent, AgentContext
from Services.video.multi_shot import ShotPlanner

logger = logging.getLogger("titan.video")

# Model choices
_MODELS = {
    "wan-2-2": {"name": "Wan 2.2 T2V", "max_duration": 30, "quality": "standard"},
    "hunyuan": {"name": "Hunyuan Video", "max_duration": 15, "quality": "high"},
}


class VideoAgent(BaseAgent):
    """Generates short-form videos from scripts using shot planning + worker dispatch."""

    async def execute(
        self,
        ctx: AgentContext,
        script: str = "",
        model: str = "wan-2-2",
        duration_seconds: int = 30,
        hook: str = "",
        **kwargs: Any,
    ) -> dict:
        model_info = _MODELS.get(model, _MODELS["wan-2-2"])

        # Clamp duration to model limits
        duration = min(duration_seconds, model_info["max_duration"])

        # ── Plan shots from script ──
        shots = ShotPlanner.plan(script=script, hook=hook, duration=duration)

        # ── Build generation request ──
        # In production this dispatches to Kaggle video-worker.
        # For now, build the request payload that the worker would consume.
        generation_request = {
            "script": script,
            "hook": hook,
            "model": model,
            "model_name": model_info["name"],
            "duration_seconds": duration,
            "num_frames": duration * 8,  # ~8 fps
            "width": 512,
            "height": 512,
            "guidance_scale": 5.0,
            "num_inference_steps": 25,
            "shots": shots,
            "total_shots": len(shots),
        }

        # ── Estimate processing time ──
        # Wan 2.2 on T4: ~2s/frame → duration * 8 frames = est time
        est_seconds = duration * 8 * 2 if model == "wan-2-2" else duration * 8 * 5

        return {
            "video_id": "",  # Populated by worker after generation
            "url": "",  # Populated by worker after S3 upload
            "model_used": model,
            "model_name": model_info["name"],
            "duration_seconds": duration,
            "format": "9:16",
            "generation_request": generation_request,
            "shots_planned": len(shots),
            "processing_time_estimate_seconds": est_seconds,
            "quality_tier": model_info["quality"],
        }
