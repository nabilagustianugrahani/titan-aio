"""Generate thumbnail concepts."""

from __future__ import annotations

import random
from MCP.schemas import GenerateThumbnailInput, GenerateThumbnailOutput, ThumbnailConcept


_CONCEPTS = [
    {"concept": "Bold Text + Product", "description": "Product shot with bold text overlay: 'HARGA TERJANGKAU!'", "style": "bold"},
    {"concept": "Before After", "description": "Split screen showing before vs after using the product", "style": "comparison"},
    {"concept": "Lifestyle", "description": "Product in use in natural setting with warm lighting", "style": "lifestyle"},
    {"concept": "Minimal", "description": "Clean white background, product centered, simple text", "style": "minimal"},
]


async def generate_thumbnail(input_data: GenerateThumbnailInput) -> GenerateThumbnailOutput:
    """Generate thumbnail concept for product."""
    selected = [c for c in _CONCEPTS if c["style"] == input_data.style]
    if not selected:
        selected = _CONCEPTS

    concept = random.choice(selected)
    text_overlay = f"Rp {random.randint(10, 500)}rb" if random.random() > 0.5 else "DISKON 50%!"
    return GenerateThumbnailOutput(
        product_id=input_data.product_id,
        thumbnail=ThumbnailConcept(
            concept=concept["concept"],
            description=concept["description"],
            text_overlay=text_overlay,
            style=concept["style"],
        ),
    )
