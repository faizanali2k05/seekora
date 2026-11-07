from fastapi.testclient import TestClient

from app.api.dependencies import get_search_service
from app.core.config import Settings, get_settings
from app.crawler.fetcher import Fetcher
from app.db.memory import MemorySearchRepository
from app.main import app, rate_limiter
from app.search.embedding import HashingEmbedder
from app.search.service import SearchService


def test_ingest_search_answer_and_attribution_flow() -> None:
    settings = Settings(demo_mode=True, rate_limit_enabled=False)
    embedder = HashingEmbedder()
    service = SearchService(
        MemorySearchRepository(embedder),
        embedder,
        Fetcher(settings),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_search_service] = lambda: service
    rate_limiter.redis_available = False
    client = TestClient(app)
    headers = {"Authorization": "Bearer seekora-dev-key-change-me"}

    unauthorized = client.post(
        "/v1/documents/text",
        json={"url": "https://demo.local/source", "title": "Demo", "content": "Evidence"},
    )
    assert unauthorized.status_code == 401

    ingested = client.post(
        "/v1/documents/text",
        headers=headers,
        json={
            "url": "https://demo.local/source",
            "title": "Traceable hybrid retrieval",
            "content": (
                "Hybrid retrieval combines lexical search and vector similarity. "
                "Seekora attaches citations to source chunks."
            ),
        },
    )
    assert ingested.status_code == 201

    searched = client.get("/v1/search", params={"q": "hybrid vector retrieval"})
    assert searched.status_code == 200
    assert searched.json()["results"][0]["title"] == "Traceable hybrid retrieval"

    answered = client.post("/v1/answer", json={"query": "How does hybrid retrieval work?"})
    assert answered.status_code == 200
    payload = answered.json()
    assert payload["grounded"] is True
    assert payload["citations"][0]["url"] == "https://demo.local/source"
    assert "[1]" in payload["answer"]

    stats = client.get("/v1/admin/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["documents"] == 1
    assert stats.json()["searches"] == 2

    app.dependency_overrides.clear()
