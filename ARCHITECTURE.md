# Seekora Architecture

Seekora is a production-oriented, self-hosted search and retrieval-augmented generation (RAG) system. The architecture starts as a modular monolith so the first useful slice is easy to run, while preserving boundaries that can later move into workers or separate services.

## Product boundaries

```text
Browser (Next.js)
        |
        v
FastAPI API  ---- Redis (cache, rate limits, job queue)
   |    |
   |    +---- crawler/indexing worker ---- public web
   |
   +--------- PostgreSQL 16 + pgvector
                   |-- documents and chunks
                   |-- tsvector full-text index
                   |-- vector similarity index
                   |-- users, analytics, audit records
```

The API is stateless. PostgreSQL is authoritative. Redis contains disposable search caches, API rate-limit counters, and crawl jobs. Crawling can run inline or through the worker; both paths use the same ingestion service.

## Repository layout

- `backend/app/api`: HTTP routing and transport schemas
- `backend/app/core`: settings, security, logging, and cross-cutting policy
- `backend/app/crawler`: robots policy, fetching, parsing, canonicalization, and deduplication
- `backend/app/search`: embedding, indexing, retrieval, fusion, and reranking
- `backend/app/rag`: answer generation, citation validation, and model adapters
- `backend/app/db`: SQLAlchemy models, repositories, migrations, and session lifecycle
- `backend/app/workers`: queue consumers and scheduled work
- `frontend`: Next.js application and admin UI
- `tests`: integration and browser-level tests; module unit tests live near the backend package

Dependencies point inward: API routes depend on services; services depend on repository/model interfaces; infrastructure implements those interfaces. Model providers are adapters selected with environment variables.

## Data model

`documents` stores one canonical URL and its latest cleaned content. `content_hash` is unique and prevents exact duplicates. `chunks` stores bounded passages, a PostgreSQL `tsvector`, and a 384-dimensional embedding. `search_events` stores query, result count, latency, and timestamp; it is append-only and does not block retrieval.

Milestone one deliberately uses a deterministic, local hashing embedder. It gives the hybrid pipeline a working, dependency-free semantic signal and stable tests. A later milestone adds a Sentence Transformers adapter while preserving the same interface. Production deployments should rebuild vectors when changing models and record the embedding model/version on each chunk.

## Retrieval

1. PostgreSQL full-text search produces a BM25-style lexical signal using `ts_rank_cd` over weighted `tsvector` fields.
2. pgvector cosine distance produces semantic candidates.
3. Reciprocal-rank fusion combines independently ranked candidate lists without assuming comparable raw scores.
4. A reranker scores the fused shortlist. Initially this is a transparent term/proximity reranker; a local cross-encoder adapter follows later.
5. RAG receives only the final passages. The local extractive provider is the default; an OpenAI-compatible adapter is optional.
6. Citation numbers must resolve to immutable chunk IDs in the supplied result set. Invalid provider output falls back to local extraction.

PostgreSQL full-text ranking is BM25-like rather than an exact BM25 implementation. If corpus scale or ranking requirements outgrow it, the retrieval interface allows a dedicated engine without changing API contracts.

## Crawl safety

- Only `http` and `https` URLs are accepted.
- DNS results are checked to reject loopback, link-local, multicast, private, and reserved addresses (SSRF defense).
- `robots.txt` is fetched and honored for the configured user agent.
- Per-origin minimum delay and concurrency are enforced in each crawler process. Redis provides the job queue; distributed origin leasing is a documented scale-up follow-up.
- Redirects are bounded and every redirect target is revalidated.
- Response size, content type, timeout, and crawl depth are bounded.
- Canonical URLs remove fragments, normalize hosts and ports, and sort tracking-free query parameters.

## API and security

All public endpoints are versioned under `/v1`. Search and answers are public in this MVP. Corpus writes, crawl jobs, analytics, and administration require a constant-time-validated administrator API key. Redis rate limiting is keyed by client address and route, with a local fallback. Structured JSON logs include request IDs, latency, route, and outcome, but never secrets or document bodies.

Browser access is restricted by configured CORS origins. Secrets enter only through environment variables or an external secret store. Database roles should separate migrations, API access, and read-only analytics in production.

## Reliability and operations

- Idempotency: canonical URL and content hashes make ingestion safe to retry.
- Transactions: document and chunk replacement is atomic.
- Queue semantics: jobs are at-least-once; workers acknowledge only after commit.
- Cache: keys include query, filters, corpus revision, and ranking version.
- Observability: JSON logs, health/readiness endpoints, request metrics, crawl metrics, and trace propagation.
- Backups: PostgreSQL point-in-time recovery is required in production; Redis is disposable.
- Migrations: Alembic owns schema changes and the vector extension.

## Local and production topology

`docker compose up --build` runs the web UI, API, PostgreSQL/pgvector, and Redis. Development uses bind mounts and hot reload. A production deployment should build immutable images, run migrations as a release task, terminate TLS at the platform edge, set explicit CPU/memory limits, and scale API and workers independently.

## Milestone plan

### Milestone 1 — verified search vertical slice

- Compose-based local stack and environment template
- URL safety, robots-aware fetcher, HTML cleaner, canonicalization, and exact deduplication
- PostgreSQL schema with full-text and pgvector indexes
- local deterministic embeddings, lexical/vector candidate retrieval, reciprocal-rank fusion, and simple reranking
- FastAPI document ingestion and search endpoints
- modern Next.js search page with source-focused result cards
- sample documents; backend unit/API tests and frontend unit/build checks

Exit criterion: a sample document can be ingested and found through the browser/API, and all runnable host-side checks pass. Compose verification is additionally required on a Docker-capable host.

### Milestone 2 — durable crawling and corpus operations (MVP delivered)

- Redis queue workers, crawl frontier, sitemap discovery, crawl budgets, retries, and distributed per-origin limiting
- incremental recrawling, content change tracking, near-duplicate detection, and document lifecycle controls
- admin corpus dashboard and job controls

### Milestone 3 — production retrieval and RAG (grounded MVP delivered)

- Future: Sentence Transformers embedding and cross-encoder adapters
- chunking evaluation, filters, query rewriting, result cache, and offline ranking benchmarks
- pluggable local/OpenAI-compatible chat adapters, streamed answers, citation validation, prompt-injection defenses, and answer evaluations

### Milestone 4 — identity, analytics, and hardening (single-admin MVP delivered)

- delivered: administrator API key, Redis rate limiting/cache, structured logs, and privacy-minimal search analytics
- future: multi-user OIDC, scoped roles, refresh-token rotation, and durable audit identities
- OpenTelemetry/metrics, dashboards, backup/restore runbook, load tests, dependency scanning, and deployment documentation
- complete PostgreSQL/Redis integration suite and Playwright journeys in CI

## Decisions deferred intentionally

Exact model choice, crawling scale, multi-tenancy, and a dedicated search engine depend on real corpus and traffic measurements. Interfaces exist for these choices, but milestone one avoids costly managed dependencies and premature distributed complexity.
