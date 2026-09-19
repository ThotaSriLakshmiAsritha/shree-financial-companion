# Health endpoint

GET /health

Returns a small operational response and checks that the configured SQLAlchemy database can execute a trivial query.

Example:

\`\`\`json
{
  "status": "ok",
  "service": "sahachari-api",
  "database": "connected",
  "timestamp": "2026-09-18T12:00:00Z"
}
\`\`\`

