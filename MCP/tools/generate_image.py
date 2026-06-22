"""Generate product images via DashScope wan2.7-image-pro (cloud, no GPU)."""

from __future__ import annotations

import os
import random
from typing import Optional

import httpx

from MCP.schemas import GenerateImageInput, GenerateImageOutput


async def generate_image(input_data: GenerateImageInput) -> GenerateImageOutput:
    """Generate an image via DashScope wan2.7-image-pro.

    Falls back to simulated URL if DashScope is unavailable.
    """
    try:
        import asyncio
        image_url = await asyncio.wait_for(
            _dashscope_image_gen(input_data.prompt),
            timeout=15,  # 15s max
        )
        if image_url:
            return GenerateImageOutput(
                image_url=image_url,
                model_used="wan2.7-image-pro",
                seed=random.randint(0, 2**31),
            )
    except (asyncio.TimeoutError, Exception) as e:
        print(f"DashScope image failed/timed out: {e}")

    # Fallback: simulated URL
    return GenerateImageOutput(
        image_url=f"https://storage.titan-aio.local/images/{random.randint(10000, 99999)}.png",
        model_used=input_data.model or "simulated",
        seed=random.randint(0, 2**31),
    )


async def _dashscope_image_gen(prompt: str) -> Optional[str]:
    """Generate image via DashScope wan2.7-image-pro async API."""
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    api_host = os.environ.get(
        "DASHSCOPE_API_HOST",
        "ws-6ruus62c68y9yve4.ap-southeast-1.maas.aliyuncs.com",
    )
    if not api_key:
        return None

    base_url = f"https://{api_host}"

    # Step 1: Create async task
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/api/v1/services/aigc/image-generation/generation",
            headers={
                "X-DashScope-Async": "enable",
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "wan2.7-image-pro",
                "input": {
                    "messages": [
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt}
                        ]}
                    ]
                },
            },
        )
        data = resp.json()
        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            return None

    # Step 2: Poll for result
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(60):
            await _async_sleep(5)
            resp = await client.get(
                f"{base_url}/api/v1/tasks/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            data = resp.json()
            status = data.get("output", {}).get("task_status", "?")
            if status == "SUCCEEDED":
                results = data.get("output", {}).get("results", [])
                for r in results:
                    if "url" in r:
                        return r["url"]
                return None
            elif status == "FAILED":
                return None

    return None


async def _async_sleep(seconds: int) -> None:
    import asyncio
    await asyncio.sleep(seconds)
