"""
AI创作工坊 - Agent Orchestrator

A graph-based agent orchestration system inspired by LangGraph.

Key Concepts:
- **StateGraph**: A directed graph where nodes are functions and edges are routing logic
- **State**: TypedDict that flows through the graph, accumulating data
- **Nodes**: Agent functions that read state, do work, and update state
- **Edges**: Conditional routing that decides which node to execute next
- **Parallel Execution**: Independent nodes can run concurrently
- **Human-in-the-loop**: Checkpoints where human approval is required

This demonstrates LangGraph concepts WITHOUT importing LangGraph — it's a from-scratch
implementation that teaches the underlying patterns.
"""

import asyncio
import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypedDict

from observability.logger import get_logger
from observability.metrics import AGENT_EXECUTION_LATENCY, AGENT_EXECUTION_COUNT

logger = get_logger(__name__)


# ─── State Definition ───────────────────────────────────────

class GraphState(TypedDict, total=False):
    """
    Shared state that flows through the agent graph.
    Each node reads from and writes to this state.
    """
    # Input
    task_id: str
    task_type: str  # "video_generation", "comment_analysis", "research_qa"
    user_id: str
    org_id: str
    input_data: dict[str, Any]

    # Agent outputs
    research_result: dict[str, Any]
    video_result: dict[str, Any]
    comment_result: dict[str, Any]

    # Workflow state
    current_node: str
    completed_nodes: list[str]
    errors: list[str]
    needs_approval: bool
    approved: bool
    approval_reason: str

    # Metadata
    started_at: float
    finished_at: float | None
    token_usage: dict[str, int]


# ─── Node & Edge Types ──────────────────────────────────────

class NodeType(enum.Enum):
    """Types of nodes in the graph."""
    AGENT = "agent"           # Executes an agent function
    TOOL = "tool"             # Executes a tool
    CONDITIONAL = "conditional"  # Routes based on state
    HUMAN = "human"           # Waits for human approval
    PARALLEL = "parallel"     # Executes children in parallel


@dataclass
class GraphNode:
    """A node in the agent graph."""
    name: str
    func: Callable
    node_type: NodeType = NodeType.AGENT
    description: str = ""


@dataclass
class GraphEdge:
    """An edge connecting two nodes, optionally with a condition."""
    source: str
    target: str
    condition: Optional[Callable[[GraphState], bool]] = None


@dataclass
class ParallelBranch:
    """A set of nodes that can execute in parallel."""
    name: str
    node_names: list[str]


# ─── Orchestrator ───────────────────────────────────────────

