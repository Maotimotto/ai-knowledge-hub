# Observability Dashboard (可观测性仪表盘)

> LLM应用的实时监控仪表盘，演示WebSocket推送与指标聚合

## 项目简介

生产级可观测性仪表盘，实时追踪LLM应用的**请求率**、**延迟分布**、**Token用量**、**错误率**和**成本分解**，通过WebSocket实时推送到前端Chart.js可视化面板。

## 架构图

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  LLM Gateway │───▶│  Collector (main)│───▶│  Dashboard (WS)  │
│  / AI App    │    │  - Metrics store  │    │  - Chart.js      │
└──────────────┘    │  - Alert engine   │    │  - Live updates   │
                    └──────────────────┘    └──────────────────┘
                            │
                    ┌───────┴────────┐
                    │  Alerts (email │
                    │  / webhook)    │
                    └────────────────┘
```

| 组件 | 文件 | 职责 |
|------|------|------|
| FastAPI服务 | `main.py` | REST + WebSocket端点 |
| 指标收集器 | `collector.py` | 采集、聚合、存储指标 |
| 告警引擎 | `alerts.py` | 阈值告警与评估 |
| 前端面板 | `dashboard.html` | Chart.js可视化 |

---

## 代码走读 (Code Walkthrough)

### `main.py` — FastAPI服务与WebSocket广播

服务启动时自动生成50条模拟数据，并启动后台任务每3秒向所有WebSocket客户端广播最新指标。`/ws`端点处理客户端连接，支持`generate_sample`和`get_summary`消息。`/api/metrics`提供REST查询，`/api/simulate`可手动注入模拟流量。`/`直接返回`dashboard.html`前端页面。

- **关键函数**: `broadcast_metrics()` — 异步广播循环, `websocket_endpoint()` — WS连接管理
- **核心模式**: WebSocket连接池管理、异步广播、REST+WS双通道

### `collector.py` — 指标收集与聚合

`MetricsCollector`是核心数据层，使用`deque(maxlen=10000)`作为环形缓冲区存储指标点。支持五种指标类型：`latency`(延迟)、`tokens`(Token数)、`error`(错误)、`cost`(成本)、`request`(请求)。`get_summary()`在时间窗口内聚合计算P50/P95延迟、错误率、成本统计。`get_time_series()`按时间桶(bucket)分组生成时序数据用于图表展示。

- **关键类**: `MetricsCollector` — 线程安全指标收集器, `MetricPoint` — 指标数据点
- **关键函数**: `get_summary(seconds)` — 窗口内聚合, `get_time_series()` — 时序数据生成, `generate_sample_data()` — 模拟数据
- **核心模式**: 环形缓冲区(deque)、线程锁(threading.Lock)、时间窗口聚合、时间桶分组

### `alerts.py` — 告警引擎

`AlertManager`评估三类告警规则：**延迟告警**(P95 > 阈值)、**错误率告警**(错误率 > 阈值)、**成本告警**(接近或超过日预算)。成本告警分两级：80%时warning，100%时critical。阈值从环境变量读取，支持运行时调整。维护活跃告警列表和历史告警记录。

- **关键类**: `AlertManager` — 告警规则引擎, `Alert` — 告警数据类
- **核心模式**: 阈值告警、多级严重性(info/warning/critical)、告警历史

### `dashboard.html` — 前端可视化面板

基于Chart.js的实时仪表盘，通过WebSocket接收数据并动态更新图表。包含延迟时序图、成本趋势图、错误率仪表盘等组件。

---

## 运行示例 (Run Examples)

```bash
# 安装依赖
cd observability-dashboard
pip install -r requirements.txt

# 启动服务
python main.py
# 预期输出: INFO: Started server process [12345]
# 服务地址: http://localhost:8003

# 浏览器打开仪表盘
open http://localhost:8003
# 将看到实时更新的监控面板，包含延迟/成本/错误率图表

