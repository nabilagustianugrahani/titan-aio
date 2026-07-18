"""UGC Pipeline — End-to-end UGC video generation.

Flow:
1. UGCEngine → hooks, scripts, captions, video_prompts
2. CharacterConsistency → avatar image (fixed seed)
3. VoiceCloner → voiceover audio for each script
4. MusicGenerator → background music track
5. DashScope Wan 2.7 I2V → video (avatar as first frame)
6. SceneBuilder → compose final video (video + voiceover + text + music)

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

import os
import uuid
from dataclasses import dataclass, field
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
class AudioAsset:
    """Generated audio (voiceover or music)."""

    path: str
    text: str = ""
    type: str = "voiceover"  # voiceover, music
    duration_sec: float = 0


@dataclass
class PipelineResult:
    """Complete UGC pipeline output."""

    videos: list[VideoOutput]
    hooks: list[dict]
    scripts: list[dict]
    captions: list[dict]
    avatar_path: str
    voiceovers: list[AudioAsset] = field(default_factory=list)
    background_music: AudioAsset | None = None
    composed_video_path: str = ""
    product_title: str = ""
    category: str = ""
    profile_name: str = ""
    success: bool = False
    error: str = ""


class UGCPipeline:
    """Orchestrate UGC content → avatar → voiceover → music → video → compose."""

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
        with_music: bool = True,
        with_voiceover: bool = True,
        with_scene_composition: bool = True,
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
            with_music: Generate background music
            with_voiceover: Generate voiceover audio
            with_scene_composition: Compose final video from all assets

        Returns:
            PipelineResult with videos, hooks, scripts, captions, audio, composed video

        """
        print(f"\n{'='*50}")
        print(f"🎬 UGC Pipeline: {product_title}")
        print(f"   Profile: {profile_name} | Videos: {num_videos}")
        print(f"{'='*50}")

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

        # Step 3: Generate voiceovers
        voiceovers: list[AudioAsset] = []
        if with_voiceover and ugc_result.scripts:
            print("\n🗣️ Step 3: Generating voiceovers...")
            from Services.voice.voice_cloner import VoiceCloner
            cloner = VoiceCloner()

            for i, script in enumerate(ugc_result.scripts[:num_videos]):
                text = script.full_script or script.hook
                if len(text) > 500:
                    text = text[:500]
                print(f"   🔊 Voiceover {i+1}: {len(text)} chars...")
                result = await cloner.clone(
                    text=text,
                    language="id",
                    gender=avatar_gender,
                )
                if result.success:
                    voiceovers.append(AudioAsset(
                        path=result.audio_path,
                        text=text,
                        type="voiceover",
                    ))
                    print(f"   ✅ Voiceover {i+1}: {result.audio_path}")
                else:
                    print(f"   ⚠️ Voiceover {i+1} failed: {result.error}")

        # Step 4: Generate background music
        bg_music: AudioAsset | None = None
        if with_music:
            print("\n🎵 Step 4: Generating background music...")
            music_prompt = self._music_prompt_for_category(category)
            from Services.audio.music_generator import MusicGenerator
            music_gen = MusicGenerator()
            music_result = await music_gen.generate(prompt=music_prompt, duration=15)
            if music_result.success:
                bg_music = AudioAsset(
                    path=music_result.audio_path,
                    type="music",
                    duration_sec=music_result.duration_sec,
                )
                print(f"   ✅ Background music: {music_result.audio_path}")
            else:
                print(f"   ⚠️ Music failed: {music_result.error}")

        # Step 5: Generate videos via DashScope I2V
        print("\n🎬 Step 5: Generating videos...")
        videos = []

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

        # Step 6: Compose final video (scene builder)
        composed_video_path = ""
        if with_scene_composition and any(v.video_path for v in videos):
            print("\n🎬 Step 6: Composing final video...")
            composed_video_path = await self._compose_video(
                videos=videos,
                voiceovers=voiceovers,
                bg_music=bg_music,
                scripts=ugc_result.scripts[:num_videos],
            )

        # Assemble result
        hooks_data = [{"text": h.text, "style": h.style, "ctr": h.predicted_ctr} for h in ugc_result.hooks]
        scripts_data = [
            {"hook": s.hook, "full_script": s.full_script, "style": s.style, "duration": s.duration_seconds}
            for s in ugc_result.scripts
        ]
        captions_data = [
            {"text": c.text, "hashtags": c.hashtags, "platform": c.platform}
            for c in ugc_result.captions
        ]

        success = any(v.video_path for v in videos)

        print(f"\n{'='*50}")
        print("📊 Pipeline complete:")
        print(f"   Videos: {sum(1 for v in videos if v.video_path)}/{len(videos)}")
        print(f"   Voiceovers: {len(voiceovers)}")
        print(f"   Music: {'✅' if bg_music else '❌'}")
        print(f"   Composed: {'✅' if composed_video_path else '❌'}")
        print(f"{'='*50}")

        return PipelineResult(
            videos=videos,
            hooks=hooks_data,
            scripts=scripts_data,
            captions=captions_data,
            avatar_path=avatar_path,
            voiceovers=voiceovers,
            background_music=bg_music,
            composed_video_path=composed_video_path,
            product_title=product_title,
            category=category,
            profile_name=profile_name,
            success=success,
        )

    def _music_prompt_for_category(self, category: str) -> str:
        """Map product category to music description."""
        prompts = {
            "kecantikan": "upbeat electro-pop background music, fresh and feminine",
            "elektronik": "modern electronic tech background music, futuristic",
            "fashion": "trendy pop background music, stylish and energetic",
            "makanan": "lively acoustic background music, warm and appetizing",
            "otomotif": "intense epic background music, powerful and dynamic",
            "kesehatan": "calm ambient background music, soothing and clean",
            "umum": "upbeat corporate background music, positive and modern",
        }
        return prompts.get(category, prompts["umum"])

    async def _compose_video(
        self,
        videos: list[VideoOutput],
        voiceovers: list[AudioAsset],
        bg_music: AudioAsset | None,
        scripts: list,
    ) -> str:
        """Compose final video with scenes, voiceovers, text, and music."""
        try:
            from Services.ugc.scene_builder import SceneBuilder
            builder = SceneBuilder()

            for i, video in enumerate(videos):
                if not video.video_path:
                    continue

                voiceover_path = voiceovers[i].path if i < len(voiceovers) else ""
                script = scripts[i] if i < len(scripts) else None
                text = script.full_script[:100] if script and script.full_script else ""

                builder.add_scene(
                    video_path=video.video_path,
                    text_overlay=text,
                    voiceover_path=voiceover_path,
                    duration_sec=video.duration_sec,
                )

            order = list(builder.scenes.keys())
            builder.arrange(order)

            output_name = f"titan-ugc-{uuid.uuid4().hex[:8]}.mp4"
            export_result = await builder.export(output_name)

            if export_result.success:
                return export_result.video_path
            print(f"   ⚠️ Scene export failed: {export_result.error}")

        except Exception as e:
            print(f"   ⚠️ Composition failed: {e}")

        # Fallback: use first video directly
        for v in videos:
            if v.video_path:
                return v.video_path
        return ""

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
        3. HF Spaces T4 (free GPU, remote)
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
        self, avatar_path: str, prompt: str, duration: int, label: str,
    ) -> VideoOutput:
        """Try DashScope Wan 2.7 I2V (cloud, no GPU)."""
        try:
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
        self, avatar_path: str, prompt: str, duration: int, label: str,
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

    async def _try_hf_spaces(
        self, avatar_path: str, prompt: str, duration: int, label: str,
    ) -> VideoOutput:
        """Try HuggingFace Spaces with T4 GPU."""
        try:
            import httpx
            space_url = "https://api-inference.huggingface.co/models/ByteDance/AnimateDiff-Lightning"
            token = os.environ.get("HF_TOKEN", "")

            async with httpx.AsyncClient(timeout=120) as client:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                payload = {"inputs": prompt}
                resp = await client.post(space_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    video_path = str(self.OUTPUT_DIR / f"{label}-hfs-{uuid.uuid4().hex[:8]}.mp4")
                    with open(video_path, "wb") as f:
                        f.write(resp.content)
                    return VideoOutput(
                        video_path=video_path, video_url="",
                        prompt=prompt, source="hf_spaces",
                        duration_sec=duration, variant_label=label,
                    )
        except Exception as e:
            print(f"    ⚠️ HF Spaces failed: {e}")

        return VideoOutput(
            video_path="", video_url="", prompt=prompt,
            source="none", duration_sec=duration, variant_label=label,
        )

    async def _try_kaggle(
        self, avatar_path: str, prompt: str, duration: int, label: str,
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
