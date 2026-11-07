import pytest

from app.search.cache import MemorySearchCache


@pytest.mark.asyncio
async def test_memory_search_cache_normalizes_query_key() -> None:
    cache = MemorySearchCache()
    await cache.set("Hybrid Search", 10, [])
    assert await cache.get("  hybrid search ", 10) == []
    assert await cache.get("hybrid search", 5) is None
    await cache.clear()
    assert await cache.get("hybrid search", 10) is None
