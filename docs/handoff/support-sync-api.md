# Handoff: support-sync API

## Goal
Build a read-only proxy API that sits between Kustomer (knowledge base) and the Flexcar support center frontend. The frontend never calls Kustomer directly — all KB data flows through this service.

## Acceptance Criteria
- [x] `GET /health` returns `{ status: "ok" }` with no Kustomer call
- [x] `GET /api/categories` returns all published, public categories as `Category[]`
- [x] `GET /api/categories/:categorySlug/articles` returns `Article[]` for that category, 404 if slug not found
- [x] `GET /api/articles/:slug` returns a single `Article`, 404 if not found
- [x] CORS only allows origins from `ALLOWED_ORIGIN` env var — no wildcard
- [x] Kustomer failures never crash the service or expose raw errors to callers
- [x] Cache lasts 10 minutes; stale data is served if a refresh fails
- [x] All secrets come from environment variables; service exits on startup if any required var is missing
- [x] Frontend (Lovable) wired up and serving real Kustomer articles

---

## Architecture Notes

- `src/config.ts` — validates all required env vars on startup, exits with a clear error message if any are missing
- `src/types.ts` — `Article` and `Category` interfaces (matches the frontend's expected shape exactly)
- `src/kustomer/types.ts` — raw Kustomer API response types (verified against live API, not guessed)
- `src/kustomer/client.ts` — fetches from `https://api.kustomerapp.com/v1/kb/articles` and `/v1/kb/categories`; filters and maps to our interfaces
- `src/cache.ts` — in-memory cache with 10-min TTL; first request blocks until data loads; subsequent requests are served from cache and refreshed in the background after expiry; stale data is kept if refresh fails
- `src/routes/categories.ts` — handles `GET /api/categories` and `GET /api/categories/:categorySlug/articles`
- `src/routes/articles.ts` — handles `GET /api/articles/:slug`
- `src/index.ts` — Express app; `/health` registered before CORS middleware; per-request logging middleware logs method, path, and origin; global error handler returns `{ error: "Internal server error" }` with 500; cache pre-warmed on startup

**Production URL:** `https://flexcar-support-api-production.up.railway.app`

**Railway project:** `zoological-commitment` → service `flexcar-support-api`

**Connected frontend:** Lovable project `flex-lovable-landing-pages` — the swap point is `src/lib/support-content.ts`. That file's three functions (`getCategories`, `getArticlesByCategory`, `getArticleBySlug`) call this API directly.

---

## Decision Log

| # | Decision | Why | Alternatives Considered |
|---|---|---|---|
| 1 | Express over Fastify | Simpler, universally understood; no meaningful performance difference for this use case (67 articles, internal service) | Fastify (slightly better TS-first, built-in pino logging) |
| 2 | In-memory Map (custom) over node-cache | Only two data types to cache, TTL logic is trivial, no external dependency needed | node-cache library |
| 3 | Stale-while-revalidate on cache expiry | Better UX — first request after TTL doesn't block waiting for Kustomer | Block-on-expiry (simpler but adds latency to every 10th-minute request) |
| 4 | `metaDescription` for `excerpt` | No explicit excerpt field in Kustomer's API; metaDescription is pre-filled on all articles and is plain text | Strip first paragraph from htmlBody (requires HTML parsing dependency) |
| 5 | `includeLang=en_us&includeBody=true` query params | Required to surface `slug` and `htmlBody` — they live in `langVersions.en_us.currentVersion.id`, not top-level attributes | Separate per-article fetches for body content |
| 6 | Filter articles with `slug !== ''` after mapping | Edge case: articles published without a version slug would produce broken routes | Error on missing slug (too noisy for a data gap) |
| 7 | Two explicit origins in `ALLOWED_ORIGIN` | Lovable serves the editor preview from a different domain (`lovableproject.com`) than the published preview (`lovable.app`) — both needed for development | Single origin (broke editor preview), wildcard (against spec) |

---

## Known Issues & Incomplete Work

- [ ] No pagination handling — hardcoded `pageSize=500` for articles and `pageSize=200` for categories. If the KB grows beyond these limits, articles/categories will be silently truncated.
- [ ] `KUSTOMER_ORG_SUBDOMAIN` is a required env var but is only used for startup logging. The Kustomer API URL does not require it — verified against live API.
- [ ] No auth on this service's own endpoints — CORS is the only gate. A shared secret (`X-Api-Key` header check) was explicitly deferred.
- [ ] No search endpoint — deferred by spec.
- [ ] Cache is process-local — if Railway scales to multiple instances, each has its own cache and its own refresh cycle.
- [ ] `ALLOWED_ORIGIN` in Railway must be manually updated if Lovable changes its editor preview domain or a custom domain is added. Currently set to both `lovable.app` preview and `lovableproject.com` editor domains.

---

## Open Questions

- Is `metaDescription` acceptable as `excerpt` long-term, or will content editors need to manage a separate field? (Builder confirmed yes for now.)
- Should `GET /api/categories/:categorySlug/articles` return articles in the Kustomer `positions` order, or is the current (insertion) order fine?
- When Lovable publishes to a custom domain, will a new `ALLOWED_ORIGIN` entry be needed? (Yes — add it via `railway variables set`.)

---

## How to Test

1. Copy `.env.example` to `.env` and fill in values
2. `npm run dev` — server starts on port 3000 (or `PORT`)
3. Logs confirm cache pre-warm: `[cache] Refreshed — 67 articles, 19 categories`
4. Every request logs: `[req] GET /api/categories origin=...`

**Live endpoints to verify:**
```
GET https://flexcar-support-api-production.up.railway.app/health
GET https://flexcar-support-api-production.up.railway.app/api/categories
GET https://flexcar-support-api-production.up.railway.app/api/categories/getting-started/articles
GET https://flexcar-support-api-production.up.railway.app/api/articles/0-down-cancel-anytime-cheaper-than-leasing-or-buying-whats-the-catch
```

**Railway env vars required:**
```
KUSTOMER_API_KEY=<key with org.permission.kb.read role>
KUSTOMER_ORG_SUBDOMAIN=flexcar
ALLOWED_ORIGIN=https://preview--flex-lovable-landing-pages.lovable.app,https://137f8b54-3096-42dc-813c-b57eb15e51a1.lovableproject.com
```

---

## Session Notes

| Time | Note |
|---|---|
| Session start | Clean slate repo. Railway project `zoological-commitment` created and linked via CLI. Railway MCP and skills installed. |
| ~30 min | Made live Kustomer API test calls before writing any field mappings. Confirmed actual response shape: `slug` and `htmlBody` are nested in `langVersions.en_us.currentVersion.id`. No `excerpt` field exists — `metaDescription` used instead. |
| ~60 min | All 4 endpoints verified working against live Kustomer data locally. TypeScript compiles clean. 67 articles, 19 categories. Dockerfile updated for Node.js 20. |
| ~75 min | Committed and pushed. Railway deployed successfully. Health check and all endpoints confirmed live at production URL. |
| ~90 min | Lovable frontend wired to Railway API. Categories loaded immediately. Articles showed 0 — Railway logs revealed Lovable's editor preview runs from `lovableproject.com`, not `lovable.app`. Added second origin to `ALLOWED_ORIGIN`. |
| End of session | Both origins allowed. Lovable frontend confirmed loading real Kustomer articles. Per-request logging added to ease future debugging. Service is fully operational. |
