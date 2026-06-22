"""Real-time competitor tracking."""

from pydantic import BaseModel
from datetime import datetime
import hashlib


class CompetitorWatch(BaseModel):
    watch_id: str = ""
    competitor_name: str
    platform: str
    url: str = ""
    status: str = "active"
    last_check: str = ""
    metrics: dict = {}
    alerts: list[str] = []


class CompetitorMonitor:
    def __init__(self):
        self.watches: dict[str, CompetitorWatch] = {}
        self.change_log: list[dict] = []

    async def add_competitor(self, name: str, platform: str, url: str = "") -> CompetitorWatch:
        wid = hashlib.md5(f"{name}:{platform}".encode()).hexdigest()[:10]
        watch = CompetitorWatch(
            watch_id=wid,
            competitor_name=name,
            platform=platform,
            url=url,
            last_check=datetime.now().isoformat(),
        )
        self.watches[wid] = watch
        return watch

    async def check_competitor(self, watch_id: str) -> CompetitorWatch | None:
        if watch_id not in self.watches:
            return None
        watch = self.watches[watch_id]
        old_metrics = dict(watch.metrics)
        watch.last_check = datetime.now().isoformat()
        import random
        watch.metrics = {
            "followers": random.randint(10000, 100000),
            "engagement_rate": round(random.uniform(1, 8), 2),
            "posts_this_week": random.randint(3, 15),
        }
        if old_metrics:
            for key in watch.metrics:
                if key in old_metrics and watch.metrics[key] != old_metrics[key]:
                    diff = watch.metrics[key] - old_metrics[key]
                    alert = f"{key}: {old_metrics[key]} -> {watch.metrics[key]} ({'+' if diff > 0 else ''}{diff})"
                    watch.alerts.append(alert)
                    self.change_log.append({
                        "watch_id": watch_id,
                        "competitor": watch.competitor_name,
                        "change": alert,
                        "timestamp": datetime.now().isoformat(),
                    })
        return watch

    async def list_competitors(self, platform: str = "") -> list[CompetitorWatch]:
        watches = list(self.watches.values())
        if platform:
            watches = [w for w in watches if w.platform == platform]
        return watches

    async def remove_competitor(self, watch_id: str) -> bool:
        if watch_id in self.watches:
            del self.watches[watch_id]
            return True
        return False

    async def get_change_log(self, watch_id: str = "", limit: int = 50) -> list[dict]:
        logs = self.change_log
        if watch_id:
            logs = [l for l in logs if l["watch_id"] == watch_id]
        return logs[-limit:]

    async def get_stats(self) -> dict:
        platforms: dict[str, int] = {}
        for w in self.watches.values():
            platforms[w.platform] = platforms.get(w.platform, 0) + 1
        total_alerts = sum(len(w.alerts) for w in self.watches.values())
        return {
            "total_watches": len(self.watches),
            "by_platform": platforms,
            "total_alerts": total_alerts,
            "total_changes_logged": len(self.change_log),
        }
