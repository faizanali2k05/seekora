import time

from app.crawler.fetcher import Fetcher
from app.crawler.models import ParsedPage
from app.crawler.parser import parse_html, parse_text
from app.search.chunking import chunk_text
from app.search.embedding import HashingEmbedder
from app.search.fusion import reciprocal_rank_fusion
from app.search.schemas import SearchHit


class SearchService:
    def __init__(self, repository, embedder: HashingEmbedder, fetcher: Fetcher):
        self.repository = repository
        self.embedder = embedder
        self.fetcher = fetcher

    async def ingest_url(self, url: str) -> tuple[str, str]:
        final_url, html = await self.fetcher.fetch(url)
        page = parse_html(final_url, html)
        document_id = self.repository.index_page(page, chunk_text(page.content))
        return str(document_id), page.url

    def ingest_text(self, url: str, title: str, content: str) -> tuple[str, str]:
        page: ParsedPage = parse_text(url, title, content)
        document_id = self.repository.index_page(page, chunk_text(page.content))
        return str(document_id), page.url

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        started = time.perf_counter()
        candidate_limit = max(20, limit * 4)
        lexical = self.repository.lexical(query, candidate_limit)
        semantic = self.repository.semantic(self.embedder.embed(query), candidate_limit)
        hits = reciprocal_rank_fusion([lexical, semantic], query, limit)
        self.repository.record_search(
            query,
            len(hits),
            (time.perf_counter() - started) * 1000,
        )
        return hits

    def stats(self) -> dict[str, int]:
        return self.repository.stats()

    def record_search(self, query: str, result_count: int, latency_ms: float) -> None:
        self.repository.record_search(query, result_count, latency_ms)
