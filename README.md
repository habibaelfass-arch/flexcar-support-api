# flexcar-support-api

Proxy service that sits between [Kustomer](https://kustomer.com) and the Flexcar support center frontend. The frontend never calls Kustomer directly — all knowledge base data flows through this service.

---

## Endpoints

### `GET /health`
Railway health check. Returns `{ "status": "ok" }`. No Kustomer call. No auth required.

---

### `GET /api/categories`
Returns all published, non-root categories.

**Response:** `Category[]`
```json
[
  {
    "id": "string",
    "slug": "string",
    "name": "string",
    "description": "string"
  }
]
```

---

### `GET /api/categories/:categorySlug/articles`
Returns all published public articles in the given category.

**Params:** `categorySlug` — the category's slug (e.g. `getting-started`)

**Response:** `Article[]` — same shape as below. Empty array if the category has no articles.

**404** if the category slug does not exist.

---

### `GET /api/articles/:slug`
Returns a single article by slug.

**Params:** `slug` — the article's slug (e.g. `0-down-cancel-anytime-cheaper-than-leasing-or-buying-whats-the-catch`)

**Response:**
```json
{
  "id": "string",
  "title": "string",
  "slug": "string",
  "categoryId": "string",
  "excerpt": "string",
  "bodyHtml": "string",
  "updatedAt": "string (ISO 8601)"
}
```

**404** if no article with that slug exists.

---

## Environment variables

All secrets must be set in Railway's Variables panel (or in a local `.env` for development — see `.env.example`). Nothing is committed.

| Variable | Required | Description |
|---|---|---|
| `KUSTOMER_API_KEY` | Yes | Bearer token for Kustomer API — role: `org.permission.kb.read` |
| `KUSTOMER_ORG_SUBDOMAIN` | Yes | Your Kustomer org subdomain (e.g. `flexcar`) |
| `ALLOWED_ORIGIN` | Yes | Comma-separated list of allowed frontend origins (no wildcard, e.g. `https://support.flexcar.com`) |
| `PORT` | No | Port to listen on — Railway injects this automatically. Defaults to `3000`. |

---

## Running locally

```bash
# 1. Copy env template and fill in values
cp .env.example .env

# 2. Install dependencies
npm install

# 3. Start dev server (hot-reload)
npm run dev
```

The server starts on `http://localhost:3000` by default.

---

## Caching

All Kustomer data is cached in-memory for 10 minutes. On expiry, a background refresh runs while the current request is served from stale data. If the background refresh fails, the service continues serving the last known good snapshot and logs the failure. The cache is pre-warmed at startup.

---

## Deployment

Railway auto-detects the `Dockerfile` at the repo root. The multi-stage build compiles TypeScript in the build stage and produces a lean production image. Set the deploy branch to `main` in Railway service settings.
