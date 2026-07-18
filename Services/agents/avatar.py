"""Avatar Agent -- creates AI spokesperson avatars."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from Database.models import AvatarProfile
from Services.agents.base import AgentContext, BaseAgent


class AvatarAgent(BaseAgent):
    """Generates and manages AI spokesperson avatars."""

    async def execute(
        self, ctx: AgentContext, name: str = "AI Spokesperson", **kwargs: Any,
    ) -> dict:
        result = await ctx.session.execute(
            select(AvatarProfile).where(AvatarProfile.name == name),
        )
        existing = result.scalar_one_or_none()

        if existing:
            return {
                "avatar_id": existing.id,
                "persona": existing.persona,
            }

        avatar_id = str(uuid.uuid4())
        new_avatar = AvatarProfile(
            id=avatar_id,
            name=name,
            persona={"name": name, "style": "realistic", "vibe": "trustworthy"},
            generation_params={"model": "flux-dev", "seed_consistency": True},
        )
        ctx.session.add(new_avatar)
        await ctx.session.commit()

        return {
            "avatar_id": avatar_id,
            "image_url": f"https://storage.titan-aio.local/avatars/{avatar_id}.png",
            "persona": new_avatar.persona,
        }
