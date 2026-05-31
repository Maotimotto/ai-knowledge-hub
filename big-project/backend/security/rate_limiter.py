"""
AI创作工坊 - Token Bucket Rate Limiter

Implements rate limiting using the token bucket algorithm.
Supports Redis (distributed) or in-memory (local) backends.
"""

import time
from typing import Optional, Tuple

from observability.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with Redis or in-memory backend.

    Each client gets a bucket that fills at `limit` tokens per minute
    with a burst capacity of `burst` tokens.

    Usage:
        limiter = RateLimiter(redis=None, limit=60, burst=10)
        allowed, remaining, reset_at = await limiter.check("client_ip")
    """

    def __init__(
        self,
        redis: Optional[object] = None,
        limit: int = 60,
        burst: int = 10,
        window_seconds: int = 60,
    ):
        self.redis = redis
        self.limit = limit
        self.burst = burst
        self.window_seconds = window_seconds
        self._buckets: dict[str, dict[str, float]] = {}

    async def check(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if a request is allowed for the given client.

        Args:
            client_id: Unique client identifier (e.g., IP address)

        Returns:
            Tuple of (allowed, remaining_tokens, reset_timestamp)
        """
        if self.redis is not None:
            return await self._check_redis(client_id)
        return self._check_memory(client_id)

    async def _check_redis(self, client_id: str) -> Tuple[bool, int, int]:
        """Check rate limit using Redis (distributed)."""
        key = f"ratelimit:{client_id}"
        now = time.time()

        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window_seconds)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()

            request_count = results[1]
            remaining = max(0, self.limit + self.burst - request_count)
            allowed = request_count < self.limit + self.burst
            reset_at = int(now + self.window_seconds)

            if not allowed:
                logger.warning(f"Rate limit exceeded for client={client_id}")

            return allowed, remaining, reset_at

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open — allow the request if Redis is down
            return True, self.limit, int(now + self.window_seconds)

    def _check_memory(self, client_id: str) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory dict (single instance)."""
        now = time.time()

        if client_id not in self._buckets:
            self._buckets[client_id] = {
                "tokens": float(self.limit + self.burst),
                "last_refill": now,
            }

        bucket = self._buckets[client_id]

        # Refill tokens based on elapsed time
        elapsed = now - bucket["last_refill"]
        refill_rate = self.limit / self.window_seconds  # tokens per second
        bucket["tokens"] = min(
            float(self.limit + self.burst),
            bucket["tokens"] + elapsed * refill_rate,
        )
        bucket["last_refill"] = now

        # Check if request is allowed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            remaining = int(bucket["tokens"])
            return True, remaining, int(now + self.window_seconds)
        else:
            remaining = 0
            logger.warning(f"Rate limit exceeded for client={client_id}")
            return False, remaining, int(now + self.window_seconds)

    async def reset(self, client_id: str) -> None:
        """Reset rate limit for a specific client."""
        if self.redis is not None:
            await self.redis.delete(f"ratelimit:{client_id}")
        else:
            self._buckets.pop(client_id, None)
        logger.info(f"Rate limit reset for client={client_id}")
