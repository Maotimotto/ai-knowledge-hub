"""Token usage tracking and cost estimation."""

import json
import os
import time
from pathlib import Path
from typing import Optional


class UsageTracker:
    """Track token usage and costs across providers and models."""

    def __init__(self, log_path: str = "usage_log.jsonl"):
        self.log_path = log_path
        self._session_usage: list[dict] = []

    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency_ms: float,
        cached: bool = False,
    ) -> dict:
        """Record a usage event."""
        entry = {
            "timestamp": time.time(),
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": round(cost, 6),
            "latency_ms": round(latency_ms, 2),
            "cached": cached,
        }
        self._session_usage.append(entry)

        # Append to log file
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        return entry

    def compute_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Compute cost based on provider pricing."""
        from providers import get_all_providers
        providers = get_all_providers()
        if provider in providers:
            cost_per_1k = providers[provider].cost_per_1k_tokens.get(model, 0)
            return (prompt_tokens + completion_tokens) / 1000 * cost_per_1k
        return 0.0

    def get_session_summary(self) -> dict:
        """Get summary of current session usage."""
        if not self._session_usage:
            return {"message": "No usage recorded this session"}

        total_tokens = sum(e["total_tokens"] for e in self._session_usage)
        total_cost = sum(e["cost_usd"] for e in self._session_usage)
        avg_latency = sum(e["latency_ms"] for e in self._session_usage) / len(self._session_usage)
        cache_hits = sum(1 for e in self._session_usage if e["cached"])

        by_provider: dict[str, dict] = {}
        by_model: dict[str, dict] = {}

        for entry in self._session_usage:
            p = entry["provider"]
            m = entry["model"]
            by_provider.setdefault(p, {"requests": 0, "tokens": 0, "cost": 0})
            by_provider[p]["requests"] += 1
            by_provider[p]["tokens"] += entry["total_tokens"]
            by_provider[p]["cost"] += entry["cost_usd"]

            by_model.setdefault(m, {"requests": 0, "tokens": 0, "cost": 0})
            by_model[m]["requests"] += 1
            by_model[m]["tokens"] += entry["total_tokens"]
            by_model[m]["cost"] += entry["cost_usd"]

        return {
            "total_requests": len(self._session_usage),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / len(self._session_usage), 3),
            "by_provider": by_provider,
            "by_model": by_model,
        }

    def get_daily_summary(self, days: int = 7) -> dict:
        """Read log file and summarize by day."""
        if not Path(self.log_path).exists():
            return {"message": "No usage log found"}

        daily: dict[str, dict] = {}
        with open(self.log_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    day = time.strftime("%Y-%m-%d", time.localtime(entry["timestamp"]))
                    daily.setdefault(day, {"requests": 0, "tokens": 0, "cost": 0})
                    daily[day]["requests"] += 1
                    daily[day]["tokens"] += entry.get("total_tokens", 0)
                    daily[day]["cost"] += entry.get("cost_usd", 0)
                except (json.JSONDecodeError, KeyError):
                    continue

        return dict(sorted(daily.items(), reverse=True)[:days])
