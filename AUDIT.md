# Repository audit

Audit date: 2026-11-07

## Preserved working baseline

- Safe single-URL fetching with public-host validation, bounded redirects, `robots.txt`, per-origin delay, HTML-only responses, and response-size limits.
- HTML cleaning, canonical URLs, exact-content deduplication, chunking, PostgreSQL full-text indexing, pgvector storage, reciprocal-rank fusion, and deterministic local embeddings.
- FastAPI health, document-ingestion, and search routes.
- Next.js search interface, production build, and a mocked Playwright result-rendering test.
- Dockerfiles, Compose services, Alembic migration, and sample seed content.

Baseline checks before this completion pass:

- Ruff: passed.
- Pytest: 16 passed, 1 PostgreSQL integration test skipped.
- `npm audit --audit-level=high`: 0 vulnerabilities.
- Next.js production build: passed.
- Docker unavailable on the execution host; Compose was not executable here.

## Gaps found

| Area | Audit finding |
|---|---|
| RAG | No answer endpoint, generation adapter, prompt-injection boundary, citation schema, or citation validation. |
| Authentication | No protected routes, principal model, API key validation, or authorization tests. |
| Rate limiting | Crawler delay existed, but API rate limits were not implemented and Redis was not used. |
| Analytics/admin | No persisted search events, corpus statistics, or administration API/UI. |
| Crawling jobs | Ingestion was inline only; Redis was declared but no queue contract or worker existed. |
| Frontend | Search only; no answer experience, source-attribution panel, ingestion control, or admin surface. |
| Brand | Existing green wordmark did not meet the requested purple/electric-cyan geometric identity. |
| Integration proof | Browser test mocked the API, so it did not verify browser → API → retrieval → answer. |
| Fixtures | Missing authorization, injection-resilience, malformed-document, crawler-limit, and relevance-quality fixtures. |
| Delivery | No CI workflow, feature matrix, release checklist, original SVG assets, or completion report. |

## Constraints

The repository is currently uncommitted/untracked, so there is no Git baseline to diff against. Existing files are treated as user-owned and preserved unless directly extended. Docker, PostgreSQL, Redis, and Python 3.12 are not installed on the execution host. Production Compose configuration can be statically checked, while executable integration evidence uses the same application services with a deterministic in-memory repository.
