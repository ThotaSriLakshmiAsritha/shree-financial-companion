# Privacy API

All endpoints require a valid Supabase bearer session and resolve ownership through the internal profile UUID.

## Audit events

```http
GET /privacy/audit-events
```

Returns up to 100 audit events owned by the current user. IP addresses, user agents, and auth tokens are not collected in these events.

## Delete account

```http
DELETE /privacy/account
Content-Type: application/json

{"confirmation":"DELETE_MY_ACCOUNT"}
```

The API deletes the Supabase auth user first, then removes the profile and all owned application data. It refuses to proceed if server-side service-role auth deletion is not configured or fails. A non-owned `account.deleted` audit marker is retained without the user ownership link.