# REST API查询指标
curl http://localhost:8003/api/metrics?seconds=300
# 预期输出: {"window_seconds": 300, "total_requests": 50, "total_errors": 3, "latency": {"avg_ms": 623.45, "p50_ms": 580.0, "p95_ms": 1200.0, ...}, "cost": {...}}

# 手动注入模拟数据
curl -X POST http://localhost:8003/api/simulate?count=20
# 预期输出: {"status": "generated", "count": 20}

# 查看活跃告警
curl http://localhost:8003/api/alerts
# 预期输出: {"active": [...], "history": [...]}

# WebSocket测试（用websocat等工具）
websocat ws://localhost:8003/ws
# 发送: {"type": "get_summary", "seconds": 60}
# 收到: {"type": "summary", "data": {...}}
```

---

## 知识映射 (Knowledge Mapping)

**本项目演示的知识点：**
- WebSocket实时通信与连接管理
- 时间序列数据聚合（滑动窗口、时间桶分组）
- 百分位数计算（P50、P95）
- 告警规则引擎设计
- Chart.js前端可视化

**前置知识：**
- Python基础、FastAPI
- WebSocket基本概念
- JavaScript基础（理解前端面板）

**进阶方向：**
- 完成本项目后 → 将此Dashboard接入 `llm-api-gateway` 的真实指标
- 深入 → 添加异常检测(Anomaly Detection)、预测性告警
- 生产化 → 持久化到时序数据库(InfluxDB/Prometheus)、Grafana集成

**相关知识库文件：**
- `knowledge-base/09-infrastructure/` — AI基础设施与MLOps
- `knowledge-base/11-monitoring/` — 监控与可观测性
- `knowledge-base/10-optimization/` — 性能优化

---

## 商业价值扩展 (Commercial Value Extensions)

**目标客户：**
- 使用LLM的AI应用团队（必备基础设施）
- MLOps/平台工程团队
- AI SaaS公司（SLA保障）

**定价模型：**
- SaaS: $99/月（基础版，10万条指标），$499/月（专业版，含告警+分析）
- 企业版: $2,000/月（私有部署+自定义仪表盘）
- 按量: $0.001/千条指标

**竞品对比：**

| 特性 | 本项目 | LangSmith | Helicone | Portkey |
|------|--------|-----------|----------|---------|
| 开源 | ✅ | ❌ | 部分 | 部分 |
| 实时WebSocket | ✅ | ❌ | ❌ | ❌ |
| 自托管 | ✅ | ❌ | ✅ | ✅ |
| 告警引擎 | ✅ | ✅ | ✅ | ✅ |
| 轻量级 | ✅ | ❌ | ❌ | ❌ |

**市场进入策略：**
1. 开源监控工具 → 社区采用 → 企业版SaaS
2. 与 `llm-api-gateway` 捆绑销售
3. 集成到现有监控栈（Grafana/Datadog插件）

---

## 进阶挑战 (Advanced Challenges)

### 🟢 挑战1 (初级): 添加请求日志详情页
在仪表盘中添加一个表格，展示最近100条请求的详细信息（时间、模型、provider、延迟、token数、成本），支持按延迟/成本排序。
- **学习目标**: 前端表格展示、数据分页
- **提示**: 在collector中添加`get_recent_entries()`方法，前端用HTML表格展示

### 🟡 挑战2 (中级): 实现真正的异常检测
替换简单的阈值告警，添加基于统计的异常检测：当某指标偏离移动平均值超过3个标准差时触发告警。
- **学习目标**: 统计异常检测、Z-score、移动平均
- **提示**: 维护指标的滑动均值和标准差，当新值的Z-score > 3时告警

### 🔴 挑战3 (高级): 将指标持久化到Prometheus格式
添加Prometheus指标导出端点(`/metrics`)，将内部指标转换为Prometheus文本格式，实现与Grafana的无缝集成。
- **学习目标**: Prometheus指标格式、Counter/Gauge/Histogram类型、Grafana集成
- **提示: 使用`prometheus_client`库或手动输出文本格式
