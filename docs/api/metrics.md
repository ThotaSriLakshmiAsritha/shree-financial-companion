# Performance metrics API

## `GET /metrics/performance`

Returns bounded aggregate timing data in local development and tests.

```json
{
  "metrics": {
    "api.request": {
      "count": 1,
      "errors": 0,
      "avg_ms": 3.12,
      "p50_ms": 3.12,
      "p95_ms": 3.12,
      "max_ms": 3.12,
      "sample_count": 1
    }
  }
}
```

The response is intentionally aggregate-only. It does not expose payloads,
prompts, generated responses, SQL, tokens, or personal identifiers. The route
returns `404` when `APP_ENV` is `staging` or `production`.

Instrumented names include `api.request`, `database.query`, `llm.gemini`,
`voice.sarvam_stt`, `voice.sarvam_tts`, `voice.exotel_download`, and
`voice.turn`.
