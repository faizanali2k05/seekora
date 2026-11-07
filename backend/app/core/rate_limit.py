import asyncio
import time
from collections import defaultdict, deque

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._events: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        threshold = now - window_seconds
        async with self._lock:
            events = self._events[key]
            while events and events[0] <= threshold:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


class ResilientRateLimiter:
    """Redis-backed limiter with a process-local safety fallback for local development."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=0.1,
            socket_timeout=0.1,
        )
        self.fallback = MemoryRateLimiter()
        self.redis_available = True

    async def allow(self, key: str) -> bool:
        if not self.redis_available:
            return await self.fallback.allow(
                key,
                self.settings.rate_limit_requests,
                self.settings.rate_limit_window_seconds,
            )
        try:
            bucket = int(time.time()) // self.settings.rate_limit_window_seconds
            redis_key = f"seekora:rate:{key}:{bucket}"
            count = await self.redis.incr(redis_key)
            if count == 1:
                await self.redis.expire(redis_key, self.settings.rate_limit_window_seconds + 1)
            return count <= self.settings.rate_limit_requests
        except RedisError:
            self.redis_available = False
            return await self.fallback.allow(
                key,
                self.settings.rate_limit_requests,
                self.settings.rate_limit_window_seconds,
            )

    async def close(self) -> None:
        await self.redis.aclose()
