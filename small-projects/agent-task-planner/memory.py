"""Conversation memory with summary buffer to manage context length."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_name: Optional[str] = None


class SummaryBufferMemory:
    """
    Memory that keeps recent messages verbatim and summarizes older ones.
    Prevents context window overflow while preserving key information.
    """

    def __init__(self, max_tokens: int = 2000, summary_threshold: int = 10):
        self.messages: list[Message] = []
        self.summary: str = ""
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold

    def add(self, role: str, content: str, tool_name: Optional[str] = None) -> None:
        """Add a message to memory."""
        self.messages.append(Message(role=role, content=content, tool_name=tool_name))
        if len(self.messages) > self.summary_threshold:
            self._compress()

    def _compress(self) -> None:
        """Compress old messages into a summary, keeping recent ones."""
        if len(self.messages) <= self.summary_threshold:
            return

        # Keep last 6 messages, summarize the rest
        to_summarize = self.messages[:-6]
        self.messages = self.messages[-6:]

        # Simple summarization (in production, use LLM)
        old_summary = self.summary
        action_items = []
        for msg in to_summarize:
            if msg.role == "user":
                action_items.append(f"User asked: {msg.content[:100]}")
            elif msg.role == "assistant":
                action_items.append(f"Agent did: {msg.content[:100]}")
            elif msg.role == "tool":
                action_items.append(f"Tool {msg.tool_name}: {msg.content[:80]}")

        new_part = "; ".join(action_items[-5:])  # Keep last 5 actions
        self.summary = f"{old_summary}\n{new_part}".strip()[-1000:]  # Cap summary length

    def get_context(self) -> str:
        """Get the full conversation context for the agent."""
        parts = []
        if self.summary:
            parts.append(f"[Previous context summary]: {self.summary}")
        for msg in self.messages:
            if msg.tool_name:
                parts.append(f"[{msg.role}/{msg.tool_name}]: {msg.content}")
            else:
                parts.append(f"[{msg.role}]: {msg.content}")
        return "\n".join(parts)

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """Get messages formatted for OpenAI API."""
        msgs: list[dict[str, str]] = []
        if self.summary:
            msgs.append({"role": "system", "content": f"Previous context: {self.summary}"})
        for msg in self.messages:
            msgs.append({"role": msg.role, "content": msg.content})
        return msgs

    def clear(self) -> None:
        self.messages.clear()
        self.summary = ""

    @property
    def message_count(self) -> int:
        return len(self.messages)
