"""
Anti-Shadowban Engine — humanize automated posting.

Strategies:
1. Random delay between posts (not fixed schedule)
2. Unique caption per platform (not copy-paste)
3. Warm-up period for new accounts
4. Content ratio: 30% affiliate, 70% organic-looking
5. Randomize timing (not always at :00)
6. Rotate hashtags (not same set every time)
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Optional



class AntiShadowban:
    """Humanize auto-posts to avoid platform detection."""

    # Optimal posting times by platform (WIB / UTC+7)
    PLATFORM_PEAK_HOURS = {
        "tiktok":     [7, 8, 11, 12, 18, 19, 20, 21],
        "instagram":  [6, 7, 11, 12, 17, 18, 20, 21],
        "facebook":   [6, 7, 11, 12, 18, 19, 20, 21],
    }

    # Hashtag pools to rotate
    HASHTAG_POOLS = {
        "elektronik": [
            ["gadget", "teknologi", "review"],
            ["elektronik", "smartphone", "tips"],
            ["tech", "gadgetindonesia", "reviewproduk"],
        ],
        "fashion": [
            ["fashion", "ootd", "style"],
            ["busana", "tren", "fashionindonesia"],
            ["streetwear", "outfit", "dailyfit"],
        ],
        "umum": [
            ["promo", "diskondong", "murah"],
            ["rekomendasi", "produkterbaik", "review"],
            ["shopping", "belanja", "tipsbelanja"],
        ],
    }

    def __init__(self):
        self._daily_post_count: dict[str, int] = {}
        self._last_post_time: dict[str, float] = {}
        self._warmup_phase: bool = True

    async def wait_before_post(self, platform: str, account_age_days: int = 0) -> dict:
        """Calculate and wait appropriate delay before posting.

        Returns dict with wait_seconds, reason, next_post_time.
        """
        now = time.time()
        last = self._last_post_time.get(platform, 0)

        # Base delay: minimum seconds between posts
        if account_age_days < 7:
            # New account: slow. Max 1 post per 3 hours
            base_delay = random.randint(7200, 14400)  # 2-4 jam
            max_daily = 2
            phase = "warming"
        elif account_age_days < 30:
            base_delay = random.randint(3600, 7200)   # 1-2 jam
            max_daily = 4
            phase = "growing"
        else:
            base_delay = random.randint(1800, 5400)   # 30-90 menit
            max_daily = 8
            phase = "established"

        # Calculate delay since last post
        time_since_last = now - last if last > 0 else 99999
        delay = max(base_delay - time_since_last, 0)

        # Add random jitter (±30%)
        jitter = random.uniform(0.7, 1.3)
        delay = int(delay * jitter)

        # Daily limit check
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"{platform}_{today}"
        count = self._daily_post_count.get(key, 0)

        if count >= max_daily:
            # Wait until tomorrow
            tomorrow = datetime.now().replace(hour=6, minute=0, second=0) + timedelta(days=1)
            delay = int((tomorrow - datetime.now()).total_seconds())
            self._daily_post_count[key] = 0
            reason = "daily_limit_reached"
        else:
            self._daily_post_count[key] = count + 1
            reason = "normal_delay"

        self._last_post_time[platform] = now + delay

        if delay > 0:
            print(f"  ⏳ Anti-shadowban: waiting {delay//60} min ({reason})")
            await asyncio.sleep(delay)

        return {
            "wait_seconds": delay,
            "reason": reason,
            "phase": phase,
            "daily_posts_remaining": max_daily - max(count, 0),
            "next_post_available": datetime.fromtimestamp(now + delay).isoformat() if delay > 0 else None,
        }

    def generate_caption(self, platform: str, base_caption: str, category: str = "umum") -> str:
        """Generate a platform-adapted caption with rotated hashtags."""
        # Platform-specific formatting
        formats = {
            "tiktok":    "{text}\n\n{hashtags}",
            "instagram": "{text}\n\n{hashtags}",
            "facebook":  "{text}\n\n{hashtags}",
        }

        # Pick random hashtag set
        pools = self.HASHTAG_POOLS.get(category, self.HASHTAG_POOLS["umum"])
        hashtag_set = random.choice(pools)
        hashtags = " ".join(f"#{h}" for h in hashtag_set)

        # Add 1-2 random trending hashtags occasionally
        if random.random() < 0.3:
            trending = ["fyp", "foryou", "viral", "trending"]
            hashtags += f" #{random.choice(trending)}"

        # Add affiliate disclosure occasionally (not every post)
        disclosure = ""
        if random.random() < 0.5:
            disclosure = "\n\n*affiliate link"
        else:
            disclosure = "\n\n#ad" if random.random() < 0.3 else ""

        fmt = formats.get(platform, "{text}\n\n{hashtags}")
        return fmt.format(
            text=base_caption[:250] + disclosure,
            hashtags=hashtags,
        )

    def is_peak_hour(self, platform: str, hour: Optional[int] = None) -> bool:
        """Check if current hour is peak for this platform."""
        if hour is None:
            hour = datetime.now().hour
        peaks = self.PLATFORM_PEAK_HOURS.get(platform, [])
        return hour in peaks

    def suggest_next_time(self, platform: str) -> str:
        """Suggest next good posting time."""
        now = datetime.now()
        peaks = sorted(self.PLATFORM_PEAK_HOURS.get(platform, [12, 18]))

        for peak_hour in peaks:
            if now.hour < peak_hour:
                next_time = now.replace(hour=peak_hour, minute=random.randint(0, 59), second=0)
                if next_time > now:
                    return next_time.strftime("%H:%M WIB")

        # Next day
        tomorrow_peak = peaks[0]
        next_time = now.replace(hour=tomorrow_peak, minute=random.randint(0, 59), second=0) + timedelta(days=1)
        return next_time.strftime("%H:%M WIB besok")
