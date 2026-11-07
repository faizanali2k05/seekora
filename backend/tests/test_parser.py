from app.crawler.parser import parse_html, parse_text


def test_parse_html_prefers_main_and_removes_noise() -> None:
    page = parse_html(
        "HTTPS://Example.COM:443/guide?utm_source=test&b=2&a=1#part",
        """<html><head><title>  Useful   guide </title><script>secret()</script></head>
        <body><nav>Menu</nav><main><h1>Useful guide</h1><p>Index this text.</p></main>
        <footer>Legal noise</footer></body></html>""",
    )

    assert page.url == "https://example.com/guide?a=1&b=2"
    assert page.title == "Useful guide"
    assert page.content == "Useful guide Index this text."
    assert len(page.content_hash) == 64


def test_parse_html_rejects_empty_content() -> None:
    try:
        parse_html("https://example.com", "<html><script>onlyNoise()</script></html>")
    except ValueError as exc:
        assert "no indexable text" in str(exc)
    else:
        raise AssertionError("expected empty page rejection")


def test_parse_text_rejects_whitespace_only_malformed_document() -> None:
    try:
        parse_text("https://example.com/empty", " ", "\n\t")
    except ValueError as exc:
        assert "no indexable text" in str(exc)
    else:
        raise AssertionError("expected malformed document rejection")
