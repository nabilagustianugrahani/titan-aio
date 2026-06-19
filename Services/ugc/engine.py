"""
UGC Engine — AI-powered User Generated Content creation.

Uses Gemini 2.5 Flash for:
1. Hook generation (attention grabbers)
2. Script writing (UGC-style, sounds like real people)
3. Caption generation (platform-optimized)
4. Hashtag generation (trending + relevant)
5. Video prompt generation (for Google Flow/Kaggle)

Replaces hardcoded templates with AI-generated content.

Usage:
    from Services.ugc.engine import UGCEngine
    engine = UGCEngine()
    result = await engine.generate(product_title="Serum Vitamin C", category="kecantikan")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class UGCHook:
    """Single UGC hook."""
    text: str
    style: str  # curiosity, problem, social_proof, testimonial, scarcity, urgency
    platform: str  # tiktok, instagram, youtube
    predicted_ctr: str  # high, medium, low


@dataclass
class UGCScript:
    """Full UGC script."""
    hook: str
    problem: str
    solution: str
    demo: str
    social_proof: str
    cta: str
    full_script: str
    duration_seconds: int
    style: str  # talking_head, voiceover, text_overlay, unboxing


@dataclass
class UGCCaption:
    """Platform-optimized caption."""
    text: str
    hashtags: list[str]
    emoji: str
    platform: str
    character_count: int


@dataclass
class UGCResult:
    """Complete UGC package."""
    hooks: list[UGHook]
    scripts: list[UGCScript]
    captions: list[UGCCaption]
    video_prompts: list[str]
    product_title: str
    category: str
    avatar_path: str = ""  # Consistent avatar reference image
    character_seed: int = 0  # Fixed seed for character consistency


class UGCEngine:
    """AI-powered UGC content generator."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Get Gemini client (lazy init)."""
        if self._client is not None:
            return self._client

        api_key = os.environ.get("GOOGLE_AI_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            return self._client
        except Exception:
            return None

    async def generate(
        self,
        product_title: str,
        product_description: str = "",
        category: str = "umum",
        price: float = 0,
        platform: str = "tiktok",
        num_hooks: int = 10,
        num_scripts: int = 5,
        profile_name: str = "",
    ) -> UGCResult:
        """Generate complete UGC package using AI.

        Args:
            product_title: Product name
            product_description: What the product does
            category: Product category (kecantikan, elektronik, etc.)
            price: Product price in IDR
            platform: Target platform
            num_hooks: Number of hooks to generate
            num_scripts: Number of scripts to generate
            profile_name: Consistency profile name (for consistent character/brand)

        Returns:
            UGCResult with hooks, scripts, captions, video prompts
        """
        # Load consistency profile if provided
        profile = None
        avatar_path = ""
        character_seed = 0
        if profile_name:
            from Services.ugc.consistency import UGCConsistency
            cons = UGCConsistency()
            profile = cons.get_or_create(profile_name)
            character_seed = profile.avatar.seed

            # Get or generate avatar
            from Services.ugc.character import CharacterConsistency
            char = CharacterConsistency()
            avatar = await char.generate_avatar(
                profile_name=profile_name,
                gender=profile.avatar.gender,
                age_range=profile.avatar.age_range,
                skin_tone=profile.avatar.skin_tone,
                hair_style=profile.avatar.hair_style,
                style=profile.avatar.style,
                seed=character_seed,
            )
            avatar_path = avatar.image_path

        client = self._get_client()

        if client:
            # AI-generated content with consistency
            hooks = await self._ai_hooks(client, product_title, category, num_hooks, profile)
            scripts = await self._ai_scripts(client, product_title, category, num_scripts, profile)
            captions = await self._ai_captions(client, product_title, category, platform, profile)
            video_prompts = await self._ai_video_prompts(client, product_title, category, profile)
        else:
            # Fallback to templates
            hooks = self._template_hooks(product_title, num_hooks)
            scripts = self._template_scripts(product_title, num_scripts)
            captions = self._template_captions(product_title, platform)
            video_prompts = self._template_video_prompts(product_title)

        return UGCResult(
            hooks=hooks,
            scripts=scripts,
            captions=captions,
            video_prompts=video_prompts,
            product_title=product_title,
            category=category,
            avatar_path=avatar_path,
            character_seed=character_seed,
        )

    # ── AI Generation ───────────────────────────────────────────

    async def _ai_hooks(
        self, client, product: str, category: str, count: int, profile=None
    ) -> list[UGHook]:
        """Generate hooks using Gemini."""
        voice_context = ""
        if profile:
            voice_context = f"""
Brand voice: {profile.voice.tone} tone, {profile.voice.language}
Vocabulary: {', '.join(profile.voice.vocabulary[:5])}
Avoid: {', '.join(profile.voice.avoid_words[:3])}
Emoji usage: {profile.voice.emoji_usage}
"""

        prompt = f"""Generate {count} UGC hooks for a {category} product called "{product}".
{voice_context}
Rules:
- Sound like a REAL person talking to camera, NOT an ad
- Mix styles: curiosity, problem, social_proof, testimonial, scarcity, urgency
- Use Indonesian informal language (aku/gue/kamu)
- Keep under 15 words each
- Include specific numbers when possible
- Make them clickable and scroll-stopping

Output JSON array:
[
  {{"text": "hook text", "style": "curiosity", "predicted_ctr": "high"}},
  ...
]"""

        try:
            response = await self._run_ai(client, prompt)
            hooks_data = self._parse_json(response)
            return [
                UGCHook(
                    text=h.get("text", ""),
                    style=h.get("style", "curiosity"),
                    platform="tiktok",
                    predicted_ctr=h.get("predicted_ctr", "medium"),
                )
                for h in hooks_data[:count]
            ]
        except Exception:
            return self._template_hooks(product, count)

    async def _ai_scripts(
        self, client, product: str, category: str, count: int, profile=None
    ) -> list[UGCScript]:
        """Generate UGC scripts using Gemini."""
        prompt = f"""Generate {count} UGC scripts for a {category} product called "{product}".

Each script should sound like a REAL person talking to camera. Not an ad.

Structure for each script:
- hook (3s): attention grabber
- problem (5s): relatable pain point
- solution (10s): how this product helps
- demo (10s): show the product
- social_proof (5s): results/proof
- cta (3s): call to action

Use informal Indonesian (aku/gue/kamu).
Mix styles: talking_head, voiceover, unboxing.

Output JSON array:
[
  {{
    "hook": "...",
    "problem": "...",
    "solution": "...",
    "demo": "...",
    "social_proof": "...",
    "cta": "...",
    "full_script": "[HOOK] ...\\n[PROBLEM] ...\\n[SOLUTION] ...\\n[DEMO] ...\\n[SOCIAL] ...\\n[CTA] ...",
    "duration_seconds": 30,
    "style": "talking_head"
  }},
  ...
]"""

        try:
            response = await self._run_ai(client, prompt)
            scripts_data = self._parse_json(response)
            return [
                UGCScript(
                    hook=s.get("hook", ""),
                    problem=s.get("problem", ""),
                    solution=s.get("solution", ""),
                    demo=s.get("demo", ""),
                    social_proof=s.get("social_proof", ""),
                    cta=s.get("cta", ""),
                    full_script=s.get("full_script", ""),
                    duration_seconds=s.get("duration_seconds", 30),
                    style=s.get("style", "talking_head"),
                )
                for s in scripts_data[:count]
            ]
        except Exception:
            return self._template_scripts(product, count)

    async def _ai_captions(
        self, client, product: str, category: str, platform: str, profile=None
    ) -> list[UGCCaption]:
        """Generate platform-optimized captions."""
        prompt = f"""Generate 5 captions for a {category} product called "{product}" for {platform}.

Rules:
- First line is the hook (most important)
- Include relevant hashtags (5-10)
- Use emojis appropriately
- Stay within {self._char_limit(platform)} characters
- Sound authentic, not salesy

Output JSON array:
[
  {{"text": "caption text with hashtags", "hashtags": ["tag1", "tag2"], "emoji": "✨"}},
  ...
]"""

        try:
            response = await self._run_ai(client, prompt)
            captions_data = self._parse_json(response)
            return [
                UGCCaption(
                    text=c.get("text", ""),
                    hashtags=c.get("hashtags", []),
                    emoji=c.get("emoji", ""),
                    platform=platform,
                    character_count=len(c.get("text", "")),
                )
                for c in captions_data[:5]
            ]
        except Exception:
            return self._template_captions(product, platform)

    async def _ai_video_prompts(
        self, client, product: str, category: str, profile=None
    ) -> list[str]:
        """Generate video prompts for Google Flow/Kaggle."""
        prompt = f"""Generate 5 video prompts for a {category} product called "{product}".

These are for AI video generation (text-to-video).
Each prompt should describe a UGC-style video scene.

Rules:
- Describe visual scene (camera angles, lighting, actions)
- Include product placement
- UGC style (handheld feel, natural lighting)
- Vertical format (9:16) for TikTok/Reels
- 5-10 seconds each

Output JSON array of strings:
["prompt 1", "prompt 2", ...]"""

        try:
            response = await self._run_ai(client, prompt)
            prompts = self._parse_json(response)
            if isinstance(prompts, list):
                return [str(p) for p in prompts[:5]]
            return self._template_video_prompts(product)
        except Exception:
            return self._template_video_prompts(product)

    # ── Helpers ─────────────────────────────────────────────────

    async def _run_ai(self, client, prompt: str) -> str:
        """Run Gemini API call."""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text or ""

    def _parse_json(self, text: str):
        """Extract JSON from AI response."""
        # Try to find JSON array or object
        import re
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return []

    def _char_limit(self, platform: str) -> int:
        """Character limit per platform."""
        limits = {
            "tiktok": 300,
            "instagram": 2200,
            "facebook": 63206,
        }
        return limits.get(platform, 300)

    # ── Fallback Templates ──────────────────────────────────────

    def _template_hooks(self, product: str, count: int) -> list[UGHook]:
        """Template hooks (fallback when AI unavailable)."""
        templates = [
            (f"STOP! Jangan beli {product} sebelum nonton ini...", "urgency"),
            (f"Aku gak nyangka {product} sebagus ini...", "testimonial"),
            (f"Udah 10.000+ orang pakai {product}, kamu kapan?", "social_proof"),
            (f"Review jujur {product} setelah 30 hari pakai...", "curiosity"),
            (f"Harga segini? Serius? {product}??", "comparison"),
            (f"Flash sale {product} cuma 2 jam lagi!", "scarcity"),
            (f"Dari skeptic jadi fanboy {product}!", "transformation"),
            (f"POV: kamu belum tau {product} exist", "curiosity"),
            (f"Kenapa sih semua orang ribet soal {product}?", "social_proof"),
            (f"Last chance! {product} diskon ends tonight", "urgency"),
        ]
        return [
            UGCHook(
                text=t, style=s, platform="tiktok",
                predicted_ctr="high" if s in ["urgency", "scarcity"] else "medium",
            )
            for t, s in templates[:count]
        ]

    def _template_scripts(self, product: str, count: int) -> list[UGCScript]:
        """Template scripts (fallback)."""
        scripts = []
        styles = ["talking_head", "voiceover", "unboxing"]
        for i in range(min(count, 3)):
            style = styles[i % len(styles)]
            scripts.append(UGCScript(
                hook=f"Stop scrolling! Ini yang kamu butuhin...",
                problem="Selama ini gue cari produk yang beneran works...",
                solution=f"Dan ternyata {product} jawabannya!",
                demo=f"*show product close-up* Lihat ini, kualitasnya gila...",
                social_proof="Udah ribuan orang buktiin sendiri.",
                cta="Link di bio! Diskon terbatas!",
                full_script=(
                    f"[HOOK - 3s] Stop scrolling! Ini yang kamu butuhin...\n"
                    f"[PROBLEM - 5s] Selama ini gue cari produk yang beneran works...\n"
                    f"[SOLUTION - 10s] Dan ternyata {product} jawabannya!\n"
                    f"[DEMO - 7s] *show product close-up* Lihat ini, kualitasnya gila...\n"
                    f"[SOCIAL - 3s] Udah ribuan orang buktiin sendiri.\n"
                    f"[CTA - 2s] Link di bio! Diskon terbatas!"
                ),
                duration_seconds=30,
                style=style,
            ))
        return scripts

    def _template_captions(self, product: str, platform: str) -> list[UGCCaption]:
        """Template captions (fallback)."""
        captions = [
            UGCCaption(
                text=f"Review jujur {product} ✨ Worth it atau engga? Cek videonya!",
                hashtags=["review", "honestreview", "productreview", "rekomendasi", "fyp"],
                emoji="✨",
                platform=platform,
                character_count=60,
            ),
            UGCCaption(
                text=f"Flash sale {product}! Harga gila guys 🔥",
                hashtags=["flashsale", "diskon", "promo", "viral", "fyp"],
                emoji="🔥",
                platform=platform,
                character_count=40,
            ),
        ]
        return captions

    def _template_video_prompts(self, product: str) -> list[str]:
        """Template video prompts (fallback)."""
        return [
            f"Person holding {product} close to camera, natural lighting, handheld style, vertical format",
            f"Unboxing {product} on clean desk, overhead shot, satisfying reveal moment",
            f"Before/after transformation using {product}, split screen, natural lighting",
            f"Close-up of {product} texture/details, macro shot, soft lighting",
            f"Person using {product} in daily routine, lifestyle setting, casual vibes",
        ]
