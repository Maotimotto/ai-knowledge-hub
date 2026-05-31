# AI知识体系实战项目集

> 6个生产级实战项目，覆盖AI工程核心知识域，每个项目都可独立运行

## 项目总览

| # | Project | 知识域 | 难度 | 时间 | 商业价值 |
|---|---------|--------|------|------|----------|
| 1 | **rag-qa-bot** | RAG, Embeddings, Vector DB, LLM | ⭐⭐⭐ | 8h | 企业搜索、客服自动化 |
| 2 | **agent-task-planner** | Agents, Tool Use, Planning, ReAct | ⭐⭐⭐⭐ | 10h | 自主工作流、AI Copilot |
| 3 | **llm-api-gateway** | API Design, Rate Limiting, Caching | ⭐⭐ | 6h | LLM基础设施、成本控制 |
| 4 | **model-finetune-demo** | Fine-tuning, LoRA, Training Pipeline | ⭐⭐⭐⭐ | 12h | 领域模型、垂直AI |
| 5 | **observability-dashboard** | Monitoring, WebSockets, Metrics | ⭐⭐⭐ | 8h | MLOps、生产可靠性 |
| 6 | **ai-safety-guardrails** | Safety, PII, Content Filtering | ⭐⭐⭐ | 6h | 合规、企业信任 |

**总预估时间: ~50小时**

---

## 学习路径图 (Learning Path)

```
 推荐学习顺序（由易到难，箭头表示依赖关系）

 ┌─────────────────┐
 │  llm-api-gateway │  ← 起点：API基础，最容易上手
 │  (⭐⭐ 6h)       │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │   rag-qa-bot    │  ← 核心：RAG是AI应用最广范式
 │  (⭐⭐⭐ 8h)     │
 └────────┬────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌──────────┐  ┌──────────────────┐
│observ-   │  │ model-finetune   │
│ability   │  │ demo             │
│dashboard │  │ (⭐⭐⭐⭐ 12h)     │
│(⭐⭐⭐ 8h)│  │                  │
└────┬─────┘  └────────┬─────────┘
     │                 │
     └────────┬────────┘
              ▼
     ┌─────────────────┐
     │ agent-task      │  ← 进阶：Agent架构综合能力
     │ planner         │
     │ (⭐⭐⭐⭐ 10h)    │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ ai-safety       │  ← 贯穿全程的安全意识
     │ guardrails      │
     │ (⭐⭐⭐ 6h)      │
     └─────────────────┘
```

**路径说明：**
- **阶段1** (入门): `llm-api-gateway` → 理解LLM API调用、路由、缓存基础
- **阶段2** (核心): `rag-qa-bot` → 掌握最核心的RAG范式
- **阶段3** (生产): `observability-dashboard` + `model-finetune-demo` → 并行学习监控与训练
- **阶段4** (进阶): `agent-task-planner` → Agent架构综合应用
- **贯穿**: `ai-safety-guardrails` → 任何时候都可以学，建议在每个项目中集成安全检查

---

## 跨项目集成指南 (Cross-Project Integration)

这些项目不是孤立的，它们可以组合成完整的AI系统：

### 集成方案1: RAG + Gateway + Monitoring
```
用户 → llm-api-gateway(路由+缓存) → rag-qa-bot(检索+生成) → observability-dashboard(监控)
```
- 将rag-qa-bot中的OpenAI调用替换为通过llm-api-gateway
- 所有请求经过gateway路由和缓存
- observability-dashboard监控整个链路

### 集成方案2: Agent + RAG + Safety
```
用户 → agent-task-planner(规划) → rag-qa-bot(知识检索) → ai-safety-guardrails(安全检查)
```
- Agent在规划过程中调用RAG检索知识
- 所有输入/输出经过安全护栏过滤

### 集成方案3: 全栈AI应用
```
用户输入 → ai-safety-guardrails(输入检查)
         → llm-api-gateway(路由选择)
         → agent-task-planner(任务分解)
         → rag-qa-bot(知识检索)
         → model-finetune-demo(领域模型生成)
         → ai-safety-guardrails(输出检查)
         → observability-dashboard(全链路监控)
```

### 集成代码示例
```python
# 在rag-qa-bot中使用llm-api-gateway替代直接OpenAI调用
import httpx

def generate_answer(question: str, context: str) -> str:
    resp = httpx.post("http://localhost:8002/v1/chat/completions", json={
        "messages": [
            {"role": "system", "content": "基于上下文回答问题"},
            {"role": "user", "content": f"上下文：{context}\n问题：{question}"}
        ],
        "strategy": "cost"  # 按成本路由
    })
    return resp.json()["choices"][0]["message"]["content"]
```

---

## 技能进阶矩阵 (Skill Progression Matrix)

| 技能维度 | 入门项目 | 核心项目 | 进阶项目 |
|----------|---------|---------|---------|
| **LLM API调用** | llm-api-gateway | rag-qa-bot | agent-task-planner |
| **检索增强生成(RAG)** | — | rag-qa-bot | agent-task-planner |
| **Agent架构** | — | — | agent-task-planner |
| **模型微调** | — | — | model-finetune-demo |
| **向量数据库** | — | rag-qa-bot | model-finetune-demo |
| **API设计** | llm-api-gateway | rag-qa-bot | agent-task-planner |
| **缓存策略** | llm-api-gateway | — | — |
| **WebSocket实时** | — | — | observability-dashboard |
| **监控告警** | — | — | observability-dashboard |
| **安全防护** | — | — | ai-safety-guardrails |
| **正则表达式** | — | — | ai-safety-guardrails |
| **系统设计** | llm-api-gateway | rag-qa-bot | observability-dashboard |
| **商业思维** | 所有项目均包含商业价值分析和市场策略 |

---

## 知识体系映射

| 知识主题 | 涉及项目 |
|----------|----------|
| LLM API & 提示工程 | llm-api-gateway, rag-qa-bot |
| RAG & 向量搜索 | rag-qa-bot |
| Agent架构 | agent-task-planner |
| 模型训练 & 微调 | model-finetune-demo |
| 生产MLOps | observability-dashboard, llm-api-gateway |
| AI安全 & 合规 | ai-safety-guardrails |
| WebSocket & 实时通信 | observability-dashboard |
| 系统设计 & 扩展 | llm-api-gateway, observability-dashboard |

---

## Quick Start

```bash
# 克隆仓库
git clone git@github.com:Maototto/ai-knowledge-hub.git
cd ai-knowledge-hub/small-projects

# 选择一个项目开始
cd <project-name>
cp .env.example .env
pip install -r requirements.txt
python main.py  # 或: uvicorn main:app --reload
```

每个项目都是自包含的，有独立的 `requirements.txt`、`.env.example` 和 `README.md`。

---

## 设计原则

- **生产级模式** — 不是玩具demo，每个项目使用真实生产中的设计模式
- **渐进复杂度** — 从简单开始，逐步添加特性
- **真实商业价值** — 每个项目解决真实商业问题，附带市场分析
- **可本地验证** — 所有项目无需外部服务即可在本地运行验证
- **代码即文档** — 每个README包含完整代码走读，讲解设计决策
