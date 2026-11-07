from collections import defaultdict
from uuid import UUID

from app.search.schemas import Candidate, SearchHit


def reciprocal_rank_fusion(
    ranked_lists: list[list[Candidate]], query: str, limit: int = 10, k: int = 60
) -> list[SearchHit]:
    scores: defaultdict[UUID, float] = defaultdict(float)
    candidates: dict[UUID, Candidate] = {}
    for ranked in ranked_lists:
        for rank, candidate in enumerate(ranked, start=1):
            scores[candidate.chunk_id] += 1.0 / (k + rank)
            candidates[candidate.chunk_id] = candidate

    terms = set(query.lower().split())
    for chunk_id, candidate in candidates.items():
        text = candidate.content.lower()
        coverage = sum(term in text for term in terms) / max(1, len(terms))
        scores[chunk_id] += coverage * 0.02

    ordered = sorted(candidates.values(), key=lambda item: scores[item.chunk_id], reverse=True)
    seen_documents: set[UUID] = set()
    hits: list[SearchHit] = []
    for candidate in ordered:
        if candidate.document_id in seen_documents:
            continue
        seen_documents.add(candidate.document_id)
        hits.append(
            SearchHit(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                url=candidate.url,
                title=candidate.title,
                snippet=candidate.content[:360].strip(),
                score=round(scores[candidate.chunk_id], 6),
            )
        )
        if len(hits) >= limit:
            break
    return hits
