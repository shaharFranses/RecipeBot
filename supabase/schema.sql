-- Run once in Supabase: Dashboard → SQL Editor → paste → Run.
create table if not exists public.recipes (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  source_url   text unique,          -- the Instagram reel
  author       text default '',      -- Instagram account
  thumbnail    text,
  title        text not null,
  description  text default '',
  servings     text default '',
  total_time   text default '',
  ingredients  jsonb not null default '[]',   -- [{item, amount}]
  steps        jsonb not null default '[]',   -- ["step 1", ...]
  tags         text[] not null default '{}',
  notes        text default '',      -- Michal's own notes ("more sugar")
  raw_caption  text default '',
  added_by     text default ''       -- WhatsApp number that sent it
);

create index if not exists recipes_created_at on public.recipes (created_at desc);

-- Row level security: the bot uses the service key (bypasses RLS).
-- Website access rules get added in the website step.
alter table public.recipes enable row level security;
