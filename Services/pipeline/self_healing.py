"""
Self-Healing Pipeline — wraps pipeline execution with failure detection and auto-recovery.

Features:
  - Monitor each pipeline step for failures
  - Classify failure types (timeout, rate_limit, model_error, quality_low, unknown)
  - Select recovery strategies (retry, fallback_model, skip, reduce_scope)
  - Execute recovery with backoff and validation
  - Learn failure patterns across runs

Usage:
    from Services.pipeline.self_healing import SelfHealingPipeline

    pipeline = SelfHealingPipeline()
    result = await pipeline.execute_step("generate_video", generate_fn, prompt="...")
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Awaitable, Optional

from pydantic import BaseModel, Field

from Services.agents.message_bus import get_bus

logger = logging.getLogger("titan.pipeline.self_healing")


# ── Enums ──────────────────────────────────────────────────────

class FailureType(str, Enum):
    """Classified failure categories."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    MODEL_ERROR = "model_error"
    QUALITY_LOW = "quality_low"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    """Available recovery actions."""
    RETRY = "retry"
    FALLBACK_MODEL = "fallback_model"
    SKIP = "skip"
    REDUCE_SCOPE = "reduce_scope"


class StepStatus(str, Enum):
    """Pipeline step lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERED = "recovered"
    SKIPPED = "skipped"


# ── Models ─────────────────────────────────────────────────────

class PipelineStep(BaseModel):
    """A single step in the pipeline with lifecycle tracking."""
    step_id: str = ""
    name: str = ""
    status: StepStatus = StepStatus.PENDING
    error: str = ""
    error_type: str = ""
    recovery_strategy: str = ""
    recovery_time: float = 0.0
    retries: int = 0
    started_at: str = ""
    completed_at: str = ""
    output: Any = None

    model_config = {"arbitrary_types_allowed": True}


class PipelineFailure(BaseModel):
    """Record of a failure event for learning."""
    step: str
    error: str
    error_type: str = FailureType.UNKNOWN
    timestamp: str = ""
    recovery_strategy: str = ""
    recovery_success: bool = False


class RecoveryStrategy(BaseModel):
    """Definition of a recovery strategy."""
    name: str
    description: str
    applicable_errors: list[str] = Field(default_factory=list)
    max_retries: int = 3
    backoff_seconds: float = 2.0
    backoff_multiplier: float = 2.0


class PipelineHealth(BaseModel):
    """Overall pipeline health snapshot."""
    pipeline_id: str = ""
    status: str = "running"
    steps: list[PipelineStep] = Field(default_factory=list)
    failures: list[PipelineFailure] = Field(default_factory=list)
    total_recovery_time: float = 0.0
    success_rate: float = 0.0
    learned_patterns: list[str] = Field(default_factory=list)
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    recovered_steps: int = 0


# ── Failure Classifier ─────────────────────────────────────────

_TIMEOUT_PATTERNS: list[str] = [
    "timeout", "timed out", "deadline exceeded", "asyncio.timeout",
    "read timed out", "connect timed out", "request timeout",
    "gateway timeout", "504",
]

_RATE_LIMIT_PATTERNS: list[str] = [
    "rate limit", "ratelimit", "429", "too many requests",
    "throttl", "quota exceeded", "limit exceeded", "retry-after",
]

_MODEL_ERROR_PATTERNS: list[str] = [
    "model error", "inference failed", "cuda", "oom", "out of memory",
    "model loading", "weights not found", "checkpoint", "gpu",
    "vram", "runtime error", "500", "502", "503", "model not found",
    "connection refused", "service unavailable",
]

_QUALITY_LOW_PATTERNS: list[str] = [
    "quality", "low quality", "blurry", "artifact", "distort",
    "unusable", "rejected", "validation failed", "score below",
    "below threshold", "nsfw", "safety filter", "content policy",
]


def classify_failure(error: str) -> str:
    """Classify an error message into a failure type.

    Pattern matching against known error signatures.
    Returns FailureType value (string).
    """
    lower = error.lower()

    for pat in _TIMEOUT_PATTERNS:
        if pat in lower:
            return FailureType.TIMEOUT

    for pat in _RATE_LIMIT_PATTERNS:
        if pat in lower:
            return FailureType.RATE_LIMIT

    for pat in _MODEL_ERROR_PATTERNS:
        if pat in lower:
            return FailureType.MODEL_ERROR

    for pat in _QUALITY_LOW_PATTERNS:
        if pat in lower:
            return FailureType.QUALITY_LOW

    return FailureType.UNKNOWN


# ── Default Strategies ─────────────────────────────────────────

DEFAULT_STRATEGIES: list[RecoveryStrategy] = [
    RecoveryStrategy(
        name="retry",
        description="Retry the same step with exponential backoff.",
        applicable_errors=["timeout", "rate_limit", "unknown"],
        max_retries=3,
        backoff_seconds=2.0,
        backoff_multiplier=2.0,
    ),
    RecoveryStrategy(
        name="fallback_model",
        description="Switch to a fallback model/provider.",
        applicable_errors=["model_error", "timeout"],
        max_retries=1,
        backoff_seconds=1.0,
    ),
    RecoveryStrategy(
        name="skip",
        description="Skip the step and continue pipeline.",
        applicable_errors=["quality_low", "model_error", "unknown"],
        max_retries=0,
    ),
    RecoveryStrategy(
        name="reduce_scope",
        description="Reduce input size/complexity and retry.",
        applicable_errors=["model_error", "timeout", "rate_limit"],
        max_retries=2,
        backoff_seconds=3.0,
    ),
]


# ── Pattern Learner ────────────────────────────────────────────

class FailurePatternLearner:
    """Learns failure patterns across pipeline runs.

    Stores patterns in-memory (singleton) and persists to MessageBus
    for cross-agent visibility.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, list[dict]] = {}  # step_name -> [{error_type, count, last_seen, best_strategy}]
        self._max_patterns: int = 500

    def record(self, failure: PipelineFailure, strategy_used: str, strategy_worked: bool) -> None:
        """Record a failure and its outcome for pattern learning."""
        key = f"{failure.step}:{failure.error_type}"
        if key not in self._patterns:
            self._patterns[key] = []

        entries = self._patterns[key]
        # Find existing entry for this strategy
        found = False
        for entry in entries:
            if entry.get("strategy") == strategy_used:
                entry["count"] = entry.get("count", 0) + 1
                entry["success_count"] = entry.get("success_count", 0) + (1 if strategy_worked else 0)
                entry["last_seen"] = datetime.now(timezone.utc).isoformat()
                found = True
                break

        if not found:
            entries.append({
                "strategy": strategy_used,
                "count": 1,
                "success_count": 1 if strategy_worked else 0,
                "last_seen": datetime.now(timezone.utc).isoformat(),
            })

        # Publish learning event
        bus = get_bus()
        bus.publish("pipeline.pattern_learned", {
            "step": failure.step,
            "error_type": failure.error_type,
            "strategy": strategy_used,
            "worked": strategy_worked,
        }, "SelfHealingPipeline")

    def suggest_strategy(self, step_name: str, error_type: str) -> str | None:
        """Suggest the best strategy based on historical data.

        Returns the strategy name with highest success rate, or None.
        """
        key = f"{step_name}:{error_type}"
        entries = self._patterns.get(key, [])
        if not entries:
            return None

        # Sort by success rate (desc), then by count (desc)
        best = max(entries, key=lambda e: (e.get("success_count", 0) / max(e.get("count", 1), 1), e.get("count", 0)))
        success_rate = best.get("success_count", 0) / max(best.get("count", 1), 1)

        # Only suggest if success rate > 30%
        if success_rate > 0.3:
            return best.get("strategy")
        return None

    def get_learned_patterns(self, limit: int = 20) -> list[str]:
        """Return human-readable learned patterns."""
        patterns: list[str] = []
        for key, entries in self._patterns.items():
            for entry in entries:
                rate = entry.get("success_count", 0) / max(entry.get("count", 1), 1)
                if rate > 0.3 and entry.get("count", 0) >= 2:
                    patterns.append(
                        f"{key}: strategy={entry['strategy']} "
                        f"(success={entry.get('success_count', 0)}/{entry.get('count', 0)}, "
                        f"rate={rate:.0%})"
                    )
        patterns.sort(key=lambda p: p, reverse=True)
        return patterns[:limit]

    def get_pattern_count(self) -> int:
        """Total number of learned pattern entries."""
        return sum(len(v) for v in self._patterns.values())


