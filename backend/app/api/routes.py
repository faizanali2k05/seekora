import time
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_crawl_queue, get_search_cache, get_search_service
from app.api.schemas import (
    AdminStatsResponse,
    AnswerRequest,
    AnswerResponse,
    CitationResponse,
    CrawlJobResponse,
    IngestRequest,
    IngestResponse,
    SearchResponse,
    SearchResult,
    TextIngestRequest,
)
from app.core.config import Settings, get_settings
from app.core.security import Principal, require_admin, resolve_principal
from app.crawler.fetcher import CrawlRejectedError
from app.crawler.queue import CrawlJob
from app.crawler.url_policy import UnsafeUrlError
from app.db.repository import DuplicateContentError
from app.rag.service import GroundedAnswerService
from app.search.service import SearchService

router = APIRouter(prefix="/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/documents", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest(
    request: IngestRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
    cache: Annotated[object, Depends(get_search_cache)],
    _principal: Annotated[Principal, Depends(require_admin)],
) -> IngestResponse:
    try:
        document_id, url = await service.ingest_url(str(request.url))
    except (UnsafeUrlError, CrawlRejectedError, DuplicateContentError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await cache.clear()
    return IngestResponse(id=document_id, url=url)


@router.post("/documents/text", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_text(
    request: TextIngestRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
    cache: Annotated[object, Depends(get_search_cache)],
    settings: Annotated[Settings, Depends(get_settings)],
    _principal: Annotated[Principal, Depends(require_admin)],
) -> IngestResponse:
    if len(request.content) > settings.max_document_characters:
        raise HTTPException(status_code=413, detail="Document exceeds the configured text limit")
    try:
        document_id, url = service.ingest_text(str(request.url), request.title, request.content)
    except (DuplicateContentError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await cache.clear()
    return IngestResponse(id=document_id, url=url)


@router.get("/search", response_model=SearchResponse)
async def search(
    service: Annotated[SearchService, Depends(get_search_service)],
    cache: Annotated[object, Depends(get_search_cache)],
    q: Annotated[str, Query(min_length=2, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> SearchResponse:
    started = time.perf_counter()
    hits = await cache.get(q, limit)
    if hits is None:
        hits = service.search(q.strip(), limit)
        await cache.set(q, limit, hits)
    else:
        service.record_search(q.strip(), len(hits), (time.perf_counter() - started) * 1000)
    took_ms = (time.perf_counter() - started) * 1000
    return SearchResponse(
        query=q,
        results=[
            SearchResult(
                **{
                    **asdict(hit),
                    "chunk_id": str(hit.chunk_id),
                    "document_id": str(hit.document_id),
                }
            )
            for hit in hits
        ],
        took_ms=round(took_ms, 2),
    )


@router.post("/answer", response_model=AnswerResponse)
async def answer(
    request: AnswerRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnswerResponse:
    result = await GroundedAnswerService(service, settings).answer(request.query.strip())
    return AnswerResponse(
        query=result.query,
        answer=result.answer,
        citations=[CitationResponse(**asdict(item)) for item in result.citations],
        grounded=result.grounded,
        provider=result.provider,
    )


@router.get("/admin/stats", response_model=AdminStatsResponse)
def admin_stats(
    service: Annotated[SearchService, Depends(get_search_service)],
    _principal: Annotated[Principal, Depends(require_admin)],
) -> AdminStatsResponse:
    return AdminStatsResponse(**service.stats())


@router.get("/auth/session")
def auth_session(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | bool]:
    principal = resolve_principal(request, settings)
    return {
        "authenticated": principal is not None,
        "role": principal.role if principal else "anonymous",
    }


@router.post("/crawl/jobs", response_model=CrawlJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_crawl_job(
    request: IngestRequest,
    queue: Annotated[object, Depends(get_crawl_queue)],
    _principal: Annotated[Principal, Depends(require_admin)],
) -> CrawlJobResponse:
    job: CrawlJob = await queue.enqueue(str(request.url))
    return CrawlJobResponse(**asdict(job))


@router.get("/crawl/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: str,
    queue: Annotated[object, Depends(get_crawl_queue)],
    _principal: Annotated[Principal, Depends(require_admin)],
) -> CrawlJobResponse:
    job: CrawlJob | None = await queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return CrawlJobResponse(**asdict(job))
