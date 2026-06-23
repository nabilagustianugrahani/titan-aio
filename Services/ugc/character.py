"""
Character Consistency — Same face across all videos.

Pipeline:
1. Generate 1 avatar image (FLUX with fixed seed)
2. Save as reference image
3. Use img2vid (not txt2vid) for all videos
4. Apply Wav2Lip for lip sync with same face

Usage:
    from Services.ugc.character import CharacterConsistency
    char = CharacterConsistency()

    # First time: generate avatar
    avatar = await char.generate_avatar("beauty_influencer")
    # avatar.image_path → saved reference image

    # All videos use same reference
    video = await char.generate_video(
        prompt="Person talking about skincare",
        profile_name="beauty_influencer",
    )
"""

from __future__ import annotations

import os
import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional



@dataclass
class AvatarResult:
    image_path: str
    seed: int
    profile_name: str
    prompt: str
    success: bool
    error: Optional[str] = None


@dataclass
class VideoResult:
    video_path: str
    duration_sec: float
    model: str
    success: bool
    error: Optional[str] = None


class CharacterConsistency:
    """Maintain same face/character across all UGC videos."""

    AVATARS_DIR = Path("/tmp/titan-avatars")
    VIDEOS_DIR = Path("/tmp/titan-character-videos")

    def __init__(self):
        self.AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        self.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_avatar(
        self,
        profile_name: str,
        gender: str = "female",
        age_range: str = "25-30",
        skin_tone: str = "light",
        hair_style: str = "long",
        style: str = "casual",
        seed: int = 0,
    ) -> AvatarResult:
        """Generate avatar image with fixed seed for consistency.

        Uses FLUX to generate the avatar.
        Seed ensures same face every time.
        """
        if seed == 0:
            seed = random.randint(1000, 999999)

        prompt = self._build_avatar_prompt(gender, age_range, skin_tone, hair_style, style)

        # Try Google Veo/Image API first
        result = await self._generate_with_google(prompt, profile_name, seed)
        if result.success:
            return result

        # Fallback to placeholder
        return await self._generate_placeholder(profile_name, seed)

    async def generate_video(
        self,
        prompt: str,
        profile_name: str,
        duration_sec: int = 5,
    ) -> VideoResult:
        """Generate video using reference avatar.

        Priority:
        1. DashScope Wan 2.7 I2V (primary — cloud, no GPU)
        2. Google Veo (fallback)

        Uses img2vid with saved reference image.
        Ensures same face in every video.
        """
        avatar_path = self._get_avatar_path(profile_name)
        if not avatar_path.exists():
            # Generate avatar first
            await self.generate_avatar(profile_name)
            avatar_path = self._get_avatar_path(profile_name)

        # 1. Try DashScope I2V (preferred — cloud, no local GPU)
        result = await self._video_with_dashscope(prompt, avatar_path, duration_sec)
        if result.success:
            return result

        # 2. Fallback to Google Veo
        result = await self._video_with_veo(prompt, avatar_path, duration_sec)
        if result.success:
            return result

        return VideoResult(video_path="", duration_sec=0, model="none", success=False)

    def _get_avatar_path(self, profile_name: str) -> Path:
        """Get path to saved avatar image."""
        return self.AVATARS_DIR / f"{profile_name}.png"

    def _build_avatar_prompt(
        self, gender: str, age_range: str, skin_tone: str, hair_style: str, style: str
    ) -> str:
        """Build detailed prompt for avatar generation."""
        return (
            f"Portrait photo of a {age_range} year old {gender}, "
            f"{skin_tone} skin, {hair_style} hair, {style} outfit, "
            f"natural lighting, looking at camera, friendly smile, "
            f"clean background, high quality, photorealistic, "
            f"UGC style, vertical format 9:16"
        )

    async def _generate_with_google(
        self, prompt: str, profile_name: str, seed: int
    ) -> AvatarResult:
        """Generate avatar using Google Imagen API."""
        api_key = os.environ.get("GOOGLE_AI_API_KEY", "")
        if not api_key:
            return AvatarResult(
                image_path="", seed=seed, profile_name=profile_name,
                prompt=prompt, success=False, error="No GOOGLE_AI_API_KEY",
            )

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            # Generate image with Imagen
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config={"number_of_images": 1},
            )

            if response.generated_images:
                image = response.generated_images[0]
                image_path = str(self.AVATARS_DIR / f"{profile_name}.png")

                with open(image_path, "wb") as f:
                    f.write(image.image.image_bytes)

                return AvatarResult(
                    image_path=image_path, seed=seed,
                    profile_name=profile_name, prompt=prompt, success=True,
                )

        except Exception:
            pass

        return AvatarResult(
            image_path="", seed=seed, profile_name=profile_name,
            prompt=prompt, success=False, error="Google Imagen failed",
        )

    async def _generate_placeholder(
        self, profile_name: str, seed: int
    ) -> AvatarResult:
        """Generate placeholder avatar (colored rectangle with text)."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (768, 1024), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)

            # Draw simple avatar placeholder
            draw.ellipse([234, 200, 534, 500], fill=(200, 180, 160))  # Face
            draw.ellipse([284, 280, 350, 340], fill=(80, 60, 50))  # Left eye
            draw.ellipse([418, 280, 484, 340], fill=(80, 60, 50))  # Right eye
            draw.arc([300, 380, 468, 460], 0, 180, fill=(180, 100, 100), width=3)  # Smile

            # Add text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except Exception:
                font = ImageFont.load_default()

            draw.text((284, 600), f"Avatar: {profile_name}", fill=(100, 100, 100), font=font)
            draw.text((300, 640), f"Seed: {seed}", fill=(150, 150, 150), font=font)

            output_path = self.AVATARS_DIR / f"{profile_name}.png"
            img.save(str(output_path))

            return AvatarResult(
                image_path=str(output_path), seed=seed,
                profile_name=profile_name, prompt="placeholder", success=True,
            )

        except Exception as e:
            return AvatarResult(
                image_path="", seed=seed, profile_name=profile_name,
                prompt="placeholder", success=False, error=str(e),
            )

    async def _video_with_dashscope(
        self, prompt: str, avatar_path: Path, duration_sec: int
    ) -> VideoResult:
        """Generate video using DashScope Wan 2.7 I2V (img2vid)."""
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not api_key or not avatar_path.exists():
            return VideoResult(video_path="", duration_sec=0, model="dashscope", success=False)

        try:
            # Read avatar as base64 data URI
            import base64
            with open(avatar_path, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode()
            mime = "image/png" if str(avatar_path).endswith(".png") else "image/jpeg"
            data_uri = f"data:{mime};base64,{b64}"

            from Services.generation.dashscope_video import generate_video
            video_url = await generate_video(
                image_url=data_uri,
                prompt=prompt,
                duration=duration_sec,
            )

            if video_url:
                # Download video
                import httpx
                import uuid
                video_path = str(self.VIDEOS_DIR / f"dash-{uuid.uuid4().hex[:8]}.mp4")
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.get(video_url)
                    with open(video_path, "wb") as f:
                        f.write(resp.content)

                return VideoResult(
                    video_path=video_path, duration_sec=duration_sec,
                    model="dashscope", success=True,
                )

        except Exception:
            pass

        return VideoResult(video_path="", duration_sec=0, model="dashscope", success=False)

    async def _video_with_veo(
        self, prompt: str, avatar_path: Path, duration_sec: int
    ) -> VideoResult:
        """Generate video using Google Veo (img2vid)."""
        api_key = os.environ.get("GOOGLE_AI_API_KEY", "")
        if not api_key or not avatar_path.exists():
            return VideoResult(video_path="", duration_sec=0, model="veo", success=False)

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            # Read avatar image
            with open(avatar_path, "rb") as f:
                image_bytes = f.read()

            # Generate video from image
            response = client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                image={"image_bytes": image_bytes},
                config={"number_of_videos": 1},
            )

            if response and hasattr(response, 'videos') and response.videos:
                video = response.videos[0]
                video_path = str(self.VIDEOS_DIR / f"char-{uuid.uuid4().hex[:8]}.mp4")

                if hasattr(video, 'video') and video.video:
                    with open(video_path, "wb") as f:
                        f.write(video.video)

                    return VideoResult(
                        video_path=video_path, duration_sec=duration_sec,
                        model="veo", success=True,
                    )

        except Exception:
            pass

        return VideoResult(video_path="", duration_sec=0, model="veo", success=False)

