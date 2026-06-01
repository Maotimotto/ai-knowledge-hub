# RAG Q&A Bot (RAG知识问答)

> 基于检索增强生成的文档问答系统，生产级RAG管线的完整实现

## 项目简介

上传文档（PDF/Markdown/TXT），用自然语言提问，获取带引用源的答案。采用**混合检索**策略：BM25关键词匹配 + Dense语义向量，通过权重融合获得最优结果。

## 架构图

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Document     │    │   Chunker    │    │  Embedder    │
│  Loader       │───▶│  (500 chars) │───▶│ (MiniLM)     │
│  PDF/MD/TXT   │    │  + overlap   │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │  ChromaDB    │
                                        │  Vector Store│
                                        └──────┬───────┘
                                               │
┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐
│  FastAPI      │◀──│  LLM Answer  │◀──│  Hybrid      │
│  /ask         │    │  Generator   │    │  Retriever   │
│  Endpoint     │    │  (OpenAI)    │    │  BM25+Dense  │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 代码走读 (Code Walkthrough)

### `main.py` — FastAPI应用入口

提供文档问答的HTTP接口，包括文档上传(`/ingest`)、问答(`/ask`)和统计(`/stats`)端点。展示了**懒初始化**模式：`get_store()`和`get_retriever()`使用全局单例，首次调用时才创建实例。`_generate_answer()`实现了**优雅降级**——有OpenAI Key时调用GPT生成答案，无Key时返回检索到的原文作为兜底。

- **关键类/函数**: `AskRequest`(请求模型), `AskResponse`(响应模型), `lifespan`(生命周期管理)
- **设计模式**: 懒加载单例、策略模式（LLM vs 本地抽取）、Pydantic数据验证

### `retriever.py` — 混合检索器

展示**混合检索模式**：BM25(关键词) + Dense(语义)，通过加权融合两路结果。`HybridRetriever`类维护两套索引——BM25使用`rank_bm25`库的Okapi算法，Dense使用`SentenceTransformer`编码后在ChromaDB中做余弦相似度搜索。`alpha`参数控制两路权重：`alpha=0.0`为纯关键词，`alpha=1.0`为纯语义。

- **关键函数**: `search(query, top_k, alpha)` — 混合检索入口, `_build_bm25_index()` — 从ChromaDB重建BM25索引
- **核心模式**: 分数归一化（BM25原始分/max归一化到[0,1]）、双路融合排序

### `ingest.py` — 文档摄入管线

实现完整的文档摄入流程：**加载 → 分块 → 向量化 → 存储**。`load_document()`支持PDF(用PyPDF2)、Markdown和TXT。`chunk_text()`按句子边界切分，使用**重叠窗口**（overlap=50字符）防止上下文断裂。`DocumentStore`类用`SentenceTransformer`生成嵌入，存入ChromaDB并使用MD5哈希去重。

- **关键函数**: `chunk_text(text, chunk_size, overlap)` — 智能分块, `ingest_file()` — 完整摄入流程
- **核心模式**: 流水线模式（Pipeline）、哈希去重、余弦相似度空间配置(`hnsw:space: cosine`)

---

## 运行示例 (Run Examples)

```bash
# 安装依赖
cd rag-qa-bot
pip install -r requirements.txt

# 可选：配置OpenAI（无Key也能运行，使用本地抽取模式）
cp .env.example .env
# 编辑 .env 设置 OPENAI_API_KEY

# 启动服务
python main.py
# 预期输出: 🚀 Initializing RAG Q&A Bot... ✅ Ready!
# 服务地址: http://localhost:8001

# 上传文档
curl -X POST http://localhost:8001/ingest \
  -F "file=@your_document.pdf"
# 预期输出: {"status": "success", "file": "your_document.pdf", "chunks": 15, "source": "your_document.pdf"}

# 提问
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是RAG?", "top_k": 3}'
# 预期输出: {"answer": "RAG是检索增强生成...", "sources": [...], "model": "gpt-3.5-turbo"}

# 调整检索策略
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "neural networks", "alpha": 0.0}'  # 纯关键词
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "脑启发系统如何工作", "alpha": 1.0}'  # 纯语义

# 查看统计
curl http://localhost:8001/stats
# 预期输出: {"document_count": 15}
```

