-- Allow the shared voice session table to record Sarvam Voice Agent calls.

alter table public.voice_call_sessions drop constraint if exists voice_call_sessions_provider_check;
alter table public.voice_call_sessions drop constraint if exists ck_voice_call_sessions_provider;
alter table public.voice_call_sessions
  add constraint ck_voice_call_sessions_provider check (provider in ('exotel', 'sarvam'));
