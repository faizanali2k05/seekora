import hashlib
import re

from bs4 import BeautifulSoup

from app.crawler.models import ParsedPage
from app.crawler.url_policy import canonicalize_url

WHITESPACE = re.compile(r"\s+")
REMOVED_TAGS = ("script", "style", "noscript", "svg", "canvas", "template", "form", "nav", "footer")


def parse_html(url: str, html: str) -> ParsedPage:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(REMOVED_TAGS):
        element.decompose()
    title = WHITESPACE.sub(
        " ", soup.title.get_text(" ", strip=True) if soup.title else "Untitled"
    ).strip()
    scope = soup.find("main") or soup.find("article") or soup.body or soup
    content = WHITESPACE.sub(" ", scope.get_text(" ", strip=True)).strip()
    if not content:
        raise ValueError("Page has no indexable text")
    return parse_text(url, title, content)


def parse_text(url: str, title: str, content: str) -> ParsedPage:
    canonical = canonicalize_url(url)
    clean_title = WHITESPACE.sub(" ", title).strip()[:500]
    clean_content = WHITESPACE.sub(" ", content).strip()
    if not clean_title:
        clean_title = "Untitled"
    if not clean_content:
        raise ValueError("Document has no indexable text")
    digest = hashlib.sha256(clean_content.encode("utf-8")).hexdigest()
    return ParsedPage(
        url=canonical,
        title=clean_title,
        content=clean_content,
        content_hash=digest,
    )
