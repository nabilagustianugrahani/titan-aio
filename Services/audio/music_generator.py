"""AI Background Music Generator — HuggingFace Inference API.

No GPU needed. Uses facebook/musicgen-medium via HF Inference API.

Usage:
    from Services.audio.music_generator import MusicGenerator
    gen = MusicGenerator()
    result = await gen.generate("upbeat electronic background music", duration=15)
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import httpx
from pydantic import BaseModel


class MusicResult(BaseModel):
    audio_path: str = ""
    prompt: str = ""
    duration_sec: int = 15
    model: str = ""
    success: bool = False
    error: str = ""


class MusicGenerator:
    """Generate background music from text prompt via HF Inference API."""

    OUTPUT_DIR = Path("/tmp/titan-music")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._token = os.environ.get("HF_TOKEN", "")
        self._primary_model = "facebook/musicgen-medium"
        self._fallback_space = "https://api-inference.huggingface.co/models/facebook/musicgen-medium"

    async def generate(
        self,
        prompt: str,
        duration: int = 15,
        model: str = "",
    ) -> MusicResult:
        """Generate music from text prompt.

        Args:
            prompt: Description of music (e.g. "upbeat electronic background")
            duration: Seconds of music to generate (5-30)
            model: Override HF model ID (optional)

        Returns:
            MusicResult with path to .wav file

        """
        duration = max(5, min(30, duration))
        max_length = {5: 128, 10: 192, 15: 256, 20: 320, 25: 384, 30: 512}
        length = max_length.get(duration, 256)

        model_id = model or self._primary_model
        url = f"https://api-inference.huggingface.co/models/{model_id}"

        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": length,
                "temperature": 0.8,
                "top_k": 250,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()

                output_path = str(self.OUTPUT_DIR / f"music-{uuid.uuid4().hex[:8]}.wav")
                with open(output_path, "wb") as f:
                    f.write(resp.content)

                return MusicResult(
                    audio_path=output_path,
                    prompt=prompt,
                    duration_sec=duration,
                    model=model_id,
                    success=True,
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                # Model loading — retry once
                import asyncio
                await asyncio.sleep(10)
                return await self.generate(prompt, duration, model)

            return MusicResult(
                prompt=prompt, duration_sec=duration,
                model=model_id, success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )

        except Exception as e:
            return MusicResult(
                prompt=prompt, duration_sec=duration,
                model=model_id, success=False,
                error=str(e),
            )
