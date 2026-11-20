-- Newest candles per pair and timeframe, refreshed by every scan, so setup charts can show
-- what happened after a setup was logged.
create table if not exists latest_candles (
  pair text not null,
  tf text not null,
  data jsonb not null,                 -- [[unix_seconds, o, h, l, c], ...]
  updated_at timestamptz not null default now(),
  primary key (pair, tf)
);
alter table latest_candles enable row level security;
