# Phase 13 — Safety and privacy controls

## Safety boundary

All web and feature-phone messages use the same deterministic safety service before Gemini. It detects OTP and credential requests, urgent payment requests, fake bank calls, suspicious links, prize scams, scam reports, and guaranteed-return language. Scam-related messages receive localized deterministic guidance and never create a transaction proposal.

Gemini is instructed to use only the compact context package, disclose missing information, avoid guarantees, and never claim that a write happened. The response validator rejects guarantee claims and unsupported numeric financial claims. Financial writes still follow proposal → explicit confirmation → transaction.

## Privacy boundary

- Every protected route resolves the Supabase session to the internal `profiles.id` and filters owned data by that UUID.
- Supabase RLS policies cover identity, financial, context, education, voice, and audit tables. Transaction proposals are readable by the owner but cannot be inserted or confirmed directly through PostgREST.
- Consent now records acceptance, version, and timestamp. Consent changes create an audit event.
- `audit_events` records security-relevant actions without collecting IP addresses or user agents by default.
- `DELETE /privacy/account` requires the exact confirmation token `DELETE_MY_ACCOUNT`, deletes the Supabase auth account first, then deletes owned application data. A non-owned deletion marker is retained for operational auditability.

The API refuses account deletion when the server-side Supabase service-role configuration is absent or the auth deletion call fails, so application data is not deleted while the auth account remains active.
