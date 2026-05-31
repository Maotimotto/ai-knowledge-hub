"""
AI创作工坊 - Multi-Agent System

This package implements a graph-based agent orchestration system inspired by LangGraph.
Each agent is a node in a directed graph; edges define routing logic.

Agents:
- VideoAgent: Generates video content using AI models
- CommentAgent: Analyzes and responds to comments
- ResearchAgent: Retrieves and synthesizes information via RAG

The Orchestrator manages state, routing, parallel execution, and human-in-the-loop.
"""

from agents.orchestrator import AgentOrchestrator, GraphState
from agents.video_agent import VideoAgent
from agents.comment_agent import CommentAgent
from agents.research_agent import ResearchAgent

__all__ = [
    "AgentOrchestrator",
    "GraphState",
    "VideoAgent",
    "CommentAgent",
    "ResearchAgent",
]
