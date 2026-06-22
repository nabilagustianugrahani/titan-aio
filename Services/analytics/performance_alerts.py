"""Performance Alerts — monitor metrics and trigger alerts."""

from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
import hashlib


class AlertRule(BaseModel):
    rule_id: str = ""
    name: str
    metric: str
    condition: str
    threshold: float = 0.0
    platform: str = ""
    enabled: bool = True


class PerformanceAlert(BaseModel):
    alert_id: str = ""
    rule_name: str = ""
    metric: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    message: str = ""
    severity: str = "info"
    timestamp: str = ""
    acknowledged: bool = False


class PerformanceAlertManager:
    def __init__(self):
        self.rules: dict[str, AlertRule] = {}
        self.alerts: list[PerformanceAlert] = []
        self.metric_history: list[dict] = []

    async def create_rule(self, name: str, metric: str, condition: str, threshold: float, platform: str = "") -> AlertRule:
        rule_id = hashlib.md5(f"{name}:{metric}".encode()).hexdigest()[:10]
        rule = AlertRule(rule_id=rule_id, name=name, metric=metric, condition=condition, threshold=threshold, platform=platform)
        self.rules[rule_id] = rule
        return rule

    async def record_metric(self, metric: str, value: float, platform: str = "", campaign_id: str = ""):
        self.metric_history.append({"metric": metric, "value": value, "platform": platform, "campaign_id": campaign_id, "timestamp": datetime.now().isoformat()})
        for rule in self.rules.values():
            if not rule.enabled or rule.metric != metric:
                continue
            if rule.platform and rule.platform != platform:
                continue
            triggered = (rule.condition == "below" and value < rule.threshold) or (rule.condition == "above" and value > rule.threshold)
            if triggered:
                alert = PerformanceAlert(
                    alert_id=hashlib.md5(f"{rule.rule_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:10],
                    rule_name=rule.name, metric=metric, current_value=value, threshold=rule.threshold,
                    message=f"{rule.name}: {metric} is {value} (threshold: {rule.condition} {rule.threshold})",
                    severity="warning" if rule.condition == "below" else "info",
                    timestamp=datetime.now().isoformat(),
                )
                self.alerts.append(alert)

    async def get_alerts(self, limit: int = 20, acknowledged: bool = False) -> list[PerformanceAlert]:
        return [a for a in self.alerts if a.acknowledged == acknowledged][-limit:]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        for a in self.alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return True
        return False

    async def get_rules(self) -> list[AlertRule]:
        return list(self.rules.values())

    async def get_stats(self) -> dict:
        return {"total_rules": len(self.rules), "total_alerts": len(self.alerts), "unacknowledged": sum(1 for a in self.alerts if not a.acknowledged)}
