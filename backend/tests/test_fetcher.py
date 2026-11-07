import httpx
import pytest

from app.core.config import Settings
from app.crawler.fetcher import CrawlRejectedError, Fetcher


@pytest.mark.asyncio
async def test_fetcher_honors_robots(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.crawler.fetcher.validate_public_url", lambda value: value)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private")
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<p>no</p>")

    fetcher = Fetcher(Settings(crawl_min_delay_seconds=0), transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlRejectedError, match="robots.txt"):
        await fetcher.fetch("https://example.com/private")


@pytest.mark.asyncio
async def test_fetcher_returns_bounded_html(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.crawler.fetcher.validate_public_url", lambda value: value)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<main>Searchable page</main>",
        )

    fetcher = Fetcher(Settings(crawl_min_delay_seconds=0), transport=httpx.MockTransport(handler))
    url, html = await fetcher.fetch("https://example.com/page")
    assert url == "https://example.com/page"
    assert "Searchable" in html


@pytest.mark.asyncio
async def test_fetcher_rejects_oversized_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.crawler.fetcher.validate_public_url", lambda value: value)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"x" * 2048,
        )

    fetcher = Fetcher(
        Settings(crawl_min_delay_seconds=0, max_response_bytes=1024),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(CrawlRejectedError, match="size limit"):
        await fetcher.fetch("https://example.com/page")


@pytest.mark.asyncio
async def test_fetcher_rejects_cross_origin_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.crawler.fetcher.validate_public_url", lambda value: value)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(302, headers={"location": "https://other.example/page"})

    fetcher = Fetcher(
        Settings(crawl_min_delay_seconds=0),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(CrawlRejectedError, match="Cross-origin"):
        await fetcher.fetch("https://example.com/page")
