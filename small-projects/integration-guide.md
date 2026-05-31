# Integration Guide — AI Knowledge Hub Small Projects

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         AI-Safety-Guardrails         │
                    │           (middleware :8004)          │
                    └──────┬──────────────┬───────────────┘
                           │              │
              ┌────────────▼──┐    ┌──────▼────────────┐
              │  LLM-API-     │    │   Observability    │
              │  Gateway      │    │   Dashboard        │
              │  (:8000)      │    │   (:8003)          │
              └──┬────────┬───┘    └────────────────────┘
                 │        │               ▲  ▲  ▲
      ┌──────────▼──┐  ┌──▼──────────┐   │  │  │  metrics from all services
      │  RAG-QA-Bot │  │ Agent-Task- │   │  │  │
      │  (:8001)    │  │ Planner     │───┘  │  │
      └─────────────┘  │ (:8002)     │──────┘  │
                       └─────────────┘         │
                                               │
                       ┌───────────────────┐   │
                       │ Model-Finetune-   │───┘
                       │ Demo (no port)    │
                       └───────────────────┘
```

## How the Projects Connect

### 1. LLM-API-Gateway (Central API Layer)
The gateway is the single entry point for all LLM calls. Both **rag-qa-bot** and **agent-task-planner** route their inference requests through it. Benefits:
- Unified authentication and rate limiting
- Provider abstraction (OpenAI, Anthropic, Ollama)
- Centralized token counting and cost tracking

### 2. AI-Safety-Guardrails (Middleware)
Sits as a middleware layer in front of any project. Intercepts requests and responses to:
- Detect and redact PII (emails, SSNs, credit cards)
- Block prompt injection attempts
- Filter toxic or harmful content
- Log all safety events

### 3. Observability-Dashboard (Monitoring)
Collects metrics, logs, and traces from all running services:
- Request latency and throughput
- Token usage and cost breakdowns
- Error rates and safety guardrail triggers
- Real-time dashboards

### 4. RAG-QA-Bot
A retrieval-augmented generation chatbot. Uses the gateway for LLM calls, guardrails for safety, and reports metrics to observability.

### 5. Agent-Task-Planner
Breaks complex tasks into sub-tasks and orchestrates execution. Uses the gateway for planning LLM calls.

### 6. Model-Finetune-Demo
Demonstrates fine-tuning workflows. Uses demo training data and reports training metrics to observability.

## Step-by-Step: Running the Stack

### Prerequisites
- Docker & Docker Compose
- API keys for at least one LLM provider (or Ollama running locally)

### Quick Start

```bash
# 1. Clone and navigate to the project
cd ~/projects/ai-knowledge-hub/small-projects

# 2. Set environment variables
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Start the full stack
docker compose up -d

# 4. Verify services are healthy
curl http://localhost:8000/health   # Gateway
curl http://localhost:8001/health   # RAG Bot
curl http://localhost:8002/health   # Agent Planner
curl http://localhost:8003/health   # Observability
curl http://localhost:8004/health   # Guardrails

# 5. Test a request through the gateway
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"Hello!"}]}'

# 6. Open the observability dashboard
open http://localhost:8003
```

### Running Individual Projects

```bash
# Run just the gateway
cd llm-api-gateway && pip install -r requirements.txt && python main.py

# Run the RAG bot (requires gateway running)
cd rag-qa-bot && pip install -r requirements.txt && python main.py

# Run benchmarks
cd rag-qa-bot && python benchmark.py
```

### Connecting a New Project to the Gateway

1. Point your LLM client to `http://localhost:8000` instead of the provider directly
2. Add the guardrails middleware to your request pipeline
3. Emit metrics in Prometheus format to `http://localhost:8003/metrics`

## Environment Variables

| Variable | Description | Required By |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | OpenAI API key | gateway, rag-bot, planner |
| `ANTHROPIC_API_KEY` | Anthropic API key | gateway |
| `OLLAMA_BASE_URL` | Ollama endpoint (default: http://ollama:11434) | gateway |
| `GUARDRAILS_URL` | Guardrails service URL | all (as middleware) |
| `OBSERVABILITY_URL` | Metrics endpoint | all (for reporting) |
| `VECTOR_DB_URL` | ChromaDB/Pinecone URL | rag-bot |

## Troubleshooting

- **Gateway returns 502**: Check that the target LLM provider is reachable and API key is valid
- **Guardrails blocking safe content**: Adjust threshold in `ai-safety-guardrails/config.yaml`
- **High latency**: Check observability dashboard for bottleneck; likely LLM provider response time
- **Metrics not showing**: Verify all services have `OBSERVABILITY_URL` configured correctly