# ── Core Pipeline ──────────────────────────────────────────────

# Fallback models for media generation steps
FALLBACK_MODELS: dict[str, list[str]] = {
    "generate_video": ["wan-2-2-fallback", "wan-2-2-t2v"],
    "generate_image": ["sd-3.5-medium", "flux-schnell-fallback"],
    "generate_avatar": ["sd-3.5-medium", "wan-2-2"],
    "lip_sync": ["sadtalker", "wan_native"],
}

# Scope reduction map: step_name -> parameter to reduce
SCOPE_REDUCTION: dict[str, dict[str, Any]] = {
    "generate_video": {"max_duration": 15, "resolution": "480p"},
    "generate_image": {"max_images": 1, "resolution": "512"},
    "analyze_reviews": {"max_reviews": 25},
    "analyze_competitors": {"max_competitors": 5},
    "generate_batch_variants": {"num_variants": 1},
}


class SelfHealingPipeline:
    """Wraps pipeline execution with failure detection and auto-recovery.

    Monitors steps, classifies failures, selects and executes recovery
    strategies, validates results, and learns from failure patterns.
    """

    def __init__(
        self,
        pipeline_id: str = "",
        strategies: list[RecoveryStrategy] | None = None,
        max_global_retries: int = 5,
    ) -> None:
        self.pipeline_id = pipeline_id or f"sh-{uuid.uuid4().hex[:12]}"
        self.strategies = {s.name: s for s in (strategies or DEFAULT_STRATEGIES)}
        self.max_global_retries = max_global_retries
        self.steps: list[PipelineStep] = []
        self.failures: list[PipelineFailure] = []
        self.learned = FailurePatternLearner()
        self._total_recovery_time: float = 0.0
        self._bus = get_bus()

        logger.info("SelfHealingPipeline created: %s", self.pipeline_id)

    # ── Health ─────────────────────────────────────────────────

    def health(self) -> PipelineHealth:
        """Return current pipeline health snapshot."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.SUCCESS)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        recovered = sum(1 for s in self.steps if s.status == StepStatus.RECOVERED)
        success_rate = (completed + recovered) / total if total > 0 else 0.0

        overall = "completed"
        if any(s.status == StepStatus.RUNNING for s in self.steps):
            overall = "running"
        elif failed > 0 and recovered == 0:
            overall = "failed"
        elif failed > 0:
            overall = "recovered"

        return PipelineHealth(
            pipeline_id=self.pipeline_id,
            status=overall,
            steps=self.steps,
            failures=self.failures,
            total_recovery_time=round(self._total_recovery_time, 3),
            success_rate=round(success_rate, 3),
            learned_patterns=self.learned.get_learned_patterns(),
            total_steps=total,
            completed_steps=completed,
            failed_steps=failed,
            recovered_steps=recovered,
        )

    # ── Step execution with healing ────────────────────────────

    async def execute_step(
        self,
        name: str,
        fn: Callable[..., Awaitable[Any]],
        *,
        validator: Callable[[Any], bool] | None = None,
        fallback_fn: Callable[..., Awaitable[Any]] | None = None,
        scope_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PipelineStep:
        """Execute a pipeline step with self-healing.

        Args:
            name: Human-readable step name.
            fn: Async callable to execute.
            validator: Optional callable to validate output. Returns True if valid.
            fallback_fn: Optional fallback function (used by fallback_model strategy).
            scope_params: Parameters to override when using reduce_scope strategy.
            **kwargs: Forwarded to fn.

        Returns:
            PipelineStep with final status and output.
        """
        step_id = f"{name}-{uuid.uuid4().hex[:8]}"
        step = PipelineStep(step_id=step_id, name=name, status=StepStatus.RUNNING)
        step.started_at = datetime.now(timezone.utc).isoformat()
        self.steps.append(step)

        self._bus.publish("pipeline.step.started", {"step_id": step_id, "name": name}, "SelfHealingPipeline")

        last_error = ""
        last_error_type = FailureType.UNKNOWN

        try:
            result = await asyncio.wait_for(fn(**kwargs), timeout=120.0)
        except asyncio.TimeoutError as exc:
            last_error = f"Timeout after 120s: {exc}"
            last_error_type = FailureType.TIMEOUT
            result = None
        except Exception as exc:
            last_error = str(exc)
            last_error_type = classify_failure(last_error)
            result = None

        # Validate output if provided
        if result is not None and validator is not None:
            try:
                if not validator(result):
                    last_error = f"Validation failed: output did not pass validator"
                    last_error_type = FailureType.QUALITY_LOW
                    result = None
            except Exception as exc:
                last_error = f"Validator error: {exc}"
                last_error_type = FailureType.UNKNOWN
                result = None

        # Success path
        if result is not None and not last_error:
            step.status = StepStatus.SUCCESS
            step.output = result
            step.completed_at = datetime.now(timezone.utc).isoformat()
            self._bus.publish("pipeline.step.completed", {
                "step_id": step_id, "name": name, "status": "success",
            }, "SelfHealingPipeline")
            return step

        # ── Recovery phase ────────────────────────────────────
        failure = PipelineFailure(
            step=name,
            error=last_error,
            error_type=last_error_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.failures.append(failure)

        recovery_result = await self._attempt_recovery(
            step=step,
            failure=failure,
            fn=fn,
            validator=validator,
            fallback_fn=fallback_fn,
            scope_params=scope_params,
            **kwargs,
        )

        if recovery_result is not None:
            step.status = StepStatus.RECOVERED
            step.output = recovery_result
            step.completed_at = datetime.now(timezone.utc).isoformat()
            failure.recovery_success = True
            self._bus.publish("pipeline.step.recovered", {
                "step_id": step_id, "name": name, "strategy": step.recovery_strategy,
            }, "SelfHealingPipeline")
        else:
            step.status = StepStatus.FAILED
            step.error = last_error
            step.error_type = last_error_type
            step.completed_at = datetime.now(timezone.utc).isoformat()
            self._bus.publish("pipeline.step.failed", {
                "step_id": step_id, "name": name, "error": last_error, "error_type": last_error_type,
            }, "SelfHealingPipeline")

        return step

    # ── Recovery orchestration ─────────────────────────────────

    async def _attempt_recovery(
        self,
        step: PipelineStep,
        failure: PipelineFailure,
        fn: Callable[..., Awaitable[Any]],
        validator: Callable[[Any], bool] | None,
        fallback_fn: Callable[..., Awaitable[Any]] | None,
        scope_params: dict[str, Any] | None,
        **kwargs: Any,
    ) -> Any:
        """Try recovery strategies in priority order.

        Priority:
          1. Learner-suggested strategy (from past runs)
          2. Strategy matching the failure type
          3. Fallback chain: retry -> reduce_scope -> fallback_model -> skip
        """
        t0 = time.time()

        # Check learner for best strategy
        learned_strategy = self.learned.suggest_strategy(step.name, failure.error_type)

        # Build ordered strategy list
        strategy_order = self._select_strategies(failure.error_type, learned_strategy)

        for strategy_name in strategy_order:
            strategy = self.strategies.get(strategy_name)
            if strategy is None:
                continue

            step.recovery_strategy = strategy_name
            logger.info(
                "Recovery attempt: step=%s strategy=%s error_type=%s",
                step.name, strategy_name, failure.error_type,
            )

            if strategy_name == "retry":
                result = await self._recover_retry(step, fn, validator, strategy, **kwargs)
            elif strategy_name == "fallback_model":
                result = await self._recover_fallback_model(step, fn, validator, fallback_fn, **kwargs)
            elif strategy_name == "reduce_scope":
                result = await self._recover_reduce_scope(step, fn, validator, scope_params, **kwargs)
            elif strategy_name == "skip":
                result = self._recover_skip(step)
            else:
                continue

            recovery_time = time.time() - t0
            step.recovery_time = round(recovery_time, 3)
            self._total_recovery_time += recovery_time

            failure.recovery_strategy = strategy_name
            self.learned.record(failure, strategy_name, result is not None)

            if result is not None:
                return result

        return None

    def _select_strategies(self, error_type: str, learned: str | None) -> list[str]:
        """Build ordered recovery strategy list.

        Order: learned > error-type-specific > universal fallbacks.
        """
        order: list[str] = []

        # Learned strategy first
        if learned and learned in self.strategies:
            order.append(learned)

        # Strategies that cover this error type
        for name, strat in self.strategies.items():
            if name not in order and error_type in strat.applicable_errors:
                order.append(name)

        # Universal fallbacks
        for fallback in ["retry", "reduce_scope", "fallback_model", "skip"]:
            if fallback not in order:
                order.append(fallback)

        return order

    # ── Individual recovery strategies ─────────────────────────

    async def _recover_retry(
        self,
        step: PipelineStep,
        fn: Callable[..., Awaitable[Any]],
        validator: Callable[[Any], bool] | None,
        strategy: RecoveryStrategy,
        **kwargs: Any,
    ) -> Any:
        """Retry with exponential backoff."""
        for attempt in range(1, strategy.max_retries + 1):
            step.retries += 1
            backoff = strategy.backoff_seconds * (strategy.backoff_multiplier ** (attempt - 1))
            logger.info("Retry %d/%d for step '%s' after %.1fs", attempt, strategy.max_retries, step.name, backoff)
            await asyncio.sleep(backoff)

            try:
                result = await asyncio.wait_for(fn(**kwargs), timeout=120.0)
            except asyncio.TimeoutError:
                logger.warning("Retry %d timed out for step '%s'", attempt, step.name)
                continue
            except Exception as exc:
                logger.warning("Retry %d failed for step '%s': %s", attempt, step.name, exc)
                continue

            if validator is not None:
                try:
                    if not validator(result):
                        logger.warning("Retry %d validation failed for step '%s'", attempt, step.name)
                        continue
                except Exception:
                    continue

            return result

        return None

    async def _recover_fallback_model(
        self,
        step: PipelineStep,
        fn: Callable[..., Awaitable[Any]],
        validator: Callable[[Any], bool] | None,
        fallback_fn: Callable[..., Awaitable[Any]] | None,
        **kwargs: Any,
    ) -> Any:
        """Try a fallback model/provider."""
        if fallback_fn is not None:
            try:
                result = await asyncio.wait_for(fallback_fn(**kwargs), timeout=120.0)
                if validator is not None and not validator(result):
                    return None
                return result
            except Exception as exc:
                logger.warning("Fallback model failed for step '%s': %s", step.name, exc)
                return None

        # If no explicit fallback_fn, try injecting a model override
        fallback_models = FALLBACK_MODELS.get(step.name, [])
        for model_name in fallback_models:
            modified_kwargs = {**kwargs, "model": model_name}
            try:
                result = await asyncio.wait_for(fn(**modified_kwargs), timeout=120.0)
                if validator is not None and not validator(result):
                    continue
                return result
            except Exception as exc:
                logger.warning("Fallback model '%s' failed for step '%s': %s", model_name, step.name, exc)
                continue

        return None

    async def _recover_reduce_scope(
        self,
        step: PipelineStep,
        fn: Callable[..., Awaitable[Any]],
        validator: Callable[[Any], bool] | None,
        scope_params: dict[str, Any] | None,
        **kwargs: Any,
    ) -> Any:
        """Reduce scope (fewer items, lower resolution) and retry."""
        reduced = {**kwargs}

        # Apply explicit scope_params override
        if scope_params:
            reduced.update(scope_params)

        # Apply default scope reductions for known steps
        defaults = SCOPE_REDUCTION.get(step.name, {})
        for key, val in defaults.items():
            if key not in reduced:
                reduced[key] = val

        # If nothing to reduce, skip
        if reduced == kwargs:
            return None

        for attempt in range(2):
            step.retries += 1
            backoff = 3.0 * (2.0 ** attempt)
            await asyncio.sleep(backoff)

            try:
                result = await asyncio.wait_for(fn(**reduced), timeout=120.0)
            except Exception as exc:
                logger.warning("Reduced scope attempt %d failed for '%s': %s", attempt + 1, step.name, exc)
                continue

            if validator is not None:
                try:
                    if not validator(result):
                        continue
                except Exception:
                    continue

            return result

        return None

    def _recover_skip(self, step: PipelineStep) -> Any:
        """Mark step as skipped. Returns a skip sentinel."""
        step.status = StepStatus.SKIPPED
        step.output = {"_skipped": True, "reason": "Skip recovery for step"}
        logger.info("Skipped step '%s' (skip recovery)", step.name)
        return step.output


# ── Pipeline Runner ────────────────────────────────────────────

class PipelineRunner:
    """High-level runner that executes a list of step definitions with self-healing.

    Usage:
        runner = PipelineRunner()
        runner.add_step("analyze", analyze_fn, url="...")
        runner.add_step("generate", generate_fn, prompt="...")
        result = await runner.run()
    """

    def __init__(self, pipeline_id: str = "") -> None:
        self.pipeline = SelfHealingPipeline(pipeline_id=pipeline_id)
        self._step_defs: list[dict[str, Any]] = []

    def add_step(
        self,
        name: str,
        fn: Callable[..., Awaitable[Any]],
        *,
        validator: Callable[[Any], bool] | None = None,
        fallback_fn: Callable[..., Awaitable[Any]] | None = None,
        scope_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "PipelineRunner":
        """Add a step to the pipeline. Chainable."""
        self._step_defs.append({
            "name": name,
            "fn": fn,
            "validator": validator,
            "fallback_fn": fallback_fn,
            "scope_params": scope_params,
            "kwargs": kwargs,
        })
        return self

    async def run(self) -> PipelineHealth:
        """Execute all steps sequentially with self-healing.

        Returns final PipelineHealth.
        """
        self.pipeline._bus.publish("pipeline.started", {
            "pipeline_id": self.pipeline.pipeline_id,
            "total_steps": len(self._step_defs),
        }, "SelfHealingPipeline")

        for i, step_def in enumerate(self._step_defs):
            logger.info("Running step %d/%d: %s", i + 1, len(self._step_defs), step_def["name"])
            await self.pipeline.execute_step(
                name=step_def["name"],
                fn=step_def["fn"],
                validator=step_def.get("validator"),
                fallback_fn=step_def.get("fallback_fn"),
                scope_params=step_def.get("scope_params"),
                **step_def.get("kwargs", {}),
            )

        health = self.pipeline.health()

        self.pipeline._bus.publish("pipeline.completed", {
            "pipeline_id": self.pipeline.pipeline_id,
            "status": health.status,
            "success_rate": health.success_rate,
            "total_recovery_time": health.total_recovery_time,
        }, "SelfHealingPipeline")

        return health


# ── Module-level pipeline registry ─────────────────────────────

_active_pipelines: dict[str, SelfHealingPipeline] = {}


def get_pipeline(pipeline_id: str) -> SelfHealingPipeline | None:
    """Retrieve an active pipeline by ID."""
    return _active_pipelines.get(pipeline_id)


def register_pipeline(pipeline: SelfHealingPipeline) -> None:
    """Register a pipeline for health monitoring."""
    _active_pipelines[pipeline.pipeline_id] = pipeline


def list_pipelines() -> list[PipelineHealth]:
    """List health of all active pipelines."""
    return [p.health() for p in _active_pipelines.values()]


def get_all_learned_patterns() -> list[str]:
    """Aggregate learned patterns from all active pipelines."""
    seen: set[str] = set()
    patterns: list[str] = []
    for pipeline in _active_pipelines.values():
        for p in pipeline.learned.get_learned_patterns():
            if p not in seen:
                seen.add(p)
                patterns.append(p)
    return patterns
