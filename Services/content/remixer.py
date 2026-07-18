"""Content Remix Engine — transforms one winning content piece into 10+ platform-specific formats.

Pure algorithmic adaptation (no LLM dependency, no GPU). Handles style, length, hashtags,
CTA injection, and viral potential scoring per platform.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

# ── Platform Configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class PlatformConfig:
    """Per-platform content constraints and style rules."""

    max_chars: int
    min_chars: int
    cta_style: str
    cta_examples: list[str]
    hashtag_count: int
    hashtag_categories: list[str]
    style: str  # "short-form" | "visual" | "descriptive" | "thread" | "long-form" | "conversational"
    supports_emoji: bool
    supports_thread: bool
    tone: str  # "punchy" | "aesthetic" | "educational" | "witty" | "professional" | "casual"


PLATFORMS: dict[str, PlatformConfig] = {
    "tiktok": PlatformConfig(
        max_chars=300, min_chars=50,
        cta_style="tiktok",
        cta_examples=[
            "Link di bio! 🛒",
            "Check link in bio!",
            "Grab it now! Link in bio 👆",
            "Don't miss out! Link in bio",
        ],
        hashtag_count=4,
        hashtag_categories=["umum", "trending", "niche", "branded"],
        style="short-form",
        supports_emoji=True,
        supports_thread=False,
        tone="punchy",
    ),
    "instagram": PlatformConfig(
        max_chars=2200, min_chars=100,
        cta_style="instagram",
        cta_examples=[
            "Link di bio! 🔗",
            "Tap link in bio for more!",
            "Save this for later! 📌 Link in bio",
            "Shop now via link in bio! 💫",
        ],
        hashtag_count=8,
        hashtag_categories=["umum", "trending", "niche", "lifestyle", "aesthetic", "branded", "location", "community"],
        style="visual",
        supports_emoji=True,
        supports_thread=False,
        tone="aesthetic",
    ),
    "youtube": PlatformConfig(
        max_chars=5000, min_chars=100,
        cta_style="youtube",
        cta_examples=[
            "Like & Subscribe! Link in description 👇",
            "Drop a comment if you agree!",
            "Full review in description — check it out!",
        ],
        hashtag_count=3,
        hashtag_categories=["niche", "topic", "branded"],
        style="descriptive",
        supports_emoji=True,
        supports_thread=False,
        tone="educational",
    ),
    "twitter": PlatformConfig(
        max_chars=280, min_chars=20,
        cta_style="twitter",
        cta_examples=[
            "Thread 🧵👇",
            "Link in bio 🔗",
            "RT if you agree 🔄",
        ],
        hashtag_count=2,
        hashtag_categories=["trending", "niche"],
        style="thread",
        supports_emoji=True,
        supports_thread=True,
        tone="witty",
    ),
    "facebook": PlatformConfig(
        max_chars=63206, min_chars=50,
        cta_style="facebook",
        cta_examples=[
            "Order sekarang! Link di komentar.",
            "Info lengkap di komentar! 👇",
            "Comment 'INFO' untuk link!",
        ],
        hashtag_count=3,
        hashtag_categories=["umum", "niche", "community"],
        style="long-form",
        supports_emoji=True,
        supports_thread=False,
        tone="conversational",
    ),
    "blog": PlatformConfig(
        max_chars=5000, min_chars=300,
        cta_style="blog",
        cta_examples=[
            "Read more in the full review below.",
            "Check out the product link for the latest price.",
            "Share this post if you found it helpful!",
        ],
        hashtag_count=0,
        hashtag_categories=[],
        style="long-form",
        supports_emoji=False,
        supports_thread=False,
        tone="educational",
    ),
    "newsletter": PlatformConfig(
        max_chars=4000, min_chars=200,
        cta_style="newsletter",
        cta_examples=[
            "Try it yourself — link below.",
            "Reply to this email with your thoughts!",
            "Forward this to a friend who needs this.",
        ],
        hashtag_count=0,
        hashtag_categories=[],
        style="long-form",
        supports_emoji=True,
        supports_thread=False,
        tone="conversational",
    ),
    "podcast": PlatformConfig(
        max_chars=3000, min_chars=150,
        cta_style="podcast",
        cta_examples=[
            "Subscribe for more reviews!",
            "Show notes and links at [website].",
            "Rate us 5 stars on your favorite platform!",
        ],
        hashtag_count=0,
        hashtag_categories=[],
        style="conversational",
        supports_emoji=False,
        supports_thread=False,
        tone="conversational",
    ),
}


# ── Hashtag Banks ─────────────────────────────────────────────────────────

HASHTAG_BANKS: dict[str, list[str]] = {
    "umum": ["#viral", "#fyp", "#trending", "#rekomendasi", "#review", "#terbaik", "#wajibcoba", "#produk"],
    "trending": ["#fypシ", "#tiktokviral", "#explorepage", "#trendingnow", "#viralvideo"],
    "niche": ["#productreview", "#honestreview", "#musthave", "#worthit", "#noshortcuts"],
    "lifestyle": ["#lifestyle", "#dailyroutine", "#selfcare", "#aestheticvibes", "#livebetter"],
    "aesthetic": ["#aesthetic", "#minimal", "#cleanvibes", "#mood", "#inspo"],
    "branded": ["#titanreview", "#titanpick", "#titanapproved"],
    "location": ["#indonesia", "#id", "#jakarta", "#surabaya", "#bandung"],
    "community": ["#komunitas", "#sharing", "#temanbaik", "#keseharian"],
    "topic": ["#tech", "#gadget", "#unboxing", "#handsontreview"],
}


# ── Viral Score Heuristics ────────────────────────────────────────────────

_HOOK_PATTERNS = [
    (r"\?$", 8, "question hook"),
    (r"(?i)(gak tau|kaget|ternyata|parah|gila|wah)", 10, "emotional trigger"),
    (r"(?i)(secret|rahasia|hack|trik|cara)", 7, "curiosity trigger"),
    (r"(?i)(jangan|stop|wait|hold)", 6, "pattern interrupt"),
    (r"(?i)(\d+[xXkK])", 5, "social proof number"),
    (r"(?i)(pertama|pertama kali|baru|latest|new)", 4, "novelty"),
    (r"!", 3, "exclamation energy"),
]

_EMOTIONAL_WORDS = [
    "wow", "amazing", "insane", "best", "terbaik", "gila", "parah",
    "wajib", "must", "need", "obsessed", "addicted", "game changer",
    "life hack", "mind blown", "worth it", "bukan scam", "real result",
]

_CTA_SIGNALS = [
    "link", "bio", "comment", "subscribe", "follow", "share", "save",
    "order", "beli", "check", "tap", "click", "drop",
]


def _viral_score(content: str, platform: str) -> int:
    """Score viral potential 0-100 based on engagement heuristics."""
    score = 30  # base
    text = content.lower()

    # Hook pattern matches
    for pattern, points, _ in _HOOK_PATTERNS:
        if re.search(pattern, content):
            score += points

    # Emotional word density
    max(len(text.split()), 1)
    emotional_hits = sum(1 for w in _EMOTIONAL_WORDS if w in text)
    score += min(emotional_hits * 3, 15)

    # CTA presence
    cta_hits = sum(1 for w in _CTA_SIGNALS if w in text)
    score += min(cta_hits * 4, 16)

    # Length appropriateness
    char_len = len(content)
    cfg = PLATFORMS.get(platform, PLATFORMS["tiktok"])
    optimal = (cfg.min_chars + cfg.max_chars) / 2
    length_ratio = char_len / optimal if optimal else 1
    if 0.5 <= length_ratio <= 1.5:
        score += 10
    elif length_ratio < 0.3:
        score -= 10
    elif length_ratio > 2.0:
        score -= 5

    # Emoji density (sweet spot: 2-8%)
    emoji_count = len(re.findall(r"[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff\U00002702-\U000027b0\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff]", content))
    emoji_ratio = emoji_count / max(char_len, 1)
    if 0.005 <= emoji_ratio <= 0.08:
        score += 5
    elif emoji_ratio > 0.15:
        score -= 5

    # Platform-specific bonuses
    if platform == "tiktok" and char_len <= 150:
        score += 5  # short content thrives on TikTok
    if platform == "twitter" and char_len <= 200:
        score += 5  # concise Twitter content
    if platform == "instagram" and re.search(r"\n", content):
        score += 3  # line breaks = readability on IG

    # Clamp
    return max(0, min(100, score))


# ── Content Adaptation ────────────────────────────────────────────────────

def _extract_core_message(content: str) -> str:
    """Strip noise from source content, keep the core message."""
    # Remove excess whitespace
    text = re.sub(r"\s+", " ", content).strip()
    # Remove markdown headers
    return re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)


def _truncate_to_chars(text: str, max_chars: int) -> str:
    """Truncate text at word boundary, preserving meaning."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars - 3]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.6:
        truncated = truncated[:last_space]
    return truncated.rstrip() + "..."


