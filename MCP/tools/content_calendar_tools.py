"""MCP tools module."""

from __future__ import annotations

from typing import Any

from MCP.instance import mcp

_calendar: Any = None


def _get_calendar() -> Any:
    global _calendar
    if _calendar is None:
        from Services.scheduler.content_calendar import ContentCalendar

        _calendar = ContentCalendar()
    return _calendar


@mcp.tool()
async def schedule_content_post(
    platform: str,
    content: str,
    scheduled_time: str,
    hashtags: str = "",
    campaign_id: str = "",
) -> dict:
    """Schedule a content post for a specific platform and time."""
    cal = _get_calendar()
    result = await cal.schedule_post(
        platform=platform,
        content=content,
        scheduled_time=scheduled_time,
        hashtags=[h.strip() for h in hashtags.split(",") if h.strip()]
        if hashtags
        else [],
        campaign_id=campaign_id,
    )
    return result.model_dump()


@mcp.tool()
async def get_content_calendar(
    platform: str = "", days: int = 7,
) -> list[dict]:
    """Get scheduled posts for the next N days."""
    from datetime import datetime, timedelta

    cal = _get_calendar()
    start = datetime.now().isoformat()
    end = (datetime.now() + timedelta(days=days)).isoformat()
    posts = await cal.get_calendar(
        start_date=start, end_date=end, platform=platform,
    )
    return [p.model_dump() for p in posts]


@mcp.tool()
async def find_best_posting_times(
    platform: str = "tiktok", count: int = 5,
) -> list[dict]:
    """Find optimal posting times for a platform based on engagement data."""
    cal = _get_calendar()
    slots = await cal.find_optimal_slots(platform=platform, count=count)
    return [s.model_dump() for s in slots]


@mcp.tool()
async def cancel_scheduled_post(post_id: str) -> dict:
    """Cancel a scheduled post."""
    cal = _get_calendar()
    success = await cal.cancel_post(post_id=post_id)
    return {"success": success, "post_id": post_id}


@mcp.tool()
async def reschedule_post(post_id: str, new_time: str) -> dict:
    """Reschedule a post to a new time."""
    cal = _get_calendar()
    result = await cal.reschedule_post(post_id=post_id, new_time=new_time)
    return result.model_dump() if result else {"error": "Post not found"}


@mcp.tool()
async def reorder_content_posts(post_ids: str) -> dict:
    """Reorder posts by providing comma-separated post IDs in desired order."""
    cal = _get_calendar()
    ids = [pid.strip() for pid in post_ids.split(",") if pid.strip()]
    reordered = await cal.reorder_posts(ids)
    return {"reordered": [p.model_dump() for p in reordered], "count": len(reordered)}


@mcp.tool()
async def check_scheduling_conflict(
    platform: str, proposed_time: str,
) -> dict:
    """Check if a proposed posting time has scheduling conflicts."""
    cal = _get_calendar()
    return await cal.detect_conflicts(platform=platform, proposed_time=proposed_time)


@mcp.tool()
async def get_weekly_content_plan(
    platform: str = "", start_date: str = "",
) -> dict:
    """Generate a weekly content plan grouped by day."""
    cal = _get_calendar()
    return await cal.get_weekly_plan(start_date=start_date, platform=platform)


@mcp.tool()
async def get_monthly_content_plan(
    platform: str = "", year: int = 0, month: int = 0,
) -> dict:
    """Generate a monthly content plan grouped by ISO week."""
    cal = _get_calendar()
    return await cal.get_monthly_plan(year=year, month=month, platform=platform)


@mcp.tool()
async def get_calendar_stats() -> dict:
    """Get calendar statistics — total posts, by status, by platform."""
    cal = _get_calendar()
    return await cal.get_stats()
