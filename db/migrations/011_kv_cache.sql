-- Small cached data (e.g. the week's high-impact news calendar for prop mode), refreshed by the scan.
create table if not exists kv_cache (
  key        text primary key,
  data       jsonb not null,
  updated_at timestamptz not null default now()
);
alter table kv_cache enable row level security;   -- server-side secret key only, like every other table
