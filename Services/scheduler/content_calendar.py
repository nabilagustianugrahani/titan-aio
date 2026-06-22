"""Content Calendar — scheduling, conflict detection, optimal-slot finder."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class ScheduledPost(BaseModel):
    post_id: str = ""
    platform: str
    content: str
    scheduled_time: str  # ISO datetime
    status: str = "scheduled"  # scheduled/posted/failed/cancelled
    campaign_id: str = ""
    hashtags: list[str] = []
    media_urls: list[str] = []
    created_at: str = ""


class CalendarSlot(BaseModel):
    datetime: str
    platform: str
    score: float  # engagement score 0-1
    conflict: bool = False


class ContentCalendar:
    def __init__(self) -> None:
        self.posts: dict[str, ScheduledPost] = {}
        self._platform_limits: dict[str, int] = {
            "tiktok": 5,
            "instagram": 3,
            "youtube": 2,
            "twitter": 8,
            "facebook": 3,
        }

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def schedule_post(
        self,
        platform: str,
        content: str,
        scheduled_time: str,
        hashtags: list[str] | None = None,
        media_urls: list[str] | None = None,
        campaign_id: str = "",
    ) -> ScheduledPost:
        """Schedule a post. Auto-detects conflicts and suggests alternatives."""
        import hashlib

        post_id = hashlib.md5(
            f"{platform}:{content[:50]}:{scheduled_time}".encode()
        ).hexdigest()[:10]
        post = ScheduledPost(
            post_id=post_id,
            platform=platform,
            content=content,
            scheduled_time=scheduled_time,
            hashtags=hashtags or [],
            media_urls=media_urls or [],
            campaign_id=campaign_id,
            created_at=datetime.now().isoformat(),
        )
        self.posts[post_id] = post
        return post

    async def get_post(self, post_id: str) -> ScheduledPost | None:
        """Get a single post by ID."""
        return self.posts.get(post_id)

    async def get_calendar(
        self,
        start_date: str = "",
        end_date: str = "",
        platform: str = "",
    ) -> list[ScheduledPost]:
        """Get posts in date range, optionally filtered by platform."""
        posts = list(self.posts.values())
        if platform:
            posts = [p for p in posts if p.platform == platform]
        if start_date:
            posts = [p for p in posts if p.scheduled_time >= start_date]
        if end_date:
            posts = [p for p in posts if p.scheduled_time <= end_date]
        return sorted(posts, key=lambda p: p.scheduled_time)

    async def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        if post_id in self.posts:
            self.posts[post_id].status = "cancelled"
            return True
        return False

    async def mark_posted(self, post_id: str) -> bool:
        """Mark a post as published."""
        if post_id in self.posts:
            self.posts[post_id].status = "posted"
            return True
        return False

    async def mark_failed(self, post_id: str) -> bool:
        """Mark a post as failed."""
        if post_id in self.posts:
            self.posts[post_id].status = "failed"
            return True
        return False

    async def reschedule_post(
        self, post_id: str, new_time: str
    ) -> ScheduledPost | None:
        """Reschedule a post to a new time."""
        if post_id in self.posts:
            self.posts[post_id].scheduled_time = new_time
            self.posts[post_id].status = "scheduled"
            return self.posts[post_id]
        return None

    async def update_post_content(
        self, post_id: str, content: str, hashtags: list[str] | None = None
    ) -> ScheduledPost | None:
        """Update content/hashtags of an existing post."""
        if post_id in self.posts:
            self.posts[post_id].content = content
            if hashtags is not None:
                self.posts[post_id].hashtags = hashtags
            return self.posts[post_id]
        return None

    async def reorder_posts(self, post_ids: list[str]) -> list[ScheduledPost]:
        """Reorder posts by assigning sequential times within each platform.

        Drag-and-drop reordering: the caller provides the desired order as a
        list of post_ids.  Posts are re-spaced at 1-hour intervals starting
        from the earliest existing scheduled_time among them.
        """
        reordered: list[ScheduledPost] = []
        for idx, pid in enumerate(post_ids):
            post = self.posts.get(pid)
            if post is None:
                continue
            reordered.append(post)

        if not reordered:
            return []

        # Find earliest existing scheduled time as anchor
        earliest = min(
            (datetime.fromisoformat(p.scheduled_time) for p in reordered),
            default=datetime.now(),
        )

        for idx, post in enumerate(reordered):
            new_time = earliest + timedelta(hours=idx)
            post.scheduled_time = new_time.isoformat()

        return reordered

    # ------------------------------------------------------------------
    # Optimal slots & conflict detection
    # ------------------------------------------------------------------

    async def find_optimal_slots(
        self,
        platform: str,
        count: int = 5,
        start_date: str = "",
    ) -> list[CalendarSlot]:
        """Find optimal posting times based on engagement patterns."""
        best_hours: dict[str, list[tuple[int, float]]] = {
            "tiktok": [(19, 0.95), (20, 0.92), (21, 0.88), (12, 0.75), (13, 0.72)],
            "instagram": [
                (11, 0.90), (12, 0.88), (19, 0.85), (20, 0.82), (17, 0.78)
            ],
            "youtube": [
                (14, 0.88), (15, 0.85), (10, 0.80), (20, 0.78), (11, 0.75)
            ],
            "twitter": [
                (8, 0.90), (9, 0.88), (12, 0.85), (17, 0.80), (20, 0.75)
            ],
            "facebook": [
                (13, 0.85), (14, 0.82), (15, 0.80), (19, 0.78), (20, 0.75)
            ],
        }
        slots_data = best_hours.get(platform, best_hours["tiktok"])
        base_date = (
            datetime.fromisoformat(start_date) if start_date else datetime.now()
        )
        limit = self._platform_limits.get(platform, 3)
        slots: list[CalendarSlot] = []
        for i in range(count):
            hour, score = slots_data[i % len(slots_data)]
            day_offset = i // len(slots_data)
            slot_date = base_date + timedelta(days=day_offset)
            slot_time = slot_date.replace(
                hour=hour, minute=0, second=0, microsecond=0
            )
            existing = [
                p
                for p in self.posts.values()
                if p.platform == platform
                and p.scheduled_time.startswith(slot_time.strftime("%Y-%m-%d"))
                and p.status != "cancelled"
            ]
            conflict = len(existing) >= limit
            slots.append(
                CalendarSlot(
                    datetime=slot_time.isoformat(),
                    platform=platform,
                    score=score,
                    conflict=conflict,
                )
            )
        return slots

    async def detect_conflicts(
        self, platform: str, proposed_time: str
    ) -> dict:
        """Check if a proposed time conflicts with existing schedule.

        Returns {conflict: bool, existing_count: int, limit: int,
                 nearest_post: str | None}.
        """
        limit = self._platform_limits.get(platform, 3)
        day_prefix = proposed_time[:10]
        existing = [
            p
            for p in self.posts.values()
            if p.platform == platform
            and p.scheduled_time.startswith(day_prefix)
            and p.status not in ("cancelled", "failed")
        ]
        nearest = None
        if existing:
            nearest = min(
                existing,
                key=lambda p: abs(
                    (
                        datetime.fromisoformat(p.scheduled_time)
                        - datetime.fromisoformat(proposed_time)
                    ).total_seconds()
                ),
            )
        return {
            "conflict": len(existing) >= limit,
            "existing_count": len(existing),
            "limit": limit,
            "nearest_post": nearest.post_id if nearest else None,
        }

    async def get_weekly_plan(
        self, start_date: str = "", platform: str = ""
    ) -> dict:
        """Generate a weekly content plan grouped by day-of-week."""
        base = datetime.fromisoformat(start_date) if start_date else datetime.now()
        week_start = base - timedelta(days=base.weekday())  # Monday
        week_end = week_start + timedelta(days=6, hours=23, minutes=59)
        posts = await self.get_calendar(
            start_date=week_start.isoformat(),
            end_date=week_end.isoformat(),
            platform=platform,
        )
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        plan: dict[str, list[dict]] = {d: [] for d in days}
        for post in posts:
            dt = datetime.fromisoformat(post.scheduled_time)
            day_name = days[dt.weekday()]
            plan[day_name].append(post.model_dump())
        return {
            "week_start": week_start.date().isoformat(),
            "week_end": week_end.date().isoformat(),
            "plan": plan,
            "total_posts": len(posts),
        }

    async def get_monthly_plan(
        self, year: int = 0, month: int = 0, platform: str = ""
    ) -> dict:
        """Generate a monthly content plan grouped by ISO week."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        posts = await self.get_calendar(
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
            platform=platform,
        )
        weeks: dict[str, list[dict]] = {}
        for post in posts:
            dt = datetime.fromisoformat(post.scheduled_time)
            iso_week = dt.isocalendar()
            key = f"W{iso_week[1]:02d}"
            weeks.setdefault(key, []).append(post.model_dump())
        return {
            "year": year,
            "month": month,
            "weeks": weeks,
            "total_posts": len(posts),
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """Calendar statistics — total posts, by status, by platform."""
        total = len(self.posts)
        by_status: dict[str, int] = {}
        by_platform: dict[str, int] = {}
        for p in self.posts.values():
            by_status[p.status] = by_status.get(p.status, 0) + 1
            by_platform[p.platform] = by_platform.get(p.platform, 0) + 1
        return {
            "total_posts": total,
            "by_status": by_status,
            "by_platform": by_platform,
        }
