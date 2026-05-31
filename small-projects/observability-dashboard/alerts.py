"""Simple alerting rules for LLM metrics."""

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Alert:
    severity: str  # "info", "warning", "critical"
    metric: str
    message: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "metric": self.metric,
            "message": self.message,
            "value": round(self.value, 4),
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "time_str": time.strftime("%H:%M:%S", time.localtime(self.timestamp)),
        }


class AlertManager:
    """Evaluates alerting rules against metrics."""

    def __init__(self):
        self.latency_threshold = float(os.getenv("LATENCY_THRESHOLD_MS", "5000"))
        self.error_rate_threshold = float(os.getenv("ERROR_RATE_THRESHOLD", "0.1"))
        self.cost_threshold = float(os.getenv("COST_THRESHOLD_DAILY", "100.0"))
        self._active_alerts: list[Alert] = []
        self._alert_history: list[Alert] = []

    def evaluate(self, summary: dict) -> list[Alert]:
        """Evaluate alert rules against current metrics summary."""
        alerts: list[Alert] = []
        now = time.time()

        # Latency alert
        avg_latency = summary.get("latency", {}).get("avg_ms", 0)
        p95_latency = summary.get("latency", {}).get("p95_ms", 0)
        if p95_latency > self.latency_threshold:
            alerts.append(Alert(
                severity="warning",
                metric="latency",
                message=f"P95 latency ({p95_latency:.0f}ms) exceeds threshold ({self.latency_threshold:.0f}ms)",
                value=p95_latency,
                threshold=self.latency_threshold,
            ))

        # Error rate alert
        error_rate = summary.get("error_rate", 0)
        if error_rate > self.error_rate_threshold:
            alerts.append(Alert(
                severity="critical",
                metric="error_rate",
                message=f"Error rate ({error_rate:.1%}) exceeds threshold ({self.error_rate_threshold:.1%})",
                value=error_rate,
                threshold=self.error_rate_threshold,
            ))

        # Cost alert
        total_cost = summary.get("cost", {}).get("total_usd", 0)
        if total_cost > self.cost_threshold * 0.8:  # Warn at 80%
            severity = "critical" if total_cost > self.cost_threshold else "warning"
            alerts.append(Alert(
                severity=severity,
                metric="cost",
                message=f"Cost (${total_cost:.2f}) approaching/exceeding daily threshold (${self.cost_threshold:.2f})",
                value=total_cost,
                threshold=self.cost_threshold,
            ))

        self._active_alerts = alerts
        self._alert_history.extend(alerts)
        return alerts

    def get_active(self) -> list[dict]:
        return [a.to_dict() for a in self._active_alerts]

    def get_history(self, limit: int = 50) -> list[dict]:
        return [a.to_dict() for a in self._alert_history[-limit:]]
