"""MCP tools for auto-uploading to social media platforms."""
from __future__ import annotations

from typing import Any


def _get_uploader():
    from Services.publisher.auto_upload import AutoUploader
    return AutoUploader()


async def upload_to_social(
    platform: str,
    video_path: str,
    caption: str,
    hashtags: str = "",
) -> dict[str, Any]:
    """Upload a video to TikTok, Instagram, YouTube, etc."""
    hashtag_list = [h.strip() for h in hashtags.split() if h.strip()] if hashtags else None
    uploader = _get_uploader()
    return await uploader.upload(
        platform=platform,
        video_path=video_path,
        caption=caption,
        hashtags=hashtag_list,
    )


async def login_to_platform(platform: str) -> dict[str, Any]:
    """Open interactive browser for manual login (handles 2FA)."""
    uploader = _get_uploader()
    return await uploader.login(platform=platform)


async def prepare_and_upload(product_url: str, platform: str = "tiktok") -> dict[str, Any]:
    """One-shot: analyze product → generate campaign → upload to platform."""
    from MCP.tools.analyze_product import analyze_product
    from MCP.tools.generate_hooks import generate_hooks
    from MCP.tools.generate_script import generate_script
    from MCP.tools.create_affiliate_package import create_affiliate_package
    from MCP.schemas import (
        AnalyzeProductInput,
        GenerateHooksInput,
        GenerateScriptInput,
        CreateAffiliatePackageInput,
        GenerateOfferOutput,
        Hook,
    )

    # 1. Analyze product
    product = await analyze_product(AnalyzeProductInput(url=product_url))

    # 2. Generate offer strategy (use defaults)
    from MCP.tools.generate_offer import generate_offer
    from MCP.schemas import GenerateOfferInput
    offer = await generate_offer(GenerateOfferInput(
        product_id=product.product_id,
        product_analysis=product,
    ))

    # 3. Generate hooks
    hooks_result = await generate_hooks(GenerateHooksInput(
        product_id=product.product_id,
        offer_strategy=offer,
        count=5,
    ))

    # 4. Generate script from best hook
    best_hook = hooks_result.hooks[0] if hooks_result.hooks else Hook(
        hook="Check this out!", type="curiosity"
    )
    script_result = await generate_script(GenerateScriptInput(
        product_id=product.product_id,
        hooks=[best_hook],
        offer_strategy=offer,
        count=1,
    ))

    # 5. Upload
    script_text = script_result.scripts[0].script if script_result.scripts else product.title
    uploader = _get_uploader()
    upload_result = await uploader.upload(
        platform=platform,
        video_path="",  # will need a video file path
        caption=script_text[:500],
    )

    return {
        "product": {"title": product.title, "price": product.price},
        "hooks": [h.text for h in hooks_result.hooks[:3]],
        "script_preview": script_text[:200],
        "upload": upload_result,
    }
