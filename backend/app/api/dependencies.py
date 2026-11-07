from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.crawler.fetcher import Fetcher
from app.crawler.queue import MemoryCrawlQueue, RedisCrawlQueue
from app.db.memory import MemorySearchRepository
from app.db.repository import SearchRepository
from app.db.session import get_session
from app.search.cache import MemorySearchCache, RedisSearchCache
from app.search.embedding import HashingEmbedder
from app.search.service import SearchService


@lru_cache
def get_memory_repository() -> MemorySearchRepository:
    return MemorySearchRepository(HashingEmbedder())


@lru_cache
def get_memory_crawl_queue() -> MemoryCrawlQueue:
    return MemoryCrawlQueue()


@lru_cache
def get_memory_search_cache() -> MemorySearchCache:
    return MemorySearchCache()


def get_search_cache(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.demo_mode:
        return get_memory_search_cache()
    return RedisSearchCache(
        Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=0.1,
            socket_timeout=0.1,
        )
    )


def get_crawl_queue(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.demo_mode:
        return get_memory_crawl_queue()
    return RedisCrawlQueue(Redis.from_url(settings.redis_url, decode_responses=True))


def get_search_service(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchService:
    embedder = HashingEmbedder()
    repository = (
        get_memory_repository() if settings.demo_mode else SearchRepository(session, embedder)
    )
    return SearchService(repository, embedder, Fetcher(settings))
