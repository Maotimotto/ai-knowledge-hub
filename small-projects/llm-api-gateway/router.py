"""Smart routing for LLM requests based on cost, latency, or quality."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from providers import BaseProvider, LLMResponse, get_available_providers


class Router:
    """Routes LLM requests to the best provider based on strategy."""

    STRATEGIES = ("cost", "latency", "quality", "round-robin")

    def __init__(self, strategy: Optional[str] = None):
        self.strategy = strategy or os.getenv("ROUTING_STRATEGY", "cost")
        self._rr_index = 0
        self._latency_history: dict[str, list[float]] = {}

    def route(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        strategy: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Route a completion request to the best provider."""
        strategy = strategy or self.strategy
        providers = get_available_providers()

        if not providers:
            raise RuntimeError("No LLM providers available. Set API keys in .env")

        if model:
            # Find provider that has this model
            for name, provider in providers.items():
                if model in provider.get_models():
                    return provider.complete(messages, model=model, **kwargs)

        # Auto-select based on strategy
        if strategy == "cost":
            return self._route_by_cost(providers, messages, **kwargs)
        elif strategy == "latency":
            return self._route_by_latency(providers, messages, **kwargs)
        elif strategy == "quality":
            return self._route_by_quality(providers, messages, **kwargs)
        elif strategy == "round-robin":
            return self._route_round_robin(providers, messages, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Use: {self.STRATEGIES}")

    def _route_by_cost(self, providers: dict, messages: list[dict], **kwargs) -> LLMResponse:
        """Select cheapest provider/model combination."""
        best_cost = float("inf")
        best_provider = None
        best_model = None

        for name, provider in providers.items():
            for model in provider.get_models():
                cost = provider.cost_per_1k_tokens.get(model, 999)
                if cost < best_cost:
                    best_cost = cost
                    best_provider = provider
                    best_model = model

        if best_provider and best_model:
            return best_provider.complete(messages, model=best_model, **kwargs)
        raise RuntimeError("No suitable provider found")

    def _route_by_latency(self, providers: dict, messages: list[dict], **kwargs) -> LLMResponse:
        """Select provider with lowest average latency."""
        best_latency = float("inf")
        best_provider = None
        best_model = None

        for name, provider in providers.items():
            history = self._latency_history.get(name, [])
            avg_latency = sum(history) / len(history) if history else 1000
            # Prefer local if available (typically fastest)
            if name == "local" and provider.is_available():
                avg_latency = 100
            if avg_latency < best_latency:
                best_latency = avg_latency
                best_provider = provider
                best_model = provider.get_models()[0] if provider.get_models() else "default"

        if best_provider and best_model:
            response = best_provider.complete(messages, model=best_model, **kwargs)
            # Track latency
            self._latency_history.setdefault(best_provider.name, []).append(response.latency_ms)
            return response
        raise RuntimeError("No suitable provider found")

    def _route_by_quality(self, providers: dict, messages: list[dict], **kwargs) -> LLMResponse:
        """Select highest quality model (heuristic: larger = better)."""
        quality_order = ["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini", "claude-3-haiku-20240307", "gpt-3.5-turbo"]
        for model in quality_order:
            for name, provider in providers.items():
                if model in provider.get_models():
                    return provider.complete(messages, model=model, **kwargs)

        # Fallback to first available
        provider = list(providers.values())[0]
        model = provider.get_models()[0] if provider.get_models() else "default"
        return provider.complete(messages, model=model, **kwargs)

    def _route_round_robin(self, providers: dict, messages: list[dict], **kwargs) -> LLMResponse:
        """Rotate through providers evenly."""
        provider_list = list(providers.values())
        provider = provider_list[self._rr_index % len(provider_list)]
        self._rr_index += 1
        model = provider.get_models()[0] if provider.get_models() else "default"
        return provider.complete(messages, model=model, **kwargs)
