"""Generate product images via FLUX."""

from __future__ import annotations

import random
from MCP.schemas import GenerateImageInput, GenerateImageOutput


async def generate_image(input_data: GenerateImageInput) -> GenerateImageOutput:
    """Generate an image via FLUX model (simulated)."""
    return GenerateImageOutput(
        image_url=f"https://storage.titan-aio.local/images/{random.randint(10000, 99999)}.png",
        model_used=input_data.model,
        seed=random.randint(0, 2**31),
    )
