"""Brand mention tracking across social media."""

from pydantic import BaseModel
from datetime import datetime
import hashlib


class BrandMention(BaseModel):
    mention_id: str = ""
    brand: str
    platform: str
    text: str = ""
    sentiment: str = "neutral"  # positive/neutral/negative
    url: str = ""
    author: str = ""
    timestamp: str = ""


class SocialListener:
    def __init__(self):
        self.mentions: list[BrandMention] = []
        self.watched_brands: list[str] = []

    async def add_brand(self, brand: str):
        if brand not in self.watched_brands:
            self.watched_brands.append(brand)

    async def record_mention(
        self,
        brand: str,
        platform: str,
        text: str = "",
        sentiment: str = "neutral",
        url: str = "",
        author: str = "",
    ) -> BrandMention:
        mid = hashlib.md5(f"{brand}:{platform}:{text[:50]}".encode()).hexdigest()[:10]
        mention = BrandMention(
            mention_id=mid,
            brand=brand,
            platform=platform,
            text=text,
            sentiment=sentiment,
            url=url,
            author=author,
            timestamp=datetime.now().isoformat(),
        )
        self.mentions.append(mention)
        if brand not in self.watched_brands:
            self.watched_brands.append(brand)
        return mention

    async def get_mentions(
        self,
        brand: str = "",
        platform: str = "",
        sentiment: str = "",
        limit: int = 50,
    ) -> list[BrandMention]:
        result = self.mentions
        if brand:
            result = [m for m in result if m.brand.lower() == brand.lower()]
        if platform:
            result = [m for m in result if m.platform == platform]
        if sentiment:
            result = [m for m in result if m.sentiment == sentiment]
        return result[-limit:]

    async def get_sentiment_summary(self, brand: str = "") -> dict:
        mentions = [
            m for m in self.mentions
            if not brand or m.brand.lower() == brand.lower()
        ]
        pos = sum(1 for m in mentions if m.sentiment == "positive")
        neg = sum(1 for m in mentions if m.sentiment == "negative")
        neu = sum(1 for m in mentions if m.sentiment == "neutral")
        total = len(mentions)
        return {
            "total": total,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "positive_ratio": round(pos / max(1, total), 2),
        }

    async def get_mentions_by_author(self, brand: str = "") -> dict[str, int]:
        mentions = [
            m for m in self.mentions
            if not brand or m.brand.lower() == brand.lower()
        ]
        authors: dict[str, int] = {}
        for m in mentions:
            key = m.author or "unknown"
            authors[key] = authors.get(key, 0) + 1
        return authors

    async def get_platform_breakdown(self, brand: str = "") -> dict[str, dict]:
        mentions = [
            m for m in self.mentions
            if not brand or m.brand.lower() == brand.lower()
        ]
        breakdown: dict[str, dict] = {}
        for m in mentions:
            if m.platform not in breakdown:
                breakdown[m.platform] = {"count": 0, "positive": 0, "negative": 0, "neutral": 0}
            breakdown[m.platform]["count"] += 1
            breakdown[m.platform][m.sentiment] = breakdown[m.platform].get(m.sentiment, 0) + 1
        return breakdown

    async def get_stats(self) -> dict:
        return {
            "total_mentions": len(self.mentions),
            "watched_brands": len(self.watched_brands),
            "sentiment_summary": await self.get_sentiment_summary(),
        }
