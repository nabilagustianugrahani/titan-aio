"""Real TTS Generator — generates actual audio files using edge-tts (free Microsoft TTS)."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

# Voice mapping per language
VOICE_MAP = {
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"},
    "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
    "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
    "pt": {"male": "pt-BR-AntonioNeural", "female": "pt-BR-FranciscaNeural"},
    "th": {"male": "th-TH-PremwadeeNeural", "female": "th-TH-PremwadeeNeural"},
    "vi": {"male": "vi-VN-HoaiMyNeural", "female": "vi-VN-NamMinhNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
    "ar": {"male": "ar-SA-HamedNeural", "female": "ar-SA-ZariyahNeural"},
    "tr": {"male": "tr-TR-AhmetNeural", "female": "tr-TR-EmelNeural"},
}

EMOTION_RATE_MAP = {
    "excited": "+20%",
    "enthusiastic": "+15%",
    "neutral": "+0%",
    "calm": "-10%",
    "serious": "-5%",
    "funny": "+10%",
    "sad": "-15%",
}


class TTSResult(BaseModel):
    voice_id: str = ""
    audio_path: str = ""
    audio_url: str = ""
    duration_estimate: float = 0.0
    voice_used: str = ""
    language: str = ""
    text: str = ""
    emotion: str = "neutral"
    speed: float = 1.0
    status: str = "generated"


class TTSGenerator:
    """Generate real audio files using edge-tts (free Microsoft TTS)."""

    def __init__(self, output_dir: str = "/tmp/titan-voice"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated: list[TTSResult] = []

    async def generate(
        self,
        text: str,
        language: str = "id",
        gender: str = "female",
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> TTSResult:
        """Generate audio file from text using edge-tts."""
        voice_id = hashlib.md5(f"{text}:{language}:{gender}:{emotion}".encode()).hexdigest()[:10]
        output_path = self.output_dir / f"{voice_id}.mp3"

        # Get voice for language
        lang_voices = VOICE_MAP.get(language, VOICE_MAP["id"])
        voice = lang_voices.get(gender, lang_voices["female"])

        try:
            import edge_tts

            rate = EMOTION_RATE_MAP.get(emotion, "+0%")
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
            )
            await communicate.save(str(output_path))

            # Estimate duration (~150 words per minute)
            word_count = len(text.split())
            duration = word_count / 2.5  # ~2.5 words per second

            result = TTSResult(
                voice_id=voice_id,
                audio_path=str(output_path),
                audio_url=f"/voice/{voice_id}.mp3",
                duration_estimate=round(duration, 1),
                voice_used=voice,
                language=language,
                text=text,
                emotion=emotion,
                speed=speed,
                status="generated",
            )
            self.generated.append(result)
            return result

        except ImportError:
            return TTSResult(
                voice_id=voice_id,
                voice_used=voice,
                language=language,
                text=text,
                emotion=emotion,
                speed=speed,
                status="error: edge-tts not installed. Run: pip install edge-tts",
            )
        except Exception as e:
            return TTSResult(
                voice_id=voice_id,
                voice_used=voice,
                language=language,
                text=text,
                emotion=emotion,
                speed=speed,
                status=f"error: {str(e)}",
            )

    async def generate_batch(
        self,
        texts: list[str],
        language: str = "id",
        gender: str = "female",
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> list[TTSResult]:
        """Generate multiple audio files."""
        results = []
        for text in texts:
            result = await self.generate(text=text, language=language, gender=gender, emotion=emotion, speed=speed)
            results.append(result)
        return results

    def list_voices(self) -> dict[str, dict[str, str]]:
        """List all available voices."""
        return VOICE_MAP

    def list_generated(self) -> list[TTSResult]:
        """List all generated audio files."""
        return self.generated

    async def cleanup(self):
        """Remove generated audio files."""
        for f in self.output_dir.glob("*.mp3"):
            f.unlink()
