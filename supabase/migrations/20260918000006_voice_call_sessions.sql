create table if not exists public.voice_call_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  provider text not null default 'exotel' check (provider in ('exotel', 'sarvam')),
  external_call_id text not null,
  phone_number text not null,
  conversation_id uuid not null unique references public.conversations(id) on delete cascade,
  language text not null check (language in ('en', 'hi', 'te')),
  status text not null default 'active' check (status in ('active', 'completed', 'failed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider, external_call_id)
);

create index if not exists voice_call_sessions_user_id_idx on public.voice_call_sessions(user_id);

alter table public.voice_call_sessions enable row level security;

create policy "voice_call_sessions_own" on public.voice_call_sessions
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());
