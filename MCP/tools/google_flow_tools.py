"""Google Flow (VideoFX) — MCP tools for AI video generation."""

from __future__ import annotations


from pydantic import BaseModel, Field


class FlowGenerateInput(BaseModel):
    """Input for Google Flow video generation."""

    prompt: str = Field(description="Text prompt for video generation")
    style: str = Field(default="cinematic", description="Video style: cinematic | animated | realistic")
    duration: str = Field(default="5s", description="Duration: 5s | 10s | 15s")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 16:9 | 9:16 | 1:1")


class FlowGenerateOutput(BaseModel):
    """Output from Google Flow generation."""

    status: str
    video_path: str = ""
    url: str = ""
    prompt: str = ""
    credits_used: int = 0
    error: str | None = None


class FlowLoginOutput(BaseModel):
    """Output from Google Flow login."""

    status: str
    session_file: str = ""
    error: str | None = None


async def generate_flow_video(input_data: FlowGenerateInput) -> FlowGenerateOutput:
    """Generate a video using Google Flow (VideoFX).

    High-quality AI video generation via labs.google/flow.
    Free tier: 50 credits/day.
    """
    from Services.video.google_flow import GoogleFlowGenerator

    gen = GoogleFlowGenerator()
    result = await gen.generate(
        prompt=input_data.prompt,
        style=input_data.style,
        duration=input_data.duration,
        aspect_ratio=input_data.aspect_ratio,
    )

    return FlowGenerateOutput(
        status=result.get("status", "failed"),
        video_path=result.get("video_path", ""),
        url=result.get("url", ""),
        prompt=result.get("prompt", input_data.prompt),
        credits_used=result.get("credits_used", 0),
        error=result.get("error"),
    )


async def login_google_flow() -> FlowLoginOutput:
    """Login to Google Flow (interactive, handles 2FA).

    Run this once to save session cookies.
    Subsequent generate calls will reuse the session.
    """
    from Services.video.google_flow import GoogleFlowGenerator

    gen = GoogleFlowGenerator()
    result = await gen.login()

    return FlowLoginOutput(
        status=result.get("status", "failed"),
        session_file=result.get("session_file", ""),
        error=result.get("error"),
    )
