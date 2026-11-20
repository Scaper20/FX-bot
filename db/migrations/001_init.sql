-- CRT scanner website: tables (spec v1.3). Only the server (secret key) reads and writes:
-- row level security is on with no policies, so the public/anon key can do nothing.

create table if not exists settings (
  id int primary key default 1 check (id = 1),
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists setups (
  id text primary key,
  source text not null default 'live' check (source in ('live', 'practice')),
  pair text not null,
  direction text not null,
  range_tf text not null,
  k int not null,
  range_open timestamptz not null,
  decision_time timestamptz,
  first_seen timestamptz not null default now(),
  recommended boolean not null default false,
  engine text not null,
  card jsonb not null,                       -- snapshot when first shown; never updated
  added jsonb not null default '[]'::jsonb,  -- options first seen later, with their time
  status jsonb not null default '{}'::jsonb, -- option id -> tracked outcome
  final boolean not null default false,
  updated_at timestamptz not null default now()
);
create index if not exists setups_open_idx on setups (source, final, pair);
create index if not exists setups_seen_idx on setups (first_seen desc);

-- The snapshot is the forward record: refuse any change to it.
create or replace function setups_card_is_immutable() returns trigger language plpgsql as $$
begin
  if new.card is distinct from old.card or new.first_seen is distinct from old.first_seen then
    raise exception 'setup snapshot (card, first_seen) cannot be changed';
  end if;
  return new;
end $$;
drop trigger if exists setups_card_immutable on setups;
create trigger setups_card_immutable before update on setups
  for each row execute function setups_card_is_immutable();

create table if not exists reviews (
  id bigserial primary key,
  setup_id text not null references setups(id) on delete cascade,
  decision text not null check (decision in ('take', 'skip', 'unsure')),
  option_id text,
  reasons text[] not null default '{}',
  notes text not null default '',
  confidence int check (confidence between 1 and 5),
  actual_entry double precision,
  actual_exit double precision,
  actual_r double precision,
  actual_closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists reviews_setup_idx on reviews (setup_id);

create table if not exists scans (
  id bigserial primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  trigger text,
  ok boolean not null default false,
  message text,
  credits int not null default 0,
  ready int not null default 0,
  armed int not null default 0,
  result jsonb
);
create index if not exists scans_started_idx on scans (started_at desc);

create table if not exists usage (
  day date primary key,
  credits int not null default 0
);

create or replace function add_credits(n int) returns void language sql as $$
  insert into usage (day, credits) values ((now() at time zone 'utc')::date, n)
  on conflict (day) do update set credits = usage.credits + excluded.credits;
$$;

-- Token for the scheduled scan. Generated inside the database; nobody types or sees it.
create table if not exists app_secrets (
  name text primary key,
  token text not null
);
insert into app_secrets (name, token)
  values ('cron', replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', ''))
  on conflict (name) do nothing;

alter table settings enable row level security;
alter table setups enable row level security;
alter table reviews enable row level security;
alter table scans enable row level security;
alter table usage enable row level security;
alter table app_secrets enable row level security;
revoke all on function add_credits(int) from anon, authenticated;
