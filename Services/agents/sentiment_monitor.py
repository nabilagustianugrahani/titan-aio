"""Sentiment Monitor — real-time brand sentiment tracking and crisis detection."""

from __future__ import annotations

import random
from datetime import datetime

from pydantic import BaseModel

# ── Models ───────────────────────────────────────────────────────

class SentimentAlert(BaseModel):
    alert_type: str = "info"
    severity: str = "low"
    message: str
    recommended_action: str = ""
    platform: str = ""
    timestamp: str = ""


class PlatformSentiment(BaseModel):
    platform: str
    sentiment_score: float = 0.0
    mention_count: int = 0
    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    trend: str = "stable"


class SentimentReport(BaseModel):
    overall_sentiment: float = 0.0
    sentiment_trend: str = "stable"
    crisis_detected: bool = False
    alerts: list[SentimentAlert]
    content_pivots: list[str]
    platform_breakdown: list[PlatformSentiment]
    total_mentions: int = 0
    recommendation: str = ""


# ── Engine ───────────────────────────────────────────────────────

async def monitor_sentiment(
    brand_name: str,
    platforms: str = "tiktok,instagram,twitter",
    niche: str = "general",
) -> SentimentReport:
    """Monitor brand sentiment across platforms."""
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    platform_sentiments = []
    all_alerts = []
    total_mentions = 0
    overall_scores = []

    for platform in platform_list:
        # Simulate sentiment analysis
        sentiment = round(random.uniform(-0.3, 0.8), 2)
        mentions = random.randint(10, 500)
        positive = round(random.uniform(0.4, 0.8), 2)
        negative = round(1 - positive - random.uniform(0.1, 0.3), 2)
        negative = max(0.0, negative)
        trend = "stable"
        if sentiment > 0.5:
            trend = "improving"
        elif sentiment < -0.1:
            trend = "declining"

        ps = PlatformSentiment(
            platform=platform,
            sentiment_score=sentiment,
            mention_count=mentions,
            positive_ratio=positive,
            negative_ratio=negative,
            trend=trend,
        )
        platform_sentiments.append(ps)
        total_mentions += mentions
        overall_scores.append(sentiment)

        # Generate alerts
        if sentiment < -0.2:
            all_alerts.append(SentimentAlert(
                alert_type="crisis",
                severity="high" if sentiment < -0.4 else "medium",
                message=f"Negative sentiment detected on {platform} (score: {sentiment})",
                recommended_action="Pause affiliate content, create response content",
                platform=platform,
                timestamp=datetime.now().isoformat(),
            ))
        elif sentiment > 0.6:
            all_alerts.append(SentimentAlert(
                alert_type="opportunity",
                severity="low",
                message=f"Positive sentiment surge on {platform} (score: {sentiment})",
                recommended_action="Scale posting frequency, double down on winning content",
                platform=platform,
                timestamp=datetime.now().isoformat(),
            ))

    overall = round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0
    crisis = any(a.alert_type == "crisis" for a in all_alerts)

    # Content pivots
    pivots = []
    if crisis:
        pivots = [
            "Create empathetic response content",
            "Switch to educational/value content temporarily",
            "Address negative feedback directly",
        ]
    elif overall < 0:
        pivots = [
            "Focus on positive testimonials",
            "Create comparison content showing benefits",
            "Use user-generated content for authenticity",
        ]

    # Recommendation
    if crisis:
        rec = "🚨 Crisis mode — pause affiliate posting, focus on brand reputation recovery"
    elif overall > 0.5:
        rec = "✅ Sentiment is strong — scale posting and increase ad spend"
    elif overall > 0:
        rec = "👍 Sentiment is positive — maintain current strategy"
    else:
        rec = "⚠️ Sentiment needs improvement — adjust content tone"

    return SentimentReport(
        overall_sentiment=overall,
        sentiment_trend="improving" if overall > 0.3 else ("declining" if overall < 0 else "stable"),
        crisis_detected=crisis,
        alerts=all_alerts,
        content_pivots=pivots,
        platform_breakdown=platform_sentiments,
        total_mentions=total_mentions,
        recommendation=rec,
    )
