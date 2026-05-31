"""
AI创作工坊 - Embedding Models

Provides text embedding functionality for the RAG pipeline.

Supports:
- Sentence Transformers (local, open-source)
- OpenAI Embeddings (API-based)
- Caching for efficiency

Key concepts:
- Embeddings convert text to dense vector representations
- Similar vectors indicate semantically similar text
- Used for semantic search in vector databases
"""

import hashlib
import time
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from observability.logger import get_logger

logger = get_logger(__name__)


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        ...


class SentenceTransformerEmbeddings(EmbeddingModel):
    """
    Local embedding using sentence-transformers.

    Default model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    Alternatives:
    - all-mpnet-base-v2 (768 dimensions, higher quality)
    - paraphrase-multilingual-MiniLM-L12-v2 (384 dims, multilingual)
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self._model_name}")
                self._model = SentenceTransformer(self._model_name)
                # Get dimension from a test embedding
                test = self._model.encode(["test"])
                self._dimension = test.shape[1]
                logger.info(f"Model loaded: {self._dimension} dimensions")
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback")
                self._model = "fallback"
                self._dimension = 384

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        self._load_model()
        if self._model == "fallback":
            # Deterministic fallback for testing (hash-based pseudo-embedding)
            return self._fallback_embed(text)
        embedding = self._model.encode([text])[0]
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        self._load_model()
        if self._model == "fallback":
            return [self._fallback_embed(t) for t in texts]
        embeddings = self._model.encode(texts)
        return embeddings.tolist()

    def _fallback_embed(self, text: str) -> list[float]:
        """Generate a deterministic pseudo-embedding for testing."""
        h = hashlib.sha256(text.encode()).digest()
        # Generate 384 float values from hash
        vec = []
        for i in range(0, min(len(h), 48), 1):
            for j in range(8):
                if len(vec) >= 384:
                    break
                vec.append(((h[i] >> j) & 1) * 2.0 - 1.0)
        # Pad to 384
        while len(vec) < 384:
            vec.append(0.0)
        # Normalize
        norm = sum(x**2 for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec[:384]

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension or 384

    @property
    def model_name(self) -> str:
        return self._model_name


class OpenAIEmbeddings(EmbeddingModel):
    """
    OpenAI API-based embeddings.

    Models:
    - text-embedding-3-small: 1536 dimensions, cost-effective
    - text-embedding-3-large: 3072 dimensions, highest quality
    - text-embedding-ada-002: 1536 dimensions, legacy
    """

    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = ""):
        self._model_name = model_name
        self._api_key = api_key
        self._client = None

        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """Embed text using OpenAI API."""
        client = self._get_client()
        response = await client.embeddings.create(
            input=text,
            model=self._model_name,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch using OpenAI API (single API call)."""
        client = self._get_client()
        response = await client.embeddings.create(
            input=texts,
            model=self._model_name,
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimensions.get(self._model_name, 1536)

    @property
    def model_name(self) -> str:
        return self._model_name


def get_embedding_model(provider: str = "local", **kwargs) -> EmbeddingModel:
    """
    Factory function to get an embedding model.

    Args:
        provider: "local" for sentence-transformers, "openai" for OpenAI API
        **kwargs: Additional arguments for the model constructor
    """
    if provider == "openai":
        return OpenAIEmbeddings(**kwargs)
    else:
        return SentenceTransformerEmbeddings(**kwargs)
