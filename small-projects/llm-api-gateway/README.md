# LLM API Gateway (LLM推理网关)

A unified API gateway for multiple LLM providers with **smart routing**, **semantic caching**, and **usage tracking** — essential infrastructure for production AI applications.

## What It Does

Single OpenAI-compatible API endpoint that routes requests to the best LLM provider (OpenAI, Anthropic, local models) based on cost, latency, or quality. Includes semantic caching to reduce costs and full usage tracking.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  API Gateway                      │
│  POST /v1/chat/completions (OpenAI-compatible)   │
├──────────┬──────────┬──────────┬─────────────────┤
│          │          │          │                  │
│  ┌───────▼──┐ ┌─────▼────┐ ┌──▼────────┐        │
│  │ Semantic │ │  Router  │ │  Usage    │        │
│  │ Cache    │ │ (cost/   │ │  Tracker  │        │
│  │          │ │ latency/ │ │           │        │
│  └──────────┘ │ quality) │ └───────────┘        │
│               └────┬─────┘                       │
│        ┌───────────┼───────────┐                 │
│  ┌─────▼───┐ ┌─────▼───┐ ┌────▼─────┐          │
│  │ OpenAI  │ │Anthropic│ │  Local   │          │
│  │ GPT-4o  │ │ Claude  │ │  Ollama  │          │
│  └─────────┘ └─────────┘ └──────────┘          │
└──────────────────────────────────────────────────┘
```

## Setup

```bash
cd llm-api-gateway
pip install -r requirements.txt
cp .env.example .env
# Add at least one provider API key
```

## Run

```bash
python main.py
# Gateway available at http://localhost:8002
```

## Demo Scenarios

### 1. List available models
```bash
curl http://localhost:8002/v1/models
```

### 2. Chat completion (auto-routing)
```bash
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "strategy": "cost"
  }'
```

### 3. Route by quality
```bash
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "strategy": "quality"
  }'
```

### 4. Check usage and costs
```bash
curl http://localhost:8002/usage
curl http://localhost:8002/cache/stats
```

## What You Learn

- **API Gateway Pattern**: Unified interface for multiple backends
- **Smart Routing**: Cost/latency/quality-based provider selection
- **Semantic Caching**: Reduce costs by caching similar queries
- **Usage Tracking**: Token counting, cost estimation, analytics
- **OpenAI Compatibility**: Standard API format for drop-in replacement
- **Provider Abstraction**: Clean interface for adding new LLM providers

## Commercial Applications

| Use Case | Description | Market |
|----------|-------------|--------|
| API Aggregation | Single endpoint for all LLM providers | AI infrastructure |
| Cost Optimization | Route to cheapest provider per query | Enterprise AI |
| Multi-Provider Fallback | Automatic failover between providers | Reliability |
| Usage Analytics | Track and optimize LLM spending | FinOps |
| White-label API | Resell LLM access with custom pricing | SaaS |

## Key Design Decisions

1. **OpenAI-compatible API** — drop-in replacement, works with existing tools
2. **Pluggable providers** — easy to add new LLM backends
3. **Semantic cache** — fuzzy matching catches paraphrased queries
4. **Strategy pattern** — swap routing logic per request
5. **JSONL logging** — append-only usage logs for analysis
