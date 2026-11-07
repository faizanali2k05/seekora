import pytest

from app.crawler.url_policy import UnsafeUrlError, canonicalize_url, validate_public_host


def test_canonicalize_url_removes_fragment_default_port_and_trackers() -> None:
    assert (
        canonicalize_url("https://EXAMPLE.com:443/path?utm_medium=x&z=2&a=1#top")
        == "https://example.com/path?a=1&z=2"
    )


@pytest.mark.parametrize("url", ["file:///etc/passwd", "//example.com", "mailto:a@example.com"])
def test_canonicalize_rejects_non_http_urls(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        canonicalize_url(url)


def test_validate_public_host_rejects_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 0))]
    )
    with pytest.raises(UnsafeUrlError, match="Private"):
        validate_public_host("internal.example")
