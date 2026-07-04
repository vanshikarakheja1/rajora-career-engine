create extension if not exists pgcrypto;

create table if not exists public.user_profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    email text,
    profile jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.recommendation_history (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    profile jsonb not null,
    recommendations jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists recommendation_history_user_created_idx
    on public.recommendation_history (user_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_user_profiles_updated_at on public.user_profiles;
create trigger set_user_profiles_updated_at
before update on public.user_profiles
for each row
execute function public.set_updated_at();

alter table public.user_profiles enable row level security;
alter table public.recommendation_history enable row level security;

drop policy if exists "Users can read own profile" on public.user_profiles;
create policy "Users can read own profile"
on public.user_profiles
for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own profile" on public.user_profiles;
create policy "Users can insert own profile"
on public.user_profiles
for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own profile" on public.user_profiles;
create policy "Users can update own profile"
on public.user_profiles
for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can read own recommendation history" on public.recommendation_history;
create policy "Users can read own recommendation history"
on public.recommendation_history
for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own recommendation history" on public.recommendation_history;
create policy "Users can insert own recommendation history"
on public.recommendation_history
for insert
with check (auth.uid() = user_id);
