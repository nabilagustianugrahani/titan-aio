"""Google Flow (VideoFX) — API-based video generation.

Uses Google GenAI SDK (no browser needed).
Falls back to Kaggle Wan 2.2 if API unavailable.

Usage:
    from Services.video.google_flow import GoogleFlowGenerator
    gen = GoogleFlowGenerator()
    result = await gen.generate(prompt="Product review, close-up shot")
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FlowResult:
    video_path: str
    url: str
    source: str  # "google_veo" | "kaggle_wan" | "none"
    success: bool
    error: Optional[str] = None
    credits_used: int = 0


class GoogleFlowGenerator:
    """Generate videos using Google AI (Veo 2) or fallback to Kaggle.

    No browser automation — pure API calls.
    Safe for VPS (no memory issues).
    """

    OUTPUT_DIR = Path("/tmp/titan-output")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._client = None

    def _get_client(self):
        """Get Google GenAI client (lazy init)."""
        if self._client is not None:
            return self._client

        api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            return self._client
        except Exception as e:
            print(f"⚠️  Google GenAI init failed: {e}")
            return None

    async def generate(
        self,
        prompt: str,
        style: str = "cinematic",
        duration: str = "5s",
        aspect_ratio: str = "16:9",
    ) -> dict:
        """Generate a video.

        Strategy:
        1. Try Google Veo 2 API (high quality)
        2. Fallback to Kaggle Wan 2.2 (free, local)

        Returns:
            Dict with video_path, url, source, success
        """
        # 1. Try Google Veo 2
        result = await self._generate_veo(prompt, style, duration, aspect_ratio)
        if result.success:
            return {
                "video_path": result.video_path,
                "url": result.url,
                "source": "google_veo",
                "success": True,
            }

        # 2. Fallback to Kaggle
        result = await self._generate_kaggle(prompt)
        return {
            "video_path": result.video_path,
            "url": result.url,
            "source": result.source,
            "success": result.success,
            "error": result.error,
        }

    async def _generate_veo(
        self, prompt: str, style: str, duration: str, aspect_ratio: str
    ) -> FlowResult:
        """Generate video using Google Veo 2 API."""
        client = self._get_client()
        if not client:
            return FlowResult(
                video_path="", url="", source="google_veo",
                success=False, error="No GOOGLE_AI_API_KEY set",
            )

        try:
            # Generate with Veo 2
            response = await asyncio.to_thread(
                client.models.generate_videos,
                model="veo-2.0-generate-001",
                prompt=prompt,
                config={
                    "number_of_videos": 1,
                    "aspect_ratio": aspect_ratio,
                },
            )

            # Download the video
            if response and hasattr(response, 'videos') and response.videos:
                video = response.videos[0]
                video_path = str(self.OUTPUT_DIR / f"veo-{uuid.uuid4().hex[:8]}.mp4")

                # Download video bytes
                if hasattr(video, 'video') and video.video:
                    with open(video_path, "wb") as f:
                        f.write(video.video)

                return FlowResult(
                    video_path=video_path,
                    url="",
                    source="google_veo",
                    success=True,
                    credits_used=1,
                )

            return FlowResult(
                video_path="", url="", source="google_veo",
                success=False, error="No video in response",
            )

        except Exception as e:
            return FlowResult(
                video_path="", url="", source="google_veo",
                success=False, error=str(e),
            )

    async def _generate_kaggle(self, prompt: str) -> FlowResult:
        """Fallback: generate video using Kaggle Wan 2.2."""
        try:
            from Workers.kaggle_video import KaggleVideoWorker
            worker = KaggleVideoWorker()
            result = await worker.generate(
                script=prompt,
                model="wan-2-2",
                resolution=(512, 512),
                num_frames=81,
            )
            return FlowResult(
                video_path=result.video_path if result.success else "",
                url="",
                source="kaggle_wan",
                success=result.success,
                error=result.error,
            )
        except Exception as e:
            return FlowResult(
                video_path="", url="", source="kaggle_wan",
                success=False, error=str(e),
            )
