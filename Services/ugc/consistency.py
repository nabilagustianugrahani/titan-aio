"""
UGC Consistency — Maintain consistent character, brand voice, and visual style.

Ensures all UGC content looks like it's from the same creator:
1. Same face/avatar across all videos
2. Same voice/tone in scripts
3. Same visual style (colors, fonts, lighting)
4. Same hook patterns and CTA style

Usage:
    from Services.ugc.consistency import UGCConsistency
    cons = UGCConsistency()
    profile = cons.get_or_create("beauty_influencer")
    # Use profile.seed for video generation
    # Use profile.voice for script generation
    # Use profile.style for visual generation
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AvatarProfile:
    """Consistent character profile."""
    id: str
    name: str
    gender: str  # male, female, neutral
    age_range: str  # 20-25, 25-30, etc.
    skin_tone: str  # light, medium, dark
    hair_style: str  # long, short, hijab, etc.
    style: str  # casual, professional, trendy, minimal
    vibe: str  # friendly, trustworthy, energetic, calm
    seed: int  # For consistent AI generation
    reference_images: list[str] = field(default_factory=list)


@dataclass
class BrandVoice:
    """Consistent brand voice/tone."""
    tone: str  # casual, formal, friendly, professional
    vocabulary: list[str]  # words to use
    avoid_words: list[str]  # words to avoid
    sentence_length: str  # short, medium, long
    emoji_usage: str  # heavy, moderate, minimal
    language: str  # informal_id, formal_id, english


@dataclass
class VisualStyle:
    """Consistent visual style."""
    color_palette: list[str]  # hex colors
    font_style: str  # bold, minimal, playful
    lighting: str  # natural, studio, warm, cool
    filter: str  # none, warm, cool, vintage
    aspect_ratio: str  # 9:16, 1:1, 16:9
    resolution: tuple[int, int] = (1080, 1920)


@dataclass
class ConsistencyProfile:
    """Complete consistency profile for a brand/creator."""
    id: str
    name: str
    avatar: AvatarProfile
    voice: BrandVoice
    visual: VisualStyle
    hook_patterns: list[str]  # recurring hook patterns
    cta_patterns: list[str]  # recurring CTA patterns
    hashtags: list[str]  # brand hashtags


class UGCConsistency:
    """Maintain consistency across all UGC content."""

    PROFILES_DIR = Path("/tmp/titan-ugc-profiles")

    def __init__(self):
        self.PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    def get_or_create(self, name: str) -> ConsistencyProfile:
        """Get existing profile or create new one."""
        profile_file = self.PROFILES_DIR / f"{name}.json"
        if profile_file.exists():
            return self._load_profile(profile_file)
        return self._create_profile(name)

    def _create_profile(self, name: str) -> ConsistencyProfile:
        """Create a new consistency profile."""
        seed = random.randint(1000, 999999)

        avatar = AvatarProfile(
            id=str(uuid.uuid4()),
            name=name,
            gender=random.choice(["female", "male"]),
            age_range=random.choice(["20-25", "25-30", "30-35"]),
            skin_tone=random.choice(["light", "medium", "dark"]),
            hair_style=random.choice(["long", "short", "hijab"]),
            style="casual",
            vibe="friendly",
            seed=seed,
        )

        voice = BrandVoice(
            tone="casual",
            vocabulary=["aku", "kamu", "guys", "bestie", "worth it", "recommended"],
            avoid_words=["formal", "corporate", "expensive"],
            sentence_length="short",
            emoji_usage="moderate",
            language="informal_id",
        )

        visual = VisualStyle(
            color_palette=["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"],
            font_style="bold",
            lighting="natural",
            filter="warm",
            aspect_ratio="9:16",
            resolution=(1080, 1920),
        )

        profile = ConsistencyProfile(
            id=str(uuid.uuid4()),
            name=name,
            avatar=avatar,
            voice=voice,
            visual=visual,
            hook_patterns=[
                "STOP! Jangan beli sebelum...",
                "Aku gak nyangka...",
                "Review jujur setelah...",
                "POV: kamu belum tau...",
                "Udah {n} orang pakai...",
            ],
            cta_patterns=[
                "Link di bio!",
                "Beli sekarang!",
                "Diskon terbatas!",
                "Check link di bio ya!",
                "Stok terbatas, buruan!",
            ],
            hashtags=["fyp", "viral", "rekomendasi", "review", "honestreview"],
        )

        self._save_profile(profile)
        return profile

    def _save_profile(self, profile: ConsistencyProfile):
        """Save profile to disk."""
        profile_file = self.PROFILES_DIR / f"{profile.name}.json"
        data = {
            "id": profile.id,
            "name": profile.name,
            "avatar": {
                "id": profile.avatar.id,
                "name": profile.avatar.name,
                "gender": profile.avatar.gender,
                "age_range": profile.avatar.age_range,
                "skin_tone": profile.avatar.skin_tone,
                "hair_style": profile.avatar.hair_style,
                "style": profile.avatar.style,
                "vibe": profile.avatar.vibe,
                "seed": profile.avatar.seed,
            },
            "voice": {
                "tone": profile.voice.tone,
                "vocabulary": profile.voice.vocabulary,
                "avoid_words": profile.voice.avoid_words,
                "sentence_length": profile.voice.sentence_length,
                "emoji_usage": profile.voice.emoji_usage,
                "language": profile.voice.language,
            },
            "visual": {
                "color_palette": profile.visual.color_palette,
                "font_style": profile.visual.font_style,
                "lighting": profile.visual.lighting,
                "filter": profile.visual.filter,
                "aspect_ratio": profile.visual.aspect_ratio,
                "resolution": list(profile.visual.resolution),
            },
            "hook_patterns": profile.hook_patterns,
            "cta_patterns": profile.cta_patterns,
            "hashtags": profile.hashtags,
        }
        profile_file.write_text(json.dumps(data, indent=2))

    def _load_profile(self, path: Path) -> ConsistencyProfile:
        """Load profile from disk."""
        data = json.loads(path.read_text())
        return ConsistencyProfile(
            id=data["id"],
            name=data["name"],
            avatar=AvatarProfile(**data["avatar"]),
            voice=BrandVoice(**data["voice"]),
            visual=VisualStyle(**{**data["visual"], "resolution": tuple(data["visual"]["resolution"])}),
            hook_patterns=data["hook_patterns"],
            cta_patterns=data["cta_patterns"],
            hashtags=data["hashtags"],
        )

    def list_profiles(self) -> list[str]:
        """List all saved profiles."""
        return [f.stem for f in self.PROFILES_DIR.glob("*.json")]

    def delete_profile(self, name: str):
        """Delete a profile."""
        profile_file = self.PROFILES_DIR / f"{name}.json"
        if profile_file.exists():
            profile_file.unlink()
