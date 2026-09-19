create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  display_name text,
  phone_number text unique,
  preferred_language text not null default 'en' check (preferred_language in ('en', 'hi', 'te')),
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_identities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  provider text not null,
  provider_subject text not null,
  created_at timestamptz not null default now(),
  unique (provider, provider_subject)
);

create index if not exists user_identities_user_id_idx on public.user_identities(user_id);

create table if not exists public.user_preferences (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  preferred_channel text not null default 'web',
  voice_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.current_internal_user_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select ui.user_id
  from public.user_identities ui
  where ui.provider = 'supabase'
    and ui.provider_subject = auth.uid()::text
  limit 1
$$;

alter table public.profiles enable row level security;
alter table public.user_identities enable row level security;
alter table public.user_preferences enable row level security;

create policy "profiles_select_own"
  on public.profiles for select
  using (id = public.current_internal_user_id());

create policy "profiles_update_own"
  on public.profiles for update
  using (id = public.current_internal_user_id())
  with check (id = public.current_internal_user_id());

create policy "identities_select_own"
  on public.user_identities for select
  using (user_id = public.current_internal_user_id());

create policy "preferences_select_own"
  on public.user_preferences for select
  using (user_id = public.current_internal_user_id());

create policy "preferences_update_own"
  on public.user_preferences for update
  using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute procedure public.set_updated_at();

drop trigger if exists preferences_set_updated_at on public.user_preferences;
create trigger preferences_set_updated_at
before update on public.user_preferences
for each row execute procedure public.set_updated_at();

