# Voice and feature-phone integration

The feature-phone path is a transport adapter around the web conversation system:

`phone dialer → Sarvam Voice Agent → caller phone mapping → internal user_id → shared context/financial/education services`

Browser recordings use `Sarvam STT → ConversationOrchestrator → Sarvam TTS`. There is no separate voice identity, context store, or financial write path.

## Endpoints

### Authenticated browser microphone turn

```http
POST /voice/exotel/browser/turn
Authorization: Bearer <Supabase access token>
Content-Type: application/json
```

```json
{
  "call_id": "browser-turn-id",
  "audio_base64": "<short microphone recording>",
  "audio_mime_type": "audio/webm",
  "idempotency_key": "turn-key"
}
```

The API derives the internal user from the verified session. The browser
cannot provide or modify a caller phone number. This uses the same STT,
orchestrator, context, proposal-confirmation workflow, and TTS as feature
phone traffic.

### Short audio turn

```http
POST /voice/exotel/turn
X-Exotel-Signature: <optional configured HMAC signature>
Content-Type: application/json
```

```json
{
  "call_id": "exotel-call-id",
  "caller_number": "+919876543210",
  "audio_base64": "<short audio chunk>",
  "audio_mime_type": "audio/wav"
}
```

This endpoint decodes the short audio chunk, sends it to Sarvam STT, sends the transcript through the existing `ConversationOrchestrator` with `channel=feature_phone`, and returns base64-encoded Sarvam TTS audio.

### Exotel webhook adapter

```http
POST /voice/exotel/webhook
```

The adapter accepts JSON or URL-encoded Exotel events containing the call ID and caller number. It can process a transcript, inline base64 audio, or an HTTPS recording URL. Events without an audio turn are acknowledged without creating an AI response.

Configure `EXOTEL_WEBHOOK_SECRET` in staging/production. The adapter accepts an HMAC-SHA256 hex or base64 signature in `X-Exotel-Signature` or `X-Exotel-Webhook-Signature`.

### Sarvam Voice Agent context tool

Configure the Sarvam Voice Agent with a static masked header named
`X-Sarvam-Agent-Key`. Its value should be `SARVAM_AGENT_TOOL_KEY`; when that
setting is omitted during development, the server accepts the existing
server-side `SARVAM_API_KEY` instead.

```http
POST /voice/sarvam/agent/context
X-Sarvam-Agent-Key: <server-side-agent-key>
Content-Type: application/json
```

```json
{
  "user_phone_number": "{{user_identifier}}",
  "query": "what is my current savings?"
}
```

The response is a compact context package, not the complete database.

### Sarvam Voice Agent transaction tool

Use `POST /voice/sarvam/agent/transaction` with the same header. The agent
may call `action=propose` after collecting a transaction, then ask the user
for confirmation and call `action=confirm` with the returned `proposal_id`.
`action=reject` is available when the user corrects the entry. The endpoint
never accepts a `user_id`; it resolves the registered caller phone to the
internal profile UUID and applies the same ownership checks as the web UI.

### Sarvam deployment completion webhook

Configure the deployed agent's completion webhook as:

```http
POST /voice/sarvam/webhook
X-Sarvam-Agent-Key: <server-side-agent-key>
```

The endpoint maps `user_phone_number`, stores the call transcript in the
shared conversation, and is idempotent for repeated `interaction_id` values.

## Shared identity and persistence

`caller_number` is normalized and resolved through `profiles.phone_number`. Unknown callers are rejected. A `voice_call_sessions` row links the Exotel call ID to the same `conversations.id` and internal `profiles.id` used by the web application. Repeated events for one Exotel call reuse that conversation.

The orchestrator preserves the financial proposal-confirmation rule: a voice statement creates a pending proposal, never a direct transaction. Conversation messages, educational evidence, goals, memories, and financial context all use the existing shared services.

## Provider configuration

Server-side configuration is defined in `.env.example`:

- Exotel account credentials, region/base URL, ExoPhone, and webhook secret.
- Sarvam API key, Saaras STT model/mode, Bulbul TTS model/speaker, optional agent ID, and agent-tool key.

Sarvam REST STT is intended for short turns; longer call media should be chunked or moved to a streaming/batch adapter later.
