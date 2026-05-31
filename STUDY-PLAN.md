# 📅 30 天 AI 全栈学习计划

> **每日节奏**：📖 1-2 小时阅读知识库 + 💻 1-2 小时动手编码
> **配套工具**：[LEARNING-CARDS.md](./LEARNING-CARDS.md) 提供每张学习卡片的详细阅读清单

---

## 第一周：基础筑基（Day 1-7）

**目标**：掌握 NLP → Transformer → ML/DL 基础，搭建 display 仪表盘

### Day 1 — NLP 基础
- [ ] 📖 阅读：`AI大模型/01-NLP基础/NLP概述与技术演进.md`
- [ ] 📖 阅读：`AI大模型/01-NLP基础/分词与词表构建.md`
- [ ] 💻 在 display/ 中创建 NLP 基础概念卡片
- [ ] 📝 笔记：分词器选型对比

### Day 2 — 词向量与 RNN
- [ ] 📖 阅读：`AI大模型/01-NLP基础/词向量与Word2Vec.md`
- [ ] 📖 阅读：`AI大模型/01-NLP基础/传统序列模型RNN.md`
- [ ] 💻 在 display/ 中创建 Word2Vec 交互类比
- [ ] 📝 笔记：RNN 的梯度消失问题

### Day 3 — Transformer 架构
- [ ] 📖 阅读：`AI大模型/02-Transformer架构/Transformer架构原理.md`
- [ ] 📖 阅读：`LLM/Transformer注意力机制演进笔记：从MHA到GQA.md`
- [ ] 💻 在 display/ 中创建 Transformer 架构关系图
- [ ] 📝 笔记：Self-Attention 计算流程

### Day 4 — 大模型技术栈全景
- [ ] 📖 阅读：`AI大模型/03-大模型技术栈/大模型技术栈全景.md`
- [ ] 📖 阅读：`AI大模型/MOC-AI大模型知识体系.md`
- [ ] 💻 在 display/ 中创建学习路径图（全栈路线）
- [ ] 📝 笔记：技术栈 6 大模块梳理

### Day 5 — 机器学习基础
- [ ] 📖 阅读：`机器学习/2.机器学习/机器学习概述.md`
- [ ] 📖 阅读：`机器学习/2.机器学习/08.集成算法笔记.md`
- [ ] 💻 在 display/ 中创建 ML 算法对比卡片
- [ ] 📝 笔记：监督 vs 无监督 vs 强化学习

### Day 6 — 深度学习与 NLP 进阶
- [ ] 📖 阅读：`NLP/NLP基础.md`
- [ ] 📖 阅读：`NLP/RNN循环神经网络核心笔记.md`
- [ ] 💻 在 display/ 中创建 DL 技术演进知识图谱
- [ ] 📝 笔记：CNN → RNN → Transformer 演进

### Day 7 — 第一周回顾
- [ ] 📝 整理本周笔记，完善 display/ 仪表盘
- [ ] 🔍 自测：能否画出从 NLP 到 Transformer 的完整技术演进图？
- [ ] 📊 检查：display/ 中已有几张卡片/图表？

---

## 第二周：核心技能（Day 8-14）

**目标**：掌握 RAG + 向量数据库 + 推理部署，构建 rag-qa-bot 和 llm-api-gateway

### Day 8 — RAG 技术入门
- [ ] 📖 阅读：`AI大模型/04-RAG技术/README-RAG技术.md`
- [ ] 📖 阅读：`AI大模型/04-RAG技术/01-知识库构建/切片策略总览.md`
- [ ] 💻 初始化 small-projects/rag-qa-bot/ 项目结构
- [ ] 📝 笔记：切片策略对比

### Day 9 — RAG 检索与生成
- [ ] 📖 阅读：`AI大模型/04-RAG技术/03-检索策略/向量检索与Embedding.md`
- [ ] 📖 阅读：`AI大模型/04-RAG技术/04-检索后处理/重排序与融合.md`
- [ ] 💻 实现 rag-qa-bot 的文档加载和切片功能
- [ ] 📝 笔记：Embedding 模型选型

### Day 10 — 向量数据库实战
- [ ] 📖 阅读：`AI大模型/13-向量数据库/01-Milvus分布式向量DB.md`
- [ ] 📖 阅读：`AI大模型/13-向量数据库/05-向量DB选型对比矩阵.md`
- [ ] 💻 rag-qa-bot 接入向量数据库，完成检索功能
- [ ] 📝 笔记：向量索引类型对比

