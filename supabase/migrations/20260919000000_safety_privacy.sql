alter table public.user_preferences
  add column if not exists consent_version text,
  add column if not exists consent_at timestamptz;

create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete set null,
  event_type text not null,
  resource_type text,
  resource_id uuid,
  channel text,
  details text,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create index if not exists audit_events_user_id_idx on public.audit_events(user_id);

alter table public.audit_events enable row level security;

create policy "audit_events_select_own" on public.audit_events
  for select using (user_id = public.current_internal_user_id());

-- Transaction proposals are created and confirmed through the backend only.
-- Authenticated clients may read their own pending/history rows but cannot bypass
-- server-side validation or confirmation by writing directly through PostgREST.
drop policy if exists "transaction_proposals_own" on public.transaction_proposals;
create policy "transaction_proposals_select_own" on public.transaction_proposals
  for select using (user_id = public.current_internal_user_id());
