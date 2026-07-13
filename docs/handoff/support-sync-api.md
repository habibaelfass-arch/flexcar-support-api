# Handoff: support-sync API

## Goal
Build a read-only proxy API that sits between Kustomer (knowledge base) and the Flexcar support center frontend. The frontend never calls Kustomer directly — all KB data flows through this service.

## Acceptance Criteria
- [ ] `GET /health` returns `{ status: "ok" }` with no Kustomer call
- [ ] `GET /api/categories` returns all published, public categories as `Category[]`
- [ ] `GET /api/categories/:categorySlug/articles` returns `Article[]` for that category, 404 if slug not found
- [ ] `GET /api/articles/:slug` returns a single `Article`, 404 if not found
- [ ] CORS only allows origins from `ALLOWED_ORIGIN` env var — no wildcard
- [ ] Kustomer failures never crash the service or expose raw errors to callers
- [ ] Cache lasts 10 minutes; stale data is served if a refresh fails
- [ ] All secrets come from environment variables; service exits on startup if any required var is missing

---

## Architecture Notes

- `src/config.ts` — validates all required env vars on startup, exits with a clear error message if any are missing
- `src/types.ts` — `Article` and `Category` interfaces (matches the frontend's expected shape exactly)
- `src/kustomer/types.ts` — raw Kustomer API response types (verified against live API, not guessed)
- `src/kustomer/client.ts` — fetches from `https://api.kustomerapp.com/v1/kb/articles` and `/v1/kb/categories`; filters and maps to our interfaces
- `src/cache.ts` — in-memory cache with 10-min TTL; first request blocks until data loads; subsequent requests are served from cache and refreshed in the background after expiry; stale data is kept if refresh fails
- `src/routes/categories.ts` — handles `GET /api/categories` and `GET /api/categories/:categorySlug/articles`
- `src/routes/articles.ts` — handles `GET /api/articles/:slug`
- `src/index.ts` — Express app; `/health` registered before CORS middleware; global error handler returns `{ error: "Internal server error" }` with 500 status; cache pre-warmed on startup

---

## Decision Log

| # | Decision | Why | Alternatives Considered |
|---|---|---|---|
| 1 | Express over Fastify | Simpler, universally understood; no meaningful performance difference for this use case (67 articles, internal service) | Fastify (slightly better TS-first, built-in pino logging) |
| 2 | In-memory Map (custom) over node-cache | Only two data types to cache, TTL logic is trivial, no external dependency needed | node-cache library |
| 3 | Stale-while-revalidate on cache expiry | Better user experience — first request after TTL doesn't block waiting for Kustomer | Block-on-expiry (simpler but adds latency to every 10th-minute request) |
| 4 | `metaDescription` for `excerpt` | No explicit excerpt field in Kustomer's API; metaDescription is pre-filled on all articles and is plain text | Strip first paragraph from htmlBody (requires HTML parsing dependency) |
| 5 | `includeLang=en_us&includeBody=true` query params | Required to surface `slug` and `htmlBody` — they live in `langVersions.en_us.currentVersion.id`, not in top-level attributes | Separate per-article fetches for body content |
| 6 | Filter articles with `slug !== ''` after mapping | Edge case: articles published without a version slug would produce broken routes | Error on missing slug (would be too noisy for a data gap) |

---

## Known Issues & Incomplete Work

- [ ] No pagination handling — hardcoded `pageSize=500` for articles and `pageSize=200` for categories. If the KB grows beyond these limits, articles/categories will be silently truncated.
- [ ] `KUSTOMER_ORG_SUBDOMAIN` is a required env var but is only used for startup logging. The Kustomer API URL does not require the subdomain — verified against live API.
- [ ] No auth on this service's own endpoints — CORS is the only gate. A shared secret (`X-Api-Key` header check or similar) was explicitly deferred.
- [ ] No search endpoint — deferred by spec.
- [ ] Cache is process-local — if Railway scales to multiple instances, each will have its own cache and its own 10-minute refresh cycle.

---

## Open Questions

- Is `metaDescription` acceptable as `excerpt` long-term, or will content editors need to manage a separate field? (Builder confirmed yes for now.)
- Should `GET /api/categories/:categorySlug/articles` return articles in the Kustomer `positions` order, or is the current (insertion) order fine?

---

## How to Test

1. Copy `.env.example` to `.env` and fill in values
2. `npm run dev` — server starts on port 3000 (or `PORT`)
3. Check cache pre-warm in logs: `[cache] Refreshed — 67 articles, 19 categories`
4. Hit endpoints:
   - `GET /health`
   - `GET /api/categories` — should return 19 categories
   - `GET /api/categories/getting-started/articles` — should return 22 articles
   - `GET /api/articles/0-down-cancel-anytime-cheaper-than-leasing-or-buying-whats-the-catch`
   - `GET /api/articles/does-not-exist` — should 404 with `{ "error": "Article not found: does-not-exist" }`

Railway env vars to set before first deploy:
- `KUSTOMER_API_KEY`
- `KUSTOMER_ORG_SUBDOMAIN` (= `flexcar`)
- `ALLOWED_ORIGIN` (= frontend origin(s))

---

## Session Notes

| Time | Note |
|---|---|
| Session start | Clean slate repo — wiped previous project. Railway project `zoological-commitment` already created and linked via CLI. |
| ~30 min | Made live Kustomer API test calls before writing any field mappings — confirmed actual response shape differs from docs in key ways: `slug` and `htmlBody` are nested in `langVersions.en_us.currentVersion.id`, not top-level attributes. No `excerpt` field exists. |
| End of session | All 4 endpoints verified working against live Kustomer data. TypeScript compiles clean. Smoke test confirmed: 67 articles, 19 categories. Dockerfile updated for Node.js 20. Ready for Railway env var setup and first deploy. |
