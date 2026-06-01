# LLM API Gateway (LLM推理网关)

> 统一的LLM API网关，支持智能路由、语义缓存和用量追踪

## 项目简介

单一OpenAI兼容API端点，将请求路由到最佳LLM提供商（OpenAI、Anthropic、本地模型），支持按成本、延迟或质量自动选择。语义缓存降低重复查询成本，完整用量追踪支持FinOps分析。

## 架构图

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

---

## 代码走读 (Code Walkthrough)

### `main.py` — FastAPI网关入口

实现OpenAI兼容的`/v1/chat/completions`端点。请求流程：**检查缓存 → 路由到提供商 → 记录用量 → 缓存结果**。还提供`/v1/models`、`/v1/providers`、`/usage`、`/cache/stats`等管理端点。所有组件（Router、SemanticCache、UsageTracker）在启动时初始化。

- **关键类**: `ChatRequest`(请求模型), `ChatResponse`(响应模型，含provider/cached字段)
- **设计模式**: OpenAI兼容接口、中间件式请求处理流水线

### `router.py` — 智能路由引擎

实现四种路由策略：**cost**(选最便宜)、**latency**(选最快)、**quality**(选最强模型)、**round-robin**(轮询)。`Router.route()`方法根据策略选择最佳provider/model组合。quality策略使用硬编码的质量排序（GPT-4o > Claude Sonnet > GPT-4o-mini > ...）。latency策略维护历史延迟记录做滑动平均。

- **关键类**: `Router` — 策略模式路由器
- **核心模式**: 策略模式(Strategy Pattern)、延迟历史追踪、provider自动发现

### `providers.py` — LLM提供商抽象层

定义`BaseProvider`抽象基类和三个具体实现：`OpenAIProvider`(调用OpenAI SDK)、`AnthropicProvider`(调用Anthropic REST API)、`LocalProvider`(调用Ollama本地模型)。每个Provider实现`complete()`、`is_available()`、`get_models()`、`cost_per_1k_tokens`。`LLMResponse`统一响应格式，包含内容、token数、延迟等。

- **关键类**: `BaseProvider`(抽象基类), `LLMResponse`(统一响应)
- **核心模式**: 抽象工厂模式、Provider插件化、接口统一化

### `cache.py` — 语义缓存

实现查询结果缓存，支持精确匹配和模糊匹配。精确匹配使用SHA256哈希，模糊匹配使用**Jaccard相似度**(词集重叠)。TTL过期自动清除，LRU策略淘汰最不常访问的条目。缓存统计包括命中率、大小等。

- **关键类**: `SemanticCache` — 带TTL和LRU的语义缓存
- **核心模式**: 精确+模糊双重匹配、TTL过期策略、LRU淘汰、Jaccard相似度

### `usage.py` — 用量追踪与成本分析

`UsageTracker`记录每次请求的token数、成本、延迟，写入JSONL日志文件。`get_session_summary()`按provider和model维度聚合统计。`compute_cost()`根据provider定价计算费用。`get_daily_summary()`从日志文件读取历史数据按天汇总。

- **关键类**: `UsageTracker` — 用量记录与分析
- **核心模式**: JSONL追加日志、多维聚合分析、FinOps成本追踪

---

## 运行示例 (Run Examples)

```bash
# 安装依赖
cd llm-api-gateway
pip install -r requirements.txt

# 配置API Key（至少一个）
cp .env.example .env
# 编辑 .env: OPENAI_API_KEY=sk-xxx 或 ANTHROPIC_API_KEY=sk-ant-xxx

# 启动网关
python main.py
# 服务地址: http://localhost:8002

# 查看可用模型
curl http://localhost:8002/v1/models
# 预期输出: {"models": [{"id": "gpt-4o", "provider": "openai", "available": true, "cost_per_1k": 0.01}, ...]}

# 按成本路由（自动选最便宜的）
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is 2+2?"}], "strategy": "cost"}'
# 预期输出: {"model": "gpt-4o-mini", "provider": "openai", "choices": [...], "latency_ms": 823.45, "cached": false}

# 按质量路由（自动选最强模型）
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Explain quantum computing"}], "strategy": "quality"}'

# 重复查询（命中缓存）
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is 2+2?"}], "strategy": "cost"}'
# 预期输出: ... "cached": true

# 查看用量统计
curl http://localhost:8002/usage
# 预期输出: {"total_requests": 3, "total_tokens": 450, "total_cost_usd": 0.0012, ...}

# 查看缓存统计
curl http://localhost:8002/cache/stats
# 预期输出: {"size": 2, "hits": 1, "misses": 2, "hit_rate": 0.333}
```

