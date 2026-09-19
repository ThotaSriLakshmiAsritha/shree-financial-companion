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

create index if not exists conversation_messages_conversation_id_idx
  on public.conversation_messages(conversation_id);

alter table public.educational_context enable row level security;
alter table public.memories enable row level security;
alter table public.conversations enable row level security;
alter table public.conversation_messages enable row level security;

create policy "educational_context_own" on public.educational_context
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "memories_own" on public.memories
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "conversations_own" on public.conversations
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "conversation_messages_own" on public.conversation_messages
  for all
  using (
    exists (
      select 1 from public.conversations c
      where c.id = conversation_id
        and c.user_id = public.current_internal_user_id()
    )
  )
  with check (
    exists (
      select 1 from public.conversations c
      where c.id = conversation_id
        and c.user_id = public.current_internal_user_id()
    )
  );
