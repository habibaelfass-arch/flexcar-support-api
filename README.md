# Flexcar Reddit Tool

A Reddit monitoring, drafting, and approval system that replaces Karmic. It watches relevant subreddits 24/7, scores opportunities by relevance, drafts comments in `flexcar_sam`'s voice using Claude, and surfaces them in a Lovable approval queue for Sydney to review and post manually.

**Nothing ever auto-posts.**

## Stack

| Layer | Tool |
|-------|------|
| Core engine | Python |
| Reddit API | PRAW |
| AI drafting + scoring | Claude (claude-sonnet-4-20250514) |
| Scheduler | GitHub Actions (cron every 30 min) |
| Database | Supabase (Postgres) |
| Approval UI | Lovable (internal section) |
| API | FastAPI |

## Setup

1. Copy `.env.example` to `.env` and fill in all values:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the pipeline once manually:
   ```bash
   python main.py
   ```

4. Start the FastAPI server (for Lovable UI):
   ```bash
   uvicorn api.server:app --reload
   ```

## Reddit App Setup

Go to https://www.reddit.com/prefs/apps, create a **script** type app, and copy the client ID and secret into `.env`.

## Pipeline

Every 30 minutes via GitHub Actions cron:

1. **Fetch** — pulls new posts from target subreddits
2. **Deduplicate** — skips already-processed threads
3. **Rules check** — Claude rates subreddit safety (Green/Yellow/Red)
4. **Relevance score** — Claude scores thread 0–100; below 65 = skip
5. **Frequency check** — enforces max 3 posts/day
6. **Draft** — Claude writes comment in `flexcar_sam` voice
7. **Safety pass** — similarity check, link strip, banned terms
8. **Save** — stored in Supabase with `pending_review` status
9. **Queue** — Sydney reviews and approves in Lovable UI

## Supabase Schema

Run the SQL in `database/schema.sql` against your Supabase project to create all tables.

## Environment Variables (GitHub Actions)

Add all `.env` keys as repository secrets in GitHub → Settings → Secrets and variables → Actions.
