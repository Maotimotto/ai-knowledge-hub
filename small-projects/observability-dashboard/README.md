# Observability Dashboard

> Real-time monitoring for LLM-powered applications

## What It Does

A production-grade observability dashboard that tracks **request rates**, **latency distributions**, **token usage**, **error rates**, and **cost breakdowns** across multiple LLM providers — all updated in real time via WebSocket.

## Architecture

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

| Component | File | Role |
|-----------|------|------|
| FastAPI server | `main.py` | REST + WebSocket endpoints |
| Metrics collector | `collector.py` | Ingest, aggregate, store metrics |
| Alert engine | `alerts.py` | Threshold-based alerting |
| Frontend | `dashboard.html` | Chart.js visualisation |

## Setup

```bash
cd small-projects/observability-dashboard
cp .env.example .env        # edit with your config
pip install -r requirements.txt
uvicorn main:app --reload   # open http://localhost:8000/dashboard
```

## Demo

1. Start the server, open `/dashboard` in a browser.
2. Send sample requests via the `/collect` endpoint or run the built-in demo simulator.
3. Watch charts update in real time; trigger an alert by exceeding latency thresholds.

## Learning Outcomes

- WebSocket streaming for live dashboards
- Time-series aggregation (sliding windows, histograms)
- Chart.js for professional data visualisation
- Alerting patterns (threshold, anomaly)
- Multi-model cost tracking

## Commercial Value

Every company using LLMs at scale needs observability. This project demonstrates the core of products like **LangSmith**, **Helicone**, and **Portkey** — a $100M+ market segment.
