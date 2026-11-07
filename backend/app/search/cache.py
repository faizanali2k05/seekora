import json
from dataclasses import asdict
from hashlib import sha256
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.search.schemas import SearchHit


class MemorySearchCache:
    def __init__(self) -> None:
        self.values: dict[str, list[SearchHit]] = {}

    async def get(self, query: str, limit: int) -> list[SearchHit] | None:
        return self.values.get(self._key(query, limit))

    async def set(self, query: str, limit: int, hits: list[SearchHit]) -> None:
        self.values[self._key(query, limit)] = hits

    async def clear(self) -> None:
        self.values.clear()

    @staticmethod
    def _key(query: str, limit: int) -> str:
        return f"{query.strip().lower()}:{limit}"


class RedisSearchCache:
    def __init__(self, redis: Redis, ttl_seconds: int = 120) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def get(self, query: str, limit: int) -> list[SearchHit] | None:
        try:
            payload = await self.redis.get(self._key(query, limit))
        except RedisError:
            return None
        if not payload:
            return None
        values = json.loads(payload)
        return [
            SearchHit(
                **{
                    **item,
                    "chunk_id": UUID(item["chunk_id"]),
                    "document_id": UUID(item["document_id"]),
                }
            )
            for item in values
        ]

    async def set(self, query: str, limit: int, hits: list[SearchHit]) -> None:
        payload = [
            {
                **asdict(hit),
                "chunk_id": str(hit.chunk_id),
                "document_id": str(hit.document_id),
            }
            for hit in hits
        ]
        try:
            await self.redis.set(self._key(query, limit), json.dumps(payload), ex=self.ttl_seconds)
        except RedisError:
            return

    async def clear(self) -> None:
        try:
            keys = [key async for key in self.redis.scan_iter(match="seekora:search:*")]
            if keys:
                await self.redis.delete(*keys)
        except RedisError:
            return

    @staticmethod
    def _key(query: str, limit: int) -> str:
        digest = sha256(f"{query.strip().lower()}:{limit}:ranking-v1".encode()).hexdigest()
        return f"seekora:search:{digest}"
