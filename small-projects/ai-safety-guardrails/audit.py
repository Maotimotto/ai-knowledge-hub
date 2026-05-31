"""Audit logging for all AI safety interactions."""

import time
from collections import deque
from typing import Any


class AuditLogger:
    """In-memory audit log (swap for DB/ELK in production)."""

    def __init__(self, max_entries: int = 10000):
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_entries)

    def log_request(self, request_id: str, path: str, duration: float, status: int):
        self._entries.append({
            "type": "http_request",
            "request_id": request_id,
            "path": path,
            "duration_ms": round(duration * 1000, 2),
            "status": status,
            "timestamp": time.time(),
        })

    def log_check(self, decision: dict[str, Any]):
        """Log a safety check result."""
        entry = {
            "type": "safety_check",
            "timestamp": time.time(),
            **decision,
        }
        self._entries.append(entry)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        entries = list(self._entries)
        return entries[-limit:]

    def query(self, tenant_id: str | None = None, blocked: bool | None = None,
              since: float | None = None, limit: int = 100) -> list[dict[str, Any]]:
        results = list(self._entries)
        if tenant_id:
            results = [e for e in results if e.get("tenant_id") == tenant_id]
        if blocked is not None:
            results = [e for e in results if e.get("blocked") == blocked]
        if since:
            results = [e for e in results if e.get("timestamp", 0) >= since]
        return results[-limit:]

    def stats(self) -> dict[str, Any]:
        checks = [e for e in self._entries if e.get("type") == "safety_check"]
        blocked = sum(1 for e in checks if e.get("blocked"))
        return {
            "total_checks": len(checks),
            "blocked": blocked,
            "passed": len(checks) - blocked,
            "block_rate": round(blocked / len(checks) * 100, 1) if checks else 0,
        }
