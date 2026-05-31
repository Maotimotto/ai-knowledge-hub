# Agent Task Planner (Agent任务规划)

> ReAct风格的任务规划Agent，演示工具调用、结构化输出和记忆管理

## 项目简介

输入高层目标（如"规划AI工具的营销活动"），Agent将其分解为结构化任务列表，包含优先级、时间线和资源估计。支持计算器、搜索、文件操作等工具调用。

## 架构图

```
┌──────────────┐
│   User Goal  │
└──────┬───────┘
       │
┌──────▼───────┐    ┌──────────────┐
│  ReAct Agent │───▶│   Memory     │
│  (think-act- │    │  (Summary    │
│   observe)   │◀──│   Buffer)    │
└──────┬───────┘    └──────────────┘
       │
┌──────▼───────┐
│  Tool Router │
├──────────────┤
│ • calculator │    ┌──────────────┐
│ • web_search │───▶│ Structured   │
│ • file_ops   │    │ Task Plan    │
│ • code_exec  │    │ (JSON)       │
└──────────────┘    └──────────────┘
```

---

## 代码走读 (Code Walkthrough)

### `main.py` — CLI入口与Rich终端展示

程序主入口，负责解析命令行参数、调用PlanningAgent规划，并用**Rich库**美化输出。`display_plan()`将JSON格式的任务计划渲染为彩色表格，展示ID、标题、优先级、工时和描述。支持命令行传参和交互式输入两种模式。

- **关键函数**: `display_plan(plan)` — Rich格式化展示, `main()` — CLI入口
- **设计模式**: 命令行参数解析(sys.argv)、Rich美化输出

### `planner.py` — ReAct规划Agent核心

实现**ReAct(Reasoning + Acting)循环**：思考→调用工具→观察结果→继续推理，直到得出最终计划。`PlanningAgent.plan()`方法驱动最多10轮迭代，每轮解析LLM响应中的`TOOL:`指令或`FINAL_ANSWER:`。`_fallback_plan()`在无LLM时使用模板生成结构化计划，确保系统始终可用。

- **关键类**: `PlanningAgent` — ReAct循环控制器
- **关键函数**: `_parse_tool_call()` — 正则解析工具调用, `_parse_final_answer()` — 解析最终JSON答案
- **核心模式**: ReAct循环、正则解析structured output、模板化fallback

### `tools.py` — 工具注册与执行

定义Agent可调用的工具集：`calculator`(安全数学计算)、`web_search`(模拟搜索)、`file_operation`(文件读写)、`code_execute`(沙箱执行Python)。`TOOLS`字典作为**工具注册表**，包含函数引用、描述和参数说明。`execute_tool()`统一调度入口，`get_tools_description()`生成工具描述注入Prompt。

- **关键函数**: `execute_tool(name, input)` — 统一工具调度, `calculator()` — 沙箱eval(字符白名单)
- **核心模式**: 工具注册表模式、安全沙箱执行、Prompt注入工具描述

### `memory.py` — 带摘要压缩的记忆管理

实现**SummaryBufferMemory**：保留最近N条消息原文，超出时将旧消息压缩为摘要。`_compress()`截取每条消息前100字符拼接为摘要，总长度限制1000字符。`get_messages_for_llm()`将摘要作为system消息注入，确保LLM了解之前上下文。

- **关键类**: `SummaryBufferMemory` — 摘要缓冲记忆, `Message` — 消息数据类
- **核心模式**: 滑动窗口+摘要压缩、上下文窗口管理

---

## 运行示例 (Run Examples)

