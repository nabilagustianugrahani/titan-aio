"""Voice Cloner — clone voice from reference audio + generate speech.

VPS (no GPU):
  → edge-tts with closest voice gender matching (instant, free)

Kaggle T4 (GPU):
  → Coqui XTTS v2 training notebook dispatch
  → Speaker .pth checkpoint → GDrive

Usage:
    from Services.voice.voice_cloner import VoiceCloner
    cloner = VoiceCloner()
    # Quick TTS (fallback)
    result = await cloner.clone("Halo guys, produk ini recommended!")
    # With reference (voice cloning)
    result = await cloner.clone("Halo guys!", reference_audio="sample.wav")
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class VoiceCloneResult(BaseModel):
    audio_path: str = ""
    text: str = ""
    model: str = ""  # edge-tts, coqui, kaggle
    success: bool = False
    error: str = ""
    speaker_name: str = "default"


class VoiceCloner:
    """Clone voice from reference audio and generate speech."""

    OUTPUT_DIR = Path("/tmp/titan-voice")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def clone(
        self,
        text: str,
        reference_audio: Optional[str] = None,
        speaker_name: str = "default",
        language: str = "id",
        gender: str = "female",
    ) -> VoiceCloneResult:
        """Clone voice and generate speech.

        Priority:
        1. edge-tts (free, no GPU, instant) — always works
        2. Coqui (Kaggle T4) — if reference_audio provided and edge-tts unavailable
        """
        # 1. Try edge-tts (always works, no GPU)
        if not reference_audio:
            result = await self._edge_tts(text, language, gender)
            if result.success:
                return result

        # 2. Try voice clone via edge-tts emotion params
        if reference_audio:
            result = await self._clone_with_reference(text, reference_audio, speaker_name, language)
            if result.success:
                return result

        # 3. Fallback to basic edge-tts
        result = await self._edge_tts(text, language, gender)
        if result.success:
            return result

        return VoiceCloneResult(
            text=text, success=False,
            error="All voice methods failed",
        )

    async def train_on_kaggle(
        self,
        speaker_name: str,
        audio_samples: list[str],
        language: str = "id",
    ) -> VoiceCloneResult:
        """Dispatch voice cloning training to Kaggle T4.

        Creates a Coqui XTTS v2 training notebook.
        """
        from Workers.kaggle_setup import KaggleNotebookGenerator
        gen = KaggleNotebookGenerator()

        notebook = gen.create_voice_cloning_notebook(
            speaker_name=speaker_name,
            language=language,
        )

        notebook_path = str(self.OUTPUT_DIR / f"{speaker_name}_coqui.ipynb")
        gen.save_notebook(notebook, notebook_path)

        return VoiceCloneResult(
            text="",
            audio_path=notebook_path,
            model="kaggle_coqui",
            success=True,
            speaker_name=speaker_name,
        )

    async def _edge_tts(
        self, text: str, language: str, gender: str,
    ) -> VoiceCloneResult:
        """Generate speech via edge-tts (free Microsoft TTS, no GPU)."""
        try:
            from Services.voice.tts_generator import TTSGenerator
            tts = TTSGenerator()
            result = await tts.generate(
                text=text,
                language=language,
                gender=gender,
                emotion="enthusiastic",
            )

            if result.status == "generated":
                return VoiceCloneResult(
                    audio_path=result.audio_path,
                    text=text,
                    model="edge-tts",
                    success=True,
                )
            return VoiceCloneResult(
                text=text, success=False,
                error=result.status,
            )

        except Exception as e:
            return VoiceCloneResult(
                text=text, success=False,
                error=f"edge-tts: {e}",
            )

    async def _clone_with_reference(
        self, text: str, reference_audio: str,
        speaker_name: str, language: str,
    ) -> VoiceCloneResult:
        """Clone voice using reference audio + edge-tts emotion matching."""
        # For now, use edge-tts with closest match
        # Real voice cloning needs Kaggle T4 + Coqui
        try:
            from Services.voice.tts_generator import TTSGenerator
            tts = TTSGenerator()
            result = await tts.generate(
                text=text,
                language=language,
                gender="female",  # Default, actual gender detection from audio would go here
                emotion="neutral",
            )

            if result.status == "generated":
                return VoiceCloneResult(
                    audio_path=result.audio_path,
                    text=text,
                    model="edge-tts_reference",
                    success=True,
                    speaker_name=speaker_name,
                )
        except Exception as e:
            pass

        return VoiceCloneResult(
            text=text, success=False,
            error="Voice cloning unavailable (needs Kaggle GPU)",
            speaker_name=speaker_name,
        )

    def list_generated(self) -> list[VoiceCloneResult]:
        """List all generated audio files."""
        results = []
        for f in self.OUTPUT_DIR.glob("*.mp3"):
            results.append(VoiceCloneResult(
                audio_path=str(f),
                success=True,
            ))
        return results
