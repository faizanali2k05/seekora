# Release checklist

## Required before every release

- [ ] Review `git diff` and confirm no secrets, `.env`, database dumps, or user content are included.
- [ ] Set a unique `SEEKORA_ADMIN_API_KEY`; confirm production rejects the development key.
- [ ] Run `ruff check`, the full pytest suite, TypeScript build, `npm audit`, and the real Playwright story.
- [ ] Run Alembic against a disposable PostgreSQL 16 + pgvector database.
- [ ] Run `docker compose up --build` and verify API, worker, Redis, PostgreSQL, seed, and web health.
- [ ] Ingest the sample corpus, ask a question, and open every returned citation.
- [ ] Verify `robots.txt` denial, private-network rejection, rate limits, malformed documents, and oversized responses.
- [ ] Rotate any temporary keys and remove test data.
- [ ] Review analytics retention and privacy requirements.
- [ ] Back up PostgreSQL and rehearse restore for production upgrades.
- [ ] Record image digests, migration revision, test output, and known limitations in release notes.

## Optional provider checks

- [ ] If `openai-compatible` RAG is enabled, confirm endpoint/model compatibility and budget limits.
- [ ] Test invalid/missing provider credentials and verify deterministic fallback.
- [ ] Confirm no provider receives secrets or documents beyond the selected retrieved passages.
