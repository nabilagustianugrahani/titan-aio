"""Lip Sync — MCP tools for voice-driven face animation."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class LipSyncInput(BaseModel):
    """Input for lip sync generation."""
    audio_path: str = Field(description="Path to audio file (wav/mp3)")
    face_image: Optional[str] = Field(default=None, description="Path to face image (for Wav2Lip/SadTalker)")
    face_video: Optional[str] = Field(default=None, description="Path to existing video (for re-sync)")
    engine: str = Field(default="auto", description="Engine: auto | wav2lip | sadtalker | wan_native")
    resolution: tuple[int, int] = Field(default=(512, 512), description="Output resolution")


class LipSyncOutput(BaseModel):
    """Output from lip sync generation."""
    video_path: str
    audio_path: str
    engine: str
    duration_sec: float
    resolution: tuple[int, int]
    success: bool
    error: Optional[str] = None


class InstallLipSyncInput(BaseModel):
    """Input for installing lip sync engine."""
    engine: str = Field(default="wav2lip", description="Engine to install: wav2lip | sadtalker")


class InstallLipSyncOutput(BaseModel):
    """Output from lip sync installation."""
    engine: str
    installed: bool
    path: str
    message: str


async def generate_lip_sync_video(input_data: LipSyncInput) -> LipSyncOutput:
    """Generate lip sync video from audio + face image/video.

    Engines:
    - wav2lip: High quality lip sync (requires face image + audio)
    - sadtalker: Lip sync + head movement (requires face image + audio)
    - wan_native: Text-to-video without lip sync (fallback)

    Auto-detects best available engine.
    """
    from Services.video.lip_sync import LipSyncEngine

    engine = LipSyncEngine()
    result = await engine.sync(
        audio_path=input_data.audio_path,
        face_image=input_data.face_image,
        face_video=input_data.face_video,
        engine=input_data.engine,
        resolution=input_data.resolution,
    )

    return LipSyncOutput(
        video_path=result.video_path,
        audio_path=result.audio_path,
        engine=result.engine,
        duration_sec=result.duration_sec,
        resolution=result.resolution,
        success=result.success,
        error=result.error,
    )


async def install_lip_sync_engine(input_data: InstallLipSyncInput) -> InstallLipSyncOutput:
    """Install a lip sync engine (Wav2Lip or SadTalker).

    Downloads models and sets up the environment.
    Requires: git, python3, pip
    """
    import subprocess
    from pathlib import Path

    models_dir = Path("/opt/lip-sync-models")
    models_dir.mkdir(parents=True, exist_ok=True)

    if input_data.engine == "wav2lip":
        target = models_dir / "Wav2Lip"
        if target.exists():
            return InstallLipSyncOutput(
                engine="wav2lip", installed=True,
                path=str(target), message="Already installed",
            )
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/Rudrabha/Wav2Lip", str(target)],
                capture_output=True, timeout=120,
            )
            subprocess.run(
                ["pip", "install", "-r", str(target / "requirements.txt")],
                capture_output=True, timeout=300,
            )
            return InstallLipSyncOutput(
                engine="wav2lip", installed=True,
                path=str(target), message="Installed successfully",
            )
        except Exception as e:
            return InstallLipSyncOutput(
                engine="wav2lip", installed=False,
                path=str(target), message=f"Installation failed: {e}",
            )

    elif input_data.engine == "sadtalker":
        target = models_dir / "SadTalker"
        if target.exists():
            return InstallLipSyncOutput(
                engine="sadtalker", installed=True,
                path=str(target), message="Already installed",
            )
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/OpenTalker/SadTalker", str(target)],
                capture_output=True, timeout=120,
            )
            subprocess.run(
                ["pip", "install", "-r", str(target / "requirements.txt")],
                capture_output=True, timeout=300,
            )
            return InstallLipSyncOutput(
                engine="sadtalker", installed=True,
                path=str(target), message="Installed successfully",
            )
        except Exception as e:
            return InstallLipSyncOutput(
                engine="sadtalker", installed=False,
                path=str(target), message=f"Installation failed: {e}",
            )

    return InstallLipSyncOutput(
        engine=input_data.engine, installed=False,
        path="", message=f"Unknown engine: {input_data.engine}",
    )
