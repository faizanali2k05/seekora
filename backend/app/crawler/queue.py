import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from redis.asyncio import Redis


@dataclass(slots=True)
class CrawlJob:
    id: str
    url: str
    status: str
    created_at: str
    error: str | None = None
    document_id: str | None = None


class MemoryCrawlQueue:
    def __init__(self) -> None:
        self.jobs: dict[str, CrawlJob] = {}
        self.pending: asyncio.Queue[CrawlJob] = asyncio.Queue()

    async def enqueue(self, url: str) -> CrawlJob:
        job = CrawlJob(
            id=str(uuid4()),
            url=url,
            status="queued",
            created_at=datetime.now(UTC).isoformat(),
        )
        self.jobs[job.id] = job
        await self.pending.put(job)
        return job

    async def dequeue(self, wait_seconds: int = 5) -> CrawlJob | None:
        try:
            job = await asyncio.wait_for(self.pending.get(), timeout=wait_seconds)
        except TimeoutError:
            return None
        job.status = "running"
        return job

    async def update(
        self,
        job: CrawlJob,
        *,
        status: str,
        document_id: str | None = None,
        error: str | None = None,
    ) -> None:
        job.status = status
        job.document_id = document_id
        job.error = error
        self.jobs[job.id] = job

    async def get(self, job_id: str) -> CrawlJob | None:
        return self.jobs.get(job_id)


class RedisCrawlQueue:
    queue_key = "seekora:crawl:pending"

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def enqueue(self, url: str) -> CrawlJob:
        job = CrawlJob(
            id=str(uuid4()),
            url=url,
            status="queued",
            created_at=datetime.now(UTC).isoformat(),
        )
        await self._save(job)
        await self.redis.lpush(self.queue_key, job.id)
        return job

    async def dequeue(self, wait_seconds: int = 5) -> CrawlJob | None:
        item = await self.redis.brpop(self.queue_key, timeout=wait_seconds)
        if not item:
            return None
        job = await self.get(item[1])
        if job:
            await self.update(job, status="running")
        return job

    async def update(
        self,
        job: CrawlJob,
        *,
        status: str,
        document_id: str | None = None,
        error: str | None = None,
    ) -> None:
        job.status = status
        job.document_id = document_id
        job.error = error
        await self._save(job)

    async def get(self, job_id: str) -> CrawlJob | None:
        payload = await self.redis.get(f"seekora:crawl:job:{job_id}")
        return CrawlJob(**json.loads(payload)) if payload else None

    async def _save(self, job: CrawlJob) -> None:
        await self.redis.set(
            f"seekora:crawl:job:{job.id}",
            json.dumps(asdict(job)),
            ex=86_400,
        )
