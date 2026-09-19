create table if not exists public.voice_turns (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.voice_call_sessions(id) on delete cascade,
  idempotency_key text not null,
  status text not null default 'processing' check (status in ('processing', 'completed', 'failed')),
  response_payload jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id, idempotency_key)
);

create index if not exists voice_turns_session_id_idx on public.voice_turns(session_id);

alter table public.voice_turns enable row level security;

create policy "voice_turns_select_own" on public.voice_turns
  for select using (
    exists (
      select 1 from public.voice_call_sessions s
      where s.id = session_id
        and s.user_id = public.current_internal_user_id()
    )
  );
