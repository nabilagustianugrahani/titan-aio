"""
UGC Pipeline — End-to-end UGC video generation.

Flow:
1. UGCEngine → hooks, scripts, captions, video_prompts
2. CharacterConsistency → avatar image (fixed seed)
3. DashScope Wan 2.7 I2V → video (avatar as first frame)
4. Assembly → final video + metadata

Usage:
    from Services.ugc.pipeline import UGCPipeline
    pipeline = UGCPipeline()
    result = await pipeline.run(
        product_title="Serum Vitamin C",
        category="kecantikan",
        profile_name="beauty_influencer",
    )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoOutput:
    """Single generated video."""
    video_path: str
    video_url: str
    prompt: str
    source: str  # dashscope, veo, modal
    duration_sec: int
    variant_label: str = ""


@dataclass
class PipelineResult:
    """Complete UGC pipeline output."""
    videos: list[VideoOutput]
    hooks: list[dict]
    scripts: list[dict]
    captions: list[dict]
    avatar_path: str
    product_title: str
    category: str
    profile_name: str
    success: bool
    error: str = ""


class UGCPipeline:
    """Orchestrate UGC content → avatar → video generation."""

    OUTPUT_DIR = Path("/tmp/titan-ugc-pipeline")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        product_title: str,
        product_description: str = "",
        category: str = "umum",
        price: float = 0,
        platform: str = "tiktok",
        profile_name: str = "default",
        num_videos: int = 3,
    ) -> PipelineResult:
        """Run full UGC pipeline.

        Args:
            product_title: Product name
            product_description: What the product does
            category: Product category
            price: Price in IDR
            platform: Target platform
            profile_name: Consistency profile name
            num_videos: Number of video variants to generate

        Returns:
            PipelineResult with videos, hooks, scripts, captions
        """
        print(f"\n🎬 UGC Pipeline: {product_title}")
        print(f"   Profile: {profile_name} | Videos: {num_videos}")

        # Step 1: Generate UGC content
        print("\n📝 Step 1: Generating UGC content...")
        from Services.ugc.engine import UGCEngine
        engine = UGCEngine()
        ugc_result = await engine.generate(
            product_title=product_title,
            product_description=product_description,
            category=category,
            price=price,
            platform=platform,
            num_hooks=10,
            num_scripts=num_videos,
            profile_name=profile_name,
        )
        print(f"   ✅ {len(ugc_result.hooks)} hooks, {len(ugc_result.scripts)} scripts, {len(ugc_result.video_prompts)} prompts")

        # Step 2: Generate avatar
        print("\n🎨 Step 2: Generating avatar...")
        from Services.ugc.character import CharacterConsistency
        char = CharacterConsistency()

        # Get profile for avatar params
        avatar_gender = "female"
        avatar_age = "25-30"
        avatar_seed = ugc_result.character_seed or 42

        if profile_name != "default":
            try:
                from Services.ugc.consistency import UGCConsistency
                cons = UGCConsistency()
                profile = cons.get_or_create(profile_name)
                avatar_gender = profile.avatar.gender
                avatar_age = profile.avatar.age_range
                avatar_seed = profile.avatar.seed
            except Exception:
                pass

        avatar = await char.generate_avatar(
            profile_name=profile_name,
            gender=avatar_gender,
            age_range=avatar_age,
            seed=avatar_seed,
        )

        avatar_path = avatar.image_path
        if avatar.success:
            print(f"   ✅ Avatar: {avatar_path}")
        else:
            print(f"   ⚠️ Avatar failed: {avatar.error}, using placeholder")

        # Step 3: Generate videos via DashScope I2V
        print("\n🎬 Step 3: Generating videos...")
        videos = []

        # Use video prompts from UGC engine, fallback to scripts
        prompts = ugc_result.video_prompts[:num_videos]
        if not prompts and ugc_result.scripts:
            prompts = [s.full_script[:200] for s in ugc_result.scripts[:num_videos]]

        for i, prompt in enumerate(prompts):
            label = f"variant_{i+1}"
            print(f"   🎬 Generating {label}...")

            video = await self._generate_video(
                avatar_path=avatar_path,
                prompt=prompt,
                label=label,
                duration=5,
            )
            videos.append(video)

            if video.video_path:
                print(f"   ✅ {label}: {video.source}")
            else:
                print(f"   ❌ {label}: failed")

        # Step 4: Assemble result
        hooks_data = [{"text": h.text, "style": h.style, "ctr": h.predicted_ctr} for h in ugc_result.hooks]
        scripts_data = [{"hook": s.hook, "full_script": s.full_script, "style": s.style, "duration": s.duration_seconds} for s in ugc_result.scripts]
        captions_data = [{"text": c.text, "hashtags": c.hashtags, "platform": c.platform} for c in ugc_result.captions]

        success = any(v.video_path for v in videos)

        print(f"\n{'='*50}")
        print(f"📊 Pipeline complete: {sum(1 for v in videos if v.video_path)}/{len(videos)} videos generated")
        print(f"{'='*50}")

        return PipelineResult(
            videos=videos,
            hooks=hooks_data,
            scripts=scripts_data,
            captions=captions_data,
            avatar_path=avatar_path,
            product_title=product_title,
            category=category,
            profile_name=profile_name,
            success=success,
        )

    async def _generate_video(
        self,
        avatar_path: str,
        prompt: str,
        label: str = "video",
        duration: int = 5,
    ) -> VideoOutput:
        """Generate video with fallback chain.

        Priority:
        1. DashScope Wan 2.7 I2V (primary)
        2. Google Veo (fallback)
        3. Modal GPU (last resort)
        """
        # 1. Try DashScope I2V
        if avatar_path:
            video = await self._try_dashscope(avatar_path, prompt, duration, label)
            if video.video_path:
                return video

        # 2. Try Google Veo (cloud API, no VPS GPU)
        if avatar_path:
            video = await self._try_veo(avatar_path, prompt, duration, label)
            if video.video_path:
                return video

        # 3. Try HF Spaces T4 (free GPU, remote)
        video = await self._try_hf_spaces(avatar_path, prompt, duration, label)
        if video.video_path:
            return video

        return VideoOutput(
            video_path="", video_url="", prompt=prompt,
            source="none", duration_sec=duration, variant_label=label,
        )

    async def _try_dashscope(
        self, avatar_path: str, prompt: str, duration: int, label: str
    ) -> VideoOutput:
        """Try DashScope Wan 2.7 I2V (cloud, no GPU)."""
        try:
            # Read avatar as base64 data URI
            import base64
            with open(avatar_path, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode()
            mime = "image/png" if avatar_path.endswith(".png") else "image/jpeg"
            data_uri = f"data:{mime};base64,{b64}"

            from Services.generation.dashscope_video import generate_video
            video_url = await generate_video(
                image_url=data_uri,
                prompt=prompt,
                duration=duration,
            )

            if video_url:
                # Download video
                import httpx
                video_path = str(self.OUTPUT_DIR / f"{label}-{uuid.uuid4().hex[:8]}.mp4")
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.get(video_url)
                    with open(video_path, "wb") as f:
                        f.write(resp.content)

                return VideoOutput(
                    video_path=video_path,
                    video_url=video_url,
                    prompt=prompt,
                    source="dashscope",
                    duration_sec=duration,
                    variant_label=label,
                )

        except Exception as e:
            print(f"    ⚠️ DashScope failed: {e}")

        return VideoOutput(
            video_path="", video_url="", prompt=prompt,
            source="none", duration_sec=duration, variant_label=label,
        )

    async def _try_veo(
        self, avatar_path: str, prompt: str, duration: int, label: str
    ) -> VideoOutput:
        """Try Google Veo img2vid (cloud API, no GPU on VPS)."""
        try:
            from Services.ugc.character import CharacterConsistency
            char = CharacterConsistency()
            result = await char._video_with_veo(
                prompt=prompt,
                avatar_path=Path(avatar_path),
                duration_sec=duration,
            )

            if result.success:
                return VideoOutput(
                    video_path=result.video_path,
                    video_url="",
                    prompt=prompt,
                    source="veo",
                    duration_sec=duration,
                    variant_label=label,
                )

        except Exception as e:
            print(f"    ⚠️ Veo failed: {e}")

        return VideoOutput(
            video_path="", video_url="", prompt=prompt,
            source="none", duration_sec=duration, variant_label=label,
        )

    async def _try_kaggle(
        self, avatar_path: str, prompt: str, duration: int, label: str
    ) -> VideoOutput:
        """Try Kaggle T4 x2 GPU (free, 30h/week)."""
        try:
            from Workers.kaggle_setup import KaggleNotebookGenerator
            gen = KaggleNotebookGenerator()

            notebook = gen.create_video_notebook(
                script=prompt,
                model="wan-2-2",
                resolution=(512, 512),
                num_frames=81,
            )

            notebook_path = str(self.OUTPUT_DIR / f"{label}_kaggle.ipynb")
            gen.save_notebook(notebook, notebook_path)

            print(f"    📓 Kaggle notebook: {notebook_path}")
            print("    ⚠️ Upload ke Kaggle → Enable GPU → Run → Download video")

            return VideoOutput(
                video_path="",
                video_url="",
                prompt=prompt,
                source="kaggle_pending",
                duration_sec=duration,
                variant_label=label,
            )

        except Exception as e:
            print(f"    ⚠️ Kaggle dispatch failed: {e}")
