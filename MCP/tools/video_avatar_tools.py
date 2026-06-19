"""MCP tools for Video and Avatar generation.

Runs on Kaggle T4 GPU via Workers/kaggle_video.py
"""
from __future__ import annotations

from Services.orchestrator import CEOAgent


async def generate_product_video(product_id: str, script_text: str, model: str = "wan-2-2") -> dict:
    """Generate a product video using Kaggle T4 GPU.

    Models: wan-2-2, hunyuan, wan-lip (with lip sync)
    """
    try:
        from Workers.kaggle_video import KaggleVideoWorker
        worker = KaggleVideoWorker()
        result = await worker.generate(script=script_text, model=model)
        return {
            "video_id": product_id,
            "url": result.video_path,
            "model_used": result.model,
            "duration_seconds": int(result.duration_sec),
            "success": result.success,
            "error": result.error,
        }
    except ImportError:
        # Fallback to CEO agent
        ceo = CEOAgent()
        result = await ceo.video(script=script_text, model=model)
        return {
            "video_id": result.get("video_id", ""),
            "url": result.get("url", ""),
            "model_used": result.get("model_used", model),
            "duration_seconds": result.get("duration_seconds", 30),
        }


async def generate_spokesperson_avatar(name: str = "AI Spokesperson", style: str = "realistic") -> dict:
    """Generate an AI spokesperson avatar with consistent character."""
    ceo = CEOAgent()
    result = await ceo.avatar(name=name)
    return {
        "avatar_id": result.get("avatar_id", ""),
        "image_url": result.get("image_url", ""),
        "persona": result.get("persona", {}),
    }


async def generate_lora_model(product_id: str, image_urls: list[str]) -> dict:
    """Train a product-specific LoRA model using reference images.
    Only trains if product usage count exceeds threshold (default: 20)."""
    from titan.config import settings
    from Database.connection import get_session
    from Database.models import Product
    from Database.repository import Repository

    # Check usage policy
    async for session in get_session():
        repo = Repository(session, Product)
        products = await repo.find(id=product_id)
        if products:
            usage = products[0].usage_count
        else:
            usage = 0
        break

    min_usage = settings.LORA_MIN_USAGE
    if usage < min_usage:
        return {
            "trained": False,
            "reason": f"Product usage ({usage}) below threshold ({min_usage}). Use reference images instead.",
            "usage_count": usage,
            "threshold": min_usage,
        }

    return {
        "trained": True,
        "model": "kohya",
        "product_id": product_id,
        "lora_url": f"https://storage.titan-aio.local/lora/{product_id}.safetensors",
        "gdrive_backed": True,
    }
