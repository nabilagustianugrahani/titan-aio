"""MCP tools module."""

from __future__ import annotations

from pydantic import BaseModel, Field

from MCP.instance import mcp

# ── Input models (used internally for validation) ─────────────

class TranslateContentInput(BaseModel):
    """Input for multi-language translation."""

    content: str = Field(..., min_length=1, description="Content to translate/adapt")
    source_language: str = Field("id", description="Source language code (id, en, es, pt, ja, ko, th, vi, hi, ar, tr)")
    target_languages: str = Field(
        "en,es,pt,ja,ko",
        description="Comma-separated target language codes",
    )
    platform: str = Field("tiktok", description="Target platform (tiktok, instagram, facebook, twitter, youtube)")
    niche: str = Field("general", description="Content niche (general, electronics, fashion, beauty, food)")
    optimize_emojis: bool = Field(True, description="Culturally optimize emoji usage")


class TranslateSingleInput(BaseModel):
    """Input for single-language translation."""

    content: str = Field(..., min_length=1, description="Content to translate/adapt")
    source_language: str = Field("id", description="Source language code")
    target_language: str = Field("en", description="Target language code")
    platform: str = Field("tiktok", description="Target platform")
    niche: str = Field("general", description="Content niche")


class LocalizeCTAInput(BaseModel):
    """Input for CTA localization."""

    cta_text: str = Field(..., description="CTA text to localize")
    source_language: str = Field("id", description="Source language code")
    target_language: str = Field("en", description="Target language code")
    platform: str = Field("tiktok", description="Target platform")


class HashtagPackInput(BaseModel):
    """Input for getting trending hashtags per language."""

    language: str = Field("en", description="Language code")
    niche: str = Field("general", description="Content niche")
    count: int = Field(5, ge=1, le=10, description="Number of hashtags")


class PlatformLimitInput(BaseModel):
    """Input for getting platform character limits."""

    platform: str = Field("tiktok", description="Platform name")
    language: str = Field("", description="Language code (empty = all languages)")


# ── MCP Tool Functions ───────────────────────────────────────

@mcp.tool()
async def translate_content(
    content: str,
    source_language: str = "id",
    target_languages: str = "en,es,pt,ja,ko",
    platform: str = "tiktok",
    niche: str = "general",
    optimize_emojis: bool = True,
) -> dict:
    """Translate and culturally adapt content to multiple languages with platform-specific formatting.

    Args:
        content: Source content to translate (Indonesian recommended as source).
        source_language: Source language code. Options: id, en, es, pt, ja, ko, th, vi, hi, ar, tr
        target_languages: Comma-separated target language codes. E.g. "en,es,pt,ja,ko"
        platform: Target platform. Options: tiktok, instagram, facebook, twitter, youtube
        niche: Content niche for hashtag selection. Options: general, electronics, fashion, beauty, food
        optimize_emojis: Whether to culturally optimize emoji usage per language.

    Returns:
        MultilingualPackage with variants per language, each including translated content,
        localized CTA, trending hashtags, character count/limit, and cultural notes.

    """
    from Services.content.multilingual import translate_content as _translate

    languages = [lang.strip() for lang in target_languages.split(",") if lang.strip()]

    result = await _translate(
        content=content,
        source_language=source_language,
        target_languages=languages,
        platform=platform,
        niche=niche,
        optimize_emojis=optimize_emojis,
    )
    return result.model_dump()


@mcp.tool()
async def translate_single_language(
    content: str,
    source_language: str = "id",
    target_language: str = "en",
    platform: str = "tiktok",
    niche: str = "general",
) -> dict:
    """Translate and culturally adapt content to a single target language.

    Args:
        content: Source content to translate.
        source_language: Source language code.
        target_language: Target language code (en, es, pt, ja, ko, th, vi, hi, ar, tr).
        platform: Target platform for formatting and CTA selection.
        niche: Content niche for hashtag selection.

    Returns:
        SingleTranslateOutput with translated content, hashtags, CTA, char count/limit.

    """
    from Services.content.multilingual import translate_single as _translate_single

    result = await _translate_single(
        content=content,
        source_language=source_language,
        target_language=target_language,
        platform=platform,
        niche=niche,
    )
    return result.model_dump()


