# Authentication API

The browser authenticates with Supabase Auth using email/password or Google OAuth. It sends the resulting access token as a bearer token to the FastAPI API.

The API verifies the token with Supabase Auth's user endpoint, then resolves or creates an internal UUID in profiles. Provider identifiers are stored in user_identities; email is not used as the primary key.

## Protected endpoints

- GET /auth/me — restore the internal profile and identity mappings.
- PATCH /auth/me — update onboarding profile data with ownership enforced by the bearer session.
- POST /auth/phone/resolve — resolve a registered phone number for an authenticated voice integration.

All protected endpoints require an Authorization: Bearer <supabase-access-token> header.

A Supabase token subject is mapped to user_identities(provider=supabase, provider_subject=<subject>). Linked Google identities are synced into the same internal profile.

