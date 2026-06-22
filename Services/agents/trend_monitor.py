"""Real-Time Trend Monitor — detect emerging trends across platforms."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta

from pydantic import BaseModel, Field


# ── Models ───────────────────────────────────────────────────────

class TrendInput(BaseModel):
    platform: str = "tiktok"
    niche: str = "general"
    limit: int = 10


class TrendAlert(BaseModel):
    trend_id: str
    platform: str
    topic: str
    velocity: float = Field(description="Growth rate 0-1")
    relevance_score: float = Field(ge=0, le=1)
    peak_prediction: str = ""
    content_suggestion: str = ""
    urgency: str = "medium"
    hashtags: list[str] = []
    engagement_score: float = 0.0


class TrendReport(BaseModel):
    trends: list[TrendAlert]
    total_trends: int
    urgent_count: int
    niche_opportunities: list[str]
    platform_summary: dict[str, int]


# ── Trend Database (in-memory, simulates real-time data) ─────────

TREND_TEMPLATES = {
    "tiktok": {
        "electronics": [
            {"topic": "Phone hack viral", "hashtags": ["#phonehack", "#techtips", "#viral"], "velocity": 0.85},
            {"topic": "Budget gadget review", "hashtags": ["#gadget", "#review", "#murah"], "velocity": 0.72},
            {"topic": "AI tool trending", "hashtags": ["#ai", "#tool", "#productivity"], "velocity": 0.91},
        ],
        "fashion": [
            {"topic": "OOTD transformation", "hashtags": ["#ootd", "#fashion", "#transformation"], "velocity": 0.88},
            {"topic": "Thrift haul", "hashtags": ["#thrift", "#haul", "#fashion"], "velocity": 0.76},
            {"topic": "Style hack", "hashtags": ["#style", "#hack", "#tips"], "velocity": 0.69},
        ],
        "beauty": [
            {"topic": "Skincare routine viral", "hashtags": ["#skincare", "#routine", "#glow"], "velocity": 0.93},
            {"topic": "Makeup transformation", "hashtags": ["#makeup", "#transformation", "#beauty"], "velocity": 0.87},
            {"topic": "Budget beauty finds", "hashtags": ["#beauty", "#budget", "#finds"], "velocity": 0.74},
        ],
        "food": [
            {"topic": "Recipe hack viral", "hashtags": ["#recipe", "#hack", "#food"], "velocity": 0.82},
            {"topic": "Street food review", "hashtags": ["#streetfood", "#review", "#foodie"], "velocity": 0.79},
            {"topic": "Cooking hack", "hashtags": ["#cooking", "#hack", "#easy"], "velocity": 0.71},
        ],
        "general": [
            {"topic": "Life hack trending", "hashtags": ["#lifehack", "#tips", "#viral"], "velocity": 0.80},
            {"topic": "Before after transformation", "hashtags": ["#beforeafter", "#transformation"], "velocity": 0.84},
            {"topic": "Day in my life", "hashtags": ["#dayinmylife", "#vlog", "#daily"], "velocity": 0.77},
        ],
    },
    "instagram": {
        "electronics": [
            {"topic": "Tech reel trending", "hashtags": ["#tech", "#reels", "#gadget"], "velocity": 0.75},
            {"topic": "Unboxing viral", "hashtags": ["#unboxing", "#tech", "#new"], "velocity": 0.82},
        ],
        "fashion": [
            {"topic": "Fashion reel", "hashtags": ["#fashion", "#reels", "#style"], "velocity": 0.88},
            {"topic": "OOTD carousel", "hashtags": ["#ootd", "#carousel", "#fashion"], "velocity": 0.79},
        ],
        "beauty": [
            {"topic": "Beauty tutorial reel", "hashtags": ["#beauty", "#tutorial", "#reels"], "velocity": 0.90},
        ],
        "general": [
            {"topic": "Motivational reel", "hashtags": ["#motivation", "#reels", "#inspiration"], "velocity": 0.76},
            {"topic": "Travel content", "hashtags": ["#travel", "#reels", "#explore"], "velocity": 0.83},
        ],
    },
    "youtube": {
        "general": [
            {"topic": "Shorts trending", "hashtags": ["#shorts", "#viral", "#trending"], "velocity": 0.81},
            {"topic": "Tutorial series", "hashtags": ["#tutorial", "#howto", "#learn"], "velocity": 0.73},
        ],
    },
    "twitter": {
        "general": [
            {"topic": "Thread trending", "hashtags": ["#thread", "#twitter", "#viral"], "velocity": 0.70},
            {"topic": "Tech discussion", "hashtags": ["#tech", "#discussion", "#hot"], "velocity": 0.68},
        ],
    },
    "facebook": {
        "general": [
            {"topic": "Video viral", "hashtags": ["#video", "#viral", "#facebook"], "velocity": 0.65},
        ],
    },
}

NICHE_CONTENT_SUGGESTIONS = {
    "electronics": "Create comparison or unboxing content. Show real usage.",
    "fashion": "Before/after transformation. Style tips with trending audio.",
    "beauty": "Tutorial format. Show real results, not just product.",
    "food": "Recipe hack or review. Show the process step by step.",
    "health": "Educational content. Share tips with credibility.",
    "fitness": "Workout routine or transformation. Show progress.",
    "tech": "How-to tutorial. Solve a specific problem.",
    "general": "Follow the trend format. Add your unique angle.",
}


# ── Engine ───────────────────────────────────────────────────────

async def monitor_trends(input_data: TrendInput) -> TrendReport:
    """Detect trending topics for a platform and niche."""
    platform = input_data.platform
    niche = input_data.niche
    limit = input_data.limit

    # Get templates for platform/niche
    platform_trends = TREND_TEMPLATES.get(platform, TREND_TEMPLATES["tiktok"])
    niche_trends = platform_trends.get(niche, platform_trends.get("general", []))

    # Add some randomness to simulate real-time data
    trends = []
    for i, t in enumerate(niche_trends[:limit]):
        velocity = min(1.0, t["velocity"] + random.uniform(-0.1, 0.1))
        engagement = round(random.uniform(0.5, 0.95), 2)
        relevance = round(random.uniform(0.6, 0.95), 2)

        urgency = "low"
        if velocity > 0.85:
            urgency = "critical"
        elif velocity > 0.75:
            urgency = "high"
        elif velocity > 0.65:
            urgency = "medium"

        # Predict peak (1-7 days from now)
        days_to_peak = max(1, int((1 - velocity) * 7) + random.randint(0, 2))
        peak = (datetime.now() + timedelta(days=days_to_peak)).strftime("%Y-%m-%d")

        trend_id = hashlib.md5(f"{platform}:{t['topic']}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        trends.append(TrendAlert(
            trend_id=trend_id,
            platform=platform,
            topic=t["topic"],
            velocity=round(velocity, 2),
            relevance_score=relevance,
            peak_prediction=peak,
            content_suggestion=NICHE_CONTENT_SUGGESTIONS.get(niche, NICHE_CONTENT_SUGGESTIONS["general"]),
            urgency=urgency,
            hashtags=t["hashtags"],
            engagement_score=engagement,
        ))

    # Sort by velocity (hottest first)
    trends.sort(key=lambda x: x.velocity, reverse=True)

    urgent_count = sum(1 for t in trends if t.urgency in ("high", "critical"))
    niche_opps = [
        f"Gap: No one covering {niche} + {t['topic'].lower()} combo"
        for t in niche_trends[:3]
        if random.random() > 0.5
    ]

    return TrendReport(
        trends=trends,
        total_trends=len(trends),
        urgent_count=urgent_count,
        niche_opportunities=niche_opps or [f"Opportunity: {niche} content on {platform} is growing"],
        platform_summary={platform: len(trends)},
    )