def _generate_hashtags(content: str, niche: str, config: PlatformConfig) -> list[str]:
    """Generate relevant hashtags from content + niche."""
    if config.hashtag_count == 0:
        return []

    selected: list[str] = []
    content.lower()

    # Pull from category banks
    for category in config.hashtag_categories:
        bank = HASHTAG_BANKS.get(category, [])
        for tag in bank:
            if len(selected) >= config.hashtag_count:
                break
            selected.append(tag)

    # Add niche-specific tag if not already present
    if niche and niche != "general":
        niche_tag = f"#{niche.lower().replace(' ', '')}"
        if niche_tag not in selected:
            selected.insert(0, niche_tag)

    # Trim to count
    return selected[:config.hashtag_count]


def _adapt_tiktok(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """TikTok: punchy, short, hook-first. Max 300 chars."""
    lines = core.split(".")
    # Take the punchiest opening line(s)
    hook = lines[0].strip() if lines else core
    if len(hook) > 80:
        words = hook.split()
        hook = " ".join(words[:12])
    return _truncate_to_chars(hook, cfg.max_chars)


def _adapt_instagram(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Instagram: caption with line breaks, emoji-rich, storytelling."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    if len(sentences) >= 3:
        hook = sentences[0]
        body = " ".join(sentences[1:3])
        result = f"{hook}\n\n{body}"
    else:
        result = core

    # Add line break structure
    paragraphs = result.split("\n")
    formatted = "\n\n".join(p.strip() for p in paragraphs if p.strip())
    return _truncate_to_chars(formatted, cfg.max_chars)


def _adapt_youtube(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """YouTube: title + description format. More detail."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    title = sentences[0] if sentences else core
    description = " ".join(sentences[1:]) if len(sentences) > 1 else ""

    result = f"**{title}**\n\n{description}" if description else title
    return _truncate_to_chars(result, cfg.max_chars)


def _adapt_twitter(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Twitter: ultra-concise, thread-worthy. Max 280 chars."""
    # Take the single most impactful sentence
    sentences = re.split(r"(?<=[.!?])\s+", core)
    best = max(sentences, key=len) if sentences else core
    if len(best) > 200:
        words = best.split()
        best = " ".join(words[:18])
    return _truncate_to_chars(best, cfg.max_chars)


def _adapt_facebook(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Facebook: conversational, longer form, engagement-driven."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    if len(sentences) >= 3:
        opener = sentences[0]
        body = " ".join(sentences[1:3])
        question = "Kalian udah coba belum?"
        result = f"{opener}\n\n{body}\n\n{question}"
    else:
        result = f"{core}\n\nKalian udah coba belum?"
    return _truncate_to_chars(result, cfg.max_chars)


def _adapt_blog(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Blog: structured, SEO-friendly, longer."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    title = sentences[0] if sentences else core
    body = " ".join(sentences[1:]) if len(sentences) > 1 else ""

    result = f"## {title}\n\n"
    if body:
        result += body
    return _truncate_to_chars(result, cfg.max_chars)


def _adapt_newsletter(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Newsletter: personal tone, value-forward, scannable."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    opener = "Hey! 👋" if sentences else "Hey!"
    body = core
    result = f"{opener}\n\n{body}"
    return _truncate_to_chars(result, cfg.max_chars)


def _adapt_podcast(content: str, core: str, niche: str, cfg: PlatformConfig) -> str:
    """Podcast: conversational, show-notes style, spoken language."""
    sentences = re.split(r"(?<=[.!?])\s+", core)
    intro = "Today we're talking about" if sentences else ""
    body = core
    result = f"{intro} {body}" if intro else body
    return _truncate_to_chars(result, cfg.max_chars)


ADAPTATORS: dict[str, callable] = {
    "tiktok": _adapt_tiktok,
    "instagram": _adapt_instagram,
    "youtube": _adapt_youtube,
    "twitter": _adapt_twitter,
    "facebook": _adapt_facebook,
    "blog": _adapt_blog,
    "newsletter": _adapt_newsletter,
    "podcast": _adapt_podcast,
}


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class ContentVariant:
    """A single platform-adapted content variant."""

    platform: str
    format: str
    content: str
    char_count: int
    viral_score: int
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class RemixPackage:
    """Complete remix output — source + all variants."""

    source_content: str
    variants: list[ContentVariant]
    total_variants: int
    platform_coverage: list[str]
    best_variant: int = 0


# ── Engine ────────────────────────────────────────────────────────────────

class ContentRemixer:
    """Transforms one winning content piece into multiple platform-specific formats.

    Pure algorithmic adaptation. No LLM calls, no GPU. Runs on VPS.
    """

    def remix(
        self,
        content: str,
        content_type: str = "script",
        niche: str = "general",
        target_platforms: list[str] | None = None,
    ) -> RemixPackage:
        """Generate platform-specific variants from a single content piece.

        Args:
            content: Source content (script, hook, or video concept).
            content_type: Type of content ("script", "hook", "video_concept").
            niche: Content niche for hashtag generation.
            target_platforms: Which platforms to generate for. None = all.

        Returns:
            RemixPackage with all variants and scores.

        """
        platforms = target_platforms or list(PLATFORMS.keys())
        core = _extract_core_message(content)
        variants: list[ContentVariant] = []

        for platform in platforms:
            if platform not in PLATFORMS:
                continue
            cfg = PLATFORMS[platform]
            adaptator = ADAPTATORS.get(platform, _adapt_tiktok)

            # Adapt content
            adapted = adaptator(content, core, niche, cfg)
            hashtags = _generate_hashtags(content, niche, cfg)

            # Inject CTA
            cta = random.choice(cfg.cta_examples)
            if platform in ("twitter", "tiktok"):
                adapted = f"{adapted}\n\n{cta}"
            else:
                adapted = f"{adapted}\n\n{cta}"

            # Hashtag append for hashtag-supported platforms
            if hashtags:
                hashtag_str = " ".join(hashtags)
                if len(adapted) + len(hashtag_str) + 1 <= cfg.max_chars:
                    adapted = f"{adapted}\n\n{hashtag_str}"

            # Score
            score = _viral_score(adapted, platform)

            # Build variant
            variant = ContentVariant(
                platform=platform,
                format=cfg.style,
                content=adapted,
                char_count=len(adapted),
                viral_score=score,
                hashtags=hashtags,
                cta=cta,
                metadata={
                    "content_type": content_type,
                    "niche": niche,
                    "tone": cfg.tone,
                    "max_chars": cfg.max_chars,
                    "supports_emoji": cfg.supports_emoji,
                },
            )
            variants.append(variant)

        # Find best variant
        best_idx = 0
        best_score = -1
        for i, v in enumerate(variants):
            if v.viral_score > best_score:
                best_score = v.viral_score
                best_idx = i

        return RemixPackage(
            source_content=content,
            variants=variants,
            total_variants=len(variants),
            platform_coverage=[v.platform for v in variants],
            best_variant=best_idx,
        )


async def remix_content(
    content: str,
    content_type: str = "script",
    niche: str = "general",
    target_platforms: list[str] | None = None,
) -> RemixPackage:
    """Async entry point for the remixer.

    Usage:
        package = await remix_content("Check out this amazing product! ...")
    """
    engine = ContentRemixer()
    return engine.remix(
        content=content,
        content_type=content_type,
        niche=niche,
        target_platforms=target_platforms,
    )
