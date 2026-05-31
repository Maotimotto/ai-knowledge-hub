# AI创作工坊 (AI Creator Workshop)

> Full-stack AI Content Creator SaaS Platform - A comprehensive learning project covering advanced AI engineering topics.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI创作工坊 Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Frontend   │    │  Mobile App  │    │  Third-party │              │
│  │  (Dashboard) │    │   (Future)   │    │  Webhooks    │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │   API Gateway   │  ← Rate Limiting, Auth, CORS    │
│                    │   (FastAPI)     │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         │                   │                   │                       │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌─────────▼──────┐               │
│  │  Video API   │  │ Knowledge    │  │  Comment API   │               │
│  │  /api/video  │  │ /api/kb      │  │  /api/comments │               │
│  └──────┬───────┘  └───────┬──────┘  └─────────┬──────┘               │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                           │
│              ┌──────────────▼──────────────┐                            │
│              │   Agent Orchestrator        │                            │
│              │   (Graph-based Workflow)    │                            │
│              │                             │                            │
│              │  ┌─────────┐ ┌───────────┐  │                            │
│              │  │ Video   │ │ Research  │  │                            │
│              │  │ Agent   │ │ Agent     │  │                            │
│              │  └────┬────┘ └─────┬─────┘  │                            │
│              │       │           │         │                            │
│              │  ┌────▼───────────▼──────┐  │                            │
│              │  │  Comment Agent        │  │                            │
│              │  └───────────────────────┘  │                            │
│              └──────────────┬──────────────┘                            │
│                             │                                           │
│    ┌────────────────────────┼────────────────────────┐                  │
│    │                        │                        │                  │
│  ┌─▼──────────┐   ┌────────▼───────┐   ┌─────────────▼──────┐         │
│  │  LLM       │   │  RAG Pipeline  │   │  Vector Store      │         │
│  │  Client    │   │  (Embed →      │   │  (ChromaDB)        │         │
│  │  (Multi-   │   │   Retrieve →   │   │                    │         │
│  │  Provider) │   │   Rerank →     │   │                    │         │
│  │            │   │   Generate)    │   │                    │         │
│  └────────────┘   └────────────────┘   └────────────────────┘         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Infrastructure Layer                          │   │
│  │                                                                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │   │
│  │  │PostgreSQL│ │  Redis   │ │Prometheus│ │    Grafana        │  │   │
│  │  │(Metadata)│ │ (Cache)  │ │(Metrics) │ │ (Dashboards)      │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Security & Observability                      │   │
│  │  JWT Auth │ Guardrails │ Rate Limiting │ Tracing │ Logging      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Knowledge Base Topics Covered

| Module | Topics | Files |
|--------|--------|-------|
| **Agent System** | Multi-agent orchestration, graph workflows, state management, human-in-the-loop | `backend/agents/` |
| **RAG Pipeline** | Embeddings, vector stores, hybrid retrieval, reranking, chain-of-thought | `backend/rag/` |
| **Model Inference** | Multi-provider LLM, streaming, token counting, quantization (GGUF/GPTQ) | `backend/inference/` |
| **AI Safety** | Prompt injection detection, content filtering, PII detection, guardrails | `backend/security/` |
| **Observability** | Prometheus metrics, OpenTelemetry tracing, structured logging, alerting | `backend/observability/` |
| **API Design** | FastAPI, REST, WebSocket, middleware, dependency injection | `backend/api/` |
| **Data Layer** | SQLAlchemy ORM, Pydantic schemas, multi-tenant architecture | `backend/models/` |
| **Fine-tuning** | LoRA/QLoRA, PEFT, data preparation, evaluation metrics | `fine_tuning/` |
| **Infrastructure** | Docker Compose, Redis caching, PostgreSQL, monitoring stack | Root configs |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- (Optional) NVIDIA GPU for local model inference

### Setup

```bash
# Clone and navigate
cd ~/projects/ai-knowledge-hub/big-project

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker-compose up -d

# Access the platform
# Frontend:  http://localhost:8080
# API Docs:  http://localhost:8000/docs
# Grafana:   http://localhost:3000
# Prometheus: http://localhost:9090
```

### Development (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

### Authentication
All endpoints require JWT Bearer token: `Authorization: Bearer <token>`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login, get JWT |
| `POST` | `/api/v1/video/generate` | Generate AI video |
| `GET` | `/api/v1/video/status/{id}` | Check video generation status |
| `POST` | `/api/v1/knowledge/query` | RAG Q&A query |
| `POST` | `/api/v1/knowledge/ingest` | Ingest documents |
| `GET` | `/api/v1/comments/{video_id}` | Get video comments |
| `POST` | `/api/v1/comments/analyze` | AI comment analysis |
| `POST` | `/api/v1/comments/respond` | Auto-generate response |
| `GET` | `/api/v1/admin/metrics` | Platform metrics |
| `GET` | `/api/v1/admin/users` | User management |
| `GET` | `/health` | Health check |

### Multi-tenant Headers
```
X-Org-ID: org_123
X-Team-ID: team_456
```

## Learning Guide

### 1. Start with Architecture
Read this README, then `docker-compose.yml` to understand the full stack.

### 2. API Layer (`backend/main.py`, `backend/api/`)
Learn FastAPI patterns: middleware, dependency injection, error handling, OpenAPI docs.

### 3. Agent System (`backend/agents/`)
Study the graph-based orchestrator — this is the core AI pattern. Each agent is a node, edges define routing.

### 4. RAG Pipeline (`backend/rag/`)
Understand the full retrieval chain: chunk → embed → store → retrieve → rerank → generate.

### 5. Model Inference (`backend/inference/`)
Multi-provider abstraction, streaming, fallback chains, quantization.

### 6. AI Safety (`backend/security/`)
Prompt injection detection, content guardrails, PII filtering — essential for production AI.

### 7. Observability (`backend/observability/`)
Metrics, traces, logs — the "three pillars" applied to AI systems.

### 8. Fine-tuning (`fine_tuning/`)
End-to-end pipeline: data prep → LoRA training → evaluation.

## Commercial Architecture

The platform follows SaaS best practices:

- **Multi-tenant**: Organization → Team → User hierarchy
- **Usage-based billing**: Token counting per API call, tracked in Redis
- **API-first**: Every feature has an API endpoint
- **Webhooks**: Event-driven integrations (video complete, comment flagged, etc.)

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Pydantic v2 |
| Agents | Custom graph orchestrator (LangGraph-inspired) |
| RAG | ChromaDB, sentence-transformers |
| LLM | OpenAI, Anthropic, llama.cpp, vLLM |
| Database | PostgreSQL (SQLAlchemy 2.0) |
| Cache | Redis |
| Monitoring | Prometheus, Grafana, OpenTelemetry |
| Container | Docker, Docker Compose |
| Frontend | Vanilla JS + HTML (SPA) |

## License

MIT - This is an educational project.
