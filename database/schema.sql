-- Run this against your Supabase project to create all tables.
-- Go to Supabase → SQL Editor → paste this → Run.

create table if not exists monitored_subreddits (
  id              bigint generated always as identity primary key,
  name            text not null unique,
  rules_text      text,
  safety_rating   text not null default 'yellow' check (safety_rating in ('green', 'yellow', 'red')),
  active          boolean not null default true,
  last_rules_check timestamptz,
  created_at      timestamptz not null default now()
);

create table if not exists reddit_threads (
  id               bigint generated always as identity primary key,
  reddit_post_id   text not null unique,
  subreddit        text not null,
  title            text not null,
  body             text,
  author           text,
  url              text,
  posted_at        timestamptz,
  relevance_score  int,
  opportunity_rank int,
  status           text not null default 'new'
                   check (status in ('new','drafted','approved','rejected','posted','skipped')),
  created_at       timestamptz not null default now()
);

create table if not exists comment_drafts (
  id                bigint generated always as identity primary key,
  thread_id         bigint references reddit_threads(id) on delete cascade,
  draft_text        text not null,
  similarity_score  float,
  safety_flags      jsonb,
  approved_by       text,
  approved_at       timestamptz,
  edited_text       text,
  posted_at         timestamptz,
  reddit_comment_id text,
  created_at        timestamptz not null default now()
);

create table if not exists post_history (
  id            bigint generated always as identity primary key,
  subreddit     text not null,
  comment_text  text not null,
  thread_url    text,
  karma_at_post int,
  created_at    timestamptz not null default now()
);

create table if not exists analytics_snapshots (
  id                      bigint generated always as identity primary key,
  week_start              timestamptz,
  account_karma           int,
  total_impressions       int,
  llm_traffic             int,
  reddit_referral_traffic int,
  organic_mentions        int,
  self_reported_leads     int,
  comments_posted         int,
  threads_posted          int,
  created_at              timestamptz not null default now()
);

-- Seed the starting subreddit list
insert into monitored_subreddits (name, safety_rating) values
  ('askcarsales',         'green'),
  ('cars',                'green'),
  ('carbuying',           'green'),
  ('Atlanta',             'green'),
  ('boston',              'green'),
  ('Charlotte',           'green'),
  ('nashville',           'green'),
  ('AskNYC',              'green'),
  ('SanFrancisco',        'green'),
  ('moving',              'green'),
  ('frugal',              'green'),
  ('personalfinance',     'yellow'),
  ('leasehackr',          'yellow'),
  ('financialindependence','yellow'),
  ('povertyfinance',      'yellow')
on conflict (name) do nothing;
