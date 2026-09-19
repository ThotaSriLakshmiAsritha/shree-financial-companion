# ADR 0001: Foundation stack

- Status: accepted
- Date: 2026-09-18

## Decision

Use React + Vite + TypeScript + Tailwind for the web shell and Python + FastAPI + Pydantic + SQLAlchemy + Alembic for the API foundation. Use Supabase PostgreSQL with pgvector as the target hosted database.

## Context

The product must support a multilingual web experience now and a shared feature-phone voice channel later. A typed frontend, a modular API, and an explicit migration layer make the shared context model easier to evolve safely.

## Consequence

Local development uses the Supabase PostgreSQL session pooler so authenticated dashboard data and transactions are persisted in the hosted database. SQLite remains available only as an explicit isolated-test fallback when `DATABASE_URL` is overridden.
