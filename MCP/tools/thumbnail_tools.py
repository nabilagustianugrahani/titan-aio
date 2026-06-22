"""MCP tools for Auto Thumbnail Generator."""

from __future__ import annotations

from MCP.server import mcp
from Services.thumbnail.auto_generator import ThumbnailInput, generate_thumbnails


@mcp.tool()
async def generate_thumbnails(
    product_name: str,
    niche: str = "general",
    content_type: str = "product_review",
    num_variants: int = 3,
) -> dict:
    """Generate AI-optimized thumbnail variants with CTR predictions and viral scoring.

    Args:
        product_name: Name of the product
        niche: Product niche (electronics/fashion/beauty/food/general)
        content_type: Type of content (product_review/tutorial/comparison)
        num_variants: Number of thumbnail variants to generate (1-5)
    """
    input_data = ThumbnailInput(
        product_name=product_name,
        niche=niche,
        content_type=content_type,
        num_variants=num_variants,
    )
    result = await generate_thumbnails(input_data)
    return result.model_dump()
