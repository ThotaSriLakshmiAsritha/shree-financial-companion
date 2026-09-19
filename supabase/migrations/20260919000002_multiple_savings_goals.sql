-- Multiple independent savings goals with milestones and contribution history.

alter table public.goals
  add column if not exists description text,
  add column if not exists category text not null default 'general',
  add column if not exists icon text not null default '✦';

create table if not exists public.goal_milestones (
  id uuid primary key default gen_random_uuid(),
  goal_id uuid not null references public.goals(id) on delete cascade,
  amount numeric(14, 2) not null check (amount > 0),
  title text not null,
  is_completed boolean not null default false,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists goal_milestones_goal_id_idx on public.goal_milestones(goal_id);

create table if not exists public.goal_contributions (
  id uuid primary key default gen_random_uuid(),
  goal_id uuid not null references public.goals(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  amount numeric(14, 2) not null check (amount > 0),
  transaction_id uuid unique references public.transactions(id) on delete set null,
  contributed_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists goal_contributions_goal_id_idx on public.goal_contributions(goal_id);
create index if not exists goal_contributions_user_id_idx on public.goal_contributions(user_id);

alter table public.goal_milestones enable row level security;
alter table public.goal_contributions enable row level security;

drop policy if exists "goal_milestones_own" on public.goal_milestones;
create policy "goal_milestones_own" on public.goal_milestones
  for all
  using (exists (select 1 from public.goals g where g.id = goal_id and g.user_id = public.current_internal_user_id()))
  with check (exists (select 1 from public.goals g where g.id = goal_id and g.user_id = public.current_internal_user_id()));

drop policy if exists "goal_contributions_own" on public.goal_contributions;
create policy "goal_contributions_own" on public.goal_contributions
  for all using (user_id = public.current_internal_user_id())
  with check (user_id = public.current_internal_user_id());
