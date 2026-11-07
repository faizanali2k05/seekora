import math
import re
from collections import Counter
from dataclasses import dataclass
from threading import Lock
from uuid import UUID, uuid4

from app.crawler.models import ParsedPage
from app.db.repository import DuplicateContentError
from app.search.embedding import HashingEmbedder
from app.search.schemas import Candidate

TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class MemoryChunk:
    id: UUID
    document_id: UUID
    position: int
    url: str
    title: str
    content: str
    embedding: list[float]


class MemorySearchRepository:
    """Deterministic repository used by tests and the explicit local demo mode."""

    def __init__(self, embedder: HashingEmbedder) -> None:
        self.embedder = embedder
        self._documents: dict[UUID, ParsedPage] = {}
        self._url_ids: dict[str, UUID] = {}
        self._hash_ids: dict[str, UUID] = {}
        self._chunks: list[MemoryChunk] = []
        self._search_events: list[tuple[str, int, float]] = []
        self._lock = Lock()

    def index_page(self, page: ParsedPage, chunks: list[str]) -> UUID:
        with self._lock:
            duplicate_id = self._hash_ids.get(page.content_hash)
            url_id = self._url_ids.get(page.url)
            if duplicate_id is not None and duplicate_id != url_id:
                raise DuplicateContentError("Equivalent content is already indexed")
            document_id = url_id or uuid4()
            if url_id is not None:
                previous = self._documents[url_id]
                self._hash_ids.pop(previous.content_hash, None)
            self._documents[document_id] = page
            self._url_ids[page.url] = document_id
            self._hash_ids[page.content_hash] = document_id
            self._chunks = [item for item in self._chunks if item.document_id != document_id]
            self._chunks.extend(
                MemoryChunk(
                    id=uuid4(),
                    document_id=document_id,
                    position=position,
                    url=page.url,
                    title=page.title,
                    content=content,
                    embedding=self.embedder.embed(content),
                )
                for position, content in enumerate(chunks)
            )
            return document_id

    def lexical(self, query: str, limit: int) -> list[Candidate]:
        query_terms = Counter(TOKEN.findall(query.lower()))
        candidates: list[Candidate] = []
        for chunk in self._chunks:
            terms = Counter(TOKEN.findall(f"{chunk.title} {chunk.content}".lower()))
            score = sum(min(count, terms[term]) for term, count in query_terms.items())
            if score:
                candidates.append(self._candidate(chunk, float(score)))
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]

    def semantic(self, vector: list[float], limit: int) -> list[Candidate]:
        candidates = [
            self._candidate(chunk, sum(a * b for a, b in zip(vector, chunk.embedding, strict=True)))
            for chunk in self._chunks
        ]
        return sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]

    def record_search(self, query: str, result_count: int, latency_ms: float) -> None:
        self._search_events.append((query, result_count, latency_ms))

    def stats(self) -> dict[str, int]:
        return {
            "documents": len(self._documents),
            "chunks": len(self._chunks),
            "searches": len(self._search_events),
        }

    def _candidate(self, chunk: MemoryChunk, score: float) -> Candidate:
        return Candidate(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            url=chunk.url,
            title=chunk.title,
            content=chunk.content,
            score=score if math.isfinite(score) else 0.0,
        )
