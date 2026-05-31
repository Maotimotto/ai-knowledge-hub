"""LLM Provider implementations for OpenAI, Anthropic, and local models."""

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()


class LLMResponse:
    """Standardized response from any LLM provider."""

    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0,
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.latency_ms = latency_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "latency_ms": round(self.latency_ms, 2),
        }


class BaseProvider(ABC):
    """Base class for LLM providers."""

    name: str = "base"

    @abstractmethod
    def complete(self, messages: list[dict], model: str, **kwargs) -> LLMResponse:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_models(self) -> list[str]:
        ...

    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> dict[str, float]:
        """Cost per 1K tokens for each model."""
        ...


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def get_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

    @property
    def cost_per_1k_tokens(self) -> dict[str, float]:
        return {"gpt-4o": 0.01, "gpt-4o-mini": 0.00015, "gpt-3.5-turbo": 0.0005}

    def complete(self, messages: list[dict], model: str = "gpt-3.5-turbo", **kwargs) -> LLMResponse:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", 0.7),
        )
        latency = (time.time() - start) * 1000
        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=model,
            provider=self.name,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency,
        )


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-ant-"))

    def get_models(self) -> list[str]:
        return ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]

    @property
    def cost_per_1k_tokens(self) -> dict[str, float]:
        return {"claude-3-5-sonnet-20241022": 0.003, "claude-3-haiku-20240307": 0.00025}

    def complete(self, messages: list[dict], model: str = "claude-3-haiku-20240307", **kwargs) -> LLMResponse:
        import httpx
        start = time.time()
        # Convert OpenAI format to Anthropic format
        system_msg = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append(msg)

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 500),
                "system": system_msg,
                "messages": anthropic_messages,
            },
            timeout=30,
        )
        latency = (time.time() - start) * 1000
        data = resp.json()
        content = data.get("content", [{}])[0].get("text", "")
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=model,
            provider=self.name,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            latency_ms=latency,
        )


class LocalProvider(BaseProvider):
    """Provider for local models (Ollama, vLLM, etc.)."""

    name = "local"

    def __init__(self):
        self.base_url = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def get_models(self) -> list[str]:
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=2)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return ["llama2", "mistral"]

    @property
    def cost_per_1k_tokens(self) -> dict[str, float]:
        return {m: 0.0 for m in self.get_models()}  # Free!

    def complete(self, messages: list[dict], model: str = "llama2", **kwargs) -> LLMResponse:
        import httpx
        start = time.time()
        resp = httpx.post(
            f"{self.base_url}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=60,
        )
        latency = (time.time() - start) * 1000
        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=model,
            provider=self.name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            latency_ms=latency,
        )


# Registry of all providers
def get_all_providers() -> dict[str, BaseProvider]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "local": LocalProvider(),
    }


def get_available_providers() -> dict[str, BaseProvider]:
    return {name: p for name, p in get_all_providers().items() if p.is_available()}
