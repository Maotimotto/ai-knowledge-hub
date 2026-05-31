"""Tests for API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check returns 200."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_comment_analyze(client):
    """Test comment analysis endpoint."""
    resp = await client.post("/api/comment/analyze", json={"text": "This is great!"})
    assert resp.status_code in (200, 401, 422)  # may need auth


@pytest.mark.asyncio
async def test_knowledge_ask(client):
    """Test knowledge Q&A endpoint."""
    resp = await client.post("/api/knowledge/ask", json={"question": "What is RAG?"})
    assert resp.status_code in (200, 401, 422)


@pytest.mark.asyncio
async def test_video_generate(client):
    """Test video generation endpoint."""
    resp = await client.post("/api/video/generate", json={"title": "AI Tutorial", "style": "educational"})
    assert resp.status_code in (200, 202, 401, 422)


@pytest.mark.asyncio
async def test_admin_stats(client):
    """Test admin stats endpoint."""
    resp = await client.get("/api/admin/stats")
    assert resp.status_code in (200, 401)
