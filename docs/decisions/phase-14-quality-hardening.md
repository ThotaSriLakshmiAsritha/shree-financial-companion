# Phase 14 — Quality hardening

Phase 14 makes the product measurable, replay-safe, and testable as a shared
financial system rather than treating the LLM as the system boundary.

## Performance instrumentation

The API records bounded in-process timing samples for:

- `api.request`
- `database.query`
- `llm.gemini`
- `voice.sarvam_stt`
- `voice.sarvam_tts`
- `voice.exotel_download`
- `voice.turn`

Development and local testing can read the aggregate counters at
`GET /metrics/performance`. Production and staging return `404` so this
diagnostic endpoint cannot become an unintended data surface. Metrics contain
durations, counts, status labels, and error counts only; they never contain
request bodies, prompts, generated text, tokens, phone numbers, or SQL.

The final frontend shell records a browser `frontend.load` measurement in the
development console using the browser Performance API. It records only load
duration and transfer size.

## Reliability controls

Voice turns are persisted in `voice_turns` with a unique `(session_id,
idempotency_key)` constraint. A replayed Exotel webhook returns the completed
response payload without invoking the orchestrator or TTS a second time.
Provider timeout and transport failures are normalized into safe service
errors, while the health endpoint remains a liveness check that reports an
unavailable database without crashing the process.

## Security invariants

- Backend ownership checks always derive the user from the verified session;
  client-supplied `user_id` values are not trusted.
- Expired Supabase sessions are rejected.
- Prompt-injection phrases are detected before Gemini is called.
- Generated payloads reject unknown fields and unsafe direct-action language.
- Financial writes remain proposal/validation/confirmation based.
- Voice webhook replays cannot duplicate a turn.

## AI evaluation

`evals/phase14_dataset.jsonl` is a small, versioned regression set covering
English, Hindi, Telugu, mixed-language input, financial statements,
ambiguity, incorrect assumptions, scam scenarios, prompt injection,
educational evidence, context retrieval, memory relevance, and deterministic
goal calculations.

Run it with:

```bash
python evals/run_evals.py
```

The runner is deterministic and does not call external LLM or voice APIs. It
reports separate scores for language, intent, entity extraction, safety,
education, memory relevance, context retrieval, and calculation correctness.

## Verification commands

```bash
cd apps/api
python -m pytest -q
python -m ruff check app tests --ignore UP017
python -m compileall -q app
alembic upgrade head

cd ../..
python evals/run_evals.py
cd shree_frontend
npm run lint
npm run build
```

`UP017` is ignored for the existing repository because the current Python
runtime's timezone-style autofix would create a broad unrelated diff. It is a
follow-up modernization task, not a Phase 14 failure.
