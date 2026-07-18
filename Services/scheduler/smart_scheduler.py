"""Smart Scheduler — ML-based optimal posting time engine.

Tracks engagement per hour/day/platform, calculates optimal posting windows,
adapts to audience behavior patterns via exponentially-weighted moving averages,
and suggests best times for new content. Falls back to industry benchmarks
when insufficient learned data exists.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta

from pydantic import BaseModel

# ── Models ──────────────────────────────────────────────────────────────

class TimeSlot(BaseModel):
    hour: int
    day_of_week: str
    platform: str
    avg_engagement: float = 0.0
    post_count: int = 0
    score: float = 0.0


class DayTimeSlot(BaseModel):
    day: str
    hour: int
    platform: str
    avg_engagement: float = 0.0
    post_count: int = 0
    score: float = 0.0


class PlatformReport(BaseModel):
    platform: str
    data_points: int
    best_hours: list[TimeSlot]
    best_days: list[str]
    peak_window: str  # e.g. "19:00-21:00"
    avg_engagement: float


# ── Smart Scheduler ─────────────────────────────────────────────────────

class SmartScheduler:
    """ML-lite optimal posting time engine.

    Uses EWMA (exponentially-weighted moving averages) to adapt to audience
    behavior over time. When data is sparse, falls back to platform-specific
    industry benchmarks. Blends learned and benchmark scores for hours with
    limited data.
    """

    def __init__(self) -> None:
        self.engagement_data: list[dict] = []

        # Industry benchmark peaks (hour, base_score) — extended set per platform
        self._platform_peaks: dict[str, list[tuple[int, float]]] = {
            "tiktok": [
                (7, 0.60), (8, 0.68), (12, 0.75), (13, 0.72),
                (17, 0.78), (18, 0.85), (19, 0.95), (20, 0.92),
                (21, 0.88), (22, 0.80),
            ],
            "instagram": [
                (7, 0.55), (8, 0.62), (11, 0.90), (12, 0.88),
                (13, 0.82), (17, 0.78), (19, 0.85), (20, 0.82),
                (21, 0.75),
            ],
            "youtube": [
                (9, 0.72), (10, 0.80), (12, 0.78), (14, 0.88),
                (15, 0.85), (16, 0.76), (19, 0.74), (20, 0.78),
            ],
            "twitter": [
                (8, 0.90), (9, 0.88), (12, 0.85), (13, 0.78),
                (17, 0.80), (18, 0.72),
            ],
            "facebook": [
                (9, 0.72), (12, 0.78), (13, 0.85), (14, 0.82),
                (15, 0.80), (19, 0.78), (20, 0.74),
            ],
            "shopee": [
                (10, 0.82), (12, 0.88), (13, 0.85), (20, 0.90),
                (21, 0.87), (22, 0.80),
            ],
            "tokopedia": [
                (10, 0.80), (11, 0.82), (13, 0.85), (20, 0.88),
                (21, 0.85), (22, 0.78),
            ],
        }

        # Day-of-week weights (affect benchmark scores)
        self._day_weights: dict[str, float] = {
            "monday": 0.85,
            "tuesday": 0.88,
            "wednesday": 0.90,
            "thursday": 0.87,
            "friday": 0.82,
            "saturday": 0.95,
            "sunday": 0.92,
        }

        # EWMA smoothing factor (0-1). Higher = more reactive to recent data.
        self._alpha: float = 0.3

        # Minimum data points before switching from benchmarks to learned data
        self._min_data_points: int = 10

        # History size limit
        self._max_history: int = 10_000

    # ── Core Public API ─────────────────────────────────────────────────

    async def record_engagement(
        self,
        platform: str,
        hour: int,
        day_of_week: str,
        engagement_rate: float,
        impressions: int = 0,
        clicks: int = 0,
        shares: int = 0,
        likes: int = 0,
        comments: int = 0,
        campaign_id: str = "",
    ) -> dict:
        """Record a single engagement data point."""
        day_lower = day_of_week.lower().strip()
        record = {
            "platform": platform.lower(),
            "hour": max(0, min(23, hour)),
            "day": day_lower,
            "engagement": max(0.0, engagement_rate),
            "impressions": impressions,
            "clicks": clicks,
            "shares": shares,
            "likes": likes,
            "comments": comments,
            "campaign_id": campaign_id,
            "timestamp": datetime.now().isoformat(),
        }
        self.engagement_data.append(record)

        # Trim history if too large
        if len(self.engagement_data) > self._max_history:
            self.engagement_data = self.engagement_data[-self._max_history:]

        return {"recorded": True, "total_points": len(self.engagement_data)}

    async def record_batch(self, records: list[dict]) -> dict:
        """Record multiple engagement data points at once.

        Each record dict should have keys: platform, hour, day_of_week,
        engagement_rate, and optionally impressions, clicks, shares, likes,
        comments, campaign_id.
        """
        count = 0
        for r in records:
            await self.record_engagement(
                platform=r.get("platform", "tiktok"),
                hour=r.get("hour", 12),
                day_of_week=r.get("day_of_week", "monday"),
                engagement_rate=r.get("engagement_rate", 0.0),
                impressions=r.get("impressions", 0),
                clicks=r.get("clicks", 0),
                shares=r.get("shares", 0),
                likes=r.get("likes", 0),
                comments=r.get("comments", 0),
                campaign_id=r.get("campaign_id", ""),
            )
            count += 1
        return {"recorded": count, "total_points": len(self.engagement_data)}

    async def get_optimal_times(
        self, platform: str, count: int = 5,
    ) -> list[TimeSlot]:
        """Return the best posting hours for a platform.

        Uses learned data when >= min_data_points exist, else benchmarks.
        For partially-learned hours, blends 80% learned + 20% benchmark.
        """
        platform_data = [
            d for d in self.engagement_data if d["platform"] == platform
        ]

        if len(platform_data) >= self._min_data_points:
            return self._compute_learned_times(platform, platform_data, count)
        return self._compute_benchmark_times(platform, count)

    async def get_optimal_day_times(
        self, platform: str, count: int = 5,
    ) -> list[DayTimeSlot]:
        """Return best day+hour combinations.

        Gives more nuanced scheduling than hour-only optimal times.
        """
        platform_data = [
            d for d in self.engagement_data if d["platform"] == platform
        ]

        if len(platform_data) >= self._min_data_points:
            return self._compute_learned_day_times(platform, platform_data, count)
        return self._compute_benchmark_day_times(platform, count)

    async def suggest_posting_schedule(
        self, platform: str, posts_per_day: int = 2, days: int = 7,
    ) -> list[dict]:
        """Suggest a full posting schedule for the next N days.

        Returns a sorted list of {date, day, hour, time, expected_engagement,
        score, platform} dicts.
        """
        optimal = await self.get_optimal_day_times(
            platform, count=posts_per_day * days,
        )
        now = datetime.now()
        schedule: list[dict] = []

        # Group by day, pick top posts_per_day per day
        by_day: dict[str, list[DayTimeSlot]] = defaultdict(list)
        for slot in optimal:
            by_day[slot.day].append(slot)

        for day_offset in range(days):
            target_date = now + timedelta(days=day_offset)
            day_name = target_date.strftime("%A").lower()
            day_slots = by_day.get(day_name, [])

            if not day_slots:
                # Fill with generic optimal hours
                generic = await self.get_optimal_times(platform, count=posts_per_day)
                day_slots = [
                    DayTimeSlot(
                        day=day_name,
                        hour=s.hour,
                        platform=s.platform,
                        avg_engagement=s.avg_engagement,
                        post_count=s.post_count,
                        score=s.score,
                    )
                    for s in generic
                ]

            # Take top N for this day
            day_slots.sort(key=lambda s: s.score, reverse=True)
            for slot in day_slots[:posts_per_day]:
                time_str = f"{slot.hour:02d}:00"
                schedule.append({
                    "date": target_date.strftime("%Y-%m-%d"),
                    "day": day_name,
                    "hour": slot.hour,
                    "time": time_str,
                    "expected_engagement": slot.avg_engagement,
                    "score": slot.score,
                    "platform": platform,
                })

        # Sort by date+hour
        schedule.sort(key=lambda s: (s["date"], s["hour"]))
        return schedule

    async def get_platform_report(self, platform: str) -> PlatformReport:
        """Generate a summary report for a platform."""
        optimal = await self.get_optimal_times(platform, count=5)
        platform_data = [
            d for d in self.engagement_data if d["platform"] == platform
        ]

        avg_eng = 0.0
        if platform_data:
            avg_eng = sum(d["engagement"] for d in platform_data) / len(
                platform_data,
            )

        # Best days from data
        day_eng: dict[str, list[float]] = defaultdict(list)
        for d in platform_data:
            day_eng[d["day"]].append(d["engagement"])

        if day_eng:
            best_days = sorted(
                day_eng.keys(),
                key=lambda d: (
                    sum(day_eng[d]) / len(day_eng[d]) if day_eng[d] else 0
                ),
                reverse=True,
            )[:3]
        else:
            best_days = ["saturday", "sunday", "wednesday"]

        # Peak window from top hours
        if optimal:
            peak_hours = sorted([s.hour for s in optimal[:3]])
            peak_window = f"{peak_hours[0]:02d}:00-{peak_hours[-1] + 1:02d}:00"
        else:
            peak_window = "12:00-14:00"

        return PlatformReport(
            platform=platform,
            data_points=len(platform_data),
            best_hours=optimal,
            best_days=best_days,
            peak_window=peak_window,
            avg_engagement=round(avg_eng, 4),
        )

    async def get_all_reports(self) -> dict[str, PlatformReport]:
        """Generate reports for all tracked platforms plus all defaults."""
        platforms = set(d["platform"] for d in self.engagement_data)
        platforms.update(self._platform_peaks.keys())
        reports: dict[str, PlatformReport] = {}
        for p in platforms:
            reports[p] = await self.get_platform_report(p)
        return reports

    async def get_stats(self) -> dict:
        """Return usage statistics."""
        platforms: dict[str, int] = defaultdict(int)
        for d in self.engagement_data:
            platforms[d["platform"]] += 1

        return {
            "total_data_points": len(self.engagement_data),
            "platforms": dict(platforms),
            "min_data_threshold": self._min_data_points,
            "learned_platforms": [
                p for p, c in platforms.items()
                if c >= self._min_data_points
            ],
            "benchmark_fallback_platforms": [
                p for p, c in platforms.items()
                if c < self._min_data_points
            ],
        }

    # ── Internal: Learned Data Computation ───────────────────────────────

    def _compute_learned_times(
        self, platform: str, data: list[dict], count: int,
    ) -> list[TimeSlot]:
        """Compute optimal hours from actual engagement data with EWMA weighting.

        More recent data points get exponentially higher weight. For hours
        with limited data, blends with benchmark scores (80/20).
        """
        hour_scores: dict[int, list[float]] = defaultdict(list)
        hour_recency: dict[int, list[float]] = defaultdict(list)

        now = datetime.now()
        for d in data:
            h = d["hour"]
            hour_scores[h].append(d["engagement"])

            # Recency weight: exponential decay with ~14-day half-life
            try:
                ts = datetime.fromisoformat(d["timestamp"])
                age_days = max((now - ts).total_seconds() / 86400, 0.01)
            except (ValueError, TypeError):
                age_days = 7.0

            recency = math.exp(-0.05 * age_days)
            hour_recency[h].append(recency)

        # Compute weighted average per hour
        ranked: list[tuple[int, float, int]] = []
        for hour in hour_scores:
            scores = hour_scores[hour]
            weights = hour_recency[hour]
            total_weight = sum(weights)

            if total_weight > 0:
                weighted_avg = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                weighted_avg = sum(scores) / len(scores)

            ranked.append((hour, weighted_avg, len(scores)))

        ranked.sort(key=lambda x: x[1], reverse=True)

        # Blend with benchmark for low-data hours
        benchmark = self._platform_peaks.get(platform, [])
        benchmark_map = {h: s for h, s in benchmark}

        result: list[TimeSlot] = []
        for hour, avg, count_pts in ranked[:count]:
            bm = benchmark_map.get(hour, 0.5)
            # Blend: more data = less benchmark influence
            data_weight = min(count_pts / self._min_data_points, 1.0)
            blended = data_weight * avg + (1 - data_weight) * bm
            result.append(TimeSlot(
                hour=hour,
                day_of_week="any",
                platform=platform,
                avg_engagement=round(blended, 4),
                post_count=count_pts,
                score=round(blended * 100, 1),
            ))

        # Fill remaining slots from benchmarks if not enough learned data
        if len(result) < count and benchmark:
            existing_hours = {s.hour for s in result}
            for h, s in benchmark:
                if h not in existing_hours and len(result) < count:
                    result.append(TimeSlot(
                        hour=h,
                        day_of_week="any",
                        platform=platform,
                        avg_engagement=s,
                        post_count=0,
                        score=round(s * 100, 1),
                    ))

        return result[:count]

    def _compute_learned_day_times(
        self, platform: str, data: list[dict], count: int,
    ) -> list[DayTimeSlot]:
        """Compute best day+hour combos from actual data with recency weighting."""
        combo_eng: dict[str, dict[int, list[float]]] = defaultdict(
            lambda: defaultdict(list),
        )
        now = datetime.now()

        for d in data:
            day = d["day"]
            hour = d["hour"]
            try:
                ts = datetime.fromisoformat(d["timestamp"])
                age_days = max((now - ts).total_seconds() / 86400, 0.01)
            except (ValueError, TypeError):
                age_days = 7.0
            recency = math.exp(-0.05 * age_days)
            combo_eng[day][hour].append(d["engagement"] * recency)

        result: list[DayTimeSlot] = []
        for day in combo_eng:
            for hour in combo_eng[day]:
                scores = combo_eng[day][hour]
                avg = sum(scores) / len(scores)
                result.append(DayTimeSlot(
                    day=day,
                    hour=hour,
                    platform=platform,
                    avg_engagement=round(avg, 4),
                    post_count=len(scores),
                    score=round(avg * 100, 1),
                ))

        result.sort(key=lambda s: s.score, reverse=True)
        return result[:count]

    # ── Internal: Benchmark Fallback ────────────────────────────────────

    def _compute_benchmark_times(
        self, platform: str, count: int,
    ) -> list[TimeSlot]:
        """Use industry benchmarks when no learned data exists."""
        peaks = self._platform_peaks.get(
            platform, self._platform_peaks["tiktok"],
        )
        return [
            TimeSlot(
                hour=h,
                day_of_week="any",
                platform=platform,
                avg_engagement=s,
                post_count=0,
                score=round(s * 100, 1),
            )
            for h, s in peaks[:count]
        ]

    def _compute_benchmark_day_times(
        self, platform: str, count: int,
    ) -> list[DayTimeSlot]:
        """Benchmark day+hour combos using platform peaks * day weights."""
        peaks = self._platform_peaks.get(
            platform, self._platform_peaks["tiktok"],
        )
        result: list[DayTimeSlot] = []

        for day_name, day_weight in self._day_weights.items():
            for hour, base_score in peaks:
                adjusted = base_score * day_weight
                result.append(DayTimeSlot(
                    day=day_name,
                    hour=hour,
                    platform=platform,
                    avg_engagement=round(adjusted, 4),
                    post_count=0,
                    score=round(adjusted * 100, 1),
                ))

        result.sort(key=lambda s: s.score, reverse=True)
        return result[:count]
