# AI知识体系实战项目集

> Hands-on projects that map directly to AI engineering knowledge domains

## 项目总览

| # | Project | Knowledge Domain | Difficulty | Time | Commercial Value |
|---|---------|-----------------|------------|------|-----------------|
| 1 | **rag-qa-bot** | RAG, Embeddings, Vector DB, LLM | ⭐⭐⭐ | 8h | Enterprise search, customer support |
| 2 | **agent-task-planner** | Agents, Tool Use, Planning, ReAct | ⭐⭐⭐⭐ | 10h | Autonomous workflows, copilots |
| 3 | **llm-api-gateway** | API Design, Rate Limiting, Caching | ⭐⭐ | 6h | LLM infrastructure, cost control |
| 4 | **model-finetune-demo** | Fine-tuning, LoRA, Training Pipeline | ⭐⭐⭐⭐ | 12h | Domain-specific models, vertical AI |
| 5 | **observability-dashboard** | Monitoring, WebSockets, Metrics | ⭐⭐⭐ | 8h | MLOps, production reliability |
| 6 | **ai-safety-guardrails** | Safety, PII, Content Filtering | ⭐⭐⭐ | 6h | Compliance, enterprise trust |

**Total estimated time: ~50 hours**

## 推荐学习顺序

```
1. llm-api-gateway        ← API基础，最容易上手
2. rag-qa-bot             ← 核心RAG技术，应用最广
3. observability-dashboard ← 生产监控必备
4. model-finetune-demo    ← 深入模型定制
5. agent-task-planner     ← Agent架构进阶
6. ai-safety-guardrails   ← 安全与合规（贯穿全程）
```

## 知识体系映射

| Knowledge Topic | Projects |
|----------------|----------|
| LLM API & Prompt Engineering | llm-api-gateway, rag-qa-bot |
| RAG & Vector Search | rag-qa-bot |
| Agent Architecture | agent-task-planner |
| Model Training & Fine-tuning | model-finetune-demo |
| Production MLOps | observability-dashboard, llm-api-gateway |
| AI Safety & Compliance | ai-safety-guardrails |
| WebSocket & Real-time | observability-dashboard |
| System Design & Scaling | llm-api-gateway, observability-dashboard |

## Quick Start

```bash
# Clone and pick any project
cd ~/projects/ai-knowledge-hub/small-projects
cd <project-name>
cp .env.example .env
pip install -r requirements.txt
python main.py  # or: uvicorn main:app --reload
```

Each project is self-contained with its own `requirements.txt`, `.env.example`, and `README.md`.

## Design Principles

- **Production-ready patterns** — not toy demos
- **Incremental complexity** — start simple, add features
- **Real commercial relevance** — each project solves a real business problem
- **Testable** — every project can be verified locally without external services
