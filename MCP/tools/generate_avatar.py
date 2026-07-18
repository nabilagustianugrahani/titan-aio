"""Generate AI avatars."""

from __future__ import annotations

import uuid

from MCP.schemas import GenerateAvatarInput, GenerateAvatarOutput


async def generate_avatar(input_data: GenerateAvatarInput) -> GenerateAvatarOutput:
    """Generate an AI spokesperson avatar (simulated)."""
    avatar_id = str(uuid.uuid4())
    return GenerateAvatarOutput(
        avatar_id=avatar_id,
        image_url=f"https://storage.titan-aio.local/avatars/{avatar_id}.png",
        persona={
            "name": input_data.persona_name,
            "style": input_data.style,
            "expression": input_data.expression,
        },
    )
