-- Losses to review: Ore's feedback on each losing trade of the live-scanner replay
-- (web/data/loss_review.json.gz). One row per trade; reviewing again replaces it.
create table if not exists loss_reviews (
  item_id    text primary key,
  verdict    text not null check (verdict in ('valid', 'managed', 'invalid', 'unsure')),
  reasons    text[] not null default '{}',
  notes      text not null default '',
  created_at timestamptz not null default now()
);
alter table loss_reviews enable row level security;   -- server-side secret key only, like every other table