```bash
# 安装依赖
cd agent-task-planner
pip install -r requirements.txt

# 交互模式（会提示输入目标）
python main.py

# 直接传入目标
python main.py "Plan a marketing campaign for an AI productivity tool"
# 预期输出:
# 🎯 Task Plan: Plan a marketing campaign...
# 📋 Tasks (表格，含ID/标题/优先级/工时/描述)
# 📅 Timeline: 2-3 weeks
# 🔧 Resources: Team members, Project management tools, Budget allocation
# ⚠️  Risks: Scope creep, Resource constraints, Timeline delays
# Total estimated effort: 60 hours

# 其他示例
python main.py "Build a mobile app for fitness tracking"
python main.py "Launch a SaaS product in 3 months"
python main.py "Scale engineering team from 5 to 20 people in 6 months"

# 查看生成的JSON计划
cat plan_output.json
```

---

## 知识映射 (Knowledge Mapping)

**本项目演示的知识点：**
- ReAct模式（思考→行动→观察循环）
- Agent工具调用（Tool Use/Function Calling）
- 结构化输出（强制LLM返回JSON）
- 记忆管理（摘要缓冲防止上下文溢出）
- 优雅降级（无LLM时的模板fallback）

**前置知识：**
- Python基础、正则表达式
- LLM API基本调用
- JSON数据格式

**进阶方向：**
- 完成本项目后 → 进阶 `rag-qa-bot`（给Agent添加知识检索能力）
- 深入 → 实现多Agent协作、自主Agent
- 生产化 → `ai-safety-guardrails`（给Agent加安全护栏）

**相关知识库文件：**
- `knowledge-base/05-agents/` — Agent架构与设计模式
- `knowledge-base/06-tool-use/` — 工具调用与Function Calling
- `knowledge-base/01-llm-basics/` — 提示工程与结构化输出

---

## 商业价值扩展 (Commercial Value Extensions)

**目标客户：**
- 项目管理团队（自动分解任务）
- 咨询公司（快速生成方案框架）
- 产品经理（需求到任务的转化）
- 创业团队（商业计划分解）

**定价模型：**
- SaaS: $20/用户/月（个人版），$50/用户/月（团队版）
- API: $0.05/次规划请求
- 企业版: $30,000/年（私有部署+自定义模板）

**竞品对比：**

| 特性 | 本项目 | Notion AI | Linear | Asana Intelligence |
|------|--------|-----------|--------|-------------------|
| ReAct推理 | ✅ | ❌ | ❌ | ❌ |
| 工具调用 | ✅ | ❌ | ❌ | ❌ |
| 开源 | ✅ | ❌ | ❌ | ❌ |
| 结构化JSON输出 | ✅ | ❌ | 部分 | ❌ |
| 离线运行 | ✅ | ❌ | ❌ | ❌ |

**市场进入策略：**
1. 作为开发者工具开源 → 积累用户 → 推出SaaS
2. 集成到现有PM工具（Jira、Linear）作为插件
3. 垂直场景：IT项目规划、营销活动规划

---

## 进阶挑战 (Advanced Challenges)

### 🟢 挑战1 (初级): 添加新工具
为Agent添加一个`date_calculator`工具，可以计算项目截止日期、工作日天数等。将其注册到TOOLS字典中。
- **学习目标**: 工具注册表扩展、Agent Prompt中工具描述的注入
- **提示**: 参考`calculator`的实现，添加到TOOLS字典并编写描述

### 🟡 挑战2 (中级): 实现并行工具调用
修改planner.py，当Agent一次返回多个工具调用时并行执行它们，而非串行等待。使用`asyncio.gather`或`ThreadPoolExecutor`。
- **学习目标**: 并发执行、Agent效率优化
- **提示**: 修改`_parse_tool_call`为`_parse_tool_calls`(返回列表)，在plan()中并行执行

### 🔴 挑战3 (高级): 添加反思与自我修正机制
在ReAct循环中添加"反思"步骤：当Agent完成计划后，让它自我审查计划质量，如果发现问题则自动修正。
- **学习目标**: 反思模式(Reflection)、自我修正Agent、多轮推理
- **提示**: 在plan()返回前添加一轮反思prompt，检查任务完整性和可行性
