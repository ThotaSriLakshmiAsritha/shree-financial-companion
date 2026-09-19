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

alter table public.financial_context enable row level security;
alter table public.income_sources enable row level security;
alter table public.financial_obligations enable row level security;
alter table public.goals enable row level security;
alter table public.transaction_proposals enable row level security;
alter table public.transactions enable row level security;

create policy "financial_context_own" on public.financial_context
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "income_sources_own" on public.income_sources
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "financial_obligations_own" on public.financial_obligations
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "goals_own" on public.goals
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "transaction_proposals_own" on public.transaction_proposals
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());

create policy "transactions_own" on public.transactions
  for select using (user_id = public.current_internal_user_id());

