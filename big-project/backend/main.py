"""
AI创作工坊 - FastAPI Application Entry Point

Demonstrates:
- FastAPI app lifecycle (startup/shutdown)
- Middleware stack (CORS, auth, metrics, rate limiting, logging)
- Dependency injection
- Exception handling
- Health checks
- API router registration
"""

import time
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from observability.logger import get_logger, setup_logging
from observability.metrics import REQUEST_COUNT, REQUEST_LATENCY, setup_metrics
from observability.tracing import setup_tracing
from security.rate_limiter import RateLimiter

logger = get_logger(__name__)
settings = get_settings()


# ─── Lifespan (startup / shutdown) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: initialize resources on startup, clean up on shutdown."""
    # Startup
    setup_logging()
    logger.info("Starting AI创作工坊", extra={"env": settings.app_env})

    # Initialize Redis connection pool
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    # Initialize rate limiter
    app.state.rate_limiter = RateLimiter(
        redis=app.state.redis,
        limit=settings.rate_limit_per_minute,
        burst=settings.rate_limit_burst,
    )

    # Setup metrics and tracing
    setup_metrics(app)
    setup_tracing(app)

    # Initialize database connection (lazy — created on first request)
    from models.database import init_db
    await init_db(settings.database_url)

    logger.info("All services initialized successfully")
    yield

    # Shutdown
    logger.info("Shutting down AI创作工坊")
    await app.state.redis.close()
    logger.info("Cleanup complete")


# ─── Create App ─────────────────────────────────────────────
app = FastAPI(
    title="AI创作工坊 API",
    description="AI Content Creator SaaS Platform - Video generation, RAG Q&A, Comment management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── Middleware ──────────────────────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to every request for distributed tracing."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record request metrics (count, latency) for Prometheus."""
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log every request with structured context."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": getattr(request.state, "correlation_id", None),
            "client_ip": request.client.host if request.client else None,
        },
    )
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting per client IP."""
    if request.url.path in ("/health", "/metrics", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    rate_limiter: RateLimiter = request.app.state.rate_limiter
    client_ip = request.client.host if request.client else "unknown"

    allowed, remaining, reset_at = await rate_limiter.check(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "retry_after": reset_at},
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_at),
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# ─── Health Check ────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    Returns service status and dependency health.
    """
    checks = {"status": "healthy", "version": "1.0.0", "service": "ai-workshop"}

    # Check Redis
    try:
        redis: aioredis.Redis = app.state.redis
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"
        checks["status"] = "degraded"

    return checks


# ─── API Routes ─────────────────────────────────────────────
from api.video import router as video_router
from api.comment import router as comment_router
from api.knowledge import router as knowledge_router
from api.admin import router as admin_router

app.include_router(video_router, prefix="/api/v1/video", tags=["Video"])
app.include_router(comment_router, prefix="/api/v1/comments", tags=["Comments"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["Knowledge"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])


# ─── Global Exception Handler ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler with structured logging."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id,
        },
    )


# ─── Prometheus Metrics Endpoint ────────────────────────────
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
