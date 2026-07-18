"""Voice Cloning Service — profile management and text-to-speech generation.

Stores voice profiles (characteristics, not audio) and generates TTS parameters
for consistent AI narration across avatars. Supports multiple voice styles and
emotion modulation. Tracks usage per avatar for analytics.

Usage:
    from Services.voice.cloner import VoiceCloner
    cloner = VoiceCloner()
    profile = await cloner.create_profile(name="Nadia", style="enthusiastic")
    voice = await cloner.generate(text="Check this out!", profile_id=profile.profile_id)
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

# ── Style presets ──────────────────────────────────────────────────

STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "enthusiastic": {
        "pitch_range": (0.9, 1.15),
        "speed_range": (1.05, 1.25),
        "tone": "bright",
        "energy": "high",
        "breathiness": 0.1,
        "vibrato": 0.05,
        "emotion_map": {
            "neutral": {"pitch_mod": 1.0, "speed_mod": 1.0, "energy": 0.8},
            "excited": {"pitch_mod": 1.08, "speed_mod": 1.15, "energy": 1.0},
            "serious": {"pitch_mod": 0.95, "speed_mod": 0.95, "energy": 0.6},
            "funny": {"pitch_mod": 1.1, "speed_mod": 1.2, "energy": 0.9},
            "sad": {"pitch_mod": 0.9, "speed_mod": 0.85, "energy": 0.4},
        },
    },
    "calm": {
        "pitch_range": (0.85, 1.0),
        "speed_range": (0.85, 1.0),
        "tone": "warm",
        "energy": "medium",
        "breathiness": 0.25,
        "vibrato": 0.1,
        "emotion_map": {
            "neutral": {"pitch_mod": 1.0, "speed_mod": 1.0, "energy": 0.5},
            "excited": {"pitch_mod": 1.05, "speed_mod": 1.05, "energy": 0.7},
            "serious": {"pitch_mod": 0.92, "speed_mod": 0.9, "energy": 0.4},
            "funny": {"pitch_mod": 1.03, "speed_mod": 1.1, "energy": 0.6},
            "sad": {"pitch_mod": 0.88, "speed_mod": 0.82, "energy": 0.3},
        },
    },
    "professional": {
        "pitch_range": (0.88, 1.05),
        "speed_range": (0.95, 1.1),
        "tone": "clear",
        "energy": "medium",
        "breathiness": 0.05,
        "vibrato": 0.03,
        "emotion_map": {
            "neutral": {"pitch_mod": 1.0, "speed_mod": 1.0, "energy": 0.6},
            "excited": {"pitch_mod": 1.04, "speed_mod": 1.08, "energy": 0.8},
            "serious": {"pitch_mod": 0.94, "speed_mod": 0.92, "energy": 0.5},
            "funny": {"pitch_mod": 1.02, "speed_mod": 1.05, "energy": 0.7},
            "sad": {"pitch_mod": 0.91, "speed_mod": 0.88, "energy": 0.35},
        },
    },
    "funny": {
        "pitch_range": (0.8, 1.2),
        "speed_range": (1.0, 1.3),
        "tone": "playful",
        "energy": "high",
        "breathiness": 0.15,
        "vibrato": 0.08,
        "emotion_map": {
            "neutral": {"pitch_mod": 1.05, "speed_mod": 1.05, "energy": 0.7},
            "excited": {"pitch_mod": 1.12, "speed_mod": 1.2, "energy": 1.0},
            "serious": {"pitch_mod": 0.98, "speed_mod": 0.95, "energy": 0.5},
            "funny": {"pitch_mod": 1.15, "speed_mod": 1.25, "energy": 1.0},
            "sad": {"pitch_mod": 0.95, "speed_mod": 0.9, "energy": 0.4},
        },
    },
}

VALID_STYLES: list[str] = list(STYLE_PRESETS.keys())
VALID_EMOTIONS: list[str] = ["neutral", "excited", "serious", "funny", "sad"]
VALID_OUTPUT_FORMATS: list[str] = ["mp3", "wav", "ogg", "flac"]


# ── Pydantic models ───────────────────────────────────────────────


class VoiceProfile(BaseModel):
    """A reusable voice profile storing characteristics for TTS generation."""

    profile_id: str = ""
    name: str
    characteristics: dict[str, Any] = Field(default_factory=dict)
    sample_duration: float = 0.0
    languages: list[str] = Field(default_factory=lambda: ["id", "en"])
    style: str = "enthusiastic"
    avatar_id: str | None = None
    created_at: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.profile_id:
            self.profile_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


class VoiceGenerationRequest(BaseModel):
    """Request to generate voice narration from text."""

    text: str
    profile_id: str
    emotion: str = "neutral"
    speed: float = 1.0
    output_format: str = "mp3"
    avatar_id: str | None = None
    custom_params: dict[str, Any] = Field(default_factory=dict)


class VoiceParameters(BaseModel):
    """Computed TTS parameters for a generation request."""

    pitch: float = 1.0
    speed: float = 1.0
    tone: str = "neutral"
    energy: float = 0.5
    emotion: str = "neutral"
    pause_after_hook: float = 0.3
    pause_between_sentences: float = 0.15
    emphasis_words: list[str] = Field(default_factory=list)
    breathing_pattern: str = "natural"
    prosody_contour: str = "default"


class GeneratedVoice(BaseModel):
    """Result of a voice generation request."""

    voice_id: str
    text: str
    duration_estimate: float
    parameters: dict[str, Any]
    profile_used: str
    emotion: str
    status: str = "ready"
    output_format: str = "mp3"
    output_url: str | None = None
    created_at: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


class VoiceUsageStats(BaseModel):
    """Usage statistics for a voice profile."""

    profile_id: str
    total_generations: int = 0
    total_characters: float = 0.0
    total_duration_seconds: float = 0.0
    generations_by_emotion: dict[str, int] = Field(default_factory=dict)
    generations_by_avatar: dict[str, int] = Field(default_factory=dict)
    last_used: str | None = None


# ── Service ────────────────────────────────────────────────────────


class VoiceCloner:
    """Manages voice profiles and generates TTS parameters.

    Stores profiles in-memory with optional persistence. Generates
    parameter sets that downstream TTS engines (DashScope, ElevenLabs,
        etc.) consume to produce audio.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, VoiceProfile] = {}
        self._usage: dict[str, VoiceUsageStats] = {}
        self._history: list[GeneratedVoice] = []
        self._max_history: int = 500

    # ── Profile management ─────────────────────────────────────────

    async def create_profile(
        self,
        name: str,
        style: str = "enthusiastic",
        languages: list[str] | None = None,
        avatar_id: str | None = None,
        custom_characteristics: dict[str, Any] | None = None,
    ) -> VoiceProfile:
        """Create a new voice profile with computed characteristics."""
        if style not in STYLE_PRESETS:
            raise ValueError(
                f"Invalid style '{style}'. Must be one of: {VALID_STYLES}",
            )

        preset = STYLE_PRESETS[style]
        pitch_min, pitch_max = preset["pitch_range"]
        speed_min, speed_max = preset["speed_range"]

        characteristics: dict[str, Any] = {
            "pitch_min": pitch_min,
            "pitch_max": pitch_max,
            "pitch_center": round((pitch_min + pitch_max) / 2, 3),
            "speed_min": speed_min,
            "speed_max": speed_max,
            "speed_center": round((speed_min + speed_max) / 2, 3),
            "tone": preset["tone"],
            "energy_level": preset["energy"],
            "breathiness": preset["breathiness"],
            "vibrato": preset["vibrato"],
        }

        if custom_characteristics:
            characteristics.update(custom_characteristics)

        profile = VoiceProfile(
            name=name,
            characteristics=characteristics,
            languages=languages or ["id", "en"],
            style=style,
            avatar_id=avatar_id,
        )

        self._profiles[profile.profile_id] = profile
        self._usage[profile.profile_id] = VoiceUsageStats(
            profile_id=profile.profile_id,
        )

        return profile

    async def get_profile(self, profile_id: str) -> VoiceProfile | None:
        """Retrieve a voice profile by ID."""
        return self._profiles.get(profile_id)

    async def list_profiles(self, avatar_id: str | None = None) -> list[VoiceProfile]:
        """List all profiles, optionally filtered by avatar."""
        profiles = list(self._profiles.values())
        if avatar_id:
            profiles = [p for p in profiles if p.avatar_id == avatar_id]
        return profiles

    async def update_profile(
        self,
        profile_id: str,
        name: str | None = None,
        style: str | None = None,
        languages: list[str] | None = None,
        characteristics: dict[str, Any] | None = None,
    ) -> VoiceProfile | None:
        """Update an existing profile's properties."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        if name is not None:
            profile.name = name
        if style is not None:
            if style not in STYLE_PRESETS:
                raise ValueError(
                    f"Invalid style '{style}'. Must be one of: {VALID_STYLES}",
                )
            profile.style = style
            preset = STYLE_PRESETS[style]
            profile.characteristics["tone"] = preset["tone"]
            profile.characteristics["energy_level"] = preset["energy"]
            profile.characteristics["breathiness"] = preset["breathiness"]
            profile.characteristics["vibrato"] = preset["vibrato"]
            profile.characteristics["pitch_center"] = round(
                sum(preset["pitch_range"]) / 2, 3,
            )
            profile.characteristics["speed_center"] = round(
                sum(preset["speed_range"]) / 2, 3,
            )
        if languages is not None:
            profile.languages = languages
        if characteristics is not None:
            profile.characteristics.update(characteristics)

        return profile

    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a voice profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._usage.pop(profile_id, None)
            return True
        return False

    # ── Voice generation ───────────────────────────────────────────

    async def generate(
        self,
        text: str,
        profile_id: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        output_format: str = "mp3",
        avatar_id: str | None = None,
        custom_params: dict[str, Any] | None = None,
    ) -> GeneratedVoice:
        """Generate TTS parameters for text using a voice profile.

        Computes pitch, speed, energy, emphasis, and prosody parameters
        that a downstream TTS engine can consume directly.
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Voice profile '{profile_id}' not found")

        if emotion not in VALID_EMOTIONS:
            raise ValueError(
                f"Invalid emotion '{emotion}'. Must be one of: {VALID_EMOTIONS}",
            )

        if output_format not in VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid format '{output_format}'. Must be one of: {VALID_OUTPUT_FORMATS}",
            )

        # Clamp speed
        speed = max(0.5, min(2.0, speed))

        # Compute base parameters from profile characteristics
        params = self._compute_parameters(
            profile=profile,
            text=text,
            emotion=emotion,
            speed=speed,
        )

        # Apply custom overrides
        if custom_params:
            params.update(custom_params)

        # Estimate duration: ~150ms per character at base speed
        base_duration = len(text) * 0.15
        adjusted_duration = base_duration / (params["speed"] * speed)

        # Pause adjustments
        adjusted_duration += text.count("\n") * 0.3
        adjusted_duration += text.count(".") * params.get("pause_between_sentences", 0.15)

        voice_id = hashlib.sha256(
            f"{profile_id}:{text}:{emotion}:{datetime.now(UTC).isoformat()}"
            .encode(),
        ).hexdigest()[:16]

        result = GeneratedVoice(
            voice_id=voice_id,
            text=text,
            duration_estimate=round(adjusted_duration, 2),
            parameters=params,
            profile_used=profile_id,
            emotion=emotion,
            output_format=output_format,
            output_url=f"/tmp/titan-voices/{voice_id}.{output_format}",
        )

        # Update usage stats
        self._track_usage(
            profile_id=profile_id,
            avatar_id=avatar_id or profile.avatar_id,
            emotion=emotion,
            text_length=len(text),
            duration=adjusted_duration,
        )

        # Store in history
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return result

    def _compute_parameters(
        self,
        profile: VoiceProfile,
        text: str,
        emotion: str,
        speed: float,
    ) -> dict[str, Any]:
        """Compute TTS parameters from profile + emotion + text analysis."""
        style = profile.style
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["enthusiastic"])
        emotion_map = preset.get("emotion_map", {})
        emotion_mod = emotion_map.get(emotion, {"pitch_mod": 1.0, "speed_mod": 1.0, "energy": 0.5})

        chars = profile.characteristics
        pitch_center = chars.get("pitch_center", 1.0)
        speed_center = chars.get("speed_center", 1.0)

        # Apply emotion modifiers
        pitch = round(pitch_center * emotion_mod["pitch_mod"], 3)
        computed_speed = round(speed_center * emotion_mod["speed_mod"] * speed, 3)
        energy = round(emotion_mod["energy"], 2)

        # Text analysis for emphasis and pauses
        emphasis_words = self._detect_emphasis_words(text)
        pause_after_hook = 0.3 if "\n" in text else 0.0

        # Prosody contour based on sentence structure
        sentence_count = max(1, text.count(".") + text.count("!") + text.count("?"))
        is_question = text.strip().endswith("?")
        is_exclamation = text.strip().endswith("!")
        is_long = len(text) > 150

        if is_question:
            prosody = "rising"
        elif is_exclamation:
            prosody = "excited"
        elif is_long:
            prosody = "narrative"
        else:
            prosody = "default"

        # Breathing pattern
        if sentence_count > 3:
            breathing = "deep"
        elif energy > 0.7:
            breathing = "short"
        else:
            breathing = "natural"

        return {
            "pitch": pitch,
            "speed": computed_speed,
            "tone": chars.get("tone", "neutral"),
            "energy": energy,
            "emotion": emotion,
            "pause_after_hook": pause_after_hook,
            "pause_between_sentences": chars.get("pause_between_sentences", 0.15),
            "emphasis_words": emphasis_words,
            "breathing_pattern": breathing,
            "prosody_contour": prosody,
            "sentence_count": sentence_count,
            "breathiness": chars.get("breathiness", 0.1),
            "vibrato": chars.get("vibrato", 0.05),
        }

    def _detect_emphasis_words(self, text: str) -> list[str]:
        """Detect words that should receive emphasis in TTS."""
        words = text.split()
        emphasized: list[str] = []

        for i, word in enumerate(words):
            clean = word.strip(".,!?;:\"'")
            # All-caps words
            if clean.isupper() and len(clean) > 1:
                emphasized.append(clean.lower())
            # Words after "..." or "!"
            if i > 0 and words[i - 1] in ("...", "!", "‼"):
                emphasized.append(clean.lower())

        # Check for keywords in text
        text_upper = text.upper()
        for marker in ["BEST", "FREE", "NEW", "LIMITED", "GRATIS", "MURAH"]:
            if marker in text_upper:
                emphasized.append(marker.lower())

        return list(set(emphasized))

    # ── Usage tracking ─────────────────────────────────────────────

    def _track_usage(
        self,
        profile_id: str,
        avatar_id: str | None,
        emotion: str,
        text_length: int,
        duration: float,
    ) -> None:
        """Track generation usage for a profile."""
        stats = self._usage.get(profile_id)
        if not stats:
            stats = VoiceUsageStats(profile_id=profile_id)
            self._usage[profile_id] = stats

        stats.total_generations += 1
        stats.total_characters += text_length
        stats.total_duration_seconds += duration
        stats.last_used = datetime.now(UTC).isoformat()

        stats.generations_by_emotion[emotion] = (
            stats.generations_by_emotion.get(emotion, 0) + 1
        )
        if avatar_id:
            stats.generations_by_avatar[avatar_id] = (
                stats.generations_by_avatar.get(avatar_id, 0) + 1
            )

    async def get_usage_stats(self, profile_id: str) -> VoiceUsageStats | None:
        """Get usage statistics for a profile."""
        return self._usage.get(profile_id)

    async def get_history(self, limit: int = 50) -> list[GeneratedVoice]:
        """Get recent generation history."""
        return self._history[-limit:]

    # ── Batch operations ───────────────────────────────────────────

    async def generate_batch(
        self,
        texts: list[str],
        profile_id: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        output_format: str = "mp3",
        avatar_id: str | None = None,
    ) -> list[GeneratedVoice]:
        """Generate TTS parameters for multiple texts in sequence."""
        results: list[GeneratedVoice] = []
        for text in texts:
            voice = await self.generate(
                text=text,
                profile_id=profile_id,
                emotion=emotion,
                speed=speed,
                output_format=output_format,
                avatar_id=avatar_id,
            )
            results.append(voice)
        return results

    async def generate_with_variations(
        self,
        text: str,
        profile_id: str,
        emotions: list[str] | None = None,
        speeds: list[float] | None = None,
        output_format: str = "mp3",
    ) -> list[GeneratedVoice]:
        """Generate multiple voice variations for A/B testing."""
        if emotions is None:
            emotions = ["neutral", "excited", "serious"]
        if speeds is None:
            speeds = [1.0, 1.1]

        results: list[GeneratedVoice] = []
        for emotion in emotions:
            for speed_val in speeds:
                voice = await self.generate(
                    text=text,
                    profile_id=profile_id,
                    emotion=emotion,
                    speed=speed_val,
                    output_format=output_format,
                )
                results.append(voice)
        return results

    # ── Utility ────────────────────────────────────────────────────

    async def get_style_presets(self) -> dict[str, dict[str, Any]]:
        """Return available style presets and their characteristics."""
        return {
            style: {
                "pitch_range": preset["pitch_range"],
                "speed_range": preset["speed_range"],
                "tone": preset["tone"],
                "energy": preset["energy"],
                "emotions": list(preset["emotion_map"].keys()),
            }
            for style, preset in STYLE_PRESETS.items()
        }

    async def validate_profile(self, profile_id: str) -> dict[str, Any]:
        """Validate a profile and return health check info."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return {"valid": False, "error": "Profile not found"}

        issues: list[str] = []
        if profile.style not in STYLE_PRESETS:
            issues.append(f"Unknown style: {profile.style}")
        if not profile.name.strip():
            issues.append("Empty name")
        if not profile.languages:
            issues.append("No languages specified")

        chars = profile.characteristics
        pitch_center = chars.get("pitch_center", 1.0)
        if pitch_center < 0.5 or pitch_center > 2.0:
            issues.append(f"Abnormal pitch center: {pitch_center}")

        speed_center = chars.get("speed_center", 1.0)
        if speed_center < 0.5 or speed_center > 2.0:
            issues.append(f"Abnormal speed center: {speed_center}")

        stats = self._usage.get(profile_id)
        usage_info = {
            "total_generations": stats.total_generations if stats else 0,
            "total_duration_seconds": stats.total_duration_seconds if stats else 0,
        }

        return {
            "valid": len(issues) == 0,
            "profile_id": profile_id,
            "name": profile.name,
            "style": profile.style,
            "languages": profile.languages,
            "issues": issues,
            "usage": usage_info,
        }
