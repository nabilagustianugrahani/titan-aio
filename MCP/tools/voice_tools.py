"""MCP tools for Voice Cloning — create profiles, generate TTS parameters."""
from __future__ import annotations

from pydantic import BaseModel, Field

from Services.voice.cloner import (
    VALID_EMOTIONS,
    VALID_OUTPUT_FORMATS,
    VALID_STYLES,
    VoiceCloner,
)

# Singleton cloner instance
_cloner: VoiceCloner | None = None


def _get_cloner() -> VoiceCloner:
    """Get or create the singleton VoiceCloner."""
    global _cloner
    if _cloner is None:
        _cloner = VoiceCloner()
    return _cloner


class CreateProfileInput(BaseModel):
    """Input for creating a voice profile."""

    name: str = Field(description="Display name for the voice")
    style: str = Field(default="enthusiastic", description="Voice style preset")
    languages: str = Field(default="id,en", description="Comma-separated language codes")
    avatar_id: str | None = Field(default=None, description="Optional avatar association")


class GenerateVoiceInput(BaseModel):
    """Input for generating voice narration."""

    text: str = Field(description="Text to convert to speech")
    profile_id: str = Field(description="Voice profile ID to use")
    emotion: str = Field(default="neutral", description="Emotion modulation")
    speed: float = Field(default=1.0, description="Speed multiplier (0.5-2.0)")
    output_format: str = Field(default="mp3", description="Output format")
    avatar_id: str | None = Field(default=None, description="Avatar using this voice")


class UpdateProfileInput(BaseModel):
    """Input for updating a voice profile."""

    profile_id: str = Field(description="Profile ID to update")
    name: str | None = Field(default=None, description="New display name")
    style: str | None = Field(default=None, description="New voice style")
    languages: str | None = Field(default=None, description="New comma-separated languages")


class BatchVoiceInput(BaseModel):
    """Input for batch voice generation."""

    texts: list[str] = Field(description="List of texts to generate")
    profile_id: str = Field(description="Voice profile ID")
    emotion: str = Field(default="neutral", description="Emotion for all texts")
    speed: float = Field(default=1.0, description="Speed multiplier")
    output_format: str = Field(default="mp3", description="Output format")


class VoiceVariationInput(BaseModel):
    """Input for A/B voice variations."""

    text: str = Field(description="Text to generate variations for")
    profile_id: str = Field(description="Voice profile ID")
    emotions: str = Field(default="neutral,excited,serious", description="Comma-separated emotions")
    speeds: str = Field(default="1.0,1.1", description="Comma-separated speeds")
    output_format: str = Field(default="mp3", description="Output format")


# ── MCP Tool Functions ────────────────────────────────────────────


async def create_voice_profile(
    name: str,
    style: str = "enthusiastic",
    languages: str = "id,en",
    avatar_id: str = "",
) -> dict:
    """Create a voice profile for consistent AI narration.

    Profiles store voice characteristics (pitch, tone, speed, emotion range)
    and generate TTS parameters for downstream engines.

    Styles: enthusiastic, calm, professional, funny.
    Languages: comma-separated codes (id=Indonesian, en=English).
    """
    cloner = _get_cloner()
    lang_list = [l.strip() for l in languages.split(",") if l.strip()]

    if style not in VALID_STYLES:
        return {
            "error": f"Invalid style '{style}'. Valid: {VALID_STYLES}",
            "valid_styles": VALID_STYLES,
        }

    profile = await cloner.create_profile(
        name=name,
        style=style,
        languages=lang_list,
        avatar_id=avatar_id or None,
    )

    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "style": profile.style,
        "languages": profile.languages,
        "characteristics": profile.characteristics,
        "avatar_id": profile.avatar_id,
        "created_at": profile.created_at,
        "status": "created",
    }


async def generate_voice(
    text: str,
    profile_id: str,
    emotion: str = "neutral",
    speed: float = 1.0,
    output_format: str = "mp3",
    avatar_id: str = "",
) -> dict:
    """Generate voice narration using a cloned voice profile.

    Returns TTS parameters (pitch, speed, energy, prosody, emphasis)
    that a downstream engine (DashScope, ElevenLabs, etc.) consumes.

    Emotions: neutral, excited, serious, funny, sad.
    Speed: 0.5 (slow) to 2.0 (fast).
    """
    cloner = _get_cloner()

    if emotion not in VALID_EMOTIONS:
        return {
            "error": f"Invalid emotion '{emotion}'. Valid: {VALID_EMOTIONS}",
            "valid_emotions": VALID_EMOTIONS,
        }

    if not (0.5 <= speed <= 2.0):
        return {
            "error": f"Speed {speed} out of range. Must be 0.5-2.0.",
        }

    try:
        voice = await cloner.generate(
            text=text,
            profile_id=profile_id,
            emotion=emotion,
            speed=speed,
            output_format=output_format,
            avatar_id=avatar_id or None,
        )

        return {
            "voice_id": voice.voice_id,
            "text": voice.text,
            "duration_estimate": voice.duration_estimate,
            "parameters": voice.parameters,
            "profile_used": voice.profile_used,
            "emotion": voice.emotion,
            "output_format": voice.output_format,
            "output_url": voice.output_url,
            "status": voice.status,
            "created_at": voice.created_at,
        }
    except ValueError as e:
        return {"error": str(e), "status": "failed"}


