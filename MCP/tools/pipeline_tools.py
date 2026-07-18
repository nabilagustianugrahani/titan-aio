"""MCP tools for the self-healing pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field

from Services.pipeline.self_healing import (
    DEFAULT_STRATEGIES,
    FALLBACK_MODELS,
    SCOPE_REDUCTION,
    SelfHealingPipeline,
    classify_failure,
    get_all_learned_patterns,
    get_pipeline,
    list_pipelines,
    register_pipeline,
)

# ── Input models ───────────────────────────────────────────────

class GetPipelineHealthInput(BaseModel):
    """Input for checking pipeline health."""

    pipeline_id: str = Field(default="", description="Pipeline ID. Empty = all active pipelines.")


class CreatePipelineInput(BaseModel):
    """Input for creating a new self-healing pipeline."""

    pipeline_id: str = Field(default="", description="Custom pipeline ID (auto-generated if empty).")
    max_global_retries: int = Field(default=5, ge=1, le=20, description="Max recovery attempts per step.")


class ClassifyFailureInput(BaseModel):
    """Input for classifying an error message."""

    error: str = Field(description="Error message to classify.")


class GetRecoveryStrategiesInput(BaseModel):
    """Input for listing available recovery strategies."""

    error_type: str = Field(default="", description="Filter by error type. Empty = all.")


class GetLearnedPatternsInput(BaseModel):
    """Input for querying learned patterns."""

    limit: int = Field(default=20, ge=1, le=100, description="Max patterns to return.")


# ── Tool functions ─────────────────────────────────────────────

async def get_pipeline_health(input_data: GetPipelineHealthInput) -> dict:
    """Check self-healing pipeline status, failures, and recoveries.

    Returns health snapshot for a specific pipeline or all active pipelines.
    """
    if input_data.pipeline_id:
        pipeline = get_pipeline(input_data.pipeline_id)
        if pipeline is None:
            return {
                "error": f"Pipeline '{input_data.pipeline_id}' not found",
                "active_pipelines": [p.pipeline_id for p in list_pipelines()],
            }
        health = pipeline.health()
        return health.model_dump()

    # All pipelines
    all_health = list_pipelines()
    if not all_health:
        return {
            "status": "no_active_pipelines",
            "pipelines": [],
            "learned_patterns": get_all_learned_patterns(),
        }

    return {
        "status": "ok",
        "pipelines": [h.model_dump() for h in all_health],
        "total_pipelines": len(all_health),
        "total_steps": sum(h.total_steps for h in all_health),
        "total_success_rate": round(
            sum(h.success_rate for h in all_health) / len(all_health) if all_health else 0, 3,
        ),
        "total_recovery_time": round(sum(h.total_recovery_time for h in all_health), 3),
        "learned_patterns": get_all_learned_patterns(),
    }


async def create_pipeline(input_data: CreatePipelineInput) -> dict:
    """Create a new self-healing pipeline instance.

    Returns pipeline ID and available strategies.
    """
    pipeline = SelfHealingPipeline(
        pipeline_id=input_data.pipeline_id,
        max_global_retries=input_data.max_global_retries,
    )
    register_pipeline(pipeline)

    return {
        "pipeline_id": pipeline.pipeline_id,
        "status": "created",
        "max_global_retries": pipeline.max_global_retries,
        "strategies": [
            {
                "name": s.name,
                "description": s.description,
                "applicable_errors": s.applicable_errors,
                "max_retries": s.max_retries,
                "backoff_seconds": s.backoff_seconds,
            }
            for s in DEFAULT_STRATEGIES
        ],
    }


async def classify_pipeline_failure(input_data: ClassifyFailureInput) -> dict:
    """Classify an error message into a failure type.

    Returns failure type and recommended recovery strategies.
    """
    error_type = classify_failure(input_data.error)

    # Find matching strategies
    matching = [
        s for s in DEFAULT_STRATEGIES
        if error_type in s.applicable_errors
    ]

    return {
        "error": input_data.error,
        "error_type": error_type,
        "recommended_strategies": [
            {
                "name": s.name,
                "description": s.description,
                "max_retries": s.max_retries,
            }
            for s in matching
        ],
        "fallback_models": {
            step: models
            for step, models in FALLBACK_MODELS.items()
            if error_type in ("model_error", "timeout")
        } or {},
    }


async def get_recovery_strategies(input_data: GetRecoveryStrategiesInput) -> dict:
    """List available recovery strategies.

    Optionally filter by error type.
    """
    strategies = DEFAULT_STRATEGIES

    if input_data.error_type:
        strategies = [s for s in strategies if input_data.error_type in s.applicable_errors]

    return {
        "strategies": [
            {
                "name": s.name,
                "description": s.description,
                "applicable_errors": s.applicable_errors,
                "max_retries": s.max_retries,
                "backoff_seconds": s.backoff_seconds,
                "backoff_multiplier": s.backoff_multiplier,
            }
            for s in strategies
        ],
        "scope_reductions": {
            step: params
            for step, params in SCOPE_REDUCTION.items()
        },
        "fallback_models": dict(FALLBACK_MODELS),
    }


async def get_learned_patterns(input_data: GetLearnedPatternsInput) -> dict:
    """Query learned failure patterns across all pipelines.

    Patterns inform which recovery strategies work best for each step+error combination.
    """
    patterns = get_all_learned_patterns()

    # Also gather per-pipeline patterns
    pipeline_patterns: dict[str, list[str]] = {}
    for p in list_pipelines():
        pp = p.learned.get_learned_patterns(limit=input_data.limit)
        if pp:
            pipeline_patterns[p.pipeline_id] = pp

    return {
        "total_patterns": len(patterns),
        "patterns": patterns[:input_data.limit],
        "by_pipeline": pipeline_patterns,
    }
