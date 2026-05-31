"""
AI创作工坊 - Shared Agent Tools

Tools are reusable functions that agents can invoke.
This implements the tool-use pattern common in AI agent systems.

Each tool has:
- name: Unique identifier
- description: What it does (used by agents to decide when to use it)
- parameters: Schema for input validation
- execute: The actual function
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """A tool that agents can use."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    execute: Callable
    requires_approval: bool = False

    def to_schema(self) -> dict:
        """Convert to tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Registry of available tools for agents."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """List all tools as schemas."""
        return [t.to_schema() for t in self._tools.values()]

    async def execute(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name with parameters."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool not found: {name}"}

        start = time.perf_counter()
        try:
            if callable(tool.execute):
                import asyncio
                if asyncio.iscoroutinefunction(tool.execute):
                    result = await tool.execute(**params)
                else:
                    result = tool.execute(**params)
            else:
                result = {"error": "Tool execute is not callable"}

            duration = time.perf_counter() - start
            logger.info(f"Tool {name} executed in {duration:.2f}s")
            return {"result": result, "duration_ms": round(duration * 1000, 2)}

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return {"error": str(e)}


# ─── Built-in Tools ─────────────────────────────────────────

def search_knowledge_base(query: str, top_k: int = 5) -> dict:
    """Search the RAG knowledge base for relevant documents."""
    # In production, this would call the RAG retriever
    return {
        "query": query,
        "results": [],
        "total": 0,
        "message": "Knowledge base search executed (retriever not connected in this context)",
    }


def web_search(query: str, num_results: int = 5) -> dict:
    """Search the web for current information."""
    return {
        "query": query,
        "results": [],
        "message": "Web search executed (API not configured in this context)",
    }


def generate_image_prompt(description: str, style: str = "realistic") -> str:
    """Generate an optimized image prompt for AI image generation."""
    styles = {
        "realistic": "photorealistic, high detail, professional photography",
        "cartoon": "cartoon style, vibrant colors, clean lines",
        "anime": "anime style, detailed, Studio Ghibli inspired",
        "minimalist": "minimalist design, clean, modern, simple shapes",
    }
    style_suffix = styles.get(style, style)
    return f"{description}, {style_suffix}, 4k, high quality"


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate token count for text."""
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


# ─── Default Tool Registry ──────────────────────────────────

def get_default_tools() -> ToolRegistry:
    """Create a tool registry with default tools."""
    registry = ToolRegistry()

    registry.register(Tool(
        name="search_knowledge_base",
        description="Search the AI knowledge base for relevant documents and information",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        },
        execute=search_knowledge_base,
    ))

    registry.register(Tool(
        name="web_search",
        description="Search the web for current information not in the knowledge base",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        execute=web_search,
    ))

    registry.register(Tool(
        name="generate_image_prompt",
        description="Generate an optimized prompt for AI image generation",
        parameters={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Image description"},
                "style": {"type": "string", "enum": ["realistic", "cartoon", "anime", "minimalist"]},
            },
            "required": ["description"],
        },
        execute=generate_image_prompt,
    ))

    registry.register(Tool(
        name="count_tokens",
        description="Count the number of tokens in text for a given model",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "model": {"type": "string", "default": "gpt-4"},
            },
            "required": ["text"],
        },
        execute=count_tokens,
    ))

    return registry
