alter table public.user_preferences
  add column if not exists monthly_income_estimate numeric(12, 2),
  add column if not exists financial_setup_completed boolean not null default false,
  add column if not exists consent_accepted boolean not null default false;

