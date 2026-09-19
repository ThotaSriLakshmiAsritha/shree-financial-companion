# Phase 1 Architecture

## Runtime boundaries

\`\`\`text
React/Vite web shell
        │
        │ REST + JSON
        ▼
FastAPI API
        │
        ├── settings / logging / errors
        ├── SQLAlchemy session
        └── Alembic migrations
        │
        ▼
Supabase PostgreSQL + pgvector
\`\`\`

The local default uses the Supabase PostgreSQL session pooler. The database URL is normalized to the psycopg SQLAlchemy dialect at runtime; SQLite is reserved for isolated tests.

## Design principles

- User identity and persistent context are first-class concerns.
- The browser talks to the API through a small typed client boundary.
- API errors have a stable error object with code and message fields.
- Migration tooling is separate from application startup.
- The web shell is language-aware from the first screen and supports English, Hindi, and Telugu.
