"""UGC Engine — MCP tools for AI-powered content generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UGCGenerateInput(BaseModel):
    """Input for UGC generation."""
    product_title: str = Field(description="Product name")
    product_description: str = Field(default="", description="What the product does")
    category: str = Field(default="umum", description="Product category")
    price: float = Field(default=0, description="Product price in IDR")
    platform: str = Field(default="tiktok", description="Target platform")
    num_hooks: int = Field(default=10, ge=1, le=20, description="Number of hooks")
    num_scripts: int = Field(default=5, ge=1, le=10, description="Number of scripts")


class UGCHookOutput(BaseModel):
    """Single hook output."""
    text: str
    style: str
    platform: str
    predicted_ctr: str


class UGCScriptOutput(BaseModel):
    """Single script output."""
    hook: str
    problem: str
    solution: str
    demo: str
    social_proof: str
    cta: str
    full_script: str
    duration_seconds: int
    style: str


class UGCCaptionOutput(BaseModel):
    """Single caption output."""
    text: str
    hashtags: list[str]
    emoji: str
    platform: str
    character_count: int


class UGCGenerateOutput(BaseModel):
    """Output from UGC generation."""
    product_title: str
    category: str
    hooks: list[UGCHookOutput]
    scripts: list[UGCScriptOutput]
    captions: list[UGCCaptionOutput]
    video_prompts: list[str]
    total_items: int


async def generate_ugc_content(input_data: UGCGenerateInput) -> UGCGenerateOutput:
    """Generate complete UGC package using AI (Gemini 2.5 Flash).

    Returns hooks, scripts, captions, and video prompts.
    All content is AI-generated, sounds like real people.
    """
    from Services.ugc.engine import UGCEngine

    engine = UGCEngine()
    result = await engine.generate(
        product_title=input_data.product_title,
        product_description=input_data.product_description,
        category=input_data.category,
        price=input_data.price,
        platform=input_data.platform,
        num_hooks=input_data.num_hooks,
        num_scripts=input_data.num_scripts,
    )

    return UGCGenerateOutput(
        product_title=result.product_title,
        category=result.category,
        hooks=[
            UGCHookOutput(
                text=h.text, style=h.style,
                platform=h.platform, predicted_ctr=h.predicted_ctr,
            )
            for h in result.hooks
        ],
        scripts=[
            UGCScriptOutput(
                hook=s.hook, problem=s.problem, solution=s.solution,
                demo=s.demo, social_proof=s.social_proof, cta=s.cta,
                full_script=s.full_script, duration_seconds=s.duration_seconds,
                style=s.style,
            )
            for s in result.scripts
        ],
        captions=[
            UGCCaptionOutput(
                text=c.text, hashtags=c.hashtags, emoji=c.emoji,
                platform=c.platform, character_count=c.character_count,
            )
            for c in result.captions
        ],
        video_prompts=result.video_prompts,
        total_items=len(result.hooks) + len(result.scripts) + len(result.captions),
    )
