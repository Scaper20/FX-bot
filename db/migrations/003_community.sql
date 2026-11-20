-- Public practice ("community"): other traders review the same past setups under a username.
-- Kept completely separate from Ore's own setups/reviews. Server-only access (RLS, no policies).

create table if not exists community_users (
  username_key text primary key,              -- lower-case name, used for matching
  display_name text not null,
  token_hash text not null,                    -- hash of the browser token that first used the name
  created_at timestamptz not null default now()
);

create table if not exists community_reviews (
  id bigserial primary key,
  username_key text not null references community_users(username_key) on delete cascade,
  item_id text not null,                       -- practice item id (P-...)
  decision text not null check (decision in ('take', 'skip', 'unsure')),
  option_id text,
  reasons text[] not null default '{}',
  notes text not null default '' check (length(notes) <= 2000),
  confidence int check (confidence between 1 and 5),
  created_at timestamptz not null default now(),
  unique (username_key, item_id)               -- one answer per trader per setup
);
create index if not exists community_reviews_user_idx on community_reviews (username_key, created_at);

alter table community_users enable row level security;
alter table community_reviews enable row level security;
