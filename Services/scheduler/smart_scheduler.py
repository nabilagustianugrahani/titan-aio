"""Smart Scheduler — ML-based optimal posting time engine."""

from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class TimeSlot(BaseModel):
    hour: int
    day_of_week: str
    platform: str
    avg_engagement: float = 0.0
    post_count: int = 0
    score: float = 0.0


class SmartScheduler:
    def __init__(self):
        self.engagement_data: list[dict] = []
        self._platform_peaks = {
            "tiktok": [(19, 0.95), (20, 0.92), (21, 0.88), (12, 0.75)],
            "instagram": [(11, 0.90), (12, 0.88), (19, 0.85), (20, 0.82)],
            "youtube": [(14, 0.88), (15, 0.85), (10, 0.80), (20, 0.78)],
            "twitter": [(8, 0.90), (9, 0.88), (12, 0.85), (17, 0.80)],
            "facebook": [(13, 0.85), (14, 0.82), (15, 0.80), (19, 0.78)],
        }

    async def record_engagement(self, platform: str, hour: int, day_of_week: str, engagement_rate: float):
        self.engagement_data.append({"platform": platform, "hour": hour, "day": day_of_week, "engagement": engagement_rate, "timestamp": datetime.now().isoformat()})

    async def get_optimal_times(self, platform: str, count: int = 5) -> list[TimeSlot]:
        platform_data = [d for d in self.engagement_data if d["platform"] == platform]
        if len(platform_data) >= 10:
            hour_engagement: dict[int, list[float]] = {}
            for d in platform_data:
                h = d["hour"]
                if h not in hour_engagement:
                    hour_engagement[h] = []
                hour_engagement[h].append(d["engagement"])
            ranked = sorted(hour_engagement.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)
            slots = []
            for hour, engagements in ranked[:count]:
                avg = sum(engagements) / len(engagements)
                slots.append(TimeSlot(hour=hour, day_of_week="any", platform=platform, avg_engagement=round(avg, 3), post_count=len(engagements), score=round(avg * 100, 1)))
            return slots
        else:
            peaks = self._platform_peaks.get(platform, self._platform_peaks["tiktok"])
            return [TimeSlot(hour=h, day_of_week="any", platform=platform, avg_engagement=s, score=round(s * 100, 1)) for h, s in peaks[:count]]

    async def suggest_posting_schedule(self, platform: str, posts_per_day: int = 2) -> list[dict]:
        times = await self.get_optimal_times(platform, count=posts_per_day)
        return [{"hour": t.hour, "time": f"{t.hour:02d}:00", "expected_engagement": t.avg_engagement, "score": t.score, "platform": platform} for t in times]

    async def get_stats(self) -> dict:
        platforms = {}
        for d in self.engagement_data:
            p = d["platform"]
            platforms[p] = platforms.get(p, 0) + 1
        return {"total_data_points": len(self.engagement_data), "platforms": platforms}