class AgentOrchestrator:
    """
    Graph-based agent orchestrator.

    Usage:
        orchestrator = AgentOrchestrator()

        # Register nodes
        orchestrator.add_node("research", research_agent.execute)
        orchestrator.add_node("video", video_agent.execute)
        orchestrator.add_node("comment", comment_agent.execute)
        orchestrator.add_node("review", human_review, node_type=NodeType.HUMAN)

        # Define edges
        orchestrator.add_edge("research", "video")
        orchestrator.add_conditional_edge("video", "review", condition=lambda s: s.get("needs_approval"))
        orchestrator.add_edge("review", "comment")
        orchestrator.add_edge("video", "comment")  # Also route video → comment directly

        # Run
        result = await orchestrator.run(initial_state)
    """

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.entry_point: Optional[str] = None
        self.end_nodes: set[str] = set()
        self._approval_callbacks: dict[str, Callable] = {}

    def add_node(
        self,
        name: str,
        func: Callable,
        node_type: NodeType = NodeType.AGENT,
        description: str = "",
    ) -> "AgentOrchestrator":
        """Register a node (agent function) in the graph."""
        self.nodes[name] = GraphNode(
            name=name, func=func, node_type=node_type, description=description
        )
        logger.debug(f"Registered node: {name} ({node_type.value})")
        return self

    def add_edge(self, source: str, target: str) -> "AgentOrchestrator":
        """Add an unconditional edge from source to target node."""
        self.edges.append(GraphEdge(source=source, target=target))
        return self

    def add_conditional_edge(
        self, source: str, target: str, condition: Callable[[GraphState], bool]
    ) -> "AgentOrchestrator":
        """Add a conditional edge — only followed if condition(state) is True."""
        self.edges.append(GraphEdge(source=source, target=target, condition=condition))
        return self

    def set_entry_point(self, name: str) -> "AgentOrchestrator":
        """Set the starting node."""
        self.entry_point = name
        return self

    def add_end(self, name: str) -> "AgentOrchestrator":
        """Mark a node as a terminal node (end of graph)."""
        self.end_nodes.add(name)
        return self

    def register_approval_callback(
        self, node_name: str, callback: Callable
    ) -> "AgentOrchestrator":
        """Register a callback for human-in-the-loop approval at a specific node."""
        self._approval_callbacks[node_name] = callback
        return self

    def _get_next_nodes(self, current_node: str, state: GraphState) -> list[str]:
        """
        Determine which nodes to execute next based on edges and conditions.
        Returns a list of target node names.
        """
        next_nodes = []
        for edge in self.edges:
            if edge.source == current_node:
                if edge.condition is None:
                    # Unconditional edge
                    next_nodes.append(edge.target)
                elif edge.condition(state):
                    # Conditional edge, condition met
                    next_nodes.append(edge.target)
        return next_nodes

    async def _execute_node(self, node: GraphNode, state: GraphState) -> GraphState:
        """
        Execute a single node, updating state with the result.
        Includes metrics collection and error handling.
        """
        logger.info(f"Executing node: {node.name}", extra={"task_id": state.get("task_id")})
        state["current_node"] = node.name
        start = time.perf_counter()

        try:
            # Human-in-the-loop checkpoint
            if node.node_type == NodeType.HUMAN:
                state = await self._handle_human_approval(node, state)
            else:
                # Execute the agent/tool function
                if asyncio.iscoroutinefunction(node.func):
                    result = await node.func(state)
                else:
                    result = node.func(state)

                # Merge result into state
                if isinstance(result, dict):
                    state.update(result)

            # Record metrics
            duration = time.perf_counter() - start
            AGENT_EXECUTION_LATENCY.labels(agent=node.name).observe(duration)
            AGENT_EXECUTION_COUNT.labels(agent=node.name, status="success").inc()

            # Track completed nodes
            if "completed_nodes" not in state:
                state["completed_nodes"] = []
            state["completed_nodes"].append(node.name)

            logger.info(
                f"Node {node.name} completed in {duration:.2f}s",
                extra={"task_id": state.get("task_id")},
            )

        except Exception as e:
            AGENT_EXECUTION_COUNT.labels(agent=node.name, status="error").inc()
            error_msg = f"Node {node.name} failed: {str(e)}"
            logger.error(error_msg, extra={"task_id": state.get("task_id")}, exc_info=True)
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(error_msg)

        return state

    async def _handle_human_approval(
        self, node: GraphNode, state: GraphState
    ) -> GraphState:
        """
        Handle human-in-the-loop approval.
        If a callback is registered, use it. Otherwise, mark state for external approval.
        """
        state["needs_approval"] = True
        state["approval_reason"] = f"Approval required at node: {node.name}"

        if node.name in self._approval_callbacks:
            callback = self._approval_callbacks[node.name]
            if asyncio.iscoroutinefunction(callback):
                approved = await callback(state)
            else:
                approved = callback(state)
            state["approved"] = approved
            state["needs_approval"] = False

            if not approved:
                logger.warning(
                    f"Human approval denied at node: {node.name}",
                    extra={"task_id": state.get("task_id")},
                )
        else:
            # No callback — the workflow will pause and be resumed externally
            logger.info(
                f"Human approval requested at node: {node.name} — workflow paused",
                extra={"task_id": state.get("task_id")},
            )

        return state

    async def _execute_parallel(
        self, node_names: list[str], state: GraphState
    ) -> GraphState:
        """
        Execute multiple independent nodes in parallel using asyncio.gather.
        Results are merged into the shared state.
        """
        logger.info(
            f"Executing parallel nodes: {node_names}",
            extra={"task_id": state.get("task_id")},
        )

        tasks = []
        for name in node_names:
            if name in self.nodes:
                # Each parallel task gets a copy of state to avoid race conditions
                tasks.append(self._execute_node(self.nodes[name], dict(state)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results back — later results override earlier ones for non-conflicting keys
        for result in results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key not in ("completed_nodes", "errors"):
                        state[key] = value
                    elif key == "completed_nodes":
                        existing = state.get("completed_nodes", [])
                        state["completed_nodes"] = list(set(existing + value))
                    elif key == "errors":
                        existing = state.get("errors", [])
                        state["errors"] = existing + value

        return state

    async def run(
        self,
        initial_state: GraphState,
        max_steps: int = 50,
    ) -> GraphState:
        """
        Execute the graph starting from the entry point.

        Algorithm:
        1. Start at entry_point
        2. Execute current node
        3. Find next nodes (via edges)
        4. If multiple next nodes → parallel execution
        5. If no next nodes → end
        6. Guard against infinite loops with max_steps

        Returns the final state after graph execution completes.
        """
        if not self.entry_point:
            raise ValueError("No entry point set. Call set_entry_point() first.")

        state = initial_state.copy()
        state["started_at"] = time.time()
        state["task_id"] = state.get("task_id", str(uuid.uuid4()))
        state["completed_nodes"] = state.get("completed_nodes", [])
        state["errors"] = state.get("errors", [])

        current_node = self.entry_point
        steps = 0

        logger.info(
            f"Graph execution started from: {current_node}",
            extra={"task_id": state.get("task_id")},
        )

        while current_node and steps < max_steps:
            steps += 1

            if current_node not in self.nodes:
                logger.error(f"Node not found: {current_node}")
                state["errors"].append(f"Node not found: {current_node}")
                break

            node = self.nodes[current_node]

            # Check if workflow was paused for approval
            if state.get("needs_approval") and not state.get("approved"):
                logger.info("Workflow paused for human approval")
                break

            # Execute the current node
            state = await self._execute_node(node, state)

            # If there were errors in this node, stop unless we have error-handling edges
            if state["errors"] and len(state["errors"]) > len(initial_state.get("errors", [])):
                # Look for error-handling edges (condition checks for errors)
                next_nodes = self._get_next_nodes(current_node, state)
                if not next_nodes:
                    break

            # Determine next nodes
            next_nodes = self._get_next_nodes(current_node, state)

            if not next_nodes:
                # End of graph
                logger.info(f"Graph execution complete — no more edges from {current_node}")
                break

            if len(next_nodes) > 1:
                # Parallel execution of independent branches
                state = await self._execute_parallel(next_nodes, state)
                # After parallel execution, find the next node after all parallel branches
                all_next = []
                for nn in next_nodes:
                    all_next.extend(self._get_next_nodes(nn, state))
                current_node = all_next[0] if all_next else None
            else:
                current_node = next_nodes[0]

        state["finished_at"] = time.time()
        total_duration = state["finished_at"] - state["started_at"]

        logger.info(
            f"Graph execution finished in {total_duration:.2f}s, {steps} steps",
            extra={
                "task_id": state.get("task_id"),
                "completed_nodes": state.get("completed_nodes"),
                "errors": state.get("errors"),
            },
        )

        return state

    def visualize(self) -> str:
        """
        Generate an ASCII visualization of the graph.
        Useful for debugging and documentation.
        """
        lines = ["Graph Structure:", "=" * 40]

        for name, node in self.nodes.items():
            marker = "→ " if name == self.entry_point else "  "
            end_marker = " [END]" if name in self.end_nodes else ""
            node_type = f" ({node.node_type.value})" if node.node_type != NodeType.AGENT else ""
            lines.append(f"{marker}[{name}]{node_type}{end_marker}")

            # Show outgoing edges
            for edge in self.edges:
                if edge.source == name:
                    cond = " (conditional)" if edge.condition else ""
                    lines.append(f"    └──→ {edge.target}{cond}")

        lines.append("=" * 40)
        return "\n".join(lines)