### Day 11 — RAG 完整管道
- [ ] 📖 阅读：`AI大模型/04-RAG技术/05-生成阶段/RAG评估与优化.md`
- [ ] 📖 阅读：`AI大模型/04-RAG技术/06-项目实战/高性能RAG系统实战.md`
- [ ] 💻 完成 rag-qa-bot 的端到端 RAG 管道
- [ ] 📝 笔记：RAG 评估指标

### Day 12 — LLM 推理部署
- [ ] 📖 阅读：`AI大模型/12-LLM推理部署/01-vLLM部署与配置.md`
- [ ] 📖 阅读：`AI大模型/12-LLM推理部署/02-llama.cpp与GGUF.md`
- [ ] 💻 初始化 small-projects/llm-api-gateway/ 项目
- [ ] 📝 笔记：vLLM vs llama.cpp 适用场景

### Day 13 — API 网关开发
- [ ] 📖 阅读：`AI大模型/16-模型服务与部署/01-API服务封装.md`
- [ ] 📖 阅读：`AI大模型/16-模型服务与部署/02-负载均衡与扩展.md`
- [ ] 💻 实现 llm-api-gateway 的路由和限流功能
- [ ] 📝 笔记：负载均衡策略

### Day 14 — 第二周回顾
- [ ] 📝 整理本周笔记
- [ ] 🔍 自测：能否独立搭建一个完整的 RAG 管道？
- [ ] 🧪 测试：rag-qa-bot 对 3 个测试问题的回答质量
- [ ] 🧪 测试：llm-api-gateway 能否正确路由请求

---

## 第三周：进阶突破（Day 15-21）

**目标**：掌握 Agent + LangGraph + 微调 + 安全，构建 agent-task-planner 和 model-finetune-demo

### Day 15 — Agent 基础
- [ ] 📖 阅读：`AI大模型/05-Agent开发/README-Agent开发.md`
- [ ] 📖 阅读：`AI大模型/05-Agent开发/14-高级Prompt模式/01-ReAct推理行动循环.md`
- [ ] 💻 初始化 small-projects/agent-task-planner/ 项目
- [ ] 📝 笔记：ReAct 循环原理

### Day 16 — MCP 协议与工具调用
- [ ] 📖 阅读：`AI大模型/05-Agent开发/07-MCP协议/01-MCP协议概述.md`
- [ ] 📖 阅读：`AI大模型/05-Agent开发/11-Agent框架对比/框架横向对比矩阵.md`
- [ ] 💻 agent-task-planner 实现工具调用功能
- [ ] 📝 笔记：MCP vs Function Calling

### Day 17 — LangGraph 图编排
- [ ] 📖 阅读：`AI大模型/06-LangGraph/LangGraph-State核心概念.md`
- [ ] 📖 阅读：`AI大模型/06-LangGraph/LangGraph基础代码学习示例.md`
- [ ] 💻 agent-task-planner 用 LangGraph 重写编排逻辑
- [ ] 📝 笔记：StateGraph 核心概念

### Day 18 — Agent 记忆与评估
- [ ] 📖 阅读：`AI大模型/05-Agent开发/12-Agent记忆系统/01-短期记忆与对话管理.md`
- [ ] 📖 阅读：`AI大模型/05-Agent开发/13-Agent评估与基准/01-评估维度与指标体系.md`
- [ ] 💻 agent-task-planner 添加记忆功能并完成测试
- [ ] 📝 笔记：短期 vs 长期记忆设计

### Day 19 — 模型微调入门
- [ ] 📖 阅读：`AI大模型/07-模型微调/01-微调概述/微调方式总览.md`
- [ ] 📖 阅读：`AI大模型/07-模型微调/02-LoRA与QLoRA/LoRA原理与实践.md`
- [ ] 💻 初始化 small-projects/model-finetune-demo/ 项目
- [ ] 📝 笔记：LoRA 数学原理

### Day 20 — 微调实战
- [ ] 📖 阅读：`AI大模型/07-模型微调/02-LoRA与QLoRA/QLoRA原理与实践.md`
- [ ] 📖 阅读：`AI大模型/07-模型微调/02-LoRA与QLoRA/LLaMA-Factory使用指南.md`
- [ ] 💻 model-finetune-demo 完成一次 LoRA 微调实验
- [ ] 📝 笔记：QLoRA 的 4-bit 量化技巧

### Day 21 — 第三周回顾 + AI 安全入门
- [ ] 📖 阅读：`AI大模型/15-AI安全与护栏/01-Prompt注入与越狱防护.md`
- [ ] 📝 整理本周笔记
- [ ] 🔍 自测：能否用 LangGraph 编排一个多步骤 Agent？
- [ ] 🔍 自测：能否解释 LoRA 微调的完整流程？

