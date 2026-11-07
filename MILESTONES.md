# Delivery milestones

The milestone definitions and exit criteria live in [ARCHITECTURE.md](ARCHITECTURE.md#milestone-plan). Work is delivered in order; a milestone is complete only when its stated behavior has been exercised and its automated checks pass.

- [x] Architecture and milestone plan written
- [x] Milestone 1 implementation
- [x] Milestone 1 verification on the current host
- [x] Redis crawl queue, cache, API limits, analytics, and administration MVP
- [x] Grounded RAG with validated citations and optional provider adapter
- [x] Single-administrator authentication and authorization fixtures
- [x] Real browser → API → ingestion → retrieval → answer verification
- [ ] Docker Compose smoke test on a Docker-capable host
- [ ] Live PostgreSQL/pgvector integration test on a capable host or CI run
- [ ] Multi-user OIDC and scoped roles (post-MVP)
- [ ] Neural embedding and cross-encoder adapters (post-MVP)
