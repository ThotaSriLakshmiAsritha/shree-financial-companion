# Context engine API

The context engine is the controlled boundary between persisted user data and future conversation/LLM work.

## Build the context package

```http
GET /context?query=school%20fees%20June
Authorization: Bearer <supabase-session>
```

The response contains `context` plus its approved `prompt` representation. The package includes:

- the profile language and display name;
- financial aggregates and one active goal;
- at most six educational context records;
- at most three relevant memories;
- at most six messages from the latest conversation.

The endpoint does not return unrestricted transactions, all memories, all conversations, or raw database records for prompt construction.

## Record context events

- `POST /context/educational` upserts a concept state for the authenticated user.
- `POST /context/memories` records a bounded memory candidate.
- `POST /context/conversations` starts a conversation on `web`, `voice`, or `feature_phone`.
- `POST /context/conversations/{conversation_id}/messages` appends an owned message.

All endpoints require a Supabase bearer session and resolve ownership through the internal `profiles.id` UUID.

## Educational state machine

Educational evidence is recorded through `POST /context/educational/evidence`. The service can infer a conservative signal from a statement or accept an explicit `evidence_type`:

- `introduced`
- `understood`
- `applied`
- `needs_clarification`
- `misunderstood`

Knowledge states are canonical values: `NOT_INTRODUCED`, `INTRODUCED`, `BASIC_UNDERSTANDING`, `STRONG_UNDERSTANDING`, `SUCCESSFULLY_APPLIED`, `NEEDS_CLARIFICATION`, and `MISUNDERSTOOD`. Application state is tracked separately as `NOT_OBSERVED`, `ATTEMPTED`, or `SUCCESSFULLY_APPLIED`.

For example, a statement such as “I kept money aside for school expenses before buying something unnecessary” is detected as application evidence. Budgeting is promoted to `STRONG_UNDERSTANDING`, `application_state` becomes `SUCCESSFULLY_APPLIED`, confidence is updated, and reinforcement is not requested unless later evidence indicates confusion or misunderstanding.
