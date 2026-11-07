import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.crawler.fetcher import Fetcher
from app.db.memory import MemorySearchRepository
from app.search.embedding import HashingEmbedder
from app.search.service import SearchService

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "relevance.json").read_text())


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda item: item["expected_title"])
def test_relevance_fixture_places_expected_document_first(fixture: dict) -> None:
    embedder = HashingEmbedder()
    service = SearchService(
        MemorySearchRepository(embedder),
        embedder,
        Fetcher(Settings(crawl_min_delay_seconds=0)),
    )
    for url, title, content in fixture["documents"]:
        service.ingest_text(url, title, content)

    hits = service.search(fixture["query"], limit=3)

    assert hits
    assert hits[0].title == fixture["expected_title"]