---

## 知识映射 (Knowledge Mapping)

**本项目演示的知识点：**
- RAG全流程：加载 → 分块 → 嵌入 → 存储 → 检索 → 生成
- 向量数据库使用（ChromaDB）
- 混合检索策略（BM25 + Dense）
- 文档分块策略与重叠窗口
- 源归属（Source Attribution）

**前置知识：**
- Python基础、FastAPI入门
- 向量/嵌入的基本概念
- HTTP API基础

## Dashboard

A visual overview of the RAG pipeline, indexed documents, and retrieval configuration is available at [`dashboard.html`](dashboard.html). Open it directly in any browser.

**进阶方向：**
- 完成本项目后 → 进阶 `llm-api-gateway`（统一API管理）
- 深入 → `model-finetune-demo`（自定义嵌入模型）
- 生产化 → `observability-dashboard`（监控RAG质量）

**相关知识库文件：**
- `knowledge-base/01-llm-basics/` — LLM基础与提示工程
- `knowledge-base/02-rag/` — RAG架构详解
- `knowledge-base/03-vector-db/` — 向量数据库对比
- `knowledge-base/04-embeddings/` — 嵌入模型选型

---

## 商业价值扩展 (Commercial Value Extensions)

**目标客户：**
- 企业内部知识库团队（IT/HR/法务）
- 客服自动化团队
- 法律/医疗/金融垂直领域

**定价模型：**
- SaaS: $0.01/次查询，$500/月起（含10万次查询）
- 企业部署: $50,000/年起（私有化部署+定制）
- 按文档量: $1/文档/月（含向量化+存储+检索）

**竞品对比：**

| 特性 | 本项目 | Glean | Coveo | Algolia |
|------|--------|-------|-------|---------|
| 混合检索 | ✅ | ✅ | ✅ | ❌ |
| 开源 | ✅ | ❌ | ❌ | ❌ |
| 私有部署 | ✅ | ❌ | ✅ | ❌ |
| 本地运行(无API Key) | ✅ | ❌ | ❌ | ❌ |

**市场进入策略：**
1. 开源核心 → 社区获客 → 企业增值功能
2. 垂直切入法律/医疗知识库（高客单价）
3. 与现有企业工具集成（Confluence、Notion、SharePoint）

---

## 进阶挑战 (Advanced Challenges)

### 🟢 挑战1 (初级): 添加文档删除功能
为API添加 `DELETE /documents/{doc_id}` 端点，支持按文档ID从ChromaDB中删除向量，并更新BM25索引。
- **学习目标**: ChromaDB的CRUD操作、索引一致性维护
- **提示**: 使用 `collection.delete(ids=[...])` 并重建BM25索引

### 🟡 挑战2 (中级): 实现RRF(Reciprocal Rank Fusion)融合算法
将当前的加权分数融合替换为RRF算法，该算法对排名而非分数进行融合，对异常值更鲁棒。
- **学习目标**: 信息检索中的排名融合策略
- **提示**: `RRF_score(d) = Σ 1/(k + rank_i(d))`, k通常取60

### 🔴 挑战3 (高级): 添加重排序(Reranker)阶段
在检索后、生成前，添加一个交叉编码器(Cross-Encoder)重排序阶段，将top_k*3的候选文档精排后取top_k。
- **学习目标**: 二阶段检索架构、Cross-Encoder vs Bi-Encoder
- **提示**: 使用 `sentence-transformers` 的 `CrossEncoder` 类，模型推荐 `ms-marco-MiniLM-L-6-v2`
