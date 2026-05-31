"""LLM API Gateway - Unified OpenAI-compatible API for multiple providers."""

import os
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

from cache import SemanticCache
from providers import get_available_providers, get_all_providers
from router import Router
from usage import UsageTracker

app = FastAPI(title="LLM API Gateway", version="1.0.0")

# Initialize components
router = Router()
cache = SemanticCache(ttl_seconds=int(os.getenv("CACHE_TTL", "3600")))
tracker = UsageTracker()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: list[ChatMessage]
    max_tokens: int = 500
    temperature: float = 0.7
    strategy: Optional[str] = None  # Override routing strategy


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    provider: str
    choices: list[dict]
    usage: dict
    latency_ms: float
    cached: bool = False


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(req: ChatRequest):
    """OpenAI-compatible chat completions endpoint."""
    messages = [m.model_dump() for m in req.messages]
    model = req.model or ""

    # Check cache
    cached = cache.get(messages, model)
    if cached:
        cached["cached"] = True
        return ChatResponse(**cached)

    # Route to provider
    start = time.time()
    try:
        response = router.route(
            messages=messages,
            model=model or None,
            strategy=req.strategy,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
    except Exception as e:
        raise HTTPException(502, f"Provider error: {e}")

    # Compute cost
    cost = tracker.compute_cost(
        response.provider, response.model,
        response.prompt_tokens, response.completion_tokens
    )

    # Track usage
    tracker.record(
        provider=response.provider,
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        cost=cost,
        latency_ms=response.latency_ms,
    )

    import uuid
    result = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "model": response.model,
        "provider": response.provider,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": response.content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": response.prompt_tokens, "completion_tokens": response.completion_tokens, "total_tokens": response.total_tokens},
        "latency_ms": response.latency_ms,
        "cached": False,
    }

    # Cache response
    cache.set(messages, model, result)

    return ChatResponse(**result)


@app.get("/v1/models")
async def list_models():
    """List all available models across providers."""
    providers = get_all_providers()
    models = []
    for name, provider in providers.items():
        for model in provider.get_models():
            models.append({
                "id": model,
                "provider": name,
                "available": provider.is_available(),
                "cost_per_1k": provider.cost_per_1k_tokens.get(model, 0),
            })
    return {"models": models}


@app.get("/v1/providers")
async def list_providers():
    """List provider status."""
    providers = get_all_providers()
    return {
        name: {"available": p.is_available(), "models": p.get_models()}
        for name, p in providers.items()
    }


@app.get("/usage")
async def get_usage():
    """Get current session usage summary."""
    return tracker.get_session_summary()


@app.get("/usage/daily")
async def get_daily_usage():
    """Get daily usage summary."""
    return tracker.get_daily_summary()


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return cache.get_stats()


@app.post("/cache/clear")
async def clear_cache():
    cache.clear()
    return {"status": "cleared"}


@app.get("/")
async def root():
    return {
        "name": "LLM API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/chat/completions": "OpenAI-compatible chat endpoint",
            "GET /v1/models": "List available models",
            "GET /v1/providers": "Provider status",
            "GET /usage": "Session usage stats",
            "GET /cache/stats": "Cache statistics",
        },
        "routing_strategy": router.strategy,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
