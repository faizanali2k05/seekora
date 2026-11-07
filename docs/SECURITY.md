# Security notes

## Trust boundaries

- Crawled HTML is untrusted. Scripts, styles, forms, navigation, and other non-content elements are removed before indexing.
- Retrieved text is evidence, never instructions. The RAG prompt labels it untrusted and the local generator excludes common prompt-injection phrases.
- Citation identifiers come from retrieval results, not model-generated URLs. Answers from an optional provider are accepted only when all citation numbers resolve to supplied sources; otherwise Seekora falls back to deterministic extractive generation.

## Crawler controls

- HTTP(S) only; DNS results must be globally routable.
- Private, loopback, link-local, multicast, and reserved targets are rejected.
- `robots.txt` is checked for the configured user agent.
- Cross-origin redirects are rejected and every redirect target is revalidated.
- Request timeout, response-byte limit, redirect limit, HTML content type, and per-origin delay are enforced.
- Run crawling workers on a network segment without cloud metadata access as defense in depth.

## Authentication and secrets

- Corpus writes, crawl jobs, statistics, and administration require the administrator API key in a Bearer or `X-API-Key` header.
- Comparison uses constant-time `hmac.compare_digest`.
- Production startup rejects the documented development key.
- The browser never persists the key; the admin console retains it only in component memory.
- Secrets belong in environment variables or the deployment platform’s secret store. Never commit `.env`.

API-key auth is suitable for this single-administrator MVP. Multi-user deployments should replace it with an OIDC/session provider, scoped roles, key rotation, and audit identities.

## Availability and privacy

- API limits use Redis counters and fall back to per-process limits if Redis is unavailable.
- Search cache entries contain result metadata and expire after two minutes.
- Analytics store query text, result count, latency, and timestamp. If queries may contain personal data, disable or redact them before production use.
- Queue jobs expire after 24 hours. Worker errors are truncated before persistence.

## Reporting

Do not open a public issue for a vulnerability containing secrets or exploit details. Contact the repository owner privately with affected version, reproduction steps, impact, and suggested mitigation.