async def list_voice_profiles(avatar_id: str = "") -> dict:
    """List all voice profiles, optionally filtered by avatar."""
    cloner = _get_cloner()
    profiles = await cloner.list_profiles(avatar_id=avatar_id or None)
    return {
        "profiles": [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "style": p.style,
                "languages": p.languages,
                "avatar_id": p.avatar_id,
                "created_at": p.created_at,
            }
            for p in profiles
        ],
        "count": len(profiles),
    }


async def get_voice_profile(profile_id: str) -> dict:
    """Get a voice profile and its usage statistics."""
    cloner = _get_cloner()
    profile = await cloner.get_profile(profile_id)
    if not profile:
        return {"error": f"Profile '{profile_id}' not found"}

    stats = await cloner.get_usage_stats(profile_id)
    validation = await cloner.validate_profile(profile_id)

    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "style": profile.style,
        "languages": profile.languages,
        "characteristics": profile.characteristics,
        "avatar_id": profile.avatar_id,
        "created_at": profile.created_at,
        "usage": stats.model_dump() if stats else None,
        "validation": validation,
    }


async def update_voice_profile(
    profile_id: str,
    name: str = "",
    style: str = "",
    languages: str = "",
) -> dict:
    """Update an existing voice profile."""
    cloner = _get_cloner()

    lang_list = None
    if languages:
        lang_list = [l.strip() for l in languages.split(",") if l.strip()]

    profile = await cloner.update_profile(
        profile_id=profile_id,
        name=name or None,
        style=style or None,
        languages=lang_list,
    )

    if not profile:
        return {"error": f"Profile '{profile_id}' not found"}

    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "style": profile.style,
        "languages": profile.languages,
        "characteristics": profile.characteristics,
        "status": "updated",
    }


async def delete_voice_profile(profile_id: str) -> dict:
    """Delete a voice profile."""
    cloner = _get_cloner()
    deleted = await cloner.delete_profile(profile_id)
    return {
        "profile_id": profile_id,
        "deleted": deleted,
        "status": "deleted" if deleted else "not_found",
    }


async def generate_batch_voices(
    texts: list[str],
    profile_id: str,
    emotion: str = "neutral",
    speed: float = 1.0,
    output_format: str = "mp3",
) -> dict:
    """Generate voice narration for multiple texts at once.

    Useful for batch video production or multi-script campaigns.
    """
    cloner = _get_cloner()
    voices = await cloner.generate_batch(
        texts=texts,
        profile_id=profile_id,
        emotion=emotion,
        speed=speed,
        output_format=output_format,
    )

    return {
        "voices": [
            {
                "voice_id": v.voice_id,
                "text": v.text[:80] + ("..." if len(v.text) > 80 else ""),
                "duration_estimate": v.duration_estimate,
                "parameters": v.parameters,
                "emotion": v.emotion,
            }
            for v in voices
        ],
        "total": len(voices),
        "total_duration_estimate": round(sum(v.duration_estimate for v in voices), 2),
        "profile_used": profile_id,
    }


async def generate_voice_variations(
    text: str,
    profile_id: str,
    emotions: str = "neutral,excited,serious",
    speeds: str = "1.0,1.1",
    output_format: str = "mp3",
) -> dict:
    """Generate multiple voice variations for A/B testing.

    Returns all combinations of emotions x speeds.
    Use for testing which voice resonates best with audience.
    """
    cloner = _get_cloner()
    emotion_list = [e.strip() for e in emotions.split(",") if e.strip()]
    speed_list = [float(s.strip()) for s in speeds.split(",") if s.strip()]

    for e in emotion_list:
        if e not in VALID_EMOTIONS:
            return {
                "error": f"Invalid emotion '{e}'. Valid: {VALID_EMOTIONS}",
            }

    voices = await cloner.generate_with_variations(
        text=text,
        profile_id=profile_id,
        emotions=emotion_list,
        speeds=speed_list,
        output_format=output_format,
    )

    return {
        "variations": [
            {
                "voice_id": v.voice_id,
                "emotion": v.emotion,
                "speed": v.parameters.get("speed", 1.0),
                "pitch": v.parameters.get("pitch", 1.0),
                "energy": v.parameters.get("energy", 0.5),
                "prosody": v.parameters.get("prosody_contour", "default"),
                "duration_estimate": v.duration_estimate,
            }
            for v in voices
        ],
        "total": len(voices),
        "emotions_tested": emotion_list,
        "speeds_tested": speed_list,
    }


async def get_voice_history(limit: int = 50) -> dict:
    """Get recent voice generation history."""
    cloner = _get_cloner()
    history = await cloner.get_history(limit=limit)
    return {
        "history": [
            {
                "voice_id": v.voice_id,
                "text_preview": v.text[:60] + ("..." if len(v.text) > 60 else ""),
                "emotion": v.emotion,
                "profile_used": v.profile_used,
                "duration_estimate": v.duration_estimate,
                "status": v.status,
                "created_at": v.created_at,
            }
            for v in history
        ],
        "count": len(history),
    }


async def get_voice_style_presets() -> dict:
    """Get available voice style presets and their characteristics."""
    cloner = _get_cloner()
    presets = await cloner.get_style_presets()
    return {
        "presets": presets,
        "valid_emotions": VALID_EMOTIONS,
        "valid_formats": VALID_OUTPUT_FORMATS,
    }


async def validate_voice_profile(profile_id: str) -> dict:
    """Validate a voice profile and check for issues."""
    cloner = _get_cloner()
    return await cloner.validate_profile(profile_id)
