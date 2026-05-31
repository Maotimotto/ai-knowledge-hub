"""
AI创作工坊 - Prometheus Metrics

Exposes application metrics for monitoring and alerting.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ─── Request Metrics ──────────────────────────────────────────

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ─── Token Usage Metrics ─────────────────────────────────────

TOKEN_USAGE_COUNTER = Counter(
    "llm_token_usage_total",
    "Total LLM tokens consumed",
    ["provider", "model", "direction"],
)

# ─── Agent Metrics ────────────────────────────────────────────

AGENT_EXECUTION_LATENCY = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution latency",
    ["agent"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

AGENT_EXECUTION_COUNT = Counter(
    "agent_execution_total",
    "Total agent executions",
    ["agent", "status"],
)

# ─── Error Metrics ────────────────────────────────────────────

ERROR_RATE = Counter(
    "app_errors_total",
    "Total application errors",
    ["error_type", "endpoint"],
)

# ─── Business Metrics ────────────────────────────────────────

ACTIVE_TASKS = Gauge(
    "active_tasks",
    "Number of currently active tasks",
    ["task_type"],
)

COST_TRACKER = Counter(
    "llm_cost_usd_total",
    "Total LLM cost in USD",
    ["provider", "model"],
)

APP_INFO = Info(
    "app",
    "Application metadata",
)


def setup_metrics(app: object) -> None:
    """
    Initialize metrics with application metadata.

    Args:
        app: FastAPI application instance
    """
    APP_INFO.info({
        "name": "ai-workshop",
        "version": "1.0.0",
        "framework": "fastapi",
    })
