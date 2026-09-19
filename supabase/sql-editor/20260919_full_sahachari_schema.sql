-- Sahachari hosted schema bootstrap.
-- Run this once in Supabase SQL Editor for project oqknqbpaqpwjimpngnyx.
-- It is the ordered equivalent of supabase/migrations/*.sql.

begin;

create extension if not exists vector with schema extensions;
create extension if not exists pgcrypto;

create table if not exists public.system_metadata (
  key text primary key,
  value text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.system_metadata (key, value)
values ('schema_version', 'phase-1')
on conflict (key) do update set value = excluded.value, updated_at = now();

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
  monthly_income_estimate numeric(12, 2),
  financial_setup_completed boolean not null default false,
  consent_accepted boolean not null default false,
  consent_version text,
  consent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.current_internal_user_id()
returns uuid language sql stable security definer set search_path = public
as $$
  select ui.user_id from public.user_identities ui
  where ui.provider = 'supabase' and ui.provider_subject = auth.uid()::text
  limit 1
$$;

create or replace function public.set_updated_at()
returns trigger language plpgsql
as $$
begin new.updated_at = now(); return new; end;
$$;

create table if not exists public.financial_context (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  income_pattern text,
  monthly_income_estimate numeric(12, 2),
  current_savings numeric(14, 2) not null default 0,
  total_income numeric(14, 2) not null default 0,
  total_expenses numeric(14, 2) not null default 0,
  total_savings numeric(14, 2) not null default 0,
  currency text not null default 'INR',
  last_financial_update timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists public.income_sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  income_type text not null,
  typical_amount numeric(12, 2),
  frequency text,
  seasonal boolean not null default false,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (typical_amount is null or typical_amount >= 0)
);
create index if not exists income_sources_user_id_idx on public.income_sources(user_id);

create table if not exists public.financial_obligations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  amount numeric(12, 2) not null check (amount > 0),
  currency text not null default 'INR',
  frequency text not null,
  due_day integer check (due_day is null or due_day between 1 and 31),
  priority text not null default 'normal',
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists financial_obligations_user_id_idx on public.financial_obligations(user_id);

create table if not exists public.goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  target_amount numeric(14, 2) not null check (target_amount > 0),
  current_amount numeric(14, 2) not null default 0 check (current_amount >= 0),
  currency text not null default 'INR',
  target_date date,
  status text not null default 'active' check (status in ('active', 'completed', 'paused')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists goals_user_id_idx on public.goals(user_id);

create table if not exists public.transaction_proposals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  transaction_type text not null check (transaction_type in ('income', 'expense', 'saving')),
  amount numeric(14, 2) not null check (amount > 0),
  currency text not null default 'INR',
  category text,
  description text,
  transaction_date date not null,
  source text not null,
  confidence numeric(4, 3) not null default 0 check (confidence between 0 and 1),
  raw_statement text,
  goal_id uuid references public.goals(id) on delete set null,
  status text not null default 'pending' check (status in ('pending', 'confirmed', 'rejected')),
  created_at timestamptz not null default now(),
  confirmed_at timestamptz
);
create index if not exists transaction_proposals_user_id_idx on public.transaction_proposals(user_id);
create index if not exists transaction_proposals_goal_id_idx on public.transaction_proposals(goal_id);

create table if not exists public.transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  proposal_id uuid not null unique references public.transaction_proposals(id) on delete restrict,
  transaction_type text not null check (transaction_type in ('income', 'expense', 'saving')),
  amount numeric(14, 2) not null check (amount > 0),
  currency text not null default 'INR',
  category text,
  description text,
  transaction_date date not null,
  source text not null,
  confidence numeric(4, 3) not null check (confidence between 0 and 1),
  confirmation_status text not null default 'confirmed' check (confirmation_status in ('pending', 'confirmed', 'rejected')),
  created_at timestamptz not null default now(),
  confirmed_at timestamptz not null default now(),
  goal_id uuid references public.goals(id) on delete set null
);
create index if not exists transactions_user_id_idx on public.transactions(user_id);
create index if not exists transactions_goal_id_idx on public.transactions(goal_id);

create table if not exists public.educational_context (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  concept text not null,
  knowledge_state text not null,
  application_state text,
  reasoning text,
  misconceptions text,
  last_discussed timestamptz,
  reinforcement_needed boolean not null default false,
  confidence numeric(4, 3) not null default 0 check (confidence between 0 and 1),
  updated_at timestamptz not null default now(),
  unique (user_id, concept)
);
create index if not exists educational_context_user_id_idx on public.educational_context(user_id);

create table if not exists public.memories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  content text not null,
  memory_type text not null default 'conversation',
  source text not null default 'conversation',
  importance numeric(4, 3) not null default 0.5 check (importance between 0 and 1),
  created_at timestamptz not null default now(),
  last_retrieved_at timestamptz
);
create index if not exists memories_user_id_idx on public.memories(user_id);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  channel text not null check (channel in ('web', 'voice', 'feature_phone')),
  language text not null check (language in ('en', 'te', 'hi')),
  started_at timestamptz not null default now(),
  ended_at timestamptz
);
create index if not exists conversations_user_id_idx on public.conversations(user_id);

create table if not exists public.conversation_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  message text not null,
  language text not null check (language in ('en', 'te', 'hi')),
  intent text,
  metadata jsonb,
  created_at timestamptz not null default now()
);
create index if not exists conversation_messages_conversation_id_idx on public.conversation_messages(conversation_id);

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

-- Normalize educational states before applying the state-machine checks.
update public.educational_context
set knowledge_state = case lower(trim(knowledge_state))
  when 'not_introduced' then 'NOT_INTRODUCED'
  when 'not introduced' then 'NOT_INTRODUCED'
  when 'introduced' then 'INTRODUCED'
  when 'basic_understanding' then 'BASIC_UNDERSTANDING'
  when 'basic understanding' then 'BASIC_UNDERSTANDING'
  when 'strong_understanding' then 'STRONG_UNDERSTANDING'
  when 'strong understanding' then 'STRONG_UNDERSTANDING'
  when 'successfully_applied' then 'SUCCESSFULLY_APPLIED'
  when 'successfully applied' then 'SUCCESSFULLY_APPLIED'
  when 'needs_clarification' then 'NEEDS_CLARIFICATION'
  when 'needs clarification' then 'NEEDS_CLARIFICATION'
  when 'misunderstood' then 'MISUNDERSTOOD'
  else 'INTRODUCED'
end,
application_state = case lower(trim(coalesce(application_state, '')))
  when 'not_observed' then 'NOT_OBSERVED'
  when 'not observed' then 'NOT_OBSERVED'
  when 'attempted' then 'ATTEMPTED'
  when 'needs practice' then 'ATTEMPTED'
  when 'successfully_applied' then 'SUCCESSFULLY_APPLIED'
  when 'successfully applied' then 'SUCCESSFULLY_APPLIED'
  when 'consistent' then 'SUCCESSFULLY_APPLIED'
  else 'NOT_OBSERVED'
end;

alter table public.educational_context
  add constraint educational_context_knowledge_state_check
  check (knowledge_state in ('NOT_INTRODUCED', 'INTRODUCED', 'BASIC_UNDERSTANDING', 'STRONG_UNDERSTANDING', 'SUCCESSFULLY_APPLIED', 'NEEDS_CLARIFICATION', 'MISUNDERSTOOD'));
alter table public.educational_context
  add constraint educational_context_application_state_check
  check (application_state is null or application_state in ('NOT_OBSERVED', 'ATTEMPTED', 'SUCCESSFULLY_APPLIED'));

alter table public.profiles enable row level security;
alter table public.user_identities enable row level security;
alter table public.user_preferences enable row level security;
alter table public.financial_context enable row level security;
alter table public.income_sources enable row level security;
alter table public.financial_obligations enable row level security;
alter table public.goals enable row level security;
alter table public.transaction_proposals enable row level security;
alter table public.transactions enable row level security;
alter table public.educational_context enable row level security;
alter table public.memories enable row level security;
alter table public.conversations enable row level security;
alter table public.conversation_messages enable row level security;
alter table public.voice_call_sessions enable row level security;
alter table public.voice_turns enable row level security;
alter table public.audit_events enable row level security;

create policy "profiles_select_own" on public.profiles for select using (id = public.current_internal_user_id());
create policy "profiles_update_own" on public.profiles for update using (id = public.current_internal_user_id()) with check (id = public.current_internal_user_id());
create policy "identities_select_own" on public.user_identities for select using (user_id = public.current_internal_user_id());
create policy "preferences_select_own" on public.user_preferences for select using (user_id = public.current_internal_user_id());
create policy "preferences_update_own" on public.user_preferences for update using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());

create policy "financial_context_own" on public.financial_context for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "income_sources_own" on public.income_sources for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "financial_obligations_own" on public.financial_obligations for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "goals_own" on public.goals for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "transaction_proposals_select_own" on public.transaction_proposals for select using (user_id = public.current_internal_user_id());
create policy "transactions_own" on public.transactions for select using (user_id = public.current_internal_user_id());

create policy "educational_context_own" on public.educational_context for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "memories_own" on public.memories for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "conversations_own" on public.conversations for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "conversation_messages_own" on public.conversation_messages for all
  using (exists (select 1 from public.conversations c where c.id = conversation_id and c.user_id = public.current_internal_user_id()))
  with check (exists (select 1 from public.conversations c where c.id = conversation_id and c.user_id = public.current_internal_user_id()));
create policy "voice_call_sessions_own" on public.voice_call_sessions for all using (user_id = public.current_internal_user_id()) with check (user_id = public.current_internal_user_id());
create policy "voice_turns_select_own" on public.voice_turns for select
  using (exists (select 1 from public.voice_call_sessions s where s.id = session_id and s.user_id = public.current_internal_user_id()));
create policy "audit_events_select_own" on public.audit_events for select using (user_id = public.current_internal_user_id());

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles for each row execute procedure public.set_updated_at();
drop trigger if exists preferences_set_updated_at on public.user_preferences;
create trigger preferences_set_updated_at before update on public.user_preferences for each row execute procedure public.set_updated_at();

commit;