---

## 知识映射 (Knowledge Mapping)

**本项目演示的知识点：**
- API网关设计模式（统一接口、Provider抽象）
- 策略路由（成本/延迟/质量/轮询）
- 语义缓存（精确匹配 + 模糊匹配）
- 用量追踪与成本分析（FinOps）
- OpenAI兼容API标准

**前置知识：**
- Python基础、FastAPI
- HTTP API设计
- 基本的LLM API使用经验

## Dashboard

A visual overview of providers, models, routing strategies, and sample requests is available at [`dashboard.html`](dashboard.html). Open it directly in any browser.

**进阶方向：**
- 完成本项目后 → 用此网关替换 `rag-qa-bot` 中的OpenAI直接调用
- 深入 → 添加流式响应(Streaming)、请求队列、限流
- 生产化 → `observability-dashboard`（监控网关指标）

**相关知识库文件：**
- `knowledge-base/01-llm-basics/` — LLM API使用
- `knowledge-base/09-infrastructure/` — AI基础设施设计
- `knowledge-base/10-optimization/` — 成本优化策略

---

## 商业价值扩展 (Commercial Value Extensions)

**目标客户：**
- AI应用开发团队（统一API管理）
- 企业IT部门（LLM成本控制）
- AI SaaS公司（多模型供应商管理）

**定价模型：**
- 开源免费 → 企业增值版$5,000/月（含限流、审计、SSO）
- 托管网关: 请求量的5-10%抽成
- 企业私有部署: $50,000/年起

**竞品对比：**

| 特性 | 本项目 | LiteLLM | Portkey | Martian |
|------|--------|---------|---------|---------|
| 开源 | ✅ | ✅ | 部分 | ❌ |
| 语义缓存 | ✅ | ❌ | ✅ | ✅ |
| 智能路由 | ✅ | ✅ | ✅ | ✅ |
| 轻量级 | ✅ | ❌ | ❌ | ❌ |
| 本地运行 | ✅ | ✅ | ❌ | ❌ |

**市场进入策略：**
1. 开源核心 → 开发者社区 → 企业版增值
2. 作为AI应用的基础设施层嵌入
3. 与云厂商合作（AWS/Azure Marketplace）

---

## 进阶挑战 (Advanced Challenges)

### 🟢 挑战1 (初级): 添加流式响应(Streaming)
为`/v1/chat/completions`添加`stream: true`支持，使用SSE(Server-Sent Events)逐token返回结果。
- **学习目标**: SSE流式传输、OpenAI流式API格式
- **提示**: 使用FastAPI的`StreamingResponse`，格式为`data: {"choices": [{"delta": {"content": "..."}}]}\n\n`

### 🟡 挑战2 (中级): 实现基于嵌入的语义缓存
将当前的Jaccard词重叠替换为真正的向量语义相似度，使用`sentence-transformers`编码查询后在向量空间中匹配。
- **学习目标**: 向量相似度检索、语义缓存进阶
- **提示**: 维护一个查询向量索引，新查询编码后做余弦相似度匹配

### 🔴 挑战3 (高级): 实现请求级限流(Rate Limiting)
添加基于Token Bucket算法的限流机制，支持按API Key、按用户、按模型分别限流。
- **学习目标**: 限流算法、多级限流、Redis分布式计数
- **提示**: 实现Token Bucket，使用Redis INCR做分布式计数，按`X-RateLimit-*`头返回状态
