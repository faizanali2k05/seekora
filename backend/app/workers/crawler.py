import asyncio
import logging

from redis.asyncio import Redis

from app.core.config import get_settings
from app.crawler.fetcher import Fetcher
from app.crawler.queue import RedisCrawlQueue
from app.db.repository import SearchRepository
from app.db.session import SessionLocal
from app.search.cache import RedisSearchCache
from app.search.embedding import HashingEmbedder
from app.search.service import SearchService


async def run() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    queue = RedisCrawlQueue(redis)
    cache = RedisSearchCache(redis)
    logger = logging.getLogger("seekora.crawler_worker")
    while True:
        job = await queue.dequeue()
        if job is None:
            continue
        try:
            embedder = HashingEmbedder()
            with SessionLocal() as session:
                service = SearchService(
                    SearchRepository(session, embedder),
                    embedder,
                    Fetcher(settings),
                )
                document_id, _ = await service.ingest_url(job.url)
            await queue.update(job, status="complete", document_id=document_id)
            await cache.clear()
        except Exception as exc:  # worker boundary records and continues
            logger.exception("crawl_job_failed", extra={"job_id": job.id})
            await queue.update(job, status="failed", error=str(exc)[:500])


if __name__ == "__main__":
    asyncio.run(run())
