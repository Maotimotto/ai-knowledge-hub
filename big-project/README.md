<div align="center">

# 🚀 AI创作工坊 (AI Creator Workshop)

### Full-Stack AI Content Creator SaaS Platform

> A **comprehensive learning project** covering every advanced AI engineering topic — from multi-agent orchestration to RAG pipelines, fine-tuning, and production observability.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License MIT](https://img.shields.io/badge/license-MIT-yellow.svg)
![Docker](https://img.shields.io/badge/docker-compose-blue.svg)

</div>

---

## 📖 Table of Contents

- [🏗️ System Architecture](#️-system-architecture)
- [🗺️ 知识库映射表 (Component → Knowledge Map)](#️-知识库映射表)
- [📚 Learning Guide (学习路线)](#-learning-guide)
- [📡 API Documentation](#-api-documentation)
- [💰 商业价值设计 (Business Model)](#-商业价值设计)
- [⚡ Quick Start](#-quick-start)
- [🛠️ Tech Stack](#️-tech-stack)

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────────────────────────────────┐
                        │                   CLIENT LAYER                      │
                        │                                                     │
                        │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │
                        │  │ Frontend  │  │ Mobile App│  │  Webhook      │   │
                        │  │ Dashboard │  │ (Future)  │  │  Consumers    │   │
                        │  └─────┬─────┘  └─────┬─────┘  └──────┬────────┘   │
                        └────────┼──────────────┼───────────────┼─────────────┘
                                 │              │               │
                                 ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Rate Limit  │  │  JWT Auth    │  │  CORS        │  │  Request Logging  │  │
│  │  (Redis)     │  │  (RBAC)      │  │  Middleware  │  │  (Structured)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────────┘  │
└────────────┬───────────────┬───────────────┬──────────────────┬────────────────┘
             │               │               │                  │
     ┌───────▼───────┐ ┌─────▼──────┐ ┌──────▼──────┐ ┌────────▼────────┐
     │  Video API    │ │ Knowledge  │ │ Comment API │ │  Admin API      │
     │  /api/video   │ │ /api/kb    │ │ /api/comment│ │  /api/admin     │
     │               │ │            │ │             │ │                 │
     │ • generate    │ │ • query    │ │ • analyze   │ │ • metrics       │
     │ • status      │ │ • ingest   │ │ • respond   │ │ • users         │
     │ • list        │ │ • search   │ │ • list      │ │ • billing       │
     └───────┬───────┘ └─────┬──────┘ └──────┬──────┘ └────────┬────────┘
             │               │               │                  │
             └───────────────┴───────┬───────┘──────────────────┘
                                     │
                ┌────────────────────▼────────────────────┐
                │        AGENT ORCHESTRATOR (Graph)       │
                │                                         │
                │   ┌──────────┐  ┌───────────────┐      │
                │   │  🎬 Video│  │  🔍 Research  │      │
                │   │  Agent   │  │  Agent        │      │
                │   │          │  │               │      │
                │   │ • script │  │ • web search  │      │
                │   │ • story  │  │ • summarize   │      │
                │   │ • edit   │  │ • fact check  │      │
                │   └────┬─────┘  └──────┬────────┘      │
                │        │               │                │
                │        ▼               ▼                │
                │   ┌──────────────────────────┐         │
                │   │  💬 Comment Agent        │         │
                │   │  • sentiment analysis    │         │
                │   │  • auto-reply generation │         │
                │   │  • spam detection        │         │
                │   └──────────────────────────┘         │
                │                                         │
                │   State Machine: Graph Nodes + Edges    │
                │   Conditional Routing · Human-in-Loop   │
                └────────────────────┬────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
┌──────────────────┐   ┌───────────────────────────┐   ┌──────────────────┐
│  INFERENCE LAYER │   │      RAG PIPELINE         │   │ SECURITY LAYER   │
│                  │   │                           │   │                  │
│  ┌────────────┐  │   │ Ingest ──▶ Chunk         │   │ ┌──────────────┐ │
│  │ OpenAI     │  │   │          ──▶ Embed        │   │ │ Prompt       │ │
│  │ GPT-4/3.5  │  │   │          ──▶ Store (Vec)  │   │ │ Injection    │ │
│  ├────────────┤  │   │          ──▶ Retrieve     │   │ │ Detection    │ │
│  │ Anthropic  │  │   │          ──▶ Rerank       │   │ ├──────────────┤ │
│  │ Claude     │  │   │          ──▶ Generate     │   │ │ Content      │ │
│  ├────────────┤  │   │                           │   │ │ Filtering    │ │
│  │ llama.cpp  │  │   │  Hybrid Search:           │   │ ├──────────────┤ │
│  │ GGUF/Local │  │   │  BM25 + Dense Vectors     │   │ │ PII          │ │
│  ├────────────┤  │   │  + Cross-Encoder Rerank    │   │ │ Detection    │ │
│  │ vLLM       │  │   │                           │   │ └──────────────┘ │
│  │ Production │  │   │  ┌─────┐ ┌────┐ ┌──────┐ │   │                  │
│  └────────────┘  │   │  │Chroma│ │Post│ │Redis │ │   │  Guardrails:     │
│                  │   │  │DB    │ │gres│ │Cache │ │   │  Input/Output    │
│  Fallback Chain: │   │  └─────┘ └────┘ └──────┘ │   │  Validation      │
│  OpenAI → Claude │   └───────────────────────────┘   └──────────────────┘
│  → Local → Error │
└──────────────────┘
                        ┌─────────────────────────────────────────────────────┐
                        │              OBSERVABILITY LAYER                    │
                        │                                                     │
                        │  ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ │
                        │  │ 📊 Metrics  │ │ 🔗 Tracing   │ │ 📝 Logging  │ │
                        │  │ Prometheus  │ │ OpenTelemetry│ │ Structured  │ │
                        │  │ • latency   │ │ • spans      │ │ • JSON      │ │
                        │  │ • tokens    │ │ • traces     │ │ • Correlated│ │
                        │  │ • errors    │ │ • propagation│ │ • Leveled   │ │
                        │  └──────┬──────┘ └──────┬───────┘ └──────┬──────┘ │
                        │         └───────────────┼────────────────┘         │
                        │                         ▼                          │
                        │              ┌──────────────────┐                  │
                        │              │     Grafana      │                  │
                        │              │   Dashboards     │                  │
                        │              └──────────────────┘                  │
                        └─────────────────────────────────────────────────────┘

                        ┌─────────────────────────────────────────────────────┐
                        │                DATA LAYER                          │
                        │                                                     │
                        │  ┌──────────────┐ ┌──────────┐ ┌───────────────┐  │
                        │  │  PostgreSQL  │ │  Redis   │ │   ChromaDB    │  │
                        │  │  • users     │ │  • cache │ │   • vectors   │  │
                        │  │  • content   │ │  • rate  │ │   • embeddings│  │
                        │  │  • analytics │ │  • queue │ │   • metadata  │  │
                        │  │  • billing   │ │  • pubsub│ │               │  │
                        │  └──────────────┘ └──────────┘ └───────────────┘  │
                        └─────────────────────────────────────────────────────┘
```

---

## 🗺️ 知识库映射表

> **每个文件都是一个知识入口** — 点击文件名，进入对应知识库主题深度学习。

| 组件文件 | 知识库主题 | 你会学到什么 |
|----------|----------|------------|
| `backend/config.py` | **配置管理**, Pydantic | Settings模式, 环境变量管理, 多环境配置 |
| `backend/main.py` | **FastAPI**, API设计 | 中间件链, 依赖注入, 生命周期管理, OpenAPI |
| `backend/agents/orchestrator.py` | **Agent开发**, LangGraph | 图状态机, 条件路由, 人机协同, 工作流编排 |
| `backend/agents/video_agent.py` | **Agent开发**, 内容生成 | 多步推理, 工具调用, 结构化输出 |
| `backend/agents/comment_agent.py` | **Agent开发**, NLP | 情感分析, 自动回复, 分类流水线 |
| `backend/agents/research_agent.py` | **Agent开发**, RAG集成 | Web搜索集成, 信息综合, 事实核查 |
| `backend/agents/tools.py` | **工具设计**, Function Calling | 工具注册, Schema定义, 错误处理 |
| `backend/rag/chain.py` | **RAG技术**, RAG高级模式 | 检索管道, 混合检索, 重排序, Chain-of-Thought |
| `backend/rag/retriever.py` | **RAG技术**, 检索策略 | BM25+Dense混合, 多查询检索, 上下文压缩 |
| `backend/rag/embeddings.py` | **向量嵌入**, 表征学习 | Sentence-Transformers, 嵌入模型选型, 批处理 |
| `backend/rag/vectorstore.py` | **向量数据库**, ChromaDB | 向量索引, 相似度搜索, 元数据过滤 |
| `backend/inference/llm_client.py` | **LLM推理**, 多Provider | 流式响应, 重试策略, Fallback链, Token计数 |
| `backend/inference/model_manager.py` | **模型管理**, MLOps | 模型注册, 版本管理, A/B测试路由 |
| `backend/inference/quantization.py` | **模型量化**, GGUF/GPTQ | 权重量化, 精度-性能权衡, 本地推理优化 |
| `backend/security/auth.py` | **认证授权**, JWT | JWT签发, RBAC权限, Token刷新, 多租户隔离 |
| `backend/security/guardrails.py` | **AI安全**, 护栏系统 | 注入检测, 内容过滤, 输入/输出校验 |
| `backend/security/rate_limiter.py` | **流控**, Redis | 令牌桶, 滑动窗口, 租户级配额 |
| `backend/observability/metrics.py` | **可观测性**, Prometheus | 自定义指标, Histogram, Counter, Label设计 |
| `backend/observability/tracing.py` | **可观测性**, OpenTelemetry | Span传播, Trace上下文, 分布式追踪 |
| `backend/observability/logger.py` | **可观测性**, 结构化日志 | JSON日志, 关联ID, 日志级别策略 |
| `backend/models/database.py` | **数据层**, SQLAlchemy 2.0 | ORM建模, 连接池, 迁移管理, 异步操作 |
| `backend/models/schemas.py` | **数据校验**, Pydantic v2 | Schema设计, 验证器, 嵌套模型, API契约 |
| `backend/api/video.py` | **API设计**, RESTful | CRUD模式, 异步任务, WebSocket进度推送 |
| `backend/api/knowledge.py` | **API设计**, RAG接口 | 查询优化, 分页, 结果缓存 |
| `backend/api/comment.py` | **API设计**, 批量操作 | 批处理, 流式响应, 异步队列 |
| `backend/api/admin.py` | **后台管理**, 运营 | 指标聚合, 用户管理, 审计日志 |
| `fine_tuning/prepare_data.py` | **微调**, 数据工程 | 数据清洗, 格式转换, 训练/验证集划分 |
| `fine_tuning/train.py` | **微调**, LoRA/QLoRA | PEFT训练, 超参调优, 梯度检查点, DeepSpeed |
| `fine_tuning/evaluate.py` | **微调**, 评估指标 | BLEU/ROUGE, 人工评估, 自动化评估流水线 |
| `tests/test_*.py` | **测试**, pytest | 单元测试, 集成测试, Mock策略, Fixtures |
| `docker-compose.yml` | **容器化**, DevOps | 多服务编排, 网络配置, Volume持久化 |
| `monitoring/prometheus.yml` | **监控**, Prometheus | 采集配置, 告警规则, 指标聚合 |
| `monitoring/grafana/` | **监控**, Grafana | 仪表盘设计, 变量模板, 告警通道 |

---

## 📚 Learning Guide

> **8阶段学习路线** — 从配置到部署，循序渐进掌握全栈AI工程。

### 🟢 Phase 1: 基础配置 (30 min)

```
📄 backend/config.py
```

从这里开始！理解 **Pydantic Settings** 模式 — 所有配置集中管理，环境变量自动绑定。

**关键概念:** `BaseSettings`, `.env` 加载, 多环境切换, 嵌套配置模型

```python
# 你会看到这样的模式
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: str
    class Config:
        env_file = ".env"
```

### 🟡 Phase 2: Agent 系统 (2-3 hours)

```
📄 backend/agents/orchestrator.py    ← 核心！先读这个
📄 backend/agents/video_agent.py
📄 backend/agents/comment_agent.py
📄 backend/agents/research_agent.py
📄 backend/agents/tools.py
```

**这是项目的核心。** 理解图状态机（Graph State Machine）如何编排多个AI Agent协作完成复杂任务。

**关键概念:** 状态图, 节点/边定义, 条件路由, 人机协同中断, 工具调用

### 🔴 Phase 3: RAG Pipeline (2-3 hours)

```
📄 backend/rag/chain.py             ← 全链路入口
📄 backend/rag/retriever.py          ← 检索策略
📄 backend/rag/embeddings.py         ← 向量化
📄 backend/rag/vectorstore.py        ← 存储与检索
```

理解完整的 **检索增强生成** 流程：文档分块 → 向量嵌入 → 存储 → 混合检索 → 重排序 → 生成。

**关键概念:** Chunking策略, Hybrid Search (BM25 + Dense), Cross-Encoder Rerank, Context Window管理

### 🟣 Phase 4: 推理层 (1-2 hours)

```
📄 backend/inference/llm_client.py
📄 backend/inference/model_manager.py
📄 backend/inference/quantization.py
```

**多Provider抽象** — 一套接口对接 OpenAI、Anthropic、本地模型，带自动Fallback。

**关键概念:** Provider抽象, 流式SSE, Token计费, GGUF/GPTQ量化, 模型路由

### 🟠 Phase 5: AI 安全 (1 hour)

```
📄 backend/security/auth.py
📄 backend/security/guardrails.py
📄 backend/security/rate_limiter.py
```

**生产级AI安全** — 防注入、内容过滤、PII检测、速率限制。

**关键概念:** JWT + RBAC, Prompt Injection检测, Guardrails输入/输出校验, 令牌桶限流

### 🔵 Phase 6: 可观测性 (1 hour)

```
📄 backend/observability/metrics.py
📄 backend/observability/tracing.py
📄 backend/observability/logger.py
```

**AI系统的三大支柱** — Metrics、Traces、Logs，全部为AI场景定制。

**关键概念:** Prometheus自定义指标, OpenTelemetry Span传播, 结构化JSON日志

### ⚫ Phase 7: 模型微调 (Hands-on, 3-4 hours)

```
📄 fine_tuning/prepare_data.py      ← 数据准备
📄 fine_tuning/train.py             ← LoRA训练
📄 fine_tuning/evaluate.py          ← 评估
```

**动手实战！** 准备数据 → LoRA微调 → 评估效果。需要GPU环境。

```bash
cd fine_tuning
python prepare_data.py   # 清洗数据，生成训练集
python train.py          # 启动LoRA训练
python evaluate.py       # 自动评估
```

### 🟤 Phase 8: 全栈集成 (1 hour)

```bash
docker-compose up -d
```

一键启动全部服务，观察各组件如何协同工作。打开 Grafana 查看实时指标。

**验证清单:**
- [ ] 访问 `http://localhost:8080` — 前端仪表盘
- [ ] 访问 `http://localhost:8000/docs` — API文档 (Swagger)
- [ ] 访问 `http://localhost:3000` — Grafana监控面板
- [ ] 发送一个 `/api/v1/video/generate` 请求 — 看Agent编排
- [ ] 发送一个 `/api/v1/knowledge/query` 请求 — 看RAG流程

---

## 📡 API Documentation

### 🔐 认证方式

所有端点需要 JWT Bearer Token：

```http
Authorization: Bearer <your_jwt_token>
```

多租户请求额外Header：

```http
X-Org-ID: org_123
X-Team-ID: team_456
```

---

### 📋 端点总览

| Method | Endpoint | 描述 | Auth |
|--------|----------|------|------|
| `POST` | `/api/v1/auth/register` | 用户注册 | ❌ |
| `POST` | `/api/v1/auth/login` | 登录获取JWT | ❌ |
| `POST` | `/api/v1/video/generate` | AI视频生成 | ✅ |
| `GET` | `/api/v1/video/status/{id}` | 查询生成进度 | ✅ |
| `GET` | `/api/v1/video/list` | 视频列表 | ✅ |
| `POST` | `/api/v1/knowledge/query` | RAG知识问答 | ✅ |
| `POST` | `/api/v1/knowledge/ingest` | 文档入库 | ✅ |
| `GET` | `/api/v1/knowledge/search` | 向量搜索 | ✅ |
| `POST` | `/api/v1/comments/analyze` | 评论AI分析 | ✅ |
| `POST` | `/api/v1/comments/respond` | 自动生成回复 | ✅ |
| `GET` | `/api/v1/comments/{video_id}` | 获取评论列表 | ✅ |
| `GET` | `/api/v1/admin/metrics` | 平台指标 | ✅ Admin |
| `GET` | `/api/v1/admin/users` | 用户管理 | ✅ Admin |
| `GET` | `/health` | 健康检查 | ❌ |

---

### 📝 请求/响应示例

#### POST `/api/v1/video/generate`

```json
// Request
{
  "topic": "AI在医疗领域的应用",
  "style": "educational",
  "duration": 300,
  "language": "zh-CN",
  "voice": "alloy"
}

// Response 202 Accepted
{
  "id": "vid_abc123",
  "status": "processing",
  "estimated_time": 120,
  "progress_url": "/api/v1/video/status/vid_abc123"
}
```

#### POST `/api/v1/knowledge/query`

```json
// Request
{
  "question": "LoRA微调和全量微调有什么区别？",
  "top_k": 5,
  "rerank": true,
  "stream": false
}

// Response 200 OK
{
  "answer": "LoRA（Low-Rank Adaptation）通过在预训练模型的注意力层...",
  "sources": [
    {"doc_id": "doc_001", "chunk": "LoRA核心思想是...", "score": 0.94},
    {"doc_id": "doc_002", "chunk": "相比全量微调...", "score": 0.89}
  ],
  "usage": {"prompt_tokens": 1250, "completion_tokens": 340, "total": 1590}
}
```

#### POST `/api/v1/comments/analyze`

```json
// Request
{
  "video_id": "vid_abc123",
  "analysis_type": ["sentiment", "topics", "spam"],
  "limit": 100
}

// Response 200 OK
{
  "total_comments": 87,
  "sentiment": {"positive": 62, "neutral": 18, "negative": 7},
  "top_topics": ["AI医疗", "深度学习", "数据隐私"],
  "spam_count": 3,
  "insights": "观众对AI辅助诊断部分关注度最高..."
}
```

#### GET `/api/v1/admin/metrics`

```json
// Response 200 OK
{
  "active_users": 1247,
  "api_calls_today": 15680,
  "total_tokens_used": 2450000,
  "avg_latency_ms": 850,
  "error_rate": 0.002,
  "revenue_today_cents": 45600,
  "top_endpoints": [
    {"path": "/api/v1/knowledge/query", "calls": 8920},
    {"path": "/api/v1/video/generate", "calls": 3200}
  ]
}
```

---

## 💰 商业价值设计

### 💎 SaaS 定价方案

| 功能 | 🆓 Free | ⭐ Pro ($29/月) | 🏢 Enterprise (定制) |
|------|---------|----------------|---------------------|
| API调用 | 100次/天 | 10,000次/天 | 无限 |
| 视频生成 | 5个/月 | 200个/月 | 无限 |
| 知识库容量 | 10MB | 5GB | 无限 |
| RAG检索 | 基础 | 混合检索+重排序 | 定制模型 |
| Agent数量 | 1个 | 5个 | 无限 |
| 微调模型 | ❌ | 2个/月 | 无限 |
| SLA | ❌ | 99.5% | 99.99% |
| 支持 | 社区 | 邮件 | 专属客户经理 |

### 📊 API 用量计费

```
Token定价:
├── GPT-4o:     $0.005 / 1K input  |  $0.015 / 1K output
├── Claude 3.5: $0.003 / 1K input  |  $0.015 / 1K output
├── 本地模型:    $0.001 / 1K input  |  $0.002 / 1K output
└── 嵌入模型:    $0.0001 / 1K tokens

额外计费:
├── 视频生成:   $0.50 / 分钟
├── RAG检索:    $0.002 / 次 (含重排序)
└── 微调训练:   $2.00 / GPU小时
```

### 🏗️ 企业级增值功能

- **私有部署**: 支持客户自有云环境部署 (AWS/Azure/GCP)
- **自定义模型**: 接入客户私有LLM，数据不出域
- **合规审计**: SOC2 / GDPR / 数据审计日志
- **SLA保障**: 99.99%可用性，专属技术支持
- **SSO集成**: SAML/OIDC单点登录
- **多Region部署**: 全球低延迟访问

---

## ⚡ Quick Start

> **3条命令，启动一切。**

```bash
# 1️⃣ 克隆并配置
cd ~/projects/ai-knowledge-hub/big-project && cp .env.example .env && nano .env

# 2️⃣ 启动全部服务
docker-compose up -d

# 3️⃣ 验证运行
curl http://localhost:8000/health
```

**访问地址：**

| 服务 | 地址 | 用途 |
|------|------|------|
| 🖥️ 前端仪表盘 | `http://localhost:8080` | 用户界面 |
| 📡 API 文档 | `http://localhost:8000/docs` | Swagger UI |
| 📊 Grafana | `http://localhost:3000` | 监控面板 |
| 📈 Prometheus | `http://localhost:9090` | 指标查询 |

### 本地开发 (不用Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🛠️ Tech Stack

| 层级 | 技术 | 说明 |
|------|------|------|
| 🎨 Frontend | Vanilla JS + HTML | 轻量SPA |
| 🚀 API | FastAPI + Pydantic v2 | 高性能异步API |
| 🤖 Agents | 自研Graph Orchestrator | LangGraph风格状态机 |
| 🔍 RAG | ChromaDB + sentence-transformers | 向量检索 + 重排序 |
| 🧠 LLM | OpenAI / Anthropic / llama.cpp / vLLM | 多Provider Fallback |
| 🗄️ Database | PostgreSQL (SQLAlchemy 2.0) | 关系型存储 |
| ⚡ Cache | Redis | 缓存 + 限流 + 消息队列 |
| 📊 Monitoring | Prometheus + Grafana + OpenTelemetry | 全链路可观测 |
| 🔒 Security | JWT + Guardrails | 认证 + AI安全护栏 |
| 🏋️ Fine-tuning | LoRA / QLoRA / PEFT | 模型微调 |
| 📦 Infra | Docker + Docker Compose | 容器化部署 |

---

## 📂 Project Structure

```
big-project/
├── backend/
│   ├── main.py                    # 🚀 FastAPI 应用入口
│   ├── config.py                  # ⚙️  全局配置 (Pydantic Settings)
│   ├── api/                       # 📡 API 路由层
│   │   ├── video.py               #    视频生成接口
│   │   ├── knowledge.py           #    RAG 知识问答接口
│   │   ├── comment.py             #    评论分析接口
│   │   └── admin.py               #    管理后台接口
│   ├── agents/                    # 🤖 Agent 编排层
│   │   ├── orchestrator.py        #    图状态机编排器
│   │   ├── video_agent.py         #    视频生成 Agent
│   │   ├── comment_agent.py       #    评论分析 Agent
│   │   ├── research_agent.py      #    研究检索 Agent
│   │   └── tools.py               #    Agent 工具集
│   ├── rag/                       # 🔍 RAG 管道
│   │   ├── chain.py               #    完整检索生成链
│   │   ├── retriever.py           #    混合检索策略
│   │   ├── embeddings.py          #    向量嵌入
│   │   └── vectorstore.py         #    向量存储
│   ├── inference/                 # 🧠 推理层
│   │   ├── llm_client.py          #    多Provider LLM客户端
│   │   ├── model_manager.py       #    模型路由管理
│   │   └── quantization.py        #    模型量化
│   ├── security/                  # 🔒 安全层
│   │   ├── auth.py                #    JWT 认证
│   │   ├── guardrails.py          #    AI 护栏
│   │   └── rate_limiter.py        #    速率限制
│   ├── observability/             # 📊 可观测性
│   │   ├── metrics.py             #    Prometheus 指标
│   │   ├── tracing.py             #    OpenTelemetry 追踪
│   │   └── logger.py              #    结构化日志
│   └── models/                    # 🗄️ 数据模型
│       ├── database.py            #    SQLAlchemy ORM
│       └── schemas.py             #    Pydantic Schemas
├── frontend/                      # 🎨 前端
│   ├── index.html
│   └── server.py
├── fine_tuning/                   # 🏋️ 模型微调
│   ├── prepare_data.py
│   ├── train.py
│   └── evaluate.py
├── monitoring/                    # 📈 监控配置
│   ├── prometheus.yml
│   ├── alerting.yml
│   └── grafana/
├── tests/                         # 🧪 测试
│   ├── test_api.py
│   ├── test_agents.py
│   └── test_rag.py
└── docker-compose.yml             # 🐳 编排配置
```

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

*Built for learning. Built for production. Built for the future of AI engineering.*

[![GitHub Stars](https://img.shields.io/github/stars/Maotimotto/ai-knowledge-hub?style=social)](https://github.com/Maotimotto/ai-knowledge-hub)

**License:** MIT

</div>
