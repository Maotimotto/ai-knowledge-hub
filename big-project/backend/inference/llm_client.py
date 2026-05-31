"""
AI创作工坊 - Multi-Provider LLM Client

Supports OpenAI, Anthropic, and local model inference with:
- Automatic provider fallback chain
- Streaming responses
- Token counting and cost tracking
- Retry logic with exponential backoff
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional

import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from observability.logger import get_logger
from observability.metrics import TOKEN_USAGE_COUNTER

logger = get_logger(__name__)
settings = get_settings()


class Provider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


# Cost per 1K tokens (input, output)
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-5-sonnet-20241022": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
    "local": (0.0, 0.0),
}


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""
    content: str
    finish_reason: Optional[str] = None


class LLMClient:
    """
    Multi-provider LLM client with fallback chain.

    Usage:
        client = LLMClient()
        response = await client.generate("Explain RAG", temperature=0.7)
        async for chunk in client.stream("Write a story"):
            print(chunk.content, end="")
    """

    def __init__(
        self,
        providers: Optional[list[str]] = None,
        default_model: Optional[str] = None,
    ):
        self.providers = providers or settings.provider_list
        self.default_model = default_model or settings.llm_default_model
        self._clients: dict[str, Any] = {}
        self._total_cost: float = 0.0
        self._total_tokens: int = 0
        self._init_clients()

    def _init_clients(self) -> None:
        """Initialize provider clients lazily."""
        if "openai" in self.providers:
            from openai import AsyncOpenAI
            self._clients["openai"] = AsyncOpenAI(api_key=settings.openai_api_key)
        if "anthropic" in self.providers:
            from anthropic import AsyncAnthropic
            self._clients["anthropic"] = AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """Count tokens using tiktoken (approximation for non-OpenAI models)."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on model and token counts."""
        input_rate, output_rate = MODEL_COSTS.get(model, (0.0, 0.0))
        cost = (input_tokens / 1000) * input_rate + (output_tokens / 1000) * output_rate
        self._total_cost += cost
        return round(cost, 6)

    def _record_usage(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record token usage in Prometheus metrics."""
        TOKEN_USAGE_COUNTER.labels(provider=provider, model=model, direction="input").inc(input_tokens)
        TOKEN_USAGE_COUNTER.labels(provider=provider, model=model, direction="output").inc(output_tokens)
        self._total_tokens += input_tokens + output_tokens

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _generate_openai(
        self, prompt: str, system: str, model: str, **kwargs: Any
    ) -> LLMResponse:
        """Generate using OpenAI API."""
        client = self._clients["openai"]
        start = time.perf_counter()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        latency = (time.perf_counter() - start) * 1000

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else self._count_tokens(prompt)
        output_tokens = usage.completion_tokens if usage else self._count_tokens(response.choices[0].message.content or "")
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self._record_usage("openai", model, input_tokens, output_tokens)

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=model,
            provider="openai",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency, 2),
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _generate_anthropic(
        self, prompt: str, system: str, model: str, **kwargs: Any
    ) -> LLMResponse:
        """Generate using Anthropic API."""
        client = self._clients["anthropic"]
        start = time.perf_counter()

        params: dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if system:
            params["system"] = system
        params["max_tokens"] = kwargs.get("max_tokens", 2048)
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]

        response = await client.messages.create(**params)
        latency = (time.perf_counter() - start) * 1000

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self._record_usage("anthropic", model, input_tokens, output_tokens)

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=model,
            provider="anthropic",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency, 2),
            finish_reason=response.stop_reason or "stop",
        )

    async def _generate_local(
        self, prompt: str, system: str, model: str, **kwargs: Any
    ) -> LLMResponse:
        """Generate using a local model via model_manager."""
        from inference.model_manager import model_manager

        start = time.perf_counter()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        result = await model_manager.generate(full_prompt, model_name=model, **kwargs)
        latency = (time.perf_counter() - start) * 1000

        return LLMResponse(
            content=result["text"],
            model=model,
            provider="local",
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            cost_usd=0.0,
            latency_ms=round(latency, 2),
        )

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response with automatic provider fallback.

        Args:
            prompt: User prompt
            system: System prompt
            model: Model name (defaults to configured default)
            provider: Force a specific provider
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            LLMResponse with content, usage, and cost data
        """
        model = model or self.default_model
        providers_to_try = [provider] if provider else self.providers

        last_error: Optional[Exception] = None
        for prov in providers_to_try:
            try:
                gen_kwargs = {"temperature": temperature, "max_tokens": max_tokens, **kwargs}
                if prov == "openai":
                    return await self._generate_openai(prompt, system, model, **gen_kwargs)
                elif prov == "anthropic":
                    return await self._generate_anthropic(prompt, system, model, **gen_kwargs)
                elif prov == "local":
                    return await self._generate_local(prompt, system, model, **gen_kwargs)
            except Exception as e:
                logger.warning(f"Provider {prov} failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def stream(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a response token by token.

        Yields:
            StreamChunk objects with incremental content
        """
        model = model or self.default_model
        prov = provider or self.providers[0]

        if prov == "openai":
            client = self._clients["openai"]
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            stream = await client.chat.completions.create(
                model=model, messages=messages, stream=True, **kwargs
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield StreamChunk(content=delta.content)
                if chunk.choices[0].finish_reason:
                    yield StreamChunk(content="", finish_reason=chunk.choices[0].finish_reason)

        elif prov == "anthropic":
            client = self._clients["anthropic"]
            params: dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": kwargs.get("max_tokens", 2048)}
            if system:
                params["system"] = system

            async with client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(content=text)
                yield StreamChunk(content="", finish_reason="stop")

        else:
            # Local models: simulate streaming by yielding the full response
            response = await self._generate_local(prompt, system, model, **kwargs)
            yield StreamChunk(content=response.content, finish_reason="stop")

    @property
    def usage_stats(self) -> dict[str, Any]:
        """Return cumulative usage statistics."""
        return {
            "total_cost_usd": round(self._total_cost, 6),
            "total_tokens": self._total_tokens,
        }
