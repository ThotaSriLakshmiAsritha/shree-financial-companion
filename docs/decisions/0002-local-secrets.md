# ADR 0002: Local secret handling

- Status: accepted
- Date: 2026-09-18

## Decision

Local Supabase and Google OAuth credentials live in the root `.env` file, which is ignored by git. The tracked `.env.example` contains variable names and placeholders only.

The Supabase URL, publishable key, and anon key may eventually be used by browser code where appropriate. The Supabase service-role key, database password/connection string, and Google OAuth client secret are server-only and must never be prefixed with `VITE_` or bundled into the web app.

## Operational note

The credentials were supplied in chat, so the service-role key and Google OAuth client secret should be rotated before production deployment. The direct database URL remains a template until the database password is supplied locally.
