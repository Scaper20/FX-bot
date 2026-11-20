-- Email sign-in (6-digit codes) and update emails for public practice traders.
alter table community_users add column if not exists email text;
alter table community_users add column if not exists email_verified_at timestamptz;
alter table community_users add column if not exists notify boolean not null default false;
alter table community_users add column if not exists unsub_token text;
create unique index if not exists community_users_email_idx on community_users (lower(email)) where email is not null;

create table if not exists community_codes (
  id bigserial primary key,
  email text not null,                   -- lower-case
  username_key text not null,
  display_name text not null,
  notify boolean not null default false,
  code_hash text not null,               -- never the code itself
  expires_at timestamptz not null,
  attempts int not null default 0,
  used boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists community_codes_email_idx on community_codes (email, created_at desc);

create table if not exists community_emails (
  id bigserial primary key,
  subject text not null,
  recipients int not null default 0,
  sent int not null default 0,
  failed int not null default 0,
  note text,
  created_at timestamptz not null default now()
);

alter table community_codes enable row level security;
alter table community_emails enable row level security;