---

## 第四周：生产实战（Day 22-30）

**目标**：掌握可观测性 + 安全护栏 + Docker 部署，完成大项目集成

### Day 22 — AI 安全深入
- [ ] 📖 阅读：`AI大模型/15-AI安全与护栏/02-输出内容安全防护.md`
- [ ] 📖 阅读：`AI大模型/15-AI安全与护栏/03-Guardrails框架实战.md`
- [ ] 💻 初始化 small-projects/ai-safety-guardrails/ 项目
- [ ] 📝 笔记：Guardrails 验证流程

### Day 23 — 安全护栏实战
- [ ] 📖 阅读：`AI大模型/15-AI安全与护栏/04-红队测试方法论.md`
- [ ] 💻 ai-safety-guardrails 实现输入过滤和输出检查
- [ ] 💻 用 5 种攻击方式测试护栏效果
- [ ] 📝 笔记：红队测试 checklist

### Day 24 — 可观测性基础
- [ ] 📖 阅读：`AI大模型/14-LLM可观测性/01-LangSmith追踪与评估.md`
- [ ] 📖 阅读：`AI大模型/14-LLM可观测性/02-Langfuse开源可观测性.md`
- [ ] 💻 初始化 small-projects/observability-dashboard/ 项目
- [ ] 📝 笔记：Trace / Span / Metric 概念

### Day 25 — 监控仪表盘
- [ ] 📖 阅读：`AI大模型/14-LLM可观测性/03-OpenTelemetry-for-LLM.md`
- [ ] 📖 阅读：`AI大模型/14-LLM可观测性/04-LLM监控最佳实践.md`
- [ ] 💻 observability-dashboard 实现核心指标展示
- [ ] 📝 笔记：LLM 监控最佳实践

### Day 26 — Docker 容器化
- [ ] 📖 阅读：`Docker/Docker简介.md`
- [ ] 📖 阅读：`Docker/Docker 部署 Anaconda 环境.md`
- [ ] 💻 为 rag-qa-bot 和 llm-api-gateway 编写 Dockerfile
- [ ] 📝 笔记：多阶段构建技巧

### Day 27 — Docker Compose 编排
- [ ] 📖 阅读：`Docker/Docker 部署 MySQL.md`
- [ ] 💻 编写 docker-compose.yml 编排所有小项目
- [ ] 💻 测试一键启动整个技术栈
- [ ] 📝 笔记：服务依赖和健康检查

### Day 28 — 大项目集成（上）
- [ ] 📖 阅读：`RAG高级模式/01-Self-RAG自适应检索.md`
- [ ] 📖 阅读：`RAG高级模式/03-生产级RAG架构.md`
- [ ] 💻 big-project/backend/rag/ 集成 Self-RAG 逻辑
- [ ] 💻 big-project/backend/agents/ 集成 LangGraph Agent
- [ ] 📝 笔记：生产级 RAG 架构要点

### Day 29 — 大项目集成（下）
- [ ] 📖 阅读：`RAG高级模式/04-RAG监控与质量漂移.md`
- [ ] 💻 big-project/backend/inference/ 集成推理网关
- [ ] 💻 big-project/backend/security/ 集成安全护栏
- [ ] 💻 big-project/backend/observability/ 集成监控
- [ ] 📝 笔记：系统集成 checklist

### Day 30 — 总结与展望
- [ ] 📖 回顾 LEARNING-CARDS.md 所有卡片
- [ ] 📝 撰写学习总结（每张卡片的反思问题答案）
- [ ] 🔍 自测：能否在 30 分钟内画出整个 AI 技术栈架构图？
- [ ] 🔍 自测：能否独立设计一个新的 AI 项目从 0 到 1？
- [ ] 🎯 规划下一阶段深入方向（选择 1-2 个领域深耕）

---

## 学习进度追踪

| 周 | 主题 | 知识卡片 | 项目产出 | 完成 |
|----|------|----------|----------|------|
| 1 | 基础筑基 | #01 #02 #03 #16 #17 | display/ 仪表盘 | ⬜ |
| 2 | 核心技能 | #04 #09 #10 #13 | rag-qa-bot + llm-api-gateway | ⬜ |
| 3 | 进阶突破 | #05 #06 #07 #12 | agent-task-planner + model-finetune-demo | ⬜ |
| 4 | 生产实战 | #11 #14 #15 #08 | observability-dashboard + ai-safety-guardrails + 大项目 | ⬜ |

---

> 💡 **灵活调整**：此计划为参考模板，请根据个人基础和时间灵活调整节奏。重点是**每天保持阅读+编码的节奏**，而非追赶进度。
