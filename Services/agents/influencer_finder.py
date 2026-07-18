"""Find influencers in a niche."""

import hashlib

from pydantic import BaseModel


class Influencer(BaseModel):
    influencer_id: str = ""
    name: str
    platform: str
    niche: str
    followers: int = 0
    engagement_rate: float = 0.0
    avg_likes: int = 0
    avg_comments: int = 0
    content_type: str = ""
    collaboration_cost: str = ""
    relevance_score: float = 0.0


class InfluencerFinder:
    def __init__(self):
        self.discovered: list[Influencer] = []
        self._niche_data: dict[str, list[dict]] = {
            "electronics": [
                {"name": "TechReviewerID", "followers": 500000, "er": 4.5, "type": "reviews"},
                {"name": "GadgetHunter", "followers": 200000, "er": 6.2, "type": "unboxing"},
                {"name": "TechTipsDaily", "followers": 150000, "er": 5.8, "type": "tutorials"},
            ],
            "fashion": [
                {"name": "StyleWithMaya", "followers": 800000, "er": 3.8, "type": "ootd"},
                {"name": "FashionFinds", "followers": 300000, "er": 5.5, "type": "haul"},
                {"name": "OOTD_Inspo", "followers": 450000, "er": 4.2, "type": "lookbook"},
            ],
            "beauty": [
                {"name": "BeautyBySara", "followers": 1000000, "er": 3.2, "type": "tutorial"},
                {"name": "SkincareQueen", "followers": 600000, "er": 5.1, "type": "reviews"},
                {"name": "MakeupMoments", "followers": 350000, "er": 4.8, "type": "grwm"},
            ],
            "general": [
                {"name": "LifestyleWithA", "followers": 250000, "er": 4.0, "type": "lifestyle"},
                {"name": "DailyVlogger", "followers": 180000, "er": 5.5, "type": "vlog"},
                {"name": "TrendAlert", "followers": 400000, "er": 6.0, "type": "trends"},
            ],
        }

    async def find_influencers(
        self,
        niche: str = "general",
        platform: str = "tiktok",
        min_followers: int = 0,
        max_followers: int = 999999999,
        count: int = 5,
    ) -> list[Influencer]:
        data = self._niche_data.get(niche, self._niche_data["general"])
        results: list[Influencer] = []
        for d in data[:count]:
            if min_followers <= d["followers"] <= max_followers:
                iid = hashlib.md5(f"{d['name']}:{platform}".encode()).hexdigest()[:10]
                inf = Influencer(
                    influencer_id=iid,
                    name=d["name"],
                    platform=platform,
                    niche=niche,
                    followers=d["followers"],
                    engagement_rate=d["er"],
                    avg_likes=int(d["followers"] * d["er"] / 100),
                    avg_comments=int(d["followers"] * d["er"] / 500),
                    content_type=d["type"],
                    collaboration_cost="Mid-range" if d["followers"] < 500000 else "Premium",
                    relevance_score=round(min(1.0, d["er"] / 6), 2),
                )
                results.append(inf)
                self.discovered.append(inf)
        return results

    async def rank_by_engagement(self, platform: str = "", limit: int = 10) -> list[Influencer]:
        candidates = self.discovered
        if platform:
            candidates = [i for i in candidates if i.platform == platform]
        ranked = sorted(candidates, key=lambda i: i.engagement_rate, reverse=True)
        return ranked[:limit]

    async def rank_by_relevance(self, platform: str = "", limit: int = 10) -> list[Influencer]:
        candidates = self.discovered
        if platform:
            candidates = [i for i in candidates if i.platform == platform]
        ranked = sorted(candidates, key=lambda i: i.relevance_score, reverse=True)
        return ranked[:limit]

    async def get_discovered(self, niche: str = "", limit: int = 20) -> list[Influencer]:
        result = self.discovered
        if niche:
            result = [i for i in result if i.niche == niche]
        return result[-limit:]

    async def get_stats(self) -> dict:
        by_niche: dict[str, int] = {}
        by_platform: dict[str, int] = {}
        for i in self.discovered:
            by_niche[i.niche] = by_niche.get(i.niche, 0) + 1
            by_platform[i.platform] = by_platform.get(i.platform, 0) + 1
        return {
            "total_discovered": len(self.discovered),
            "by_niche": by_niche,
            "by_platform": by_platform,
        }
