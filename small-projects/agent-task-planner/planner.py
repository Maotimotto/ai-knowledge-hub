"""ReAct-style planning agent with tool calling capabilities."""

import json
import os
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from memory import SummaryBufferMemory
from tools import execute_tool, get_tools_description


SYSTEM_PROMPT = """You are a task planning agent. You break down complex goals into actionable plans.

You have access to these tools:
{tools}

To use a tool, respond with EXACTLY this format:
TOOL: <tool_name>
INPUT: <input>

After getting tool results, continue reasoning. When you have enough information,
provide your final plan as a structured JSON:
FINAL_ANSWER: {{
  "goal": "...",
  "tasks": [
    {{"id": 1, "title": "...", "description": "...", "priority": "high/medium/low", "estimated_hours": N}},
    ...
  ],
  "timeline": "...",
  "resources_needed": ["..."],
  "risks": ["..."]
}}

Think step by step. Use tools when they can help gather information or verify assumptions.
"""


class PlanningAgent:
    """ReAct-style agent that plans tasks using tools."""

    def __init__(self):
        self.memory = SummaryBufferMemory()
        self.max_iterations = 10

    def _call_llm(self, messages: list[dict[str, str]]) -> str:
        """Call OpenAI API or use local fallback."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your-k...":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.3,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                return self._fallback_plan(str(messages[-1]["content"]))

        return self._fallback_plan(str(messages[-1]["content"]))

    def _fallback_plan(self, goal: str) -> str:
        """Generate a structured plan without LLM (template-based)."""
        # Extract the actual goal from the message
        if "Goal:" in goal:
            goal = goal.split("Goal:")[-1].strip()

        plan = {
            "goal": goal,
            "tasks": [
                {"id": 1, "title": "Research & Analysis", "description": f"Research current landscape and best practices for: {goal}", "priority": "high", "estimated_hours": 4},
                {"id": 2, "title": "Strategy Development", "description": "Develop strategic approach based on research findings", "priority": "high", "estimated_hours": 6},
                {"id": 3, "title": "Resource Planning", "description": "Identify and allocate necessary resources (team, tools, budget)", "priority": "medium", "estimated_hours": 3},
                {"id": 4, "title": "Implementation Planning", "description": "Create detailed implementation plan with milestones", "priority": "high", "estimated_hours": 4},
                {"id": 5, "title": "Execution - Phase 1", "description": "Execute initial phase with core deliverables", "priority": "high", "estimated_hours": 16},
                {"id": 6, "title": "Review & Iterate", "description": "Review Phase 1 results, gather feedback, adjust plan", "priority": "medium", "estimated_hours": 4},
                {"id": 7, "title": "Execution - Phase 2", "description": "Execute remaining phases based on learnings", "priority": "medium", "estimated_hours": 20},
                {"id": 8, "title": "Final Review & Documentation", "description": "Final review, documentation, and handoff", "priority": "low", "estimated_hours": 3},
            ],
            "timeline": "2-3 weeks",
            "resources_needed": ["Team members", "Project management tools", "Budget allocation"],
            "risks": ["Scope creep", "Resource constraints", "Timeline delays"]
        }
        return f"FINAL_ANSWER: {json.dumps(plan, indent=2)}"

    def _parse_tool_call(self, response: str) -> Optional[tuple[str, str]]:
        """Parse tool call from agent response."""
        tool_match = re.search(r'TOOL:\s*(\w+)', response)
        input_match = re.search(r'INPUT:\s*(.+?)(?:\n|$)', response, re.DOTALL)
        if tool_match and input_match:
            return tool_match.group(1), input_match.group(1).strip()
        return None

    def _parse_final_answer(self, response: str) -> Optional[dict]:
        """Parse final answer from agent response."""
        match = re.search(r'FINAL_ANSWER:\s*(\{.+?\})\s*$', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    def plan(self, goal: str) -> dict:
        """
        Create a structured plan for the given goal using ReAct loop.

        Args:
            goal: The high-level goal to plan for

        Returns:
            Structured plan dictionary
        """
        self.memory.clear()
        system = SYSTEM_PROMPT.format(tools=get_tools_description())
        self.memory.add("system", system)

        self.memory.add("user", f"Goal: {goal}")

        for iteration in range(self.max_iterations):
            messages = self.memory.get_messages_for_llm()
            response = self._call_llm(messages)
            self.memory.add("assistant", response)

            # Check for final answer
            final = self._parse_final_answer(response)
            if final:
                return final

            # Check for tool call
            tool_call = self._parse_tool_call(response)
            if tool_call:
                tool_name, tool_input = tool_call
                result = execute_tool(tool_name, tool_input)
                self.memory.add("tool", result, tool_name=tool_name)
                continue

            # If no tool call and no final answer, assume it's the final response
            return {
                "goal": goal,
                "raw_response": response,
                "tasks": [],
                "note": "Agent provided unstructured response"
            }

        return {"goal": goal, "error": "Max iterations reached", "tasks": []}


if __name__ == "__main__":
    agent = PlanningAgent()
    result = agent.plan("Plan a marketing campaign for an AI productivity tool")
    print(json.dumps(result, indent=2))
