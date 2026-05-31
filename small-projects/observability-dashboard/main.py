"""Observability Dashboard - Real-time LLM monitoring with WebSocket updates."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

load_dotenv()

from alerts import AlertManager
from collector import get_collector

app = FastAPI(title="LLM Observability Dashboard", version="1.0.0")

alert_manager = AlertManager()
connected_clients: set[WebSocket] = set()


@app.on_event("startup")
async def startup():
    """Generate sample data and start broadcast loop."""
    collector = get_collector()
    collector.generate_sample_data(50)
    asyncio.create_task(broadcast_metrics())


async def broadcast_metrics():
    """Periodically send metrics to all connected WebSocket clients."""
    while True:
        await asyncio.sleep(3)
        if not connected_clients:
            continue

        collector = get_collector()
        summary = collector.get_summary(seconds=600)
        latency_ts = collector.get_time_series("latency", bucket_seconds=30, seconds=600)
        cost_ts = collector.get_time_series("cost", bucket_seconds=60, seconds=600)
        alerts = alert_manager.evaluate(summary)

        payload = json.dumps({
            "type": "metrics_update",
            "summary": summary,
            "latency_series": latency_ts,
            "cost_series": cost_ts,
            "alerts": alert_manager.get_active(),
        })

        disconnected = set()
        for ws in connected_clients:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.add(ws)
        connected_clients.difference_update(disconnected)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time metrics streaming."""
    await ws.accept()
    connected_clients.add(ws)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "generate_sample":
                collector = get_collector()
                collector.generate_sample_data(20)
            elif msg.get("type") == "get_summary":
                collector = get_collector()
                summary = collector.get_summary(seconds=msg.get("seconds", 300))
                await ws.send_text(json.dumps({"type": "summary", "data": summary}))

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(ws)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML."""
    html_path = Path(__file__).parent / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/metrics")
async def get_metrics(seconds: int = 300):
    """REST endpoint for metrics."""
    collector = get_collector()
    return collector.get_summary(seconds=seconds)


@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts."""
    return {"active": alert_manager.get_active(), "history": alert_manager.get_history()}


@app.post("/api/simulate")
async def simulate_traffic(count: int = 20):
    """Generate simulated metrics for demo."""
    collector = get_collector()
    collector.generate_sample_data(count)
    return {"status": "generated", "count": count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
