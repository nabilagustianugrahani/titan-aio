"""Competitor Spy System — reverse-engineer competitor strategies from social URLs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

from Services.agents.message_bus import get_bus
from titan.config import settings


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CompetitorInput(BaseModel):
    competitor_url: str
    platform: str = "tiktok"
    niche: str = "general"


class CompetitorProfile(BaseModel):
    name: str
    platform: str
    followers: int = 0
    avg_engagement: float = 0.0
    posting_frequency: str = "unknown"
    top_hooks: list[str] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    threat_level: str = "medium"
    recommendations: list[str] = Field(default_factory=list)
    growth_rate: float = 0.0
    content_analysis: dict[str, Any] = Field(default_factory=dict)


class ContentSnapshot(BaseModel):
    """Raw data extracted from one piece of competitor content."""
    text: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    posted_at: Optional[datetime] = None
    hashtags: list[str] = Field(default_factory=list)
    hook: str = ""
    content_type: str = "video"


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

_PLATFORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "tiktok": re.compile(
        r"(?:https?://)?(?:www\.)?(?:vm\.)?tiktok\.com/@([^/?]+)",
        re.I,
    ),
    "instagram": re.compile(
        r"(?:https?://)?(?:www\.)?instagram\.com/([^/?]+)",
        re.I,
    ),
    "youtube": re.compile(
        r"(?:https?://)?(?:www\.)?youtube\.com/(?:c/|channel/|@)([^/?]+)",
        re.I,
    ),
    "twitter": re.compile(
        r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([^/?]+)",
        re.I,
    ),
    "facebook": re.compile(
        r"(?:https?://)?(?:www\.)?facebook\.com/([^/?]+)",
        re.I,
    ),
}


def _extract_username(url: str, platform: str) -> str:
    """Pull the username / handle from a profile URL."""
    pat = _PLATFORM_PATTERNS.get(platform)
    if pat:
        m = pat.search(url)
        if m:
            return m.group(1)
    # Fallback: last path segment
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else "unknown"


def _detect_platform(url: str) -> str:
    """Auto-detect platform from URL when not specified."""
    url_lower = url.lower()
    for plat, pat in _PLATFORM_PATTERNS.items():
        if pat.search(url_lower):
            return plat
    return "unknown"


def _extract_hooks(texts: list[str], top_n: int = 10) -> list[str]:
    """Identify the most common hook patterns from content text.

    Hooks are the first sentence or first 80 characters of each piece of
    content.  We rank by frequency (longer unique matches first).
    """
    hooks: list[str] = []
    for text in texts:
        if not text.strip():
            continue
        # First sentence or first line
        first_line = text.strip().split("\n")[0].split(".")[0].strip()
        if len(first_line) > 80:
            first_line = first_line[:77] + "..."
        if first_line and len(first_line) > 5:
            hooks.append(first_line)
    # Rank by frequency then by length (longer = more specific)
    counter: Counter[str] = Counter(hooks)
    ranked = sorted(counter.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
    return [h for h, _ in ranked[:top_n]]


def _extract_hashtags(texts: list[str]) -> list[str]:
    """Collect and rank hashtags from all content."""
    tag_counter: Counter[str] = Counter()
    for text in texts:
        tag_counter.update(re.findall(r"#\w+", text))
    return [tag for tag, _ in tag_counter.most_common(20)]


def _compute_posting_frequency(timestamps: list[datetime]) -> str:
    """Return a human-readable posting cadence from timestamps."""
    if len(timestamps) < 2:
        return "unknown"
    timestamps_sorted = sorted(timestamps)
    gaps = [
        (timestamps_sorted[i + 1] - timestamps_sorted[i]).total_seconds()
        for i in range(len(timestamps_sorted) - 1)
    ]
    avg_hours = sum(gaps) / len(gaps) / 3600
    if avg_hours < 6:
        return f"~{int(round(avg_hours))}h (multiple times daily)"
    if avg_hours < 24:
        return f"~{int(round(avg_hours))}h (multiple times daily)"
    avg_days = avg_hours / 24
    if avg_days < 2:
        return "daily"
    if avg_days < 4:
        return f"every {int(round(avg_days))} days"
    if avg_days < 10:
        return f"weekly"
    return f"every {int(round(avg_days))} days"


def _compute_growth_rate(followers: int, post_count: int, niche_avg_followers: int = 10_000) -> float:
    """Estimate monthly growth rate (rough heuristic).

    Uses followers-to-content ratio relative to niche average.
    """
    if post_count == 0:
        return 0.0
    ratio = followers / max(post_count, 1)
    niche_ratio = niche_avg_followers / max(post_count, 1)
    if niche_ratio == 0:
        return 0.0
    return round((ratio / niche_ratio) * 100 - 100, 2)


def _assess_threat(followers: int, avg_engagement: float, posting_frequency: str) -> str:
    """Classify competitor threat level."""
    score = 0
    if followers > 100_000:
        score += 3
    elif followers > 10_000:
        score += 2
    elif followers > 1_000:
        score += 1
    if avg_engagement > 5.0:
        score += 3
    elif avg_engagement > 2.0:
        score += 2
    elif avg_engagement > 0.5:
        score += 1
    if "multiple" in posting_frequency or posting_frequency == "daily":
        score += 2
    elif posting_frequency == "weekly":
        score += 1
    if score >= 6:
        return "critical"
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _identify_content_gaps(
    hashtags: list[str],
    niche: str,
    content_types: Counter[str],
) -> list[str]:
    """Suggest content angles the competitor is *not* covering."""
    gaps: list[str] = []
    niche_lower = niche.lower()
    # Common affiliate content types not yet seen
    all_types = {
        "tutorial", "review", "unboxing", "comparison", "testimonial",
        "behind_the_scenes", "meme", "duet", "stitch", "live",
        "giveaway", "challenge", "before_after", "faq",
    }
    missing = all_types - set(content_types.keys())
    for mt in sorted(missing):
        gaps.append(f"Missing content type: {mt.replace('_', ' ')}")

    # If niche is e-commerce but no product-focused hashtags
    product_tags = {"#product", "#review", "#haul", "#unboxing", "#recommend"}
    if niche_lower in ("ecommerce", "e-commerce", "product") and not (set(hashtags) & product_tags):
        gaps.append("No product-focused hashtags — competitor is brand-aware, not product-aware")

    # If engagement is low relative to followers → audience quality gap
    # (filled externally with follower count)
    return gaps


def _generate_recommendations(
    profile: CompetitorProfile,
    hashtags: list[str],
    niche: str,
) -> list[str]:
    """Actionable recommendations based on the spy analysis."""
    recs: list[str] = []

    if profile.avg_engagement < 1.0:
        recs.append("Competitor engagement is low — target their audience with higher-quality hooks")
    if profile.threat_level in ("high", "critical"):
        recs.append("High threat — differentiate with unique UGC formats (lip-sync, A/B variants)")
    if profile.posting_frequency == "unknown" or "every" in profile.posting_frequency:
        recs.append("Outpace them with consistent daily posting cadence")
    if len(profile.top_hooks) > 0:
        recs.append(f"Adapt top hook style: \"{profile.top_hooks[0][:60]}\"")
    if len(hashtags) > 0:
        recs.append(f"Use overlapping hashtags: {', '.join(hashtags[:5])}")
    if profile.growth_rate > 50:
        recs.append("Rapid growth detected — study their latest content for trend signals")
    if not recs:
        recs.append("Monitor periodically and benchmark your metrics against theirs")
    return recs


# ---------------------------------------------------------------------------
# Scraping layer (lightweight — uses ScrapingBee or plain httpx)
# ---------------------------------------------------------------------------

async def _fetch_page(url: str) -> str:
    """Fetch a page with lightweight httpx.  Uses ScrapingBee if key is set."""
    api_key = getattr(settings, "SCRAPINGBEE_API_KEY", None)
    if api_key:
        resp = await httpx.AsyncClient(timeout=30).get(
            "https://app.scrapingbee.com/api/v1/",
            params={
                "api_key": api_key,
                "url": url,
                "render_js": "true",
            },
        )
        resp.raise_for_status()
        return resp.text
    async with httpx.AsyncClient(
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TitanAIO/1.0)"},
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_tiktok_page(html: str) -> dict[str, Any]:
    """Extract structured data from a TikTok profile page HTML."""
    data: dict[str, Any] = {
        "name": "",
        "followers": 0,
        "content": [],
    }
    # Try SIGI_STATE JSON blob (TikTok's server-rendered state)
    state_match = re.search(
        r'<script\s+id="SIGI_STATE"[^>]*>(.*?)</script>',
        html,
        re.S,
    )
    if state_match:
        import json
        try:
            state = json.loads(state_match.group(1))
            user = state.get("UserModule", {}).get("users", {})
            for _uid, info in user.items():
                data["name"] = info.get("uniqueId", info.get("nickname", ""))
                data["followers"] = info.get("stats", {}).get("followerCount", 0)
            items = state.get("ItemModule", {}).get("items", [])
            for item in items[:30]:
                desc = item.get("desc", "")
                stats = item.get("stats", {})
                data["content"].append(
                    ContentSnapshot(
                        text=desc,
                        likes=stats.get("diggCount", 0),
                        comments=stats.get("commentCount", 0),
                        shares=stats.get("shareCount", 0),
                        views=stats.get("playCount", 0),
                        hashtags=re.findall(r"#\w+", desc),
                        hook=desc.split("\n")[0][:80] if desc else "",
                    )
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    # Fallback: regex mining from meta tags
    if not data["name"]:
        og_title = re.search(r'<meta\s+(?:property|name)="og:title"\s+content="([^"]+)"', html, re.I)
        if og_title:
            data["name"] = og_title.group(1).split(" on ")[0].strip()
    return data


def _parse_instagram_page(html: str) -> dict[str, Any]:
    """Extract data from an Instagram profile page."""
    data: dict[str, Any] = {"name": "", "followers": 0, "content": []}
    name_match = re.search(r'"full_name"\s*:\s*"([^"]+)"', html)
    if name_match:
        data["name"] = name_match.group(1)
    followers_match = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
    if followers_match:
        data["followers"] = int(followers_match.group(1))
    # Extract captions from edges
    for cap_match in re.finditer(r'"edge_media_to_caption".*?"text"\s*:\s*"((?:[^"\\]|\\.)*)"', html, re.S):
        text = cap_match.group(1).encode().decode("unicode_escape")
        data["content"].append(ContentSnapshot(text=text[:500], hook=text.split("\n")[0][:80] if text else ""))
    return data


def _parse_youtube_page(html: str) -> dict[str, Any]:
    """Extract data from a YouTube channel page."""
    data: dict[str, Any] = {"name": "", "followers": 0, "content": []}
    name_match = re.search(r'"channelMetadataRenderer".*?"title"\s*:\s*"([^"]+)"', html, re.S)
    if name_match:
        data["name"] = name_match.group(1)
    subs_match = re.search(r'"subscriberCountText".*?"simpleText"\s*:\s*"([\d.]+[KMB]?)\s*subscribers"', html, re.S)
    if subs_match:
        raw = subs_match.group(1).replace(",", "")
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
        for suffix, mult in multiplier.items():
            if raw.endswith(suffix):
                raw = raw[:-1]
                data["followers"] = int(float(raw) * mult)
                break
        else:
            data["followers"] = int(float(raw))
    # Video titles as content
    for title_match in re.finditer(r'"title"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"', html):
        text = title_match.group(1)
        data["content"].append(ContentSnapshot(text=text, hook=text[:80]))
    return data


def _parse_generic_page(html: str, url: str) -> dict[str, Any]:
    """Generic parser: grab og:title, meta description, any text snippets."""
    data: dict[str, Any] = {"name": "", "followers": 0, "content": []}
    og_title = re.search(r'<meta\s+(?:property|name)="og:title"\s+content="([^"]+)"', html, re.I)
    if og_title:
        data["name"] = og_title.group(1).split("|")[0].split("-")[0].strip()
    desc_match = re.search(r'<meta\s+(?:property|name)="(?:og:)?description"\s+content="([^"]+)"', html, re.I)
    if desc_match:
        data["content"].append(ContentSnapshot(text=desc_match.group(1), hook=desc_match.group(1)[:80]))
    # Try to find any JSON-LD
    for ld_match in re.finditer(r'<script\s+type="application/ld\+json">(.*?)</script>', html, re.S):
        import json
        try:
            ld = json.loads(ld_match.group(1))
            if isinstance(ld, dict):
                if "name" in ld:
                    data["name"] = data["name"] or ld["name"]
                if "description" in ld:
                    data["content"].append(ContentSnapshot(text=ld["description"], hook=ld["description"][:80]))
        except (json.JSONDecodeError, TypeError):
            pass
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def spy_competitor(input_model: CompetitorInput) -> CompetitorProfile:
    """Full competitor spy analysis.

    Fetches the competitor's public profile, extracts content data, and
    produces a CompetitorProfile with hooks, gaps, and recommendations.
    """
    platform = input_model.platform.lower()
    if platform == "auto" or platform not in _PLATFORM_PATTERNS:
        platform = _detect_platform(input_model.competitor_url)

    username = _extract_username(input_model.competitor_url, platform)
    bus = get_bus()

    # Fetch & parse
    try:
        html = await _fetch_page(input_model.competitor_url)
    except Exception:
        html = ""

    if platform == "tiktok":
        parsed = _parse_tiktok_page(html) if html else {"name": username, "followers": 0, "content": []}
    elif platform == "instagram":
        parsed = _parse_instagram_page(html) if html else {"name": username, "followers": 0, "content": []}
    elif platform == "youtube":
        parsed = _parse_youtube_page(html) if html else {"name": username, "followers": 0, "content": []}
    else:
        parsed = _parse_generic_page(html, input_model.competitor_url) if html else {"name": username, "followers": 0, "content": []}

    name = parsed.get("name") or username
    followers = parsed.get("followers", 0)
    snapshots: list[ContentSnapshot] = parsed.get("content", [])

    # Derive metrics
    texts = [s.text for s in snapshots if s.text]
    all_hashtags = _extract_hashtags(texts)
    top_hooks = _extract_hooks(texts)
    content_types: Counter[str] = Counter()
    for s in snapshots:
        content_types[s.content_type] += 1

    # Engagement
    total_engagement = 0.0
    engagement_count = 0
    for s in snapshots:
        denom = max(s.views, 1)
        eng = (s.likes + s.comments + s.shares) / denom * 100
        total_engagement += eng
        engagement_count += 1
    avg_engagement = round(total_engagement / max(engagement_count, 1), 2)

    # Posting frequency
    timestamps = [s.posted_at for s in snapshots if s.posted_at]
    posting_freq = _compute_posting_frequency(timestamps)

    # Growth rate
    growth_rate = _compute_growth_rate(followers, len(snapshots))

    # Content gaps
    content_gaps = _identify_content_gaps(all_hashtags, input_model.niche, content_types)

    # Threat & recommendations
    threat_level = _assess_threat(followers, avg_engagement, posting_freq)

    profile = CompetitorProfile(
        name=name,
        platform=platform,
        followers=followers,
        avg_engagement=avg_engagement,
        posting_frequency=posting_freq,
        top_hooks=top_hooks,
        content_gaps=content_gaps,
        threat_level=threat_level,
        growth_rate=growth_rate,
        content_analysis={
            "total_posts_analyzed": len(snapshots),
            "hashtags": all_hashtags[:20],
            "content_type_distribution": dict(content_types),
            "top_engagement_post": _best_post(snapshots),
        },
    )
    profile.recommendations = _generate_recommendations(profile, all_hashtags, input_model.niche)

    # Publish to message bus
    bus.publish(
        "competitor.analyzed",
        {"competitor": name, "platform": platform, "threat": threat_level},
        source="competitor_spy",
    )

    return profile


def _best_post(snapshots: list[ContentSnapshot]) -> dict[str, Any]:
    """Return the highest-engagement post summary."""
    if not snapshots:
        return {}
    best = max(
        snapshots,
        key=lambda s: s.likes + s.comments + s.shares,
    )
    return {
        "text": best.text[:200],
        "likes": best.likes,
        "comments": best.comments,
        "shares": best.shares,
        "views": best.views,
    }


# ---------------------------------------------------------------------------
# Batch spy
# ---------------------------------------------------------------------------

async def spy_multiple(urls: list[str], platform: str = "auto", niche: str = "general") -> list[CompetitorProfile]:
    """Spy on multiple competitors concurrently."""
    import asyncio

    profiles = await asyncio.gather(
        *[
            spy_competitor(CompetitorInput(competitor_url=url, platform=platform, niche=niche))
            for url in urls
        ],
        return_exceptions=True,
    )
    return [p for p in profiles if isinstance(p, CompetitorProfile)]


# ---------------------------------------------------------------------------
# Historical tracking (lightweight SQLite-based growth tracker)
# ---------------------------------------------------------------------------

class GrowthRecord(BaseModel):
    competitor: str
    platform: str
    followers: int
    avg_engagement: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GrowthTracker:
    """Track competitor metrics over time for growth-rate calculation."""

    def __init__(self) -> None:
        self._records: list[GrowthRecord] = []

    def record(self, profile: CompetitorProfile) -> None:
        self._records.append(
            GrowthRecord(
                competitor=profile.name,
                platform=profile.platform,
                followers=profile.followers,
                avg_engagement=profile.avg_engagement,
            )
        )

    def get_history(self, name: str, platform: str) -> list[GrowthRecord]:
        return [
            r for r in self._records
            if r.competitor == name and r.platform == platform
        ]

    def compute_monthly_growth(self, name: str, platform: str) -> float:
        """Calculate month-over-month follower growth percentage."""
        history = self.get_history(name, platform)
        if len(history) < 2:
            return 0.0
        history_sorted = sorted(history, key=lambda r: r.timestamp)
        earliest = history_sorted[0]
        latest = history_sorted[-1]
        if earliest.followers == 0:
            return 0.0
        return round((latest.followers - earliest.followers) / earliest.followers * 100, 2)


# Module-level singleton tracker
_growth_tracker = GrowthTracker()


def get_growth_tracker() -> GrowthTracker:
    return _growth_tracker
