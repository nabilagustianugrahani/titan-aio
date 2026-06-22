"""Performance Alert System — monitors campaign metrics and triggers alerts.

Supports rules for below/above thresholds, percentage drops/surges, and
percentage changes. Includes cooldown periods, severity levels, default
rule templates, and metric history with trend analysis.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


# ── Models ──────────────────────────────────────────────────────────────

class AlertRule(BaseModel):
    rule_id: str = ""
    name: str
    metric: str  # ctr / engagement / revenue / impressions / conversion / cpc
    condition: str  # below / above / dropped / surged / changed_by
    threshold: float = 0.0
    platform: str = ""  # empty = all platforms
    campaign_id: str = ""  # empty = all campaigns
    enabled: bool = True
    cooldown_minutes: int = 60
    created_at: str = ""


class PerformanceAlert(BaseModel):
    alert_id: str = ""
    rule_id: str = ""
    rule_name: str = ""
    metric: str = ""
    current_value: float = 0.0
    previous_value: float = 0.0
    threshold: float = 0.0
    condition: str = ""
    message: str = ""
    severity: str = "info"  # info / warning / critical
    platform: str = ""
    campaign_id: str = ""
    timestamp: str = ""
    acknowledged: bool = False
    acknowledged_at: str = ""


# ── Default Rules ───────────────────────────────────────────────────────

_SEVERITY_MAP: dict[str, str] = {
    "below": "warning",
    "above": "info",
    "dropped": "critical",
    "surged": "info",
    "changed_by": "warning",
}

_DEFAULT_RULES: list[dict] = [
    {"name": "Low CTR Alert", "metric": "ctr", "condition": "below", "threshold": 0.02},
    {"name": "High Engagement", "metric": "engagement", "condition": "above", "threshold": 0.05},
    {"name": "Revenue Drop", "metric": "revenue", "condition": "dropped", "threshold": 0.20},
    {"name": "Low Impressions", "metric": "impressions", "condition": "below", "threshold": 100},
    {"name": "High CPC Warning", "metric": "cpc", "condition": "above", "threshold": 1.0},
    {"name": "Conversion Drop", "metric": "conversion", "condition": "dropped", "threshold": 0.15},
]


# ── Alert Manager ───────────────────────────────────────────────────────

class PerformanceAlertManager:
    """Monitor metrics, evaluate alert rules, and manage alert lifecycle.

    Features:
    - Configurable rules with cooldown periods
    - Trend detection (dropped/surged/changed_by compare to previous value)
    - Severity levels (info, warning, critical)
    - Bulk acknowledge and cleanup
    - Metric history with trend summaries
    """

    def __init__(self, auto_init_defaults: bool = True) -> None:
        self.rules: dict[str, AlertRule] = {}
        self.alerts: list[PerformanceAlert] = []
        self.metric_history: list[dict] = []
        self._defaults_loaded: bool = False
        self._max_history: int = 10_000

        if auto_init_defaults:
            self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Load default alert rules once."""
        if self._defaults_loaded:
            return
        self._defaults_loaded = True
        for rule_def in _DEFAULT_RULES:
            rule_id = hashlib.md5(
                f"{rule_def['name']}:{rule_def['metric']}".encode()
            ).hexdigest()[:10]
            self.rules[rule_id] = AlertRule(
                rule_id=rule_id,
                name=rule_def["name"],
                metric=rule_def["metric"],
                condition=rule_def["condition"],
                threshold=rule_def["threshold"],
                created_at=datetime.now().isoformat(),
            )

    # ── Rule Management ─────────────────────────────────────────────────

    async def create_rule(
        self,
        name: str,
        metric: str,
        condition: str,
        threshold: float,
        platform: str = "",
        campaign_id: str = "",
        cooldown_minutes: int = 60,
    ) -> AlertRule:
        """Create a new alert rule."""
        self._ensure_defaults()
        rule_id = hashlib.md5(
            f"{name}:{metric}:{condition}:{threshold}".encode()
        ).hexdigest()[:10]
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            metric=metric.lower(),
            condition=condition.lower(),
            threshold=threshold,
            platform=platform.lower(),
            campaign_id=campaign_id,
            cooldown_minutes=cooldown_minutes,
            created_at=datetime.now().isoformat(),
        )
        self.rules[rule_id] = rule
        return rule

    async def update_rule(self, rule_id: str, **kwargs) -> Optional[AlertRule]:
        """Update an existing rule by ID."""
        if rule_id not in self.rules:
            return None
        rule = self.rules[rule_id]
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by ID."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    async def toggle_rule(self, rule_id: str, enabled: bool) -> Optional[AlertRule]:
        """Enable or disable a rule."""
        if rule_id not in self.rules:
            return None
        self.rules[rule_id].enabled = enabled
        return self.rules[rule_id]

    async def get_rules(self) -> list[AlertRule]:
        """Return all alert rules."""
        self._ensure_defaults()
        return list(self.rules.values())

    # ── Metric Recording & Evaluation ───────────────────────────────────

    async def record_metric(
        self,
        metric: str,
        value: float,
        platform: str = "",
        campaign_id: str = "",
    ) -> list[PerformanceAlert]:
        """Record a metric value and evaluate all matching rules.

        Returns list of newly triggered alerts (may be empty).
        """
        self._ensure_defaults()

        point = {
            "metric": metric.lower(),
            "value": value,
            "platform": platform.lower(),
            "campaign_id": campaign_id,
            "timestamp": datetime.now().isoformat(),
        }
        self.metric_history.append(point)

        # Trim history
        if len(self.metric_history) > self._max_history:
            self.metric_history = self.metric_history[-self._max_history:]

        triggered: list[PerformanceAlert] = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if rule.metric != metric.lower():
                continue
            if rule.platform and rule.platform != platform.lower():
                continue
            if rule.campaign_id and rule.campaign_id != campaign_id:
                continue

            # Check cooldown
            if self._is_in_cooldown(rule):
                continue

            alert = self._evaluate_rule(rule, value, platform, campaign_id)
            if alert:
                self.alerts.append(alert)
                triggered.append(alert)

        return triggered

    async def record_batch(self, metrics: list[dict]) -> list[PerformanceAlert]:
        """Record multiple metrics at once. Returns all triggered alerts."""
        all_alerts: list[PerformanceAlert] = []
        for m in metrics:
            alerts = await self.record_metric(
                metric=m.get("metric", ""),
                value=m.get("value", 0.0),
                platform=m.get("platform", ""),
                campaign_id=m.get("campaign_id", ""),
            )
            all_alerts.extend(alerts)
        return all_alerts

    # ── Alert Management ────────────────────────────────────────────────

    async def get_alerts(
        self,
        limit: int = 20,
        acknowledged: Optional[bool] = None,
        severity: str = "",
        platform: str = "",
        metric: str = "",
    ) -> list[PerformanceAlert]:
        """Query alerts with optional filters."""
        filtered = list(self.alerts)

        if acknowledged is not None:
            filtered = [a for a in filtered if a.acknowledged == acknowledged]
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        if platform:
            filtered = [a for a in filtered if a.platform == platform]
        if metric:
            filtered = [a for a in filtered if a.metric == metric]

        return filtered[-limit:]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a single alert by ID."""
        for a in self.alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                a.acknowledged_at = datetime.now().isoformat()
                return True
        return False

    async def acknowledge_all(self, severity: str = "") -> int:
        """Acknowledge all unacknowledged alerts. Returns count acknowledged."""
        count = 0
        now_str = datetime.now().isoformat()
        for a in self.alerts:
            if not a.acknowledged:
                if severity and a.severity != severity:
                    continue
                a.acknowledged = True
                a.acknowledged_at = now_str
                count += 1
        return count

    async def clear_alerts(self, older_than_hours: int = 0) -> int:
        """Delete acknowledged alerts. Returns count removed.

        If older_than_hours > 0, only removes alerts older than that.
        If 0, removes all acknowledged alerts.
        """
        if older_than_hours <= 0:
            before = len(self.alerts)
            self.alerts = [a for a in self.alerts if not a.acknowledged]
            return before - len(self.alerts)

        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        before = len(self.alerts)
        self.alerts = [
            a for a in self.alerts
            if not a.acknowledged or self._parse_ts(a.timestamp) > cutoff
        ]
        return before - len(self.alerts)

    # ── Stats & Analytics ───────────────────────────────────────────────

    async def get_stats(self) -> dict:
        """Summary statistics for the alert system."""
        self._ensure_defaults()
        total = len(self.alerts)
        unack = sum(1 for a in self.alerts if not a.acknowledged)

        by_severity: dict[str, int] = defaultdict(int)
        by_metric: dict[str, int] = defaultdict(int)
        by_platform: dict[str, int] = defaultdict(int)

        for a in self.alerts:
            by_severity[a.severity] += 1
            by_metric[a.metric] += 1
            if a.platform:
                by_platform[a.platform] += 1

        return {
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules.values() if r.enabled),
            "total_alerts": total,
            "unacknowledged": unack,
            "acknowledged": total - unack,
            "by_severity": dict(by_severity),
            "by_metric": dict(by_metric),
            "by_platform": dict(by_platform),
            "metric_data_points": len(self.metric_history),
        }

    async def get_metric_summary(
        self, metric: str, hours: int = 24
    ) -> dict:
        """Summary of a metric over the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        points = [
            p for p in self.metric_history
            if p["metric"] == metric and self._parse_ts(p["timestamp"]) > cutoff
        ]
        if not points:
            return {"metric": metric, "period_hours": hours, "data_points": 0}

        values = [p["value"] for p in points]
        return {
            "metric": metric,
            "period_hours": hours,
            "data_points": len(values),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "avg": round(sum(values) / len(values), 4),
            "latest": round(values[-1], 4),
            "trend": (
                "up" if len(values) > 1 and values[-1] > values[0] else "down"
            ),
        }

    async def get_trending_alerts(
        self, hours: int = 24
    ) -> list[PerformanceAlert]:
        """Return unacknowledged alerts from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            a for a in self.alerts
            if not a.acknowledged and self._parse_ts(a.timestamp) > cutoff
        ]

    # ── Internal Helpers ────────────────────────────────────────────────

    def _evaluate_rule(
        self,
        rule: AlertRule,
        value: float,
        platform: str,
        campaign_id: str,
    ) -> Optional[PerformanceAlert]:
        """Evaluate a single rule against a metric value."""
        triggered = False
        previous = self._get_previous_value(rule.metric, platform, campaign_id)

        if rule.condition == "below":
            triggered = value < rule.threshold
        elif rule.condition == "above":
            triggered = value > rule.threshold
        elif rule.condition == "dropped" and previous is not None and previous > 0:
            change = (previous - value) / previous
            triggered = change >= rule.threshold
        elif rule.condition == "surged" and previous is not None and previous > 0:
            change = (value - previous) / previous
            triggered = change >= rule.threshold
        elif rule.condition == "changed_by" and previous is not None and previous > 0:
            change = abs(value - previous) / previous
            triggered = change >= rule.threshold

        if not triggered:
            return None

        severity = _SEVERITY_MAP.get(rule.condition, "warning")

        # Build message
        if rule.condition in ("dropped", "surged", "changed_by") and previous is not None and previous > 0:
            pct = abs(value - previous) / previous * 100
            msg = (
                f"{rule.name}: {rule.metric} {rule.condition} {pct:.1f}% "
                f"({previous:.4f} -> {value:.4f}, threshold: {rule.threshold})"
            )
        elif rule.condition == "below":
            msg = (
                f"{rule.name}: {rule.metric} is {value:.4f} "
                f"(below threshold {rule.threshold})"
            )
        else:
            msg = (
                f"{rule.name}: {rule.metric} is {value:.4f} "
                f"(above threshold {rule.threshold})"
            )

        alert_id = hashlib.md5(
            f"{rule.rule_id}:{datetime.now().isoformat()}:{value}".encode()
        ).hexdigest()[:10]

        return PerformanceAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            metric=rule.metric,
            current_value=value,
            previous_value=previous if previous is not None else 0.0,
            threshold=rule.threshold,
            condition=rule.condition,
            message=msg,
            severity=severity,
            platform=platform,
            campaign_id=campaign_id,
            timestamp=datetime.now().isoformat(),
        )

    def _get_previous_value(
        self, metric: str, platform: str, campaign_id: str
    ) -> Optional[float]:
        """Get the most recent previous value for a metric (excluding the latest)."""
        for p in reversed(self.metric_history[:-1]):
            if p["metric"] != metric:
                continue
            if platform and p["platform"] != platform:
                continue
            if campaign_id and p["campaign_id"] != campaign_id:
                continue
            return p["value"]
        return None

    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Check if a rule's most recent alert is still within cooldown."""
        if rule.cooldown_minutes <= 0:
            return False

        now = datetime.now()
        for a in reversed(self.alerts):
            if a.rule_id != rule.rule_id:
                continue
            alert_time = self._parse_ts(a.timestamp)
            elapsed = (now - alert_time).total_seconds()
            return elapsed < rule.cooldown_minutes * 60
        return False

    @staticmethod
    def _parse_ts(ts: str) -> datetime:
        """Parse ISO timestamp string, fallback to epoch."""
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return datetime(2000, 1, 1)
