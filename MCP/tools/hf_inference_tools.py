"""MCP tools for HuggingFace Inference API — text, image, and model listing.

Self-registering pattern: imports mcp from MCP.instance and uses @mcp.tool().

The HF Inference API provides free/paid access to 150k+ models.
Rate limit: 1000 requests/day for free tier.
"""

from __future__ import annotations

import os

import httpx

from titan.config import settings
from MCP.instance import mcp

_INFERENCE_BASE = "https://api-inference.huggingface.co"


def _get_headers() -> dict[str, str]:
    token = settings.HF_TOKEN or os.environ.get("HF_TOKEN", "")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@mcp.tool()
async def hf_text_generate(
    prompt: str,
    model: str = "mistralai/Mistral-7B-Instruct-v0.3",
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> dict:
    """Generate text using a HuggingFace Inference API model.

    Free tier supports 1000 requests/day. Models available:
    - mistralai/Mistral-7B-Instruct-v0.3 (default, fast)
    - meta-llama/Llama-3.2-3B-Instruct (lightweight)
    - google/gemma-2-2b-it (fast)
    - microsoft/Phi-3-mini-4k-instruct (small)
    - HuggingFaceH4/zephyr-7b-beta (chat)

    Args:
        prompt: Input text prompt.
        model: Model ID on the Hub.
        max_new_tokens: Max tokens to generate (default 256, max 1024).
        temperature: Sampling temperature 0-2 (default 0.7).
        top_p: Nucleus sampling threshold (default 0.95).
    """
    headers = _get_headers()
    url = f"{_INFERENCE_BASE}/models/{model}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": min(max_new_tokens, 1024),
            "temperature": max(0.0, min(temperature, 2.0)),
            "top_p": max(0.0, min(top_p, 1.0)),
        },
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    generated = data[0].get("generated_text", str(data[0]))
                elif isinstance(data, dict):
                    generated = data.get("generated_text", str(data))
                else:
                    generated = str(data)
                return {
                    "generated_text": generated,
                    "model": model,
                    "input_tokens": len(prompt.split()),
                }
            return {
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "model": model,
            }
    except Exception as exc:
        return {"error": str(exc), "model": model}


@mcp.tool()
async def hf_image_classify(
    image_url: str,
    model: str = "google/vit-base-patch16-224",
) -> dict:
    """Classify an image using a HuggingFace Inference API model.

    Returns top label predictions with confidence scores.

    Common models:
    - google/vit-base-patch16-224 (default, ImageNet)
    - microsoft/resnet-50 (fast)
    - facebook/convnext-large-224 (high accuracy)

    Args:
        image_url: Public URL of the image to classify.
        model: Model ID on the Hub.
    """
    headers = _get_headers()
    url = f"{_INFERENCE_BASE}/models/{model}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            img_resp = await client.get(image_url, timeout=30)
            if img_resp.status_code != 200:
                return {"error": f"Failed to fetch image: HTTP {img_resp.status_code}"}
            resp = await client.post(
                url, headers=headers, content=img_resp.content,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return {"predictions": data[:10], "model": model}
                return {"predictions": [{"label": str(data)}], "model": model}
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}", "model": model}
    except Exception as exc:
        return {"error": str(exc), "model": model}


@mcp.tool()
async def hf_image_to_text(
    image_url: str,
    model: str = "Salesforce/blip-image-captioning-base",
) -> dict:
    """Generate a caption / description for an image using HF Inference API.

    Common models:
    - Salesforce/blip-image-captioning-base (default, English)
    - nlpconnect/vit-gpt2-image-captioning (fast)
    - Salesforce/blip2-opt-2.7b (higher quality)

    Args:
        image_url: Public URL of the image to caption.
        model: Model ID on the Hub.
    """
    headers = _get_headers()
    url = f"{_INFERENCE_BASE}/models/{model}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            img_resp = await client.get(image_url, timeout=30)
            if img_resp.status_code != 200:
                return {"error": f"Failed to fetch image: HTTP {img_resp.status_code}"}
            resp = await client.post(
                url, headers=headers, content=img_resp.content,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    caption = data[0].get("generated_text", str(data[0]))
                elif isinstance(data, dict):
                    caption = data.get("generated_text", str(data))
                else:
                    caption = str(data)
                return {"caption": caption, "model": model}
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}", "model": model}
    except Exception as exc:
        return {"error": str(exc), "model": model}


@mcp.tool()
async def hf_list_available_models(search: str = "", task: str = "") -> list[dict]:
    """List models available on the HuggingFace Hub, filtered by search and task.

    Use this to discover which models can be used with the Inference API
    or for downloading.

    Args:
        search: Optional search keyword (e.g. "text-generation", "image-classification").
        task: Filter by pipeline task (e.g. "text-generation", "image-classification",
              "automatic-speech-recognition", "text-to-image").
    """
    from Services.hf_client import hf_client
    return await hf_client.hub_list_models(search=search or task, sort="downloads", limit=20)
