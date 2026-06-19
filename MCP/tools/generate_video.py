"""Generate videos via Wan 2.2 / Hunyuan."""

from __future__ import annotations

import random
import uuid
from MCP.schemas import GenerateVideoInput, GenerateVideoOutput


async def generate_video(input_data: GenerateVideoInput) -> GenerateVideoOutput:
    """Generate a video via Wan 2.2 or Hunyuan Video (simulated)."""
    return GenerateVideoOutput(
        video_url=f"https://storage.titan-aio.local/videos/{uuid.uuid4().hex[:12]}.mp4",
        model_used=input_data.model,
        duration_seconds=input_data.duration_seconds,
    )
