"""Content Ideas Generator — AI-powered content suggestions.

Generates platform-specific content ideas with hooks, descriptions,
engagement estimates, hashtags, CTAs, and scheduling suggestions.
Covers niches: electronics, fashion, beauty, food, health_fitness, general.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Models ──────────────────────────────────────────────────────────────

class ContentIdea(BaseModel):
    idea_id: str = ""
    title: str
    description: str
    platform: str
    content_type: str  # video / carousel / thread / reel / story / vlog
    hook_suggestion: str = ""
    estimated_engagement: str = ""  # High / Medium / Low
    difficulty: str = "easy"  # easy / medium / hard
    tags: list[str] = []
    category: str = ""
    cta_suggestion: str = ""
    hashtags: list[str] = []
    best_time: str = ""  # e.g. "19:00-21:00"


class NicheReport(BaseModel):
    niche: str
    total_ideas: int
    content_types: dict[str, int]
    platforms: dict[str, int]
    avg_engagement: str
    top_hooks: list[str]


# ── Niche Templates ────────────────────────────────────────────────────

_NICHE_TEMPLATES: dict[str, list[dict]] = {
    "electronics": [
        {
            "title": "Unboxing + First Impressions",
            "type": "video",
            "hook": "You won't believe what's inside this box!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk harga terbaik!",
        },
        {
            "title": "5 Features You Didn't Know",
            "type": "carousel",
            "hook": "99% of people don't know these 5 features!",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Save this post for later!",
        },
        {
            "title": "Honest Review After 30 Days",
            "type": "video",
            "hook": "I used this for 30 days... here's the truth",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Link di bio! Follow untuk review jujur lainnya.",
        },
        {
            "title": "vs Competitor Comparison",
            "type": "video",
            "hook": "Which one is ACTUALLY better? Let's find out",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Comment which one you'd pick!",
        },
        {
            "title": "Budget vs Premium",
            "type": "video",
            "hook": "Is the expensive one worth it?",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Link di bio untuk cek harga!",
        },
        {
            "title": "Top 5 Gadgets Under 100K",
            "type": "carousel",
            "hook": "5 gadgets under Rp100rb that actually work!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Save & share ke teman yang butuh!",
        },
        {
            "title": "Setup Tour / Desk Setup",
            "type": "reel",
            "hook": "My dream desk setup tour",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "All products linked di bio!",
        },
        {
            "title": "Myth Busting",
            "type": "video",
            "hook": "Stop believing these 3 tech myths!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Share ke yang masih percaya mitos ini!",
        },
        {
            "title": "One Month Later Update",
            "type": "video",
            "hook": "One month later... has my opinion changed?",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Link di bio kalau mau coba sendiri!",
        },
        {
            "title": "Gift Guide / Best Buys",
            "type": "carousel",
            "hook": "Perfect gift ideas for the tech lover in your life",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Tag someone who needs this!",
        },
    ],
    "fashion": [
        {
            "title": "OOTD Transformation",
            "type": "reel",
            "hook": "From basic to ICONIC in 60 seconds",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "All outfit details di bio!",
        },
        {
            "title": "Thrift Haul Finds",
            "type": "video",
            "hook": "I found GEMS at the thrift store!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk similar items!",
        },
        {
            "title": "Style Tips for the Season",
            "type": "carousel",
            "hook": "5 outfits that will make heads turn",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Save untuk outfit inspiration!",
        },
        {
            "title": "Outfit Challenge",
            "type": "reel",
            "hook": "Can I style this ONE piece 5 different ways?",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Comment which look is your fave!",
        },
        {
            "title": "Capsule Wardrobe Guide",
            "type": "carousel",
            "hook": "10 pieces, 30 outfits. Here's how.",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Save this for your next shopping trip!",
        },
        {
            "title": "Try-On Haul",
            "type": "video",
            "hook": "I ordered 10 outfits... here's what happened",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk shop the look!",
        },
        {
            "title": "Style Mistakes to Avoid",
            "type": "reel",
            "hook": "Stop making these 5 fashion mistakes!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Tag someone who needs to see this!",
        },
        {
            "title": "Price Comparison",
            "type": "carousel",
            "hook": "Luxury vs dupe: can you tell the difference?",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Comment if you can guess the price!",
        },
    ],
    "beauty": [
        {
            "title": "Skincare Routine",
            "type": "reel",
            "hook": "This routine changed my skin in 2 weeks!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "All products linked di bio!",
        },
        {
            "title": "Product Empties Review",
            "type": "video",
            "hook": "Products I actually finished -- honest reviews",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Link di bio untuk restock!",
        },
        {
            "title": "Get Ready With Me",
            "type": "reel",
            "hook": "GRWM for a casual day out",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Products di bio, link di bio!",
        },
        {
            "title": "Dupe vs Original",
            "type": "video",
            "hook": "Is this Rp50rb dupe as good as the Rp500rb original?",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Comment which one you'd buy!",
        },
        {
            "title": "60-Second Makeup Challenge",
            "type": "reel",
            "hook": "Full face makeup in 60 seconds -- challenge accepted!",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Try this yourself and tag me!",
        },
        {
            "title": "Skincare Ingredient Explained",
            "type": "carousel",
            "hook": "NIACINAMIDE: what it actually does (no BS)",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Save this guide for your next skincare shopping!",
        },
        {
            "title": "What I'd Buy vs What I'd Skip",
            "type": "video",
            "hook": "I tested 20 viral beauty products so you don't have to",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk yang worth it!",
        },
    ],
    "food": [
        {
            "title": "Quick Recipe Hack",
            "type": "reel",
            "hook": "This 5-minute recipe is a GAME CHANGER",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Ingredients list di bio!",
        },
        {
            "title": "Taste Test Challenge",
            "type": "video",
            "hook": "Can I guess the price? Blind taste test!",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Comment your guesses!",
        },
        {
            "title": "Food Review",
            "type": "video",
            "hook": "I tried the viral food so you don't have to",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk order!",
        },
        {
            "title": "Budget Meal Prep",
            "type": "carousel",
            "hook": "5 meals for under Rp50rb total",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Save this for your meal prep Sunday!",
        },
        {
            "title": "Street Food Tour",
            "type": "vlog",
            "hook": "I ate everything at the market -- here's the best",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Link di bio untuk lokasi!",
        },
        {
            "title": "Kitchen Gadget Test",
            "type": "video",
            "hook": "Does this viral kitchen gadget actually work?",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio kalau mau coba!",
        },
        {
            "title": "Grocery Haul on a Budget",
            "type": "reel",
            "hook": "I fed my family for a week with Rp100rb",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Save this budget shopping list!",
        },
    ],
    "health_fitness": [
        {
            "title": "Workout Routine",
            "type": "reel",
            "hook": "Full body workout you can do at home -- zero equipment",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Save this for your next workout!",
        },
        {
            "title": "What I Eat in a Day",
            "type": "video",
            "hook": "What I eat in a day to lose weight",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "All products linked di bio!",
        },
        {
            "title": "Fitness Myth Busting",
            "type": "reel",
            "hook": "Stop doing crunches if you want abs!",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Share ke teman yang masih salah informasi!",
        },
        {
            "title": "Supplement Review",
            "type": "video",
            "hook": "I tried this supplement for 30 days -- honest results",
            "difficulty": "medium",
            "engagement": "Medium",
            "cta": "Link di bio untuk harga terbaik!",
        },
        {
            "title": "Before & After Transformation",
            "type": "reel",
            "hook": "3 months of consistency. Here's the result.",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Follow untuk daily motivation!",
        },
    ],
    "general": [
        {
            "title": "Day in My Life",
            "type": "vlog",
            "hook": "A day in my life as an affiliate marketer",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Follow untuk daily content!",
        },
        {
            "title": "Before & After",
            "type": "reel",
            "hook": "The transformation is INSANE",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Link di bio untuk produk yang dipake!",
        },
        {
            "title": "Tutorial / How-To",
            "type": "video",
            "hook": "How I got results in just one week",
            "difficulty": "medium",
            "engagement": "High",
            "cta": "Save this tutorial!",
        },
        {
            "title": "Top 5 List",
            "type": "carousel",
            "hook": "5 products that changed my life in 2026",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Save & share ke teman!",
        },
        {
            "title": "Controversial Opinion",
            "type": "video",
            "hook": "This might be controversial but...",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Comment your opinion!",
        },
        {
            "title": "Challenge / Trend",
            "type": "reel",
            "hook": "Trying the viral trend -- here's what happened",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Tag someone who should try this!",
        },
        {
            "title": "Story Time",
            "type": "video",
            "hook": "Something crazy happened today...",
            "difficulty": "easy",
            "engagement": "High",
            "cta": "Follow untuk part 2!",
        },
        {
            "title": "React to Comments",
            "type": "reel",
            "hook": "Replying to your most liked comments",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Drop a comment for the next video!",
        },
        {
            "title": "Productivity Hack",
            "type": "carousel",
            "hook": "This one hack saved me 2 hours every day",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Save this for later!",
        },
        {
            "title": "Q&A Session",
            "type": "video",
            "hook": "You asked, I answered -- all your questions!",
            "difficulty": "easy",
            "engagement": "Medium",
            "cta": "Drop your questions for the next Q&A!",
        },
    ],
}

# ── Hashtag Pools ───────────────────────────────────────────────────────

_PLATFORM_HASHTAGS: dict[str, list[str]] = {
    "tiktok": [
        "fyp", "foryou", "foryoupage", "viral", "tiktokindonesia",
        "tiktokviral", "trend", "trending", "explore", "viralindonesia",
    ],
    "instagram": [
        "instagood", "photooftheday", "love", "beautiful", "happy",
        "follow", "like4like", "instadaily", "trending", "viral",
    ],
    "youtube": [
        "youtube", "subscribe", "youtubers", "newvideo", "tutorial",
        "review", "honestreview", "unboxing", "techreview", "bestof",
    ],
    "facebook": [
        "facebook", "viral", "share", "trending", "fyp",
    ],
    "twitter": [
        "twitter", "trending", "viral", "hot", "breaking",
    ],
    "shopee": [
        "shopee", "shopeefinds", "shopeesale", "rekomendasi",
        "diskon", "flashsale",
    ],
    "tokopedia": [
        "tokopedia", "tokofinds", "rekomendasi", "terlaris",
    ],
}

_NICHE_HASHTAGS: dict[str, list[str]] = {
    "electronics": [
        "tech", "gadget", "gadgetreview", "techtok", "techreview",
        "gadgettok", "electronic", "smartdevice",
    ],
    "fashion": [
        "fashion", "ootd", "style", "fashionstyle", "outfitoftheday",
        "streetstyle", "fashioninspo", "styleinspo",
    ],
    "beauty": [
        "beauty", "skincare", "makeup", "beautytok", "skincareroutine",
        "makeuptutorial", "beautyhacks", "glowup",
    ],
    "food": [
        "food", "foodie", "recipe", "cooking", "foodreview",
        "foodtok", "easyrecipe", "mukbang",
    ],
    "health_fitness": [
        "fitness", "workout", "health", "gym", "fitnesstok",
        "healthylifestyle", "motivation", "weightloss",
    ],
    "general": [
        "lifehack", "tips", "motivation", "lifestyle", "daily",
        "trending", "viral", "explore",
    ],
}

_PLATFORM_TIME_WINDOWS: dict[str, str] = {
    "tiktok": "19:00-21:00",
    "instagram": "11:00-13:00",
    "youtube": "14:00-16:00",
    "twitter": "08:00-10:00",
    "facebook": "13:00-15:00",
    "shopee": "20:00-22:00",
    "tokopedia": "20:00-22:00",
}


# ── Ideas Generator ─────────────────────────────────────────────────────

class IdeasGenerator:
    """Generate platform-specific content ideas from niche templates.

    Supports niches: electronics, fashion, beauty, food, health_fitness, general.
    Each idea includes hooks, CTAs, hashtags, and optimal posting times.
    """

    def __init__(self) -> None:
        self.ideas: list[ContentIdea] = []
        self._generated_ids: set[str] = set()

    # ── Core API ────────────────────────────────────────────────────────

    async def generate_ideas(
        self,
        niche: str = "general",
        platform: str = "tiktok",
        count: int = 5,
    ) -> list[ContentIdea]:
        """Generate content ideas for a niche and platform.

        Selects templates, adds platform-specific hashtags, hooks, and CTAs.
        Shuffles templates for variety across calls.
        """
        niche_lower = niche.lower().strip()
        templates = _NICHE_TEMPLATES.get(
            niche_lower, _NICHE_TEMPLATES["general"]
        )
        hashtags = _NICHE_HASHTAGS.get(niche_lower, _NICHE_HASHTAGS["general"])
        platform_tags = _PLATFORM_HASHTAGS.get(platform.lower(), [])
        time_window = _PLATFORM_TIME_WINDOWS.get(
            platform.lower(), "12:00-14:00"
        )

        # Shuffle for variety, then take count
        available = list(templates)
        random.shuffle(available)
        selected = available[:count]

        ideas: list[ContentIdea] = []
        for i, t in enumerate(selected):
            idea_id = self._make_id(niche_lower, platform, t["title"], i)

            # Build hashtags: 3 niche + 2 platform
            idea_hashtags = list(hashtags[:3]) + list(platform_tags[:2])

            # Build description
            desc = self._build_description(t, platform, niche_lower)

            idea = ContentIdea(
                idea_id=idea_id,
                title=t["title"],
                description=desc,
                platform=platform.lower(),
                content_type=t["type"],
                hook_suggestion=t["hook"],
                estimated_engagement=t.get("engagement", "Medium"),
                difficulty=t.get("difficulty", "easy"),
                tags=[niche_lower, platform.lower(), t["type"]],
                category=niche_lower,
                cta_suggestion=t.get(
                    "cta", f"Link di bio! ({platform})"
                ),
                hashtags=idea_hashtags,
                best_time=time_window,
            )
            ideas.append(idea)
            self.ideas.append(idea)
            self._generated_ids.add(idea_id)

        return ideas

    async def generate_for_platforms(
        self,
        niche: str = "general",
        platforms: Optional[list[str]] = None,
        count_per_platform: int = 3,
    ) -> dict[str, list[ContentIdea]]:
        """Generate ideas across multiple platforms at once."""
        if platforms is None:
            platforms = ["tiktok", "instagram", "facebook"]

        result: dict[str, list[ContentIdea]] = {}
        for platform in platforms:
            ideas = await self.generate_ideas(
                niche=niche, platform=platform, count=count_per_platform
            )
            result[platform] = ideas
        return result

    async def get_ideas(
        self,
        niche: str = "",
        platform: str = "",
        content_type: str = "",
        limit: int = 20,
    ) -> list[ContentIdea]:
        """Query previously generated ideas with optional filters."""
        result = list(self.ideas)
        if niche:
            result = [i for i in result if niche.lower() in i.tags]
        if platform:
            result = [i for i in result if i.platform == platform.lower()]
        if content_type:
            result = [
                i for i in result if i.content_type == content_type.lower()
            ]
        return result[-limit:]

    async def get_niche_report(self, niche: str) -> NicheReport:
        """Generate a summary report for a niche."""
        niche_ideas = [
            i for i in self.ideas if niche.lower() in i.tags
        ]

        content_types: dict[str, int] = defaultdict(int)
        platforms: dict[str, int] = defaultdict(int)
        hooks: list[str] = []

        for idea in niche_ideas:
            content_types[idea.content_type] += 1
            platforms[idea.platform] += 1
            if idea.hook_suggestion:
                hooks.append(idea.hook_suggestion)

        if niche_ideas:
            high_count = sum(
                1 for i in niche_ideas if i.estimated_engagement == "High"
            )
            avg_eng = "High" if high_count > len(niche_ideas) / 2 else "Medium"
        else:
            avg_eng = "N/A"

        return NicheReport(
            niche=niche,
            total_ideas=len(niche_ideas),
            content_types=dict(content_types),
            platforms=dict(platforms),
            avg_engagement=avg_eng,
            top_hooks=hooks[:5],
        )

    async def get_trending_hooks(
        self, platform: str = "", limit: int = 10
    ) -> list[str]:
        """Return top hooks, optionally filtered by platform."""
        hooks: list[str] = []
        seen: set[str] = set()
        for idea in reversed(self.ideas):
            if platform and idea.platform != platform.lower():
                continue
            hook = idea.hook_suggestion
            if hook and hook not in seen:
                hooks.append(hook)
                seen.add(hook)
            if len(hooks) >= limit:
                break
        return hooks

    async def suggest_weekly_content(
        self, niche: str = "general", platform: str = "tiktok"
    ) -> list[dict]:
        """Suggest a 7-day content calendar with one idea per day."""
        ideas = await self.generate_ideas(
            niche=niche, platform=platform, count=7
        )
        days = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]
        calendar: list[dict] = []
        for i, idea in enumerate(ideas):
            day = days[i % 7]
            calendar.append({
                "day": day,
                "title": idea.title,
                "content_type": idea.content_type,
                "hook": idea.hook_suggestion,
                "cta": idea.cta_suggestion,
                "best_time": idea.best_time,
                "engagement": idea.estimated_engagement,
                "difficulty": idea.difficulty,
                "hashtags": idea.hashtags,
            })
        return calendar

    async def get_stats(self) -> dict:
        """Return generator statistics."""
        niche_counts: dict[str, int] = defaultdict(int)
        platform_counts: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)

        for idea in self.ideas:
            for tag in idea.tags:
                niche_counts[tag] += 1
            platform_counts[idea.platform] += 1
            type_counts[idea.content_type] += 1

        return {
            "total_ideas": len(self.ideas),
            "unique_ids": len(self._generated_ids),
            "by_niche": dict(niche_counts),
            "by_platform": dict(platform_counts),
            "by_type": dict(type_counts),
        }

    # ── Internal ────────────────────────────────────────────────────────

    @staticmethod
    def _make_id(niche: str, platform: str, title: str, index: int) -> str:
        """Generate a deterministic idea ID."""
        raw = (
            f"{niche}:{platform}:{title}:{index}:"
            f"{datetime.now().strftime('%Y%m%d%H')}"
        )
        return hashlib.md5(raw.encode()).hexdigest()[:10]

    @staticmethod
    def _build_description(template: dict, platform: str, niche: str) -> str:
        """Build a rich description from a template."""
        title = template["title"]
        content_type = template["type"]
        return (
            f"Create a {content_type} about '{title.lower()}' for {platform}. "
            f"Target niche: {niche}. "
            f"Focus on providing value to the audience while showcasing "
            f"the affiliate product naturally within the content."
        )
