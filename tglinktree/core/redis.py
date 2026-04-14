"""Redis client for caching and rate limiting."""

from __future__ import annotations

import logging
import time
from typing import Optional

import redis.asyncio as aioredis

from tglinktree.config import get_settings

logger = logging.getLogger(__name__)

# ── Global client (initialized in lifespan) ──────────────────
_redis: Optional[aioredis.Redis] = None


async def init_redis() -> Optional[aioredis.Redis]:
    """Create and store the global Redis connection. Fails gracefully if Redis is down."""
    global _redis
    settings = get_settings()
    try:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # Verify connectivity
        await _redis.ping()
        logger.info("Redis connected.")
        return _redis
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Caching and rate limiting will be disabled.")
        _redis = None
        return None


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


def get_redis() -> Optional[aioredis.Redis]:
    """Return the global Redis client, or None if not available."""
    return _redis


# ── Rate Limiting (sliding window) ───────────────────────────
async def check_rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> bool:
    """
    Sliding-window rate limiter.

    Returns True if the request is ALLOWED, False if rate-limited.
    """
    r = get_redis()
    if r is None:
        return True # Allow all if Redis is down (fallback)

    now = time.time()
    window_start = now - window_seconds
    pipe_key = f"ratelimit:{key}"

    try:
        pipe = r.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(pipe_key, 0, window_start)
        # Count remaining entries
        pipe.zcard(pipe_key)
        # Add current request
        pipe.zadd(pipe_key, {str(now): now})
        # Set TTL so keys don't leak
        pipe.expire(pipe_key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]  # zcard result
        return current_count < max_requests
    except Exception:
        return True # Fallback to allowed on Redis error


# ── Cache Helpers ─────────────────────────────────────────────
async def cache_get(key: str) -> Optional[str]:
    """Get a cached value."""
    r = get_redis()
    if r is None: return None
    try:
        return await r.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    """Set a cached value with TTL in seconds."""
    r = get_redis()
    if r is None: return
    try:
        await r.set(key, value, ex=ttl)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    """Delete a cached key."""
    r = get_redis()
    if r is None: return
    try:
        await r.delete(key)
    except Exception:
        pass
