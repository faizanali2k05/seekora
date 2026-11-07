import asyncio
import time
from collections import defaultdict
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.core.config import Settings
from app.crawler.url_policy import validate_public_url


class CrawlRejectedError(ValueError):
    pass


class Fetcher:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self._transport = transport
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._last_request: dict[str, float] = {}

    async def fetch(self, raw_url: str) -> tuple[str, str]:
        url = validate_public_url(raw_url)
        parsed = urlsplit(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=self.settings.crawl_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": self.settings.crawler_user_agent},
        ) as client:
            robots = await self._robots(client, origin)
            if not robots.can_fetch(self.settings.crawler_user_agent, url):
                raise CrawlRejectedError("robots.txt disallows this URL")
            current = url
            for _ in range(5):
                current = validate_public_url(current)
                response = await self._rate_limited_get(client, origin, current)
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise CrawlRejectedError("Redirect has no location")
                    current = urljoin(current, location)
                    redirect = urlsplit(current)
                    redirect_origin = f"{redirect.scheme}://{redirect.netloc}"
                    if redirect_origin != origin:
                        raise CrawlRejectedError("Cross-origin redirects are not followed")
                    if not robots.can_fetch(self.settings.crawler_user_agent, current):
                        raise CrawlRejectedError("Redirect target is disallowed by robots.txt")
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    raise CrawlRejectedError("Only HTML pages can be indexed")
                return str(response.url), response.text
        raise CrawlRejectedError("Too many redirects")

    async def _robots(self, client: httpx.AsyncClient, origin: str) -> RobotFileParser:
        robots_url = f"{origin}/robots.txt"
        parser = RobotFileParser(robots_url)
        try:
            response = await self._rate_limited_get(client, origin, robots_url)
            parser.parse(response.text.splitlines() if response.status_code < 400 else [])
        except httpx.HTTPError:
            parser.parse([])
        return parser

    async def _rate_limited_get(
        self, client: httpx.AsyncClient, origin: str, url: str
    ) -> httpx.Response:
        async with self._locks[origin]:
            elapsed = time.monotonic() - self._last_request.get(origin, 0.0)
            delay = self.settings.crawl_min_delay_seconds - elapsed
            if delay > 0:
                await asyncio.sleep(delay)
            request = client.build_request("GET", url)
            raw_response = await client.send(request, stream=True)
            try:
                declared_size = int(raw_response.headers.get("content-length", "0"))
                if declared_size > self.settings.max_response_bytes:
                    raise CrawlRejectedError("Response exceeds the configured size limit")
                body = bytearray()
                async for chunk in raw_response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > self.settings.max_response_bytes:
                        raise CrawlRejectedError("Response exceeds the configured size limit")
                return httpx.Response(
                    raw_response.status_code,
                    headers=raw_response.headers,
                    content=bytes(body),
                    request=raw_response.request,
                    extensions=raw_response.extensions,
                )
            finally:
                self._last_request[origin] = time.monotonic()
                await raw_response.aclose()
