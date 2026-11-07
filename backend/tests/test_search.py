from uuid import UUID

from app.search.embedding import HashingEmbedder
from app.search.fusion import reciprocal_rank_fusion
from app.search.schemas import Candidate


def candidate(chunk: int, document: int, content: str) -> Candidate:
    return Candidate(
        chunk_id=UUID(int=chunk),
        document_id=UUID(int=document),
        url=f"https://example.com/{document}",
        title=f"Document {document}",
        content=content,
        score=1.0,
    )


def test_hashing_embedder_is_normalized_and_deterministic() -> None:
    embedder = HashingEmbedder()
    first = embedder.embed("hybrid semantic search")
    second = embedder.embed("hybrid semantic search")
    assert first == second
    assert len(first) == 384
    assert abs(sum(value * value for value in first) - 1.0) < 1e-9


def test_fusion_combines_lists_and_deduplicates_documents() -> None:
    first = candidate(1, 10, "hybrid search combines lexical and vector retrieval")
    second_chunk_same_document = candidate(2, 10, "another passage")
    other = candidate(3, 20, "lexical indexing")

    hits = reciprocal_rank_fusion(
        [[first, other], [other, second_chunk_same_document]], "hybrid search", limit=10
    )

    assert [hit.document_id for hit in hits].count(UUID(int=10)) == 1
    assert hits[0].title == "Document 10"
