"""MCP tools for real Voice Generation."""

from __future__ import annotations

from MCP.server import mcp

_generator = None

def _get_generator():
    global _generator
    if _generator is None:
        from Services.voice.tts_generator import TTSGenerator
        _generator = TTSGenerator()
    return _generator


@mcp.tool()
async def generate_voice_audio(text: str, language: str = "id", gender: str = "female", emotion: str = "neutral", speed: float = 1.0) -> dict:
    """Generate real audio file from text using Microsoft TTS (free, no API key).

    Supports 11 languages: id, en, ja, ko, es, pt, th, vi, hi, ar, tr.
    Emotions: excited, enthusiastic, neutral, calm, serious, funny, sad.
    """
    gen = _get_generator()
    result = await gen.generate(text=text, language=language, gender=gender, emotion=emotion, speed=speed)
    return result.model_dump()


@mcp.tool()
async def generate_voice_batch(texts: str, language: str = "id", gender: str = "female", emotion: str = "neutral") -> list[dict]:
    """Generate audio for multiple texts at once. Texts should be comma-separated."""
    gen = _get_generator()
    text_list = [t.strip() for t in texts.split("|||") if t.strip()]
    results = await gen.generate_batch(texts=text_list, language=language, gender=gender, emotion=emotion)
    return [r.model_dump() for r in results]


@mcp.tool()
async def list_tts_voices() -> dict:
    """List all available TTS voices by language and gender."""
    gen = _get_generator()
    return gen.list_voices()


@mcp.tool()
async def list_generated_voices() -> list[dict]:
    """List all generated audio files."""
    gen = _get_generator()
    return [r.model_dump() for r in gen.list_generated()]
