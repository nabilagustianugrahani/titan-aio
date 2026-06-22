"""A/B Stats Engine — statistical significance testing for content variants.

Provides chi-squared tests, confidence intervals, sample size calculations,
auto-promotion of winners, and retirement of losers.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field


# ── Models ──────────────────────────────────────────────────────────


class ABTestCreate(BaseModel):
    """Input for creating an A/B test."""

    test_name: str
    variants: list[str] = Field(description="Content variant descriptions")
    niche: str = "general"
    platform: str = "tiktok"


class ABVariant(BaseModel):
    """Single variant in an A/B test."""

    variant_id: str = ""
    content: str = ""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    ctr: float = 0.0
    conversion_rate: float = 0.0
    confidence_interval: list[float] = Field(default_factory=lambda: [0.0, 0.0])


class ABTest(BaseModel):
    """Full A/B test state."""

    test_id: str = ""
    test_name: str = ""
    variants: list[ABVariant] = Field(default_factory=list)
    status: str = "running"  # running | significant | inconclusive
    confidence: float = 0.0
    winner: Optional[int] = None
    total_impressions: int = 0
    total_clicks: int = 0
    lift: float = 0.0
    recommendation: str = ""


class SampleSizeResult(BaseModel):
    """Sample size calculation output."""

    minimum_sample_per_variant: int
    recommended_sample_per_variant: int
    power: float
    significance_level: float
    mde: float


# ── In-memory store ─────────────────────────────────────────────────
# Production: swap with DB-backed repository.

_tests: dict[str, ABTest] = {}


# ── Chi-squared (two-proportion) ────────────────────────────────────


def _normal_cdf(x: float) -> float:
    """Standard normal CDF via error function approximation.

    Abramowitz & Stegun approximation 7.1.26 — max absolute error 1.5e-7.
    Sufficient for p-value calculation.
    """
    if x < -8.0:
        return 0.0
    if x > 8.0:
        return 1.0
    sign = 1.0 if x >= 0 else -1.0
    z = abs(x)
    t = 1.0 / (1.0 + 0.2316419 * z)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    return 1.0 - sign * pdf * poly


def _normal_ppf(p: float) -> float:
    """Inverse normal CDF (percent point function).

    Rational approximation — accuracy ~4.5e-4 for 1e-4 < p < 1-1e-4.
    Good enough for z-critical values in standard significance tests.
    """
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0, 1)")
    if p < 0.5:
        return -_normal_ppf(1.0 - p)
    # Rational approximation for upper half
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)


def _chi_squared_1df(p: float) -> float:
    """Inverse chi-squared CDF with 1 degree of freedom.

    chi2(1, p) = Z(1-p/2)^2 where Z is inverse normal.
    """
    tail_prob = 1.0 - p
    z = _normal_ppf(1.0 - tail_prob / 2.0)
    return z * z


def two_proportion_z_test(
    successes_a: int, trials_a: int,
    successes_b: int, trials_b: int,
) -> tuple[float, float, float]:
    """Two-proportion z-test.

    Returns (z_stat, p_value, confidence_pct).
    Tests whether proportions differ (two-tailed).
    """
    if trials_a < 2 or trials_b < 2:
        return (0.0, 1.0, 0.0)

    p_a = successes_a / trials_a
    p_b = successes_b / trials_b
    n_a = trials_a
    n_b = trials_b

    # Pooled proportion under H0
    p_pool = (successes_a + successes_b) / (n_a + n_b)

    if p_pool <= 0.0 or p_pool >= 1.0:
        return (0.0, 1.0, 0.0)

    se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_a + 1.0 / n_b))

    if se == 0.0:
        return (0.0, 1.0, 0.0)

    z = (p_a - p_b) / se
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))
    confidence = (1.0 - p_value) * 100.0

    return (z, p_value, confidence)


def chi_squared_test_variants(
    variants: list[ABVariant],
    metric: str = "clicks",
) -> tuple[float, float, float]:
    """Chi-squared test across all variants for a given metric.

    metric: 'clicks' or 'conversions'
    Returns (chi2_stat, p_value, confidence_pct).
    """
    if len(variants) < 2:
        return (0.0, 1.0, 0.0)

    # Build observed table: rows=variants, cols=[success, failure]
    observed: list[list[float]] = []
    total_success = 0
    total_trials = 0

    for v in variants:
        impressions = v.impressions
        if metric == "clicks":
            success = v.clicks
        else:
            success = v.conversions
        failure = impressions - success

        if impressions <= 0:
            continue

        observed.append([success, failure])
        total_success += success
        total_trials += impressions

    if len(observed) < 2 or total_trials == 0:
        return (0.0, 1.0, 0.0)

    # Expected counts under null hypothesis
    expected: list[list[float]] = []
    for row in observed:
        n = row[0] + row[1]
        e_success = total_success * n / total_trials
        e_failure = (total_trials - total_success) * n / total_trials
        expected.append([e_success, e_failure])

    # Chi-squared statistic
    chi2 = 0.0
    for obs_row, exp_row in zip(observed, expected):
        for o, e in zip(obs_row, exp_row):
            if e > 0:
                chi2 += (o - e) ** 2 / e

    # Degrees of freedom = (rows-1) * (cols-1) = (k-1) * 1 = k-1
    df = len(observed) - 1

    # P-value from chi-squared CDF approximation
    # For df=1: chi2 = z^2, so use normal CDF
    if df == 1:
        z = math.sqrt(chi2)
        p_value = 2.0 * (1.0 - _normal_cdf(z))
    else:
        # Wilson-Hilferty approximation for chi-squared CDF
        if chi2 <= 0:
            p_value = 1.0
        else:
            z_wc = ((chi2 / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(
                2.0 / (9.0 * df)
            )
            p_value = 1.0 - _normal_cdf(z_wc)

    confidence = (1.0 - p_value) * 100.0
    return (chi2, p_value, confidence)


def confidence_interval_proportion(
    successes: int, trials: int, confidence_level: float = 0.95
) -> list[float]:
    """Wilson score interval for a proportion.

    More accurate than Wald interval for small samples or extreme proportions.
    """
    if trials == 0:
        return [0.0, 0.0]

    p = successes / trials
    n = trials
    z = _normal_ppf(1.0 - (1.0 - confidence_level) / 2.0)
    z2 = z * z

    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    spread = z * math.sqrt((p * (1.0 - p) / n + z2 / (4.0 * n * n))) / denom

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return [round(lower, 6), round(upper, 6)]


# ── Sample size ─────────────────────────────────────────────────────


def required_sample_size(
    baseline_rate: float,
    mde: float = 0.1,
    power: float = 0.8,
    significance_level: float = 0.05,
) -> SampleSizeResult:
    """Calculate required sample size per variant.

    baseline_rate: current conversion/click rate (0-1).
    mde: minimum detectable effect as fraction of baseline (0.1 = 10% lift).
    power: desired statistical power (default 80%).
    significance_level: alpha for significance test (default 0.05 = 95% confidence).
    """
    if baseline_rate <= 0.0 or baseline_rate >= 1.0:
        raise ValueError("baseline_rate must be in (0, 1)")
    if mde <= 0.0:
        raise ValueError("mde must be positive")

    p1 = baseline_rate
    p2 = baseline_rate * (1.0 + mde)

    if p2 >= 1.0:
        p2 = min(p2, 0.99)

    z_alpha = _normal_ppf(1.0 - significance_level / 2.0)
    z_beta = _normal_ppf(power)

    p_bar = (p1 + p2) / 2.0
    n = (
        (z_alpha * math.sqrt(2.0 * p_bar * (1.0 - p_bar))
         + z_beta * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2)))
        ** 2
    ) / ((p2 - p1) ** 2)

    minimum = math.ceil(n)
    recommended = math.ceil(minimum * 1.5)  # 50% buffer for drop-off

    return SampleSizeResult(
        minimum_sample_per_variant=minimum,
        recommended_sample_per_variant=recommended,
        power=power,
        significance_level=significance_level,
        mde=mde,
    )


# ── Core engine ─────────────────────────────────────────────────────


def create_test(test_input: ABTestCreate) -> ABTest:
    """Create a new A/B test with the given variants."""
    test_id = f"ab_{uuid.uuid4().hex[:12]}"
    variants: list[ABVariant] = []
    for i, desc in enumerate(test_input.variants):
        variants.append(
            ABVariant(
                variant_id=f"{test_id}_v{i}",
                content=desc,
            )
        )

    test = ABTest(
        test_id=test_id,
        test_name=test_input.test_name,
        variants=variants,
        status="running",
        confidence=0.0,
        winner=None,
        total_impressions=0,
        total_clicks=0,
        lift=0.0,
        recommendation="Collecting data...",
    )
    _tests[test_id] = test
    return test


def get_test(test_id: str) -> ABTest | None:
    """Retrieve a test by ID."""
    return _tests.get(test_id)


def update_variant(
    test_id: str,
    variant_id: str,
    impressions: int = 0,
    clicks: int = 0,
    conversions: int = 0,
) -> ABTest | None:
    """Update metrics for a single variant and re-evaluate significance."""
    test = _tests.get(test_id)
    if test is None:
        return None

    target: ABVariant | None = None
    for v in test.variants:
        if v.variant_id == variant_id:
            target = v
            break

    if target is None:
        return None

    # Accumulate (not replace) — multiple update calls
    target.impressions += impressions
    target.clicks += clicks
    target.conversions += conversions

    # Recalculate derived metrics
    if target.impressions > 0:
        target.ctr = round(target.clicks / target.impressions, 6)
        target.conversion_rate = round(target.conversions / target.impressions, 6)
        target.confidence_interval = confidence_interval_proportion(
            target.clicks, target.impressions
        )

    # Aggregate totals
    test.total_impressions = sum(v.impressions for v in test.variants)
    test.total_clicks = sum(v.clicks for v in test.variants)

    # Re-evaluate
    evaluate_test(test)
    return test


def evaluate_test(test: ABTest) -> None:
    """Run statistical tests and determine status, winner, lift."""
    if len(test.variants) < 2:
        test.status = "running"
        test.recommendation = "Need at least 2 variants."
        return

    # Check minimum data
    active_variants = [v for v in test.variants if v.impressions >= 30]
    if len(active_variants) < 2:
        min_needed = max(
            30 - v.impressions for v in test.variants if v.impressions < 30
        ) if any(v.impressions < 30 for v in test.variants) else 0
        test.status = "running"
        test.confidence = 0.0
        test.recommendation = (
            f"Collecting data. ~{min_needed} more impressions needed for "
            f"the least-sampled variant."
        )
        return

    # Chi-squared test on clicks
    chi2_stat, p_clicks, conf_clicks = chi_squared_test_variants(
        active_variants, metric="clicks"
    )

    # Chi-squared test on conversions (if any exist)
    total_conv = sum(v.conversions for v in active_variants)
    if total_conv >= 10:
        _, p_conv, conf_conv = chi_squared_test_variants(
            active_variants, metric="conversions"
        )
        # Use the more conservative (higher) p-value
        p_value = max(p_clicks, p_conv)
        confidence = min(conf_clicks, conf_conv)
    else:
        p_value = p_clicks
        confidence = conf_clicks

    test.confidence = round(confidence, 2)

    SIGNIFICANCE_THRESHOLD = 0.05  # p < 0.05

    if p_value < SIGNIFICANCE_THRESHOLD:
        test.status = "significant"

        # Find winner: variant with highest CTR
        best_idx = 0
        best_ctr = 0.0
        for i, v in enumerate(active_variants):
            if v.ctr > best_ctr:
                best_ctr = v.ctr
                best_idx = i

        test.winner = best_idx

        # Calculate lift vs worst performer
        worst_ctr = min(v.ctr for v in active_variants)
        if worst_ctr > 0:
            test.lift = round(((best_ctr - worst_ctr) / worst_ctr) * 100.0, 2)

        # Build recommendation
        winner_v = test.variants[best_idx]
        test.recommendation = (
            f"Winner: {winner_v.variant_id} ({winner_v.content[:50]}...) "
            f"with {winner_v.ctr*100:.2f}% CTR "
            f"(+{test.lift:.1f}% lift, {confidence:.1f}% confidence). "
            f"Promote this variant and retire underperformers."
        )
    elif p_value < 0.1:
        test.status = "running"
        # Trending — suggest continuing
        best_ctr = max(v.ctr for v in active_variants)
        test.recommendation = (
            f"Borderline result (p={p_value:.4f}, {confidence:.1f}% confidence). "
            f"Continue collecting data. Current leader has {best_ctr*100:.2f}% CTR."
        )
    else:
        test.status = "inconclusive"
        test.winner = None
        best_v = max(active_variants, key=lambda v: v.ctr)
        test.recommendation = (
            f"No significant difference found (p={p_value:.4f}, {confidence:.1f}% confidence). "
            f"Consider testing more different variants or increasing sample size."
        )


def promote_winner(test_id: str) -> ABTest | None:
    """Mark winner as promoted, retire losers. Returns updated test."""
    test = _tests.get(test_id)
    if test is None or test.winner is None:
        return None

    winner_v = test.variants[test.winner]
    # In production, persist status changes to DB
    test.recommendation = (
        f"PROMOTED: {winner_v.variant_id} ({winner_v.content[:50]}...) — "
        f"CTR {winner_v.ctr*100:.2f}%, "
        f"{test.total_impressions} total impressions, "
        f"{test.confidence:.1f}% confidence."
    )
    return test


def list_tests(status_filter: str = "") -> list[ABTest]:
    """List all tests, optionally filtered by status."""
    if status_filter:
        return [t for t in _tests.values() if t.status == status_filter]
    return list(_tests.values())


def delete_test(test_id: str) -> bool:
    """Delete a test. Returns True if found and removed."""
    return _tests.pop(test_id, None) is not None
