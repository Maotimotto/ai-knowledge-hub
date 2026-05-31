"""Semantic cache for similar LLM queries to reduce costs and latency."""

import hashlib
import json
import os
import time
from typing import Optional


class SemanticCache:
    """
    Cache LLM responses based on query similarity.
    Uses exact match + semantic hashing for efficient lookup.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: dict[str, dict] = {}  # hash -> {response, timestamp, hits}
        self._stats = {"hits": 0, "misses": 0}

    def _compute_key(self, messages: list[dict], model: str) -> str:
        """Compute cache key from messages and model."""
        # Normalize messages for consistent hashing
        content = json.dumps(messages, sort_keys=True) + model
        return hashlib.sha256(content.encode()).hexdigest()

    def _normalize_query(self, text: str) -> str:
        """Normalize query text for fuzzy matching."""
        return " ".join(text.lower().strip().split())

    def get(self, messages: list[dict], model: str) -> Optional[dict]:
        """Look up a cached response."""
        key = self._compute_key(messages, model)

        # Exact match
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                entry["hits"] += 1
                self._stats["hits"] += 1
                return entry["response"]
            else:
                del self._cache[key]

        # Fuzzy match: check last user message similarity
        if messages:
            user_msg = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_msg = self._normalize_query(msg["content"])
                    break

            if user_msg:
                for cached_key, entry in self._cache.items():
                    if time.time() - entry["timestamp"] >= self.ttl:
                        continue
                    cached_query = entry.get("normalized_query", "")
                    # Simple word overlap similarity
                    if self._similarity(user_msg, cached_query) > 0.85:
                        entry["hits"] += 1
                        self._stats["hits"] += 1
                        return entry["response"]

        self._stats["misses"] += 1
        return None

    def set(self, messages: list[dict], model: str, response: dict) -> None:
        """Store a response in cache."""
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict()

        key = self._compute_key(messages, model)
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = self._normalize_query(msg["content"])
                break

        self._cache[key] = {
            "response": response,
            "timestamp": time.time(),
            "hits": 0,
            "normalized_query": user_msg,
        }

    def _similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity (Jaccard)."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def _evict(self) -> None:
        """Remove least recently used and expired entries."""
        now = time.time()
        # Remove expired
        expired = [k for k, v in self._cache.items() if now - v["timestamp"] >= self.ttl]
        for k in expired:
            del self._cache[k]

        # Remove LRU if still over capacity
        if len(self._cache) >= self.max_size:
            lru_key = min(self._cache, key=lambda k: self._cache[k]["hits"])
            del self._cache[lru_key]

    def clear(self) -> None:
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0}

    def get_stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        return {
            "size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(self._stats["hits"] / total, 3) if total > 0 else 0,
        }
