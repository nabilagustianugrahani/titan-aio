"""Creative Agent -- plans visual direction."""

from __future__ import annotations

import random
from typing import Any

from MCP.schemas import GenerateThumbnailOutput, ThumbnailConcept
from Services.agents.base import BaseAgent, AgentContext

_CONCEPTS = [
    {"concept": "Bold Text + Product", "description": "Product shot with bold text overlay", "style": "bold"},
    {"concept": "Before After", "description": "Split screen comparison", "style": "comparison"},
    {"concept": "Lifestyle", "description": "Product in use", "style": "lifestyle"},
    {"concept": "Minimal", "description": "Clean white background", "style": "minimal"},
]


class CreativeAgent(BaseAgent):
    """Generates storyboards, thumbnails, and creative variations."""

    async def execute(
        self, ctx: AgentContext, product_id: str, **kwargs: Any
    ) -> dict:
        concept = random.choice(_CONCEPTS)
        thumbnail = GenerateThumbnailOutput(
            product_id=product_id,
            thumbnail=ThumbnailConcept(
                concept=concept["concept"],
                description=concept["description"],
                text_overlay="DISKON 50%!",
                style=concept["style"],
            ),
        )
        await ctx.session.commit()
        return {
            "thumbnail": thumbnail,
            "creative_variations": ["bold", "lifestyle", "minimal"],
        }
