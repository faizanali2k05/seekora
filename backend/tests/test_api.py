from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import get_search_service
from app.main import app
from app.search.schemas import SearchHit


class FakeSearchService:
    async def ingest_url(self, url: str) -> tuple[str, str]:
        return str(UUID(int=1)), url

    def search(self, query: str, limit: int) -> list[SearchHit]:
        return [
            SearchHit(
                chunk_id=UUID(int=2),
                document_id=UUID(int=1),
                url="https://example.com/guide",
                title="A search guide",
                snippet="Hybrid search joins lexical and semantic retrieval.",
                score=0.052,
            )
        ][:limit]


def client() -> TestClient:
    app.dependency_overrides[get_search_service] = lambda: FakeSearchService()
    return TestClient(app)


def test_health() -> None:
    response = client().get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_contract() -> None:
    response = client().get("/v1/search", params={"q": "hybrid search"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "hybrid search"
    assert payload["results"][0]["title"] == "A search guide"
    assert payload["results"][0]["document_id"] == str(UUID(int=1))


def test_search_validates_short_query() -> None:
    response = client().get("/v1/search", params={"q": "x"})
    assert response.status_code == 422


def test_ingest_contract() -> None:
    response = client().post(
        "/v1/documents",
        headers={"Authorization": "Bearer seekora-dev-key-change-me"},
        json={"url": "https://example.com/guide"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "indexed"


def test_ingest_requires_authentication() -> None:
    response = client().post("/v1/documents", json={"url": "https://example.com/guide"})
    assert response.status_code == 401
