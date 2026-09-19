create extension if not exists vector with schema extensions;

create table if not exists public.system_metadata (
  key text primary key,
  value text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.system_metadata (key, value)
values ('schema_version', 'phase-1')
on conflict (key) do update set value = excluded.value, updated_at = now();

