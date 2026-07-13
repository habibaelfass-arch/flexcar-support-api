# Handoff: Flexcar Reddit Tool

## Goal

Build a Reddit monitoring, drafting, and approval system to replace Karmic. The system watches target subreddits every 30 minutes, scores threads for relevance using Claude, drafts helpful comments in `flexcar_sam`'s voice, and surfaces them in a queue for Sydney to review and post manually. Nothing ever auto-posts.

## Acceptance Criteria

- [ ] PRAW connects to the `flexcar_sam` Reddit account and fetches posts from target subreddits
- [ ] Claude scores each thread 0–100 for relevance; threads below 65 are skipped
- [ ] Claude rates each subreddit Green / Yellow / Red; Red subreddits are skipped entirely
- [ ] Claude drafts a comment in `flexcar_sam`'s natural Reddit voice
- [ ] Drafts pass safety checks: no links, no banned terms, < 40% similar to past posts
- [ ] Max 3 posts per day enforced; posts are spaced 90 ± 30 minutes apart
- [ ] All threads and drafts are saved to Supabase
- [ ] FastAPI exposes `/queue`, `/analytics`, and `/settings` endpoints for Lovable UI
- [ ] GitHub Actions cron runs the pipeline every 30 minutes

---

## Architecture Notes

- `main.py` — full pipeline orchestrator; called by GitHub Actions
- `monitor/reddit_client.py` — singleton PRAW client with retry/backoff
- `monitor/subreddit_watcher.py` — fetches 50 most recent posts per sub, normalizes to dicts
- `monitor/deduplicator.py` — filters already-processed threads using Supabase IDs
- `monitor/rules_checker.py` — calls Claude with `RULES_CHECKER_SYSTEM_PROMPT`; caches results per sub per run
- `scoring/relevance_scorer.py` — calls Claude with `RELEVANCE_SCORER_SYSTEM_PROMPT`; threshold = 65
- `scoring/opportunity_ranker.py` — filters + sorts scored threads
- `drafting/prompt_templates.py` — all three Claude system prompts live here
- `drafting/comment_drafter.py` — drafts comment, runs through link stripper + banned terms + similarity check
- `drafting/similarity_checker.py` — TF-IDF cosine similarity vs. past `post_history` rows
- `safety/` — `banned_terms.py`, `link_stripper.py`, `frequency_limiter.py`
- `database/schema.sql` — Supabase table definitions + seed subreddit list; run once in SQL Editor
- `database/queries.py` — all DB read/write helpers
- `api/server.py` — FastAPI app with CORS + bearer-token auth middleware
- `api/routes/queue.py` — GET `/queue`, POST `/approve/{id}`, POST `/reject/{id}`, POST `/mark-posted/{id}`
- `api/routes/analytics.py` — GET `/analytics/weekly`, `/subreddits`, `/history`
- `api/routes/settings.py` — GET/PATCH subreddit list and config
- `.github/workflows/monitor.yml` — cron every 30 min + manual `workflow_dispatch`

---

## Decision Log

| # | Decision | Why | Alternatives Considered |
|---|----------|-----|------------------------|
| 1 | TF-IDF cosine similarity for duplicate detection | No extra API call needed; fast and deterministic; scikit-learn is already a common dep | Embedding-based similarity via Claude/OpenAI, exact-match hashing |
| 2 | In-memory config dict for settings (threshold, keywords, daily cap) | Settings are low-volume; a full DB config table adds schema complexity for little gain in this MVP | Supabase `config` table, env vars |
| 3 | Singleton PRAW and Supabase clients | GitHub Actions runs main.py as a single process; singletons avoid re-auth overhead | New client per module call |
| 4 | Bearer-token auth for FastAPI (API_SECRET_KEY env var) | Internal-only API for Lovable; full OAuth would be over-engineered | Supabase JWT, no auth |
| 5 | `workflow_dispatch` added alongside cron | Allows Sydney or Habiba to manually trigger a run without waiting 30 min | Cron-only |

---

## Known Issues & Incomplete Work

- [ ] The `/settings/config` endpoint stores config in-memory only — changes are lost on server restart. Should be moved to Supabase or a config file for persistence.
- [ ] `rules_checker.py` cache is in-memory per run. Subreddit safety ratings are not persisted to `monitored_subreddits.safety_rating` automatically after a run.
- [ ] `frequency_limiter.py` in-memory counter resets each GitHub Actions run. The DB-backed `get_posts_today_from_db()` is the source of truth and is wired into `main.py`, but the in-memory fallback could give a false green if the DB call fails.
- [ ] No error alerting — if the pipeline crashes, it fails silently in GitHub Actions. Should add email/Slack notification on failure.
- [ ] `api/routes/settings.py` `recheck_rules` flag is accepted but does not yet trigger an actual rules re-check via Claude. Needs wiring.
- [ ] Lovable UI not yet built — the API is ready but the frontend approval queue does not exist yet.
- [ ] `analytics_snapshots` table has no auto-population logic. Needs a separate weekly cron or a manual fill step.

---

## Open Questions

- Should the rules re-check happen on every run or only when manually triggered from the Settings UI?
- What should happen when the daily cap is reached — defer all drafts to tomorrow's queue or just skip them?
- Does Sydney want email/Slack notifications when new drafts enter the queue, or will she just check the Lovable UI on a schedule?
- Should `analytics_snapshots` be auto-populated weekly by a separate GitHub Actions job?

---

## How to Test

1. Copy `.env.example` → `.env`, fill in all credentials (Reddit app, Anthropic, Supabase)
2. Run `database/schema.sql` in Supabase SQL Editor to create tables + seed subreddits
3. Run `python main.py` from the project root — watch console output for each pipeline step
4. Run the FastAPI server: `uvicorn api.server:app --reload`, then hit `http://localhost:8000/queue`
5. Run unit tests: `pip install pytest && pytest tests/`

---

## Session Notes

| Time | Note |
|------|------|
| Session 1 | Full project scaffold built from architecture PDF. All 6 sessions implemented in one pass: monitor, scoring, rules checker, safety, drafting, database, FastAPI API, GitHub Actions workflow, and unit tests. |
