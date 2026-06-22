"""DashScope Wan 2.7 I2V — Image-to-Video via Alibaba Cloud API.

No GPU needed. Runs entirely on Alibaba Cloud.

Usage:
    from Services.generation.dashscope_video import generate_video
    video_url = await generate_video(
        image_url="https://...",
        prompt="Person reviewing a product"
    )
"""

from __future__ import annotations

import os
import time
from typing import Optional

import httpx


async def generate_video(
    image_url: str,
    prompt: str = "A person reviewing a product",
    duration: int = 5,
    resolution: str = "720P",
    api_key: Optional[str] = None,
    api_host: Optional[str] = None,
) -> Optional[str]:
    """Generate I2V video via DashScope Wan 2.7.

    Args:
        image_url: URL or base64 data URI of first frame image
        prompt: Text prompt describing the video
        duration: Video duration in seconds (2-15)
        resolution: "720P" or "1080P"
        api_key: DashScope API key (or env DASHSCOPE_API_KEY)
        api_host: DashScope API host (or env DASHSCOPE_API_HOST)

    Returns:
        Video URL (valid 24h) or None on failure
    """
    api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
    api_host = api_host or os.environ.get(
        "DASHSCOPE_API_HOST",
        "ws-6ruus62c68y9yve4.ap-southeast-1.maas.aliyuncs.com",
    )

    if not api_key:
        print("❌ No DASHSCOPE_API_KEY set")
        return None

    base_url = f"https://{api_host}"

    # Step 1: Create async task
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base_url}/api/v1/services/aigc/video-generation/video-synthesis",
                headers={
                    "X-DashScope-Async": "enable",
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "wan2.7-i2v-2026-04-25",
                    "input": {
                        "prompt": prompt,
                        "media": [
                            {"type": "first_frame", "url": image_url}
                        ],
                    },
                    "parameters": {
                        "resolution": resolution,
                        "duration": duration,
                    },
                },
            )
            data = resp.json()
            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                print(f"❌ Task creation failed: {data}")
                return None
            print(f"📤 Task created: {task_id}")
    except Exception as e:
        print(f"❌ Task creation error: {e}")
        return None

    # Step 2: Poll for result
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(60):  # Max 15 min
                await _async_sleep(15)  # Poll every 15s
                resp = await client.get(
                    f"{base_url}/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                data = resp.json()
                status = data.get("output", {}).get("task_status", "?")

                if status == "SUCCEEDED":
                    video_url = data.get("output", {}).get("video_url", "")
                    print(f"✅ Video ready: {video_url[:80]}...")
                    return video_url
                elif status == "FAILED":
                    msg = data.get("output", {}).get("message", "unknown")
                    print(f"❌ Video failed: {msg}")
                    return None
                else:
                    print(f"⏳ {status}... (attempt {attempt + 1})")

        print("❌ Timeout waiting for video")
        return None
    except Exception as e:
        print(f"❌ Polling error: {e}")
        return None


async def _async_sleep(seconds: int) -> None:
    """Async sleep without asyncio import."""
    import asyncio
    await asyncio.sleep(seconds)


async def generate_video_with_fallback(
    image_url: str,
    prompt: str = "A person reviewing a product",
    duration: int = 5,
) -> Optional[str]:
    """Generate video with fallback: DashScope → Modal → None.

    Priority:
    1. DashScope Wan 2.7 (cloud, no GPU)
    2. Modal A100 (if available, costs credits)
    """
    # 1. Try DashScope (preferred — cloud, no local GPU)
    video_url = await generate_video(image_url, prompt, duration)
    if video_url:
        return video_url

    # 2. Fallback to Modal (costs credits)
    try:
        from Workers.modal_a100 import generate_video as modal_generate
        video_bytes = modal_generate.remote(prompt)
        if video_bytes:
            # Save to temp and return path
            import tempfile
            path = tempfile.mktemp(suffix=".mp4")
            with open(path, "wb") as f:
                f.write(video_bytes)
            print(f"✅ Generated via Modal A100")
            return path
    except Exception as e:
        print(f"Modal fallback failed: {e}")

    return None
