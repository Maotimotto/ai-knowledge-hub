"""Metrics collector for LLM application monitoring."""

import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetricPoint:
    timestamp: float
    metric_type: str  # "latency", "tokens", "error", "cost", "request"
    value: float
    metadata: dict = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics from LLM applications."""

    def __init__(self, max_points: int = 10000):
        self._metrics: deque[MetricPoint] = deque(maxlen=max_points)
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "total_errors": 0,
        }

    def record_latency(self, ms: float, model: str = "", provider: str = "") -> None:
        """Record a request latency."""
        with self._lock:
            self._metrics.append(MetricPoint(
                timestamp=time.time(),
                metric_type="latency",
                value=ms,
                metadata={"model": model, "provider": provider},
            ))

    def record_tokens(self, count: int, direction: str = "total", model: str = "") -> None:
        """Record token usage."""
        with self._lock:
            self._metrics.append(MetricPoint(
                timestamp=time.time(),
                metric_type="tokens",
                value=float(count),
                metadata={"direction": direction, "model": model},
            ))
            self._counters["total_tokens"] += count

    def record_error(self, error_type: str = "unknown", provider: str = "") -> None:
        """Record an error."""
        with self._lock:
            self._metrics.append(MetricPoint(
                timestamp=time.time(),
                metric_type="error",
                value=1.0,
                metadata={"error_type": error_type, "provider": provider},
            ))
            self._counters["total_errors"] += 1

    def record_cost(self, amount: float, model: str = "", provider: str = "") -> None:
        """Record a cost event."""
        with self._lock:
            self._metrics.append(MetricPoint(
                timestamp=time.time(),
                metric_type="cost",
                value=amount,
                metadata={"model": model, "provider": provider},
            ))
            self._counters["total_cost"] += amount

    def record_request(self, model: str = "", provider: str = "", cached: bool = False) -> None:
        """Record a request."""
        with self._lock:
            self._metrics.append(MetricPoint(
                timestamp=time.time(),
                metric_type="request",
                value=1.0,
                metadata={"model": model, "provider": provider, "cached": cached},
            ))
            self._counters["total_requests"] += 1

    def get_recent(self, metric_type: Optional[str] = None, seconds: float = 300) -> list[MetricPoint]:
        """Get recent metrics within the time window."""
        cutoff = time.time() - seconds
        with self._lock:
            if metric_type:
                return [m for m in self._metrics if m.metric_type == metric_type and m.timestamp >= cutoff]
            return [m for m in self._metrics if m.timestamp >= cutoff]

    def get_summary(self, seconds: float = 300) -> dict:
        """Get aggregated summary of recent metrics."""
        recent = self.get_recent(seconds=seconds)
        if not recent:
            return {"message": "No metrics in time window"}

        latencies = [m.value for m in recent if m.metric_type == "latency"]
        costs = [m.value for m in recent if m.metric_type == "cost"]
        errors = [m for m in recent if m.metric_type == "error"]
        requests = [m for m in recent if m.metric_type == "request"]

        return {
            "window_seconds": seconds,
            "total_requests": len(requests),
            "total_errors": len(errors),
            "error_rate": round(len(errors) / max(len(requests), 1), 3),
            "latency": {
                "avg_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                "p50_ms": round(sorted(latencies)[len(latencies) // 2], 2) if latencies else 0,
                "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if latencies else 0,
                "max_ms": round(max(latencies), 2) if latencies else 0,
            },
            "cost": {
                "total_usd": round(sum(costs), 4),
                "avg_per_request": round(sum(costs) / max(len(requests), 1), 4),
            },
            "counters": dict(self._counters),
        }

    def get_time_series(self, metric_type: str, bucket_seconds: int = 60, seconds: float = 300) -> list[dict]:
        """Get time-series data for charting."""
        recent = self.get_recent(metric_type=metric_type, seconds=seconds)
        if not recent:
            return []

        buckets: dict[int, list[float]] = {}
        for m in recent:
            bucket = int(m.timestamp // bucket_seconds) * bucket_seconds
            buckets.setdefault(bucket, []).append(m.value)

        return [
            {"timestamp": ts, "avg": round(sum(vals) / len(vals), 2), "count": len(vals)}
            for ts, vals in sorted(buckets.items())
        ]

    def generate_sample_data(self, count: int = 50) -> None:
        """Generate sample metrics for demo purposes."""
        providers = ["openai", "anthropic", "local"]
        models = ["gpt-4o", "claude-3-sonnet", "llama2", "gpt-3.5-turbo"]
        now = time.time()

        for i in range(count):
            t = now - (count - i) * 10  # Spread over time
            provider = random.choice(providers)
            model = random.choice(models)

            # Simulate latency (higher for cloud, lower for local)
            base_latency = 200 if provider == "local" else 800
            latency = base_latency + random.gauss(0, 200)

            # Simulate tokens
            tokens = random.randint(50, 500)

            # Simulate cost
            cost = tokens / 1000 * random.uniform(0.0002, 0.01)

            # Simulate occasional errors
            is_error = random.random() < 0.05

            with self._lock:
                self._metrics.append(MetricPoint(t, "latency", latency, {"model": model, "provider": provider}))
                self._metrics.append(MetricPoint(t, "tokens", float(tokens), {"model": model}))
                self._metrics.append(MetricPoint(t, "request", 1.0, {"model": model, "provider": provider}))
                self._metrics.append(MetricPoint(t, "cost", cost, {"model": model, "provider": provider}))
                if is_error:
                    self._metrics.append(MetricPoint(t, "error", 1.0, {"error_type": "timeout"}))
                    self._counters["total_errors"] += 1

                self._counters["total_requests"] += 1
                self._counters["total_tokens"] += tokens
                self._counters["total_cost"] += cost


# Singleton collector
_collector: Optional[MetricsCollector] = None


def get_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
