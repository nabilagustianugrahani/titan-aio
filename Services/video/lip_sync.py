"""
Lip Sync Engine — voice-driven face animation.

Supports:
- Wav2Lip (primary): high-quality lip sync from audio + face image
- SadTalker (fallback): head movement + lip sync from single image
- Wan 2.2 native (no face): pure text-to-video without lip sync

Usage:
    from Services.video.lip_sync import LipSyncEngine
    engine = LipSyncEngine()
    result = await engine.sync(audio_path="voice.wav", face_image="face.jpg")
"""

from __future__ import annotations

import asyncio
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LipSyncResult:
    video_path: str
    audio_path: str
    engine: str  # "wav2lip" | "sadtalker" | "wan_native"
    duration_sec: float
    resolution: tuple[int, int]
    success: bool
    error: Optional[str] = None


class LipSyncEngine:
    """Lip sync with automatic engine selection."""

    MODELS_DIR = Path("/opt/lip-sync-models")
    OUTPUT_DIR = Path("/tmp/titan-lipsync")
    TEMP_DIR = Path("/tmp/titan-lipsync/temp")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def sync(
        self,
        audio_path: str,
        face_image: Optional[str] = None,
        face_video: Optional[str] = None,
        engine: str = "auto",
        resolution: tuple[int, int] = (512, 512),
    ) -> LipSyncResult:
        """Sync lips to audio.

        Args:
            audio_path: Path to audio file (wav/mp3)
            face_image: Static face image for Wav2Lip/SadTalker
            face_video: Existing video to add lip sync to
            engine: "auto" | "wav2lip" | "sadtalker" | "wan_native"
            resolution: Output resolution (w, h)

        Returns:
            LipSyncResult with video path and metadata
        """
        if engine == "auto":
            engine = self._detect_engine()

        if engine == "wav2lip":
            return await self._wav2lip_sync(audio_path, face_image, resolution)
        elif engine == "sadtalker":
            return await self._sadtalker_sync(audio_path, face_image, resolution)
        else:
            return LipSyncResult(
                video_path="",
                audio_path=audio_path,
                engine="wan_native",
                duration_sec=0,
                resolution=resolution,
                success=False,
                error="No lip sync engine available. Use Wan 2.2 for text-to-video.",
            )

    def _detect_engine(self) -> str:
        """Auto-detect best available engine.

        Checks:
        1. Local model directory
        2. pip installed package
        """
        # Check local models
        wav2lip_path = self.MODELS_DIR / "Wav2Lip"
        if wav2lip_path.exists():
            return "wav2lip"

        sadtalker_path = self.MODELS_DIR / "SadTalker"
        if sadtalker_path.exists():
            return "sadtalker"

        # Check if installed via pip
        try:
            result = subprocess.run(
                ["pip", "show", "wav2lip"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return "wav2lip"
        except Exception:
            pass

        return "wan_native"

    async def _wav2lip_sync(
        self,
        audio_path: str,
        face_image: Optional[str],
        resolution: tuple[int, int],
    ) -> LipSyncResult:
        """Run Wav2Lip for high-quality lip sync."""
        output_name = f"wav2lip-{uuid.uuid4().hex[:8]}"
        output_path = self.OUTPUT_DIR / f"{output_name}.mp4"

        cmd = [
            "python", str(self.MODELS_DIR / "Wav2Lip" / "inference.py"),
            "--checkpoint_path", str(self.MODELS_DIR / "Wav2Lip" / "wav2lip_gan.pth"),
            "--face", face_image or "",
            "--audio", audio_path,
            "--outfile", str(output_path),
            "--nosmooth",
            "--resize_factor", "1",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode == 0 and output_path.exists():
                duration = await self._get_duration(str(output_path))
                return LipSyncResult(
                    video_path=str(output_path),
                    audio_path=audio_path,
                    engine="wav2lip",
                    duration_sec=duration,
                    resolution=resolution,
                    success=True,
                )
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="wav2lip", duration_sec=0,
                resolution=resolution, success=False,
                error=stderr.decode()[:500],
            )
        except asyncio.TimeoutError:
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="wav2lip", duration_sec=0,
                resolution=resolution, success=False,
                error="Wav2Lip timed out (120s limit)",
            )
        except FileNotFoundError:
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="wav2lip", duration_sec=0,
                resolution=resolution, success=False,
                error="Wav2Lip not installed",
            )

    async def _sadtalker_sync(
        self,
        audio_path: str,
        face_image: Optional[str],
        resolution: tuple[int, int],
    ) -> LipSyncResult:
        """Run SadTalker for lip sync + head movement."""
        output_name = f"sadtalker-{uuid.uuid4().hex[:8]}"
        output_dir = self.OUTPUT_DIR / output_name
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python", str(self.MODELS_DIR / "SadTalker" / "inference.py"),
            "--driven_audio", audio_path,
            "--source_image", face_image or "",
            "--result_dir", str(output_dir),
            "--size", str(resolution[0]),
            "--enhancer", "gfpgan",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)

            # Find output video
            videos = list(output_dir.glob("*.mp4"))
            if videos:
                duration = await self._get_duration(str(videos[0]))
                return LipSyncResult(
                    video_path=str(videos[0]),
                    audio_path=audio_path,
                    engine="sadtalker",
                    duration_sec=duration,
                    resolution=resolution,
                    success=True,
                )
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="sadtalker", duration_sec=0,
                resolution=resolution, success=False,
                error=stderr.decode()[:500],
            )
        except asyncio.TimeoutError:
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="sadtalker", duration_sec=0,
                resolution=resolution, success=False,
                error="SadTalker timed out (180s limit)",
            )
        except FileNotFoundError:
            return LipSyncResult(
                video_path="", audio_path=audio_path,
                engine="sadtalker", duration_sec=0,
                resolution=resolution, success=False,
                error="SadTalker not installed",
            )

    @staticmethod
    async def _get_duration(video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return float(stdout.decode().strip()) if stdout else 0
        except Exception:
            return 0

    def is_available(self) -> bool:
        """Check if any lip sync engine is available."""
        return self._detect_engine() != "wan_native"
