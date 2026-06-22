"""Content Remix Engine — MCP tool for transforming content across platforms."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RemixContentInput(BaseModel):
    """Input for content remixing."""
    content: str = Field(description="Source content to remix (script, hook, or video concept)")
    content_type: str = Field(default="script", description="Type of content: script, hook, video_concept")
    niche: str = Field(default="general", description="Content niche for hashtag generation")
    target_platforms: list[str] = Field(
        default=["tiktok", "instagram", "youtube", "twitter", "facebook"],
        description="Platforms to generate variants for",
    )


class RemixContentOutput(BaseModel):
    """Output from content remixing."""
    source_content: str
    variants: list[dict]
    total_variants: int
    platform_coverage: list[str]
    best_variant: int = 0
    best_variant_preview: str = ""


async def remix_content(
    content: str,
    content_type: str = "script",
    niche: str = "general",
    target_platforms: list[str] | None = None,
) -> RemixContentOutput:
    """Transform one content piece into multiple platform-specific formats.

    Generates adapted content for TikTok, Instagram, YouTube, Twitter,
    Facebook, Blog, Newsletter, and Podcast. Each variant is scored
    for viral potential and includes platform-appropriate hashtags and CTAs.
    """
    from Services.content.remixer import ContentRemixer

    engine = ContentRemixer()
    package = engine.remix(
        content=content,
        content_type=content_type,
        niche=niche,
        target_platforms=target_platforms,
    )

    variants = []
    for v in package.variants:
        variants.append({
            "platform": v.platform,
            "format": v.format,
            "content": v.content,
            "char_count": v.char_count,
            "viral_score": v.viral_score,
            "hashtags": v.hashtags,
            "cta": v.cta,
            "metadata": v.metadata,
        })

    best_preview = ""
    if 0 <= package.best_variant < len(package.variants):
        best_preview = package.variants[package.best_variant].content[:200]

    return RemixContentOutput(
        source_content=package.source_content,
        variants=variants,
        total_variants=package.total_variants,
        platform_coverage=package.platform_coverage,
        best_variant=package.best_variant,
        best_variant_preview=best_preview,
    )
