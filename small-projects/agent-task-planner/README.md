# Agent Task Planner (Agent任务规划)

A task planning agent demonstrating **ReAct-style reasoning**, **tool calling**, and **structured output** — core patterns for building autonomous AI agents.

## What It Does

Input a high-level goal (e.g., "Plan a marketing campaign for an AI tool"), and the agent breaks it down into structured tasks with priorities, timelines, and resource estimates. It can use tools like web search, calculator, and file operations during planning.

## Architecture

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

## Setup

```bash
cd agent-task-planner
pip install -r requirements.txt
cp .env.example .env
# Edit .env to add OPENAI_API_KEY (optional - has fallback planner)
```

## Run

```bash
# Interactive mode
python main.py

# With a goal argument
python main.py "Plan a marketing campaign for an AI productivity tool"

# Other examples
python main.py "Build a mobile app for fitness tracking"
python main.py "Launch a SaaS product in 3 months"
```

## Demo Scenarios

### 1. Marketing Campaign Planning
```bash
python main.py "Plan a marketing campaign for an AI writing assistant"
```

### 2. Product Launch
```bash
python main.py "Launch a developer tool product with limited budget"
```

### 3. Team Scaling
```bash
python main.py "Scale engineering team from 5 to 20 people in 6 months"
```

## What You Learn

- **ReAct Pattern**: Think → Act → Observe → Repeat loop for reasoning
- **Tool Calling**: How agents invoke external tools during planning
- **Structured Output**: Forcing LLMs to return parseable JSON plans
- **Memory Management**: Summary buffer to handle long conversations
- **Fallback Design**: Graceful degradation when LLM is unavailable

## Commercial Applications

| Use Case | Description | Market |
|----------|-------------|--------|
| Project Management | Auto-generate project plans | $6B+ market |
| Workflow Orchestration | Break complex processes into steps | Enterprise automation |
| Sales Planning | Generate sales strategies and pipelines | CRM integration |
| Event Planning | Decompose event logistics into tasks | Event management |
| Strategic Planning | Board-level strategy decomposition | Consulting |

## Key Design Decisions

1. **ReAct over chain-of-thought** — explicit action steps enable tool use
2. **Summary buffer memory** — prevents context overflow in long plans
3. **Fallback planner** — works without API key using templates
4. **Rich CLI output** — beautiful terminal UI for better UX
5. **JSON structured output** — machine-readable plans for downstream use
