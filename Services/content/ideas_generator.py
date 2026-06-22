"""Content Ideas Generator — AI-powered content suggestions."""

from __future__ import annotations

from pydantic import BaseModel
import hashlib


class ContentIdea(BaseModel):
    idea_id: str = ""
    title: str
    description: str
    platform: str
    content_type: str
    hook_suggestion: str = ""
    estimated_engagement: str = ""
    difficulty: str = "easy"
    tags: list[str] = []


class IdeasGenerator:
    def __init__(self):
        self.ideas: list[ContentIdea] = []
        self._templates = {
            "electronics": [
                {"title": "Unboxing + First Impressions", "type": "video", "hook": "You won't believe what's inside this box! 📦"},
                {"title": "5 Features You Didn't Know", "type": "carousel", "hook": "99% of people don't know these 5 features!"},
                {"title": "Honest Review After 30 Days", "type": "video", "hook": "I used this for 30 days... here's the truth"},
                {"title": "vs Competitor Comparison", "type": "video", "hook": "Which one is ACTUALLY better? Let's find out"},
                {"title": "Budget vs Premium", "type": "video", "hook": "Is the expensive one worth it? 🤔"},
            ],
            "fashion": [
                {"title": "OOTD Transformation", "type": "reel", "hook": "From basic to ICONIC in 60 seconds ✨"},
                {"title": "Thrift Haul Finds", "type": "video", "hook": "I found GEMS at the thrift store! 🛍️"},
                {"title": "Style Tips for the Season", "type": "carousel", "hook": "5 outfits that will make heads turn"},
                {"title": "Outfit Challenge", "type": "reel", "hook": "Can I style this ONE piece 5 different ways?"},
            ],
            "beauty": [
                {"title": "Skincare Routine", "type": "reel", "hook": "This routine changed my skin in 2 weeks!"},
                {"title": "Product Empties Review", "type": "video", "hook": "Products I actually finished — honest reviews"},
                {"title": "Get Ready With Me", "type": "reel", "hook": "GRWM for a casual day out 💄"},
                {"title": "Dupe vs Original", "type": "video", "hook": "Is this $5 dupe as good as the $50 original?"},
            ],
            "food": [
                {"title": "Quick Recipe Hack", "type": "reel", "hook": "This 5-minute recipe is a GAME CHANGER 🍳"},
                {"title": "Taste Test Challenge", "type": "video", "hook": "Can I guess the price? Blind taste test!"},
                {"title": "Food Review", "type": "video", "hook": "I tried the viral food so you don't have to"},
            ],
            "general": [
                {"title": "Day in My Life", "type": "vlog", "hook": "A day in my life as an affiliate marketer"},
                {"title": "Before & After", "type": "reel", "hook": "The transformation is INSANE 😱"},
                {"title": "Tutorial / How-To", "type": "video", "hook": "How I got results in just one week"},
                {"title": "Top 5 List", "type": "carousel", "hook": "5 products that changed my life in 2026"},
                {"title": "Controversial Opinion", "type": "video", "hook": "This might be controversial but..."},
                {"title": "Challenge / Trend", "type": "reel", "hook": "Trying the viral trend — here's what happened"},
            ],
        }

    async def generate_ideas(self, niche: str = "general", platform: str = "tiktok", count: int = 5) -> list[ContentIdea]:
        templates = self._templates.get(niche, self._templates["general"])
        ideas = []
        for i, t in enumerate(templates[:count]):
            idea_id = hashlib.md5(f"{niche}:{t['title']}:{i}".encode()).hexdigest()[:10]
            idea = ContentIdea(
                idea_id=idea_id, title=t["title"], description=f"Create a {t['type']} about {t['title'].lower()} for {platform}",
                platform=platform, content_type=t["type"], hook_suggestion=t["hook"],
                estimated_engagement="High" if i < 2 else "Medium",
                difficulty="easy" if t["type"] in ("reel", "carousel") else "medium",
                tags=[niche, platform, t["type"]],
            )
            ideas.append(idea)
            self.ideas.append(idea)
        return ideas

    async def get_ideas(self, niche: str = "", platform: str = "", limit: int = 20) -> list[ContentIdea]:
        result = self.ideas
        if niche:
            result = [i for i in result if niche in i.tags]
        if platform:
            result = [i for i in result if i.platform == platform]
        return result[-limit:]

    async def get_stats(self) -> dict:
        return {"total_ideas": len(self.ideas)}
