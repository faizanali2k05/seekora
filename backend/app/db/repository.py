from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crawler.models import ParsedPage
from app.db.base import Chunk, Document, SearchEvent
from app.search.embedding import HashingEmbedder
from app.search.schemas import Candidate


class DuplicateContentError(ValueError):
    pass


class SearchRepository:
    def __init__(self, session: Session, embedder: HashingEmbedder):
        self.session = session
        self.embedder = embedder

    def index_page(self, page: ParsedPage, chunks: list[str]) -> UUID:
        existing_hash = self.session.scalar(
            select(Document).where(Document.content_hash == page.content_hash)
        )
        existing_url = self.session.scalar(select(Document).where(Document.url == page.url))
        if existing_hash is not None and (
            existing_url is None or existing_hash.id != existing_url.id
        ):
            raise DuplicateContentError("Equivalent content is already indexed")
        document = existing_url or Document(url=page.url)
        document.title = page.title
        document.content = page.content
        document.content_hash = page.content_hash
        self.session.add(document)
        self.session.flush()
        self.session.execute(delete(Chunk).where(Chunk.document_id == document.id))
        for position, content in enumerate(chunks):
            self.session.add(
                Chunk(
                    document_id=document.id,
                    position=position,
                    content=content,
                    search_vector=func.to_tsvector("english", f"{page.title} {content}"),
                    embedding=self.embedder.embed(content),
                )
            )
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        return document.id

    def lexical(self, query: str, limit: int) -> list[Candidate]:
        sql = text("""
            SELECT c.id AS chunk_id, d.id AS document_id, d.url, d.title, c.content,
                   ts_rank_cd(c.search_vector, websearch_to_tsquery('english', :query)) AS score
            FROM chunks c JOIN documents d ON d.id = c.document_id
            WHERE c.search_vector @@ websearch_to_tsquery('english', :query)
            ORDER BY score DESC LIMIT :limit
        """)
        return [
            Candidate(**dict(row))
            for row in self.session.execute(sql, {"query": query, "limit": limit}).mappings()
        ]

    def semantic(self, vector: list[float], limit: int) -> list[Candidate]:
        rows = self.session.execute(
            select(
                Chunk.id.label("chunk_id"),
                Document.id.label("document_id"),
                Document.url,
                Document.title,
                Chunk.content,
                (1 - Chunk.embedding.cosine_distance(vector)).label("score"),
            )
            .join(Document, Document.id == Chunk.document_id)
            .order_by(Chunk.embedding.cosine_distance(vector))
            .limit(limit)
        ).mappings()
        return [Candidate(**dict(row)) for row in rows]

    def record_search(self, query: str, result_count: int, latency_ms: float) -> None:
        self.session.add(
            SearchEvent(query=query[:300], result_count=result_count, latency_ms=latency_ms)
        )
        self.session.commit()

    def stats(self) -> dict[str, int]:
        return {
            "documents": int(self.session.scalar(select(func.count(Document.id))) or 0),
            "chunks": int(self.session.scalar(select(func.count(Chunk.id))) or 0),
            "searches": int(self.session.scalar(select(func.count(SearchEvent.id))) or 0),
        }