@mcp.tool()
async def localize_cta(
    cta_text: str,
    source_language: str = "id",
    target_language: str = "en",
    platform: str = "tiktok",
) -> dict:
    """Localize a call-to-action for a target language and platform.

    Translates CTAs culturally (not just literally) per platform conventions.
    E.g. "Link di bio!" (id) → "Link in bio!" (en) → "Enlace en bio!" (es)

    Args:
        cta_text: CTA text in source language.
        source_language: Source language code.
        target_language: Target language code.
        platform: Platform name for platform-specific CTA format.

    Returns:
        Dict with localized CTA, source, target, platform.

    """
    from Services.content.multilingual import CTA_MAP, SUPPORTED_LANGUAGES

    # Direct lookup in CTA map
    target_ctas = CTA_MAP.get(target_language, {})
    target_cta = target_ctas.get(platform, "")

    # If no exact match, try to find the source CTA type and map
    if not target_cta:
        source_ctas = CTA_MAP.get(source_language, {})
        for cta_key, cta_val in source_ctas.items():
            if cta_val.lower() in cta_text.lower():
                target_cta = target_ctas.get(cta_key, cta_text)
                break

    if not target_cta:
        target_cta = cta_text  # fallback: return as-is

    return {
        "source_cta": cta_text,
        "localized_cta": target_cta,
        "source_language": source_language,
        "target_language": target_language,
        "target_language_name": SUPPORTED_LANGUAGES.get(target_language, target_language),
        "platform": platform,
    }


@mcp.tool()
async def get_trending_hashtags(
    language: str = "en",
    niche: str = "general",
    count: int = 5,
) -> dict:
    """Get culturally trending hashtags for a language and niche.

    Returns hashtags optimized for the target language's social media trends.

    Args:
        language: Language code (id, en, es, pt, ja, ko, th, vi, hi, ar, tr).
        niche: Content niche. Options: general, electronics, fashion, beauty, food.
        count: Number of hashtags to return (1-10).

    Returns:
        Dict with hashtags list, language, niche, count.

    """
    from Services.content.multilingual import _TRENDING_HASHTAGS, SUPPORTED_LANGUAGES

    lang_hashtags = _TRENDING_HASHTAGS.get(language, {})
    niche_key = niche if niche in lang_hashtags else "general"
    hashtags = lang_hashtags.get(niche_key, lang_hashtags.get("general", ["#viral"]))

    return {
        "hashtags": hashtags[:count],
        "language": language,
        "language_name": SUPPORTED_LANGUAGES.get(language, language),
        "niche": niche,
        "total_available": len(hashtags),
        "requested": count,
    }


@mcp.tool()
async def get_platform_char_limits(
    platform: str = "tiktok",
    language: str = "",
) -> dict:
    """Get character limits for a platform, optionally filtered by language.

    Args:
        platform: Platform name (tiktok, instagram, facebook, twitter, youtube).
        language: Language code to filter (empty = all languages).

    Returns:
        Dict with platform, limits per language, or single language limit.

    """
    from Services.content.multilingual import PLATFORM_LIMITS, SUPPORTED_LANGUAGES

    platform_limits = PLATFORM_LIMITS.get(platform, {})

    if language and language in platform_limits:
        return {
            "platform": platform,
            "language": language,
            "language_name": SUPPORTED_LANGUAGES.get(language, language),
            "char_limit": platform_limits[language],
        }

    return {
        "platform": platform,
        "limits": platform_limits,
        "total_languages": len(platform_limits),
    }


@mcp.tool()
async def get_supported_languages() -> dict:
    """Get all supported languages for multilingual content generation.

    Returns dict mapping language codes to language names for all 11 supported languages.
    """
    from Services.content.multilingual import SUPPORTED_LANGUAGES

    return {
        "languages": dict(SUPPORTED_LANGUAGES),
        "total": len(SUPPORTED_LANGUAGES),
    }


@mcp.tool()
async def batch_translate_for_platforms(
    content: str,
    source_language: str = "id",
    platforms: str = "tiktok,instagram,facebook",
    niche: str = "general",
) -> dict:
    """Translate content for multiple platforms, each with platform-specific formatting.

    Returns variants per platform per language, with correct char limits and CTAs.

    Args:
        content: Source content to translate.
        source_language: Source language code.
        platforms: Comma-separated platform names.
        niche: Content niche for hashtag selection.

    Returns:
        Dict with platform → language variants mapping.

    """
    from Services.content.multilingual import translate_content as _translate

    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    target_languages = ["en", "es", "pt", "ja", "ko"]

    results: dict[str, dict] = {}

    for platform in platform_list:
        package = await _translate(
            content=content,
            source_language=source_language,
            target_languages=target_languages,
            platform=platform,
            niche=niche,
            optimize_emojis=True,
        )
        results[platform] = {
            "variants": [v.model_dump() for v in package.variants],
            "total_languages": package.total_variants,
        }

    return {
        "source_language": source_language,
        "platforms": results,
        "total_platforms": len(results),
    }
