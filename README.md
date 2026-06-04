# AI Knowledge Hub

个人 AI 知识库系统 — 从基础理论到生产实践的完整学习体系。

## 项目简介

AI Knowledge Hub 是一个将 Obsidian Markdown 笔记转化为可交互 HTML 页面的知识库系统，集成了：

- **知识仪表盘** — 可视化学习进度、概念关系图谱、翻转卡片
- **65+ HTML 知识页面** — 覆盖 AI 核心技术栈
- **6 个实战小项目** — 可运行的学习项目
- **1 个完整 SaaS 项目** — AI 创作工坊全栈应用

## 目录结构

```
ai-knowledge-hub/
├── display/                    # 知识展示层
│   ├── index.html             # 主仪表盘（Apple 风格）
│   └── kb/                    # 知识库 HTML 页面
│       ├── foundation/        # 基础理论（ML/DL/NLP/LLM）
│       ├── ai-core/           # AI 核心（RAG/Agent/微调/Transformer）
│       ├── ai-advanced/       # AI 进阶（推理/部署/多模态/安全）
│       └── applied/           # 应用实践（LangChain/创业/金融/Docker）
│
├── small-projects/            # 6 个实战小项目
│   ├── rag-qa-bot/            # RAG 问答机器人
│   ├── agent-task-planner/    # Agent 任务规划器
│   ├── model-finetune-demo/   # 模型微调演示
│   ├── llm-api-gateway/       # LLM API 网关
│   ├── observability-dashboard/ # 可观测性仪表盘
│   └── ai-safety-guardrails/  # AI 安全护栏
│
├── big-project/               # AI 创作工坊 SaaS
│   ├── backend/               # FastAPI 后端
│   ├── frontend/              # 前端界面
│   ├── fine_tuning/           # 微调模块
│   ├── monitoring/            # Prometheus + Grafana
│   └── tests/                 # 测试套件
│
├── LEARNING-CARDS.md          # 学习卡片（Anki 格式）
└── STUDY-PLAN.md              # 学习路线图
```

## 知识体系覆盖

### 基础理论 (foundation/)
| 主题 | 文件 |
|------|------|
| 机器学习 | machine-learning.html |
| 深度学习 | deep-learning.html |
| NLP 基础 | nlp.html |
| 大语言模型 | llm.html |
| RAG 进阶 | rag-advanced.html |

### AI 核心 (ai-core/)
| 主题 | 文件 |
|------|------|
| Transformer 架构 | transformer.html |
| RAG 全链路 | rag-overview / rag-indexing / rag-retrieval / rag-generation.html |
| Agent 开发 | agent.html / agent-overview / agent-prompt / agent-memory / ... |
| 微调技术 | finetune.html / finetune-lora / finetune-techniques.html |
| LangGraph | langgraph.html / langgraph-detailed.html |
| Coze/Dify | coze-dify.html |

### AI 进阶 (ai-advanced/)
| 主题 | 文件 |
|------|------|
| 模型推理 | inference.html |
| 模型部署 | serving.html |
| 向量数据库 | vectordb.html |
| 多模态 AI | multimodal.html |
| 计算机视觉 | cv.html |
| 可观测性 | observability.html |
| AI 安全 | safety.html |
| 面试指南 | interview.html |

### 应用实践 (applied/)
| 主题 | 文件 |
|------|------|
| LangChain | langchain.html |
| Docker | docker.html |
| 数据库 | database.html |
| 中间件 | middleware.html |
| 创业实战 | startup.html |
| 金融 AI | finance.html / zheshang.html |
| Hermes Agent | hermes-agent.html |
| 学习路径 | learning-paths.html |

## 快速开始

### 查看知识仪表盘

```bash
cd ~/projects/ai-knowledge-hub
python3 -m http.server 8888 --directory display
# 访问 http://localhost:8888
```

### 运行小项目

```bash
cd small-projects/rag-qa-bot
pip install -r requirements.txt
python main.py
```

### 启动 SaaS 项目

```bash
cd big-project
docker-compose up -d
# 或手动启动
cd backend && uvicorn main:app --reload
cd frontend && python server.py
```

## 设计系统

采用 Apple 设计语言：

- **色彩**：二元系统 — 白 `#ffffff` + 浅灰 `#f5f5f7` 交替，深色章节 `#1d1d1f`
- **强调色**：Apple Blue `#0071e3`（单一交互色）
- **字体**：SF Pro / Inter / Noto Sans SC
- **导航**：毛玻璃效果 `backdrop-filter: blur(20px)`
- **交互**：翻转卡片、力导向图谱、学习进度追踪

## 数据来源

本项目的 HTML 页面由 [knowledge-base](https://github.com/Maotimotto/knowledge-base) 仓库的 Markdown 文档转换而来。

- 源仓库：317 个 md 文件
- 已转换：65 个 HTML 页面（覆盖率 20.5%）
- 待转换：创业、机器学习、深度学习、金融、面试等分类

## 技术栈

- **前端**：原生 HTML/CSS/JS（零依赖）
- **后端**：FastAPI + SQLAlchemy（big-project）
- **容器化**：Docker Compose
- **监控**：Prometheus + Grafana
- **微调**：PyTorch + PEFT + LoRA

## 相关仓库

- [knowledge-base](https://github.com/Maotimotto/knowledge-base) — Obsidian Markdown 源文件
- [MoneyPrinterTurbo](https://github.com/Harry0703/MoneyPrinterTurbo) — AI 视频生成
- [comment-ai-tool](https://github.com/Maotimotto/entrepreneurship) — 评论 AI 工具

## License

MIT
