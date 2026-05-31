"""Tests for the multi-agent orchestrator system."""
import pytest
import asyncio
from backend.agents.orchestrator import Orchestrator, AgentState
from backend.agents.tools import ToolRegistry


def test_orchestrator_init():
    """Test orchestrator initializes with default agents."""
    orch = Orchestrator()
    assert "video" in orch.agents
    assert "comment" in orch.agents
    assert "research" in orch.agents


def test_tool_registry():
    """Test tool registry has expected tools."""
    registry = ToolRegistry()
    tools = registry.list_tools()
    assert len(tools) > 0
    names = [t["name"] for t in tools]
    assert "web_search" in names or "calculate" in names


@pytest.mark.asyncio
async def test_orchestrator_simple_run():
    """Test orchestrator can process a simple state."""
    orch = Orchestrator()
    state: AgentState = {
        "input": "Analyze this comment: Great product!",
        "messages": [],
        "results": {},
        "current_agent": "comment",
        "next_agent": None,
        "done": False,
    }
    result = await orch.run(state)
    assert isinstance(result, dict)
    assert "results" in result


def test_state_schema():
    """Test AgentState has required fields."""
    state: AgentState = {
        "input": "test",
        "messages": [],
        "results": {},
        "current_agent": "comment",
        "next_agent": None,
        "done": False,
    }
    assert state["input"] == "test"
    assert state["done"] is False
