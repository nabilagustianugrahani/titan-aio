"""Timezone utility — handles VPS (IST UTC+5:30) ↔ User (WIB UTC+7) conversions.

All timestamps stored in UTC internally. Display in user's timezone.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

# Timezone offsets
UTC = UTC
WIB = timezone(timedelta(hours=7))   # Asia/Jakarta (user)
IST = timezone(timedelta(hours=5, minutes=30))  # Asia/Kolkata (VPS)
WITA = timezone(timedelta(hours=8))  # Asia/Makassar
WIT = timezone(timedelta(hours=9))   # Asia/Jayapura

TIMEZONE_MAP = {
    "UTC": UTC,
    "WIB": WIB,
    "IST": IST,
    "WITA": WITA,
    "WIT": WIT,
    "Asia/Jakarta": WIB,
    "Asia/Kolkata": IST,
    "Asia/Makassar": WITA,
    "Asia/Jayapura": WIT,
}


def now_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.now(UTC)


def now_wib() -> datetime:
    """Get current time in WIB (user timezone)."""
    return datetime.now(WIB)


def utc_to_wib(dt: datetime) -> datetime:
    """Convert UTC datetime to WIB."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(WIB)


def wib_to_utc(dt: datetime) -> datetime:
    """Convert WIB datetime to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=WIB)
    return dt.astimezone(UTC)


def format_wib(dt: datetime, fmt: str = "%Y-%m-%d %H:%M WIB") -> str:
    """Format datetime in WIB string."""
    wib_dt = utc_to_wib(dt) if dt.tzinfo == UTC else dt
    return wib_dt.strftime(fmt)


def parse_to_utc(dt_str: str, source_tz: str = "WIB") -> datetime:
    """Parse a datetime string and convert to UTC."""
    tz = TIMEZONE_MAP.get(source_tz, UTC)
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(UTC)


def get_user_display_time() -> str:
    """Get current time formatted for user display (WIB)."""
    return format_wib(now_wib())


def get_vps_display_time() -> str:
    """Get current time formatted for VPS display (IST)."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
