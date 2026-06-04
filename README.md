# AI 知识库 — 从基础到实战

> 将 321 篇 Obsidian 笔记转化为可浏览的 HTML 知识图谱，覆盖 AI 全栈技术体系。

## 项目概览

| 指标 | 数值 |
|------|------|
| HTML 页面 | 57 个 |
| 源文档 | 321 篇（314 篇内容 + 7 篇元数据） |
| 总大小 | ~10 MB |
| 覆盖率 | 100% |

## 目录结构

```
ai-knowledge-hub/
├── README.md
├── LEARNING-CARDS.md      # 学习卡片 — 知识点 × 项目代码交叉参考
├── STUDY-PLAN.md          # 30 天 AI 全栈学习计划
├── display/
│   └── kb/                # HTML 知识库（可直接用浏览器打开）
│       ├── index.html     # 入口页 — 全局搜索 + 知识图谱
│       ├── foundation/    # 基础层 — NLP、LLM、Transformer
│       ├── ai-core/       # 核心层 — RAG、Agent、Prompt、Fine-tuning
│       ├── ai-advanced/   # 进阶层 — 推理部署、向量库、多模态、安全
│       └── applied/       # 应用层 — 项目实战、创业、面试
├── big-project/           # 大型项目参考
└── small-projects/        # 小型练手项目
```

## 快速开始

```bash
# 克隆仓库
git clone git@github.com:Maotimotto/ai-knowledge-hub.git
cd ai-knowledge-hub

# 直接用浏览器打开入口页
open display/kb/index.html          # macOS
xdg-open display/kb/index.html      # Linux
start display\kb\index.html         # Windows
```

无需任何构建工具或服务器，纯静态 HTML，即开即用。

## 知识体系

### 基础层（foundation）
- NLP 基础 — 分词、词向量、RNN
- Transformer 架构 — 注意力机制、位置编码
- LLM 原理 — 预训练、微调、对齐

### 核心层（ai-core）
- RAG — 检索增强生成
- AI Agent — 工具调用、记忆、规划
- Prompt Engineering — 提示词设计与优化
- Fine-tuning — LoRA、QLoRA、全参微调

### 进阶层（ai-advanced）
- 模型推理与部署 — vLLM、TensorRT、量化
- 向量数据库 — Milvus、Chroma、Pinecone
- 多模态 — 视觉、语音、视频理解
- 安全与可观测性 — 红队测试、监控、评估

### 应用层（applied）
- 项目实战 — 端到端案例
- 创业方向 — AI 编程效率、知识付费
- 面试准备 — 高频考点 + 项目包装

## 学习路径

- **LEARNING-CARDS.md** — 每张卡片对应一个知识域，含必读文件、编码检查清单、反思问题
- **STUDY-PLAN.md** — 30 天学习计划，每日 1-2h 阅读 + 1-2h 编码

## 源知识库

HTML 页面由 [knowledge-base](https://github.com/Maotimotto/knowledge-base) 仓库的 321 篇 Markdown 文档自动生成，采用 Obsidian 格式（`[[wikilink]]` 交叉引用）。

## License

MIT
