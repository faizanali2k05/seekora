from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, Field


class IngestRequest(BaseModel):
    url: AnyHttpUrl


class TextIngestRequest(BaseModel):
    url: AnyHttpUrl
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=2_000_000)


class IngestResponse(BaseModel):
    id: str
    url: str
    status: str = "indexed"


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    url: str
    title: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    took_ms: float


SearchQuery = Annotated[str, Field(min_length=2, max_length=300)]


class AnswerRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)


class CitationResponse(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    title: str
    url: str
    quote: str


class AnswerResponse(BaseModel):
    query: str
    answer: str
    citations: list[CitationResponse]
    grounded: bool
    provider: str


class AdminStatsResponse(BaseModel):
    documents: int
    chunks: int
    searches: int


class CrawlJobResponse(BaseModel):
    id: str
    url: str
    status: str
    created_at: str
    error: str | None = None
    document_id: str | None = None
