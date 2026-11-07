import pytest

from app.core.rate_limit import MemoryRateLimiter


@pytest.mark.asyncio
async def test_memory_rate_limiter_enforces_window() -> None:
    limiter = MemoryRateLimiter()
    assert await limiter.allow("client", limit=2, window_seconds=60)
    assert await limiter.allow("client", limit=2, window_seconds=60)
    assert not await limiter.allow("client", limit=2, window_seconds=60)
