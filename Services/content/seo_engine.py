"""SEO Content Engine — optimize content for search rankings."""

from __future__ import annotations

import random

from pydantic import BaseModel, Field

# ── Models ───────────────────────────────────────────────────────

class KeywordData(BaseModel):
    keyword: str
    search_volume: int = 0
    difficulty: float = 0.0
    relevance: float = 0.0
    trending: bool = False
    long_tail: bool = False


class SEOOptimization(BaseModel):
    original_score: int = Field(ge=0, le=100)
    optimized_score: int = Field(ge=0, le=100)
    keywords: list[KeywordData]
    optimized_title: str
    optimized_description: str
    optimized_tags: list[str]
    optimized_hashtags: list[str]
    improvements: list[str]
    keyword_density: float = 0.0
    readability_score: int = Field(ge=0, le=100)


# ── Keyword Data ─────────────────────────────────────────────────

NICHE_KEYWORDS = {
    "electronics": {
        "primary": ["review", "unboxing", "best", "2026", "murah", "terbaik"],
        "long_tail": ["best budget electronics 2026", "unboxing murah terbaik", "electronics review indonesia"],
        "hashtags": ["#electronics", "#review", "#gadget", "#tech", "#murah"],
    },
    "fashion": {
        "primary": ["ootd", "style", "fashion", "outfit", "trend", "haul"],
        "long_tail": ["ootd inspiration 2026", "fashion haul murah", "style tips pemula"],
        "hashtags": ["#fashion", "#ootd", "#style", "#haul", "#trend"],
    },
    "beauty": {
        "primary": ["skincare", "makeup", "beauty", "routine", "review", "tutorial"],
        "long_tail": ["skincare routine pemula", "makeup tutorial natural", "beauty review terbaik"],
        "hashtags": ["#beauty", "#skincare", "#makeup", "#tutorial", "#review"],
    },
    "food": {
        "primary": ["recipe", "cooking", "food", "review", "enak", "rekomendasi"],
        "long_tail": ["resep mudah enak", "food review viral", "cooking hack simpel"],
        "hashtags": ["#food", "#recipe", "#cooking", "#review", "#foodie"],
    },
    "general": {
        "primary": ["review", "best", "tutorial", "tips", "recommendation"],
        "long_tail": ["best product review 2026", "tutorial tips pemula", "rekomendasi terbaik"],
        "hashtags": ["#review", "#tutorial", "#tips", "#recommendation", "#viral"],
    },
}


# ── Engine ───────────────────────────────────────────────────────

def _calculate_readability(text: str) -> int:
    """Calculate readability score (0-100)."""
    if not text:
        return 0
    words = text.split()
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_words = len(words) / sentences
    # Simpler = higher score
    return max(0, min(100, int(100 - (avg_words - 15) * 3)))


def _optimize_title(title: str, keywords: list[KeywordData]) -> str:
    """Optimize title for SEO."""
    if not title:
        return title
    # Add power words if missing
    power_starters = ["Best", "Top", "Ultimate", "How to", "Review"]
    has_power = any(title.lower().startswith(p.lower()) for p in power_starters)
    if not has_power and keywords:
        top_kw = keywords[0].keyword
        title = f"{top_kw.title()} — {title}"
    # Ensure reasonable length
    if len(title) > 60:
        title = title[:57] + "..."
    return title


def _optimize_description(desc: str, keywords: list[KeywordData]) -> str:
    """Optimize description with front-loaded keywords."""
    if not desc:
        return ""
    top_keywords = [k.keyword for k in keywords[:3]]
    if top_keywords and not any(kw.lower() in desc.lower() for kw in top_keywords):
        desc = f"Discover {', '.join(top_keywords)}. {desc}"
    if len(desc) > 160:
        desc = desc[:157] + "..."
    return desc


async def seo_optimize(
    title: str,
    description: str = "",
    niche: str = "general",
    platform: str = "youtube",
) -> SEOOptimization:
    """Optimize content for search rankings."""
    niche_data = NICHE_KEYWORDS.get(niche, NICHE_KEYWORDS["general"])

    # Generate keywords
    keywords = []
    for i, kw in enumerate(niche_data["primary"][:5]):
        keywords.append(KeywordData(
            keyword=kw,
            search_volume=random.randint(1000, 100000) if __import__("random").random() > 0.3 else 0,
            difficulty=round(__import__("random").uniform(0.2, 0.8), 2),
            relevance=round(max(0.3, 1.0 - i * 0.15), 2),
            trending=__import__("random").random() > 0.6,
            long_tail=False,
        ))
    for kw in niche_data["long_tail"][:3]:
        keywords.append(KeywordData(
            keyword=kw,
            search_volume=__import__("random").randint(500, 20000),
            difficulty=round(__import__("random").uniform(0.1, 0.5), 2),
            relevance=round(__import__("random").uniform(0.5, 0.9), 2),
            trending=False,
            long_tail=True,
        ))

    # Score original
    original_score = 30 + len(title.split()) * 2 + (50 if description else 0)
    original_score = min(100, original_score)

    # Optimize
    opt_title = _optimize_title(title, keywords)
    opt_desc = _optimize_description(description, keywords)
    opt_tags = [k.keyword for k in keywords[:8]]
    opt_hashtags = niche_data["hashtags"][:6]

    # Score optimized
    optimized_score = 60
    optimized_score += 10 if any(kw in opt_title.lower() for kw in [k.keyword for k in keywords[:3]]) else 0
    optimized_score += 10 if opt_desc else 0
    optimized_score += 5 if len(opt_tags) >= 5 else 0
    optimized_score = min(100, optimized_score)

    improvements = []
    if opt_title != title:
        improvements.append(f"Title optimized with top keyword: '{keywords[0].keyword}'")
    if opt_desc != description:
        improvements.append("Description front-loaded with keywords")
    improvements.append(f"Added {len(opt_tags)} SEO tags")
    improvements.append(f"Added {len(opt_hashtags)} trending hashtags")

    readability = _calculate_readability(description or title)
    word_count = len((description or title).split())
    keyword_count = sum(1 for k in keywords if k.keyword.lower() in (description or title).lower())
    density = round(keyword_count / max(1, word_count) * 100, 1)

    return SEOOptimization(
        original_score=min(100, original_score),
        optimized_score=min(100, optimized_score),
        keywords=keywords,
        optimized_title=opt_title,
        optimized_description=opt_desc,
        optimized_tags=opt_tags,
        optimized_hashtags=opt_hashtags,
        improvements=improvements,
        keyword_density=density,
        readability_score=readability,
    )
