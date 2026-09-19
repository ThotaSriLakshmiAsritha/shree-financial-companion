# Financial domain API

Financial writes use an explicit proposal workflow:

1. A text/voice extraction layer creates a structured proposal.
2. The API validates ownership, amount, currency, type, goal, and confidence.
3. The proposal is stored as pending.
4. The user confirms or rejects it.
5. Only confirmation creates a transaction and updates financial context/goals atomically.

There is intentionally no POST endpoint for transactions.

## Endpoints

- GET /financial/context
- GET /financial/transactions
- POST /financial/proposals
- GET /financial/proposals
- POST /financial/proposals/{proposal_id}/confirm
- POST /financial/proposals/{proposal_id}/reject
- GET/POST /financial/income-sources
- GET/POST /financial/obligations
- GET/POST /financial/goals

