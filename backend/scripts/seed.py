from app.crawler.parser import parse_html
from app.db.repository import SearchRepository
from app.db.session import SessionLocal
from app.search.chunking import chunk_text
from app.search.embedding import HashingEmbedder

SAMPLES = [
    (
        "https://docs.seekora.local/hybrid-search",
        """<html><head><title>Hybrid search in Seekora</title></head><body><main>
        <h1>Hybrid search</h1><p>Seekora combines PostgreSQL full-text retrieval with vector
        similarity. Reciprocal rank fusion merges lexical and semantic candidates, then a
        lightweight reranker promotes passages that cover more query terms.</p>
        </main></body></html>""",
    ),
    (
        "https://docs.seekora.local/responsible-crawling",
        """<html><head><title>Responsible web crawling</title></head><body><main>
        <h1>Crawl politely</h1><p>A crawler should honor robots.txt, identify its user agent,
        rate limit requests per origin, reject private network targets, and keep response sizes
        bounded. Canonical URLs and content hashes prevent duplicate indexing.</p>
        </main></body></html>""",
    ),
    (
        "https://docs.seekora.local/rag-citations",
        """<html><head><title>Grounded answers and citations</title></head><body><main>
        <h1>RAG answers</h1><p>Retrieval augmented generation supplies relevant passages to a
        language model. Seekora associates every passage with an immutable source identifier and
        validates citations before returning a grounded answer.</p></main></body></html>""",
    ),
]


def main() -> None:
    embedder = HashingEmbedder()
    with SessionLocal() as session:
        repository = SearchRepository(session, embedder)
        for url, html in SAMPLES:
            page = parse_html(url, html)
            try:
                repository.index_page(page, chunk_text(page.content))
                print(f"indexed {url}")
            except Exception as exc:
                session.rollback()
                print(f"skipped {url}: {exc}")


if __name__ == "__main__":
    main()
