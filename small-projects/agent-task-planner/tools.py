"""Tools available to the planning agent."""

import json
import math
import os
import subprocess
from typing import Any


def calculator(expression: str) -> str:
    """Evaluate a math expression safely."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return f"Error: Invalid characters in expression: {expression}"
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def web_search(query: str) -> str:
    """Simulate web search (returns structured mock results)."""
    # In production, use a real search API (SerpAPI, Tavily, etc.)
    return json.dumps({
        "query": query,
        "results": [
            {"title": f"Result for '{query}' - Overview", "snippet": f"Comprehensive information about {query}..."},
            {"title": f"{query} - Best Practices", "snippet": f"Top strategies and approaches for {query}..."},
            {"title": f"{query} - Case Studies", "snippet": f"Real-world examples of {query} implementation..."},
        ],
        "note": "Mock search results - integrate real API for production"
    })


def file_operation(action: str, path: str, content: str = "") -> str:
    """Read, write, or list files."""
    try:
        if action == "read":
            with open(path, "r") as f:
                return f.read()[:2000]
        elif action == "write":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Written {len(content)} chars to {path}"
        elif action == "list":
            return "\n".join(os.listdir(path) if os.path.isdir(path) else [path])
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"Error: {e}"


def code_execute(code: str) -> str:
    """Execute Python code in a sandboxed subprocess."""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output[:1000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (10s limit)"
    except Exception as e:
        return f"Error: {e}"


# Tool registry with descriptions for the agent
TOOLS: dict[str, dict[str, Any]] = {
    "calculator": {
        "fn": calculator,
        "description": "Evaluate math expressions. Input: a math expression string like '2 + 3 * 4'",
        "param": "expression",
    },
    "web_search": {
        "fn": web_search,
        "description": "Search the web for information. Input: search query string",
        "param": "query",
    },
    "file_operation": {
        "fn": file_operation,
        "description": "File operations. Input: JSON with 'action' (read/write/list), 'path', optional 'content'",
        "param": "json_input",
    },
    "code_execute": {
        "fn": code_execute,
        "description": "Execute Python code. Input: Python code string",
        "param": "code",
    },
}


def execute_tool(name: str, input_str: str) -> str:
    """Execute a tool by name with the given input."""
    if name not in TOOLS:
        return f"Unknown tool: {name}. Available: {list(TOOLS.keys())}"

    tool = TOOLS[name]
    try:
        if name == "file_operation":
            data = json.loads(input_str)
            return tool["fn"](**data)
        else:
            return tool["fn"](input_str)
    except Exception as e:
        return f"Tool error: {e}"


def get_tools_description() -> str:
    """Get formatted description of all tools for the agent prompt."""
    lines = []
    for name, info in TOOLS.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)
