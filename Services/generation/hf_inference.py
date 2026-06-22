"""HF Inference API — Free image generation (no Modal credits needed).

FLUX Schnell on HF: free tier, 1000 requests/day.
Fallback: Modal T4 (cheaper) → Modal A100 (most expensive).

Usage:
    from Services.generation.hf_inference import generate_image
    img_bytes = await generate_image("product photography of power bank")
"""

from __future__ import annotations

import io
import os
import base64
from typing import Optional

import httpx


async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "black-forest-labs/FLUX.1-schnell",
) -> Optional[bytes]:
    """Generate image via HF Inference API (FREE!).

    Returns PNG bytes or None if failed.
    """
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "width": width,
                        "height": height,
                    },
                },
            )
            if resp.status_code == 200:
                return resp.content  # PNG bytes
            else:
                print(f"HF Inference error: {resp.status_code} {resp.text[:100]}")
                return None
    except Exception as e:
        print(f"HF Inference failed: {e}")
        return None


async def generate_image_with_fallback(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
) -> Optional[bytes]:
    """Generate image with smart fallback: HF Free → Modal T4 → Modal A100.

    Cost optimization:
    1. HF Inference API: FREE (1000 req/day)
    2. Modal T4: ~$0.001/image (10x cheaper than A100)
    3. Modal A100: ~$0.009/image (fastest)
    """
    # 1. Try HF Inference API (FREE)
    img = await generate_image(prompt, width, height)
    if img:
        print(f"✅ Generated via HF Inference (FREE)")
        return img

    # 2. Fallback to Modal T4 (cheapest GPU)
    try:
        from Workers.modal_image import generate as modal_t4_generate
        img_bytes = modal_t4_generate.remote(prompt)
        print(f"✅ Generated via Modal T4 (~$0.001)")
        return img_bytes
    except Exception as e:
        print(f"Modal T4 failed: {e}")

    # 3. Fallback to Modal A100 (most expensive)
    try:
        from Workers.modal_a100 import generate as modal_a100_generate
        img_bytes = modal_a100_generate.remote(prompt)
        print(f"✅ Generated via Modal A100 (~$0.009)")
        return img_bytes
    except Exception as e:
        print(f"Modal A100 failed: {e}")

    return None
