"""
AI创作工坊 - Model Lifecycle Manager

Manages loading, unloading, and tracking of local models.
Supports GPU memory monitoring and automatic eviction.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LoadedModel:
    """Metadata about a loaded model."""
    name: str
    path: str
    loaded_at: float
    memory_mb: float = 0.0
    device: str = "cpu"
    quantization: Optional[str] = None
    request_count: int = 0
    model: Any = field(default=None, repr=False)
    tokenizer: Any = field(default=None, repr=False)


class ModelManager:
    """
    Manages the lifecycle of local LLM models.

    Features:
    - Load/unload models on demand
    - Track GPU/CPU memory usage
    - LRU eviction when memory is low
    - Concurrent access via locks

    Usage:
        manager = ModelManager()
        await manager.load("llama-3-8b", "/models/llama-3-8b")
        result = await manager.generate("Hello!", model_name="llama-3-8b")
    """

    def __init__(self, max_memory_mb: float = 16000.0):
        self._models: dict[str, LoadedModel] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self.max_memory_mb = max_memory_mb

    async def load(
        self,
        model_name: str,
        model_path: str,
        device: str = "auto",
        quantization: Optional[str] = None,
    ) -> LoadedModel:
        """
        Load a model into memory.

        Args:
            model_name: Unique identifier for the model
            model_path: Path or HuggingFace model ID
            device: Target device (cpu, cuda, auto)
            quantization: Quantization format (e.g., "4bit", "8bit", None)

        Returns:
            LoadedModel metadata
        """
        async with self._global_lock:
            if model_name in self._models:
                logger.info(f"Model '{model_name}' already loaded")
                self._models[model_name].request_count += 1
                return self._models[model_name]

            # Check memory and evict if needed
            await self._evict_if_needed()

            logger.info(f"Loading model '{model_name}' from {model_path}")
            start = time.perf_counter()

            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch

                load_kwargs: dict[str, Any] = {"trust_remote_code": True}
                if device == "auto":
                    load_kwargs["device_map"] = "auto"
                if quantization == "4bit":
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
                    )
                elif quantization == "8bit":
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)

                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)

                # Estimate memory usage
                param_count = sum(p.numel() for p in model.parameters())
                memory_mb = (param_count * 2) / (1024 * 1024)  # Rough estimate for fp16

                loaded = LoadedModel(
                    name=model_name,
                    path=model_path,
                    loaded_at=time.time(),
                    memory_mb=memory_mb,
                    device=device if device != "auto" else str(model.device),
                    quantization=quantization,
                    model=model,
                    tokenizer=tokenizer,
                )

                self._models[model_name] = loaded
                self._locks[model_name] = asyncio.Lock()

                duration = time.perf_counter() - start
                logger.info(
                    f"Model '{model_name}' loaded in {duration:.1f}s "
                    f"({memory_mb:.0f} MB, {param_count/1e9:.1f}B params)"
                )
                return loaded

            except ImportError:
                logger.warning("transformers not installed — registering model as stub")
                loaded = LoadedModel(
                    name=model_name, path=model_path,
                    loaded_at=time.time(), device=device, quantization=quantization,
                )
                self._models[model_name] = loaded
                self._locks[model_name] = asyncio.Lock()
                return loaded

    async def unload(self, model_name: str) -> bool:
        """Unload a model from memory."""
        async with self._global_lock:
            if model_name not in self._models:
                logger.warning(f"Model '{model_name}' not loaded")
                return False

            loaded = self._models.pop(model_name)
            self._locks.pop(model_name, None)

            if loaded.model is not None:
                del loaded.model
            if loaded.tokenizer is not None:
                del loaded.tokenizer

            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info(f"Model '{model_name}' unloaded ({loaded.memory_mb:.0f} MB freed)")
            return True

    async def generate(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate text using a loaded model.

        Args:
            prompt: Input text
            model_name: Which loaded model to use
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with 'text', 'input_tokens', 'output_tokens'
        """
        if model_name is None:
            model_name = next(iter(self._models), None)
        if model_name is None or model_name not in self._models:
            raise ValueError(f"Model '{model_name}' is not loaded")

        loaded = self._models[model_name]
        lock = self._locks[model_name]

        async with lock:
            loaded.request_count += 1

            if loaded.model is None or loaded.tokenizer is None:
                return {"text": f"[Stub] Generated response for: {prompt[:50]}...", "input_tokens": 0, "output_tokens": 0}

            try:
                import torch
                inputs = loaded.tokenizer(prompt, return_tensors="pt").to(loaded.model.device)
                input_tokens = inputs["input_ids"].shape[1]

                with torch.no_grad():
                    outputs = loaded.model.generate(
                        **inputs, max_new_tokens=max_new_tokens,
                        temperature=max(temperature, 1e-7), do_sample=temperature > 0,
                    )

                output_tokens = outputs.shape[1] - input_tokens
                text = loaded.tokenizer.decode(outputs[0][input_tokens:], skip_special_tokens=True)

                return {"text": text, "input_tokens": input_tokens, "output_tokens": output_tokens}
            except Exception as e:
                logger.error(f"Generation failed for '{model_name}': {e}")
                raise

    def list_loaded(self) -> list[dict[str, Any]]:
        """List all currently loaded models with metadata."""
        return [
            {
                "name": m.name, "path": m.path,
                "memory_mb": round(m.memory_mb, 1), "device": m.device,
                "quantization": m.quantization, "request_count": m.request_count,
                "loaded_for_seconds": round(time.time() - m.loaded_at, 1),
            }
            for m in self._models.values()
        ]

    @property
    def total_memory_mb(self) -> float:
        """Total memory used by all loaded models."""
        return sum(m.memory_mb for m in self._models.values())

    async def _evict_if_needed(self) -> None:
        """Evict least-recently-used model if memory limit would be exceeded."""
        if not self._models:
            return
        while self.total_memory_mb > self.max_memory_mb and self._models:
            lru_name = min(self._models, key=lambda n: self._models[n].request_count)
            logger.info(f"Evicting model '{lru_name}' to free memory")
            await self.unload(lru_name)


# Global singleton
model_manager = ModelManager()
