"""Create complete affiliate package from a product URL."""

from __future__ import annotations

import asyncio
import uuid

from MCP.schemas import (
    CreateAffiliatePackageInput,
    AffiliatePackageOutput,
    AnalyzeProductInput,
    AnalyzeReviewsInput,
    AnalyzeCompetitorsInput,
    GenerateOfferInput,
    GenerateHooksInput,
    GenerateScriptInput,
    GenerateThumbnailInput,
    GenerateImageInput,
    GenerateVideoInput,
    GenerateAvatarInput,
)
from MCP.tools.analyze_product import analyze_product
from MCP.tools.analyze_reviews import analyze_reviews
from MCP.tools.analyze_competitors import analyze_competitors
from MCP.tools.generate_offer import generate_offer
from MCP.tools.generate_hooks import generate_hooks
from MCP.tools.generate_script import generate_script
from MCP.tools.generate_thumbnail import generate_thumbnail
from MCP.tools.generate_image import generate_image
from MCP.tools.generate_video import generate_video
from MCP.tools.generate_avatar import generate_avatar


async def create_affiliate_package(
    input_data: CreateAffiliatePackageInput,
) -> AffiliatePackageOutput:
    """Create a full affiliate package from a product URL."""
    campaign_id = str(uuid.uuid4())

    product = await analyze_product(AnalyzeProductInput(url=input_data.url))
    reviews = await analyze_reviews(
        AnalyzeReviewsInput(product_id=product.product_id)
    )
    competitors = await analyze_competitors(
        AnalyzeCompetitorsInput(category=product.category or "umum")
    )
    offer = await generate_offer(
        GenerateOfferInput(
            product_id=product.product_id,
            product_analysis=product,
            review_analysis=reviews,
            competitor_analysis=competitors,
        )
    )
    hooks = await generate_hooks(
        GenerateHooksInput(
            product_id=product.product_id,
            offer_strategy=offer,
            count=10,
        )
    )
    scripts = await generate_script(
        GenerateScriptInput(
            product_id=product.product_id,
            hooks=hooks.hooks,
            offer_strategy=offer,
            count=10,
        )
    )
    thumbnail = await generate_thumbnail(
        GenerateThumbnailInput(product_id=product.product_id, style="bold")
    )

    result = AffiliatePackageOutput(
        product=product,
        review_summary=reviews,
        competitor_analysis=competitors,
        offer_strategy=offer,
        hooks=hooks,
        scripts=scripts,
        thumbnail=thumbnail,
        image=None,
        campaign_id=campaign_id,
    )

    # Heavy generation (image/video) — fire-and-forget, non-blocking
    if input_data.include_image:
        try:
            image = await asyncio.wait_for(
                generate_image(GenerateImageInput(prompt=f"Product image for {product.title}")),
                timeout=10,
            )
            result.image = image
        except asyncio.TimeoutError:
            print("⚠️ Image gen timed out — using placeholder")

    if input_data.include_video and scripts.scripts:
        try:
            video = await asyncio.wait_for(
                generate_video(GenerateVideoInput(script=scripts.scripts[0].full_script)),
                timeout=15,
            )
            result.video = video
        except asyncio.TimeoutError:
            print("⚠️ Video gen timed out — using placeholder")

    if input_data.include_avatar:
        try:
            avatar = await asyncio.wait_for(
                generate_avatar(GenerateAvatarInput(persona_name="AI Spokesperson")),
                timeout=10,
            )
            result.avatar = avatar
        except asyncio.TimeoutError:
            print("⚠️ Avatar gen timed out — using placeholder")

    return result
