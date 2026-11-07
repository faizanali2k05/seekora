from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Candidate:
    chunk_id: UUID
    document_id: UUID
    url: str
    title: str
    content: str
    score: float


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk_id: UUID
    document_id: UUID
    url: str
    title: str
    snippet: str
    score: float
