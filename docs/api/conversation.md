# Conversation orchestrator API

## Handle a message

```http
POST /conversation/message
Authorization: Bearer <supabase-session>
Content-Type: application/json
```

```json
{
  "message": "I spent ₹250 on school books yesterday.",
  "conversation_id": null,
  "channel": "web"
}
```

The protected endpoint runs one pipeline:

`language detection → intent detection → deterministic entity extraction → bounded context retrieval → personalization → safety evaluation → Gemini response → response validation → persistence`

Gemini receives only the compact context package produced by the context builder. It does not receive unrestricted database records.

## Financial safety boundary

A detected financial statement creates a pending `transaction_proposal`. The response always says that it has not been recorded yet and asks for explicit confirmation. Only the existing proposal confirmation endpoint can create a transaction.

The orchestrator uses deterministic logic for language scripts, intents, amounts, dates, currencies, transaction types, ownership, proposal creation, and safety checks. Gemini is used for the personalized natural-language response only.

High-risk messages containing OTPs, passwords, PINs, verification codes, or urgent transfer instructions bypass Gemini and receive deterministic safety guidance.
