-- Zone trainer: Ore's labels for order blocks and breaker blocks shown at their first revisit
-- (web/data/zone_training.json.gz). One label per zone; relabelling replaces it.
create table if not exists zone_labels (
  item_id    text primary key,
  label      text not null check (label in ('good', 'weak', 'invalid')),
  tags       text[] not null default '{}',
  notes      text not null default '',
  created_at timestamptz not null default now()
);
alter table zone_labels enable row level security;   -- server-side secret key only, like every other table
