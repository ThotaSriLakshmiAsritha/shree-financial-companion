# Shree frontend

This is the final Sahachari frontend shell, built with React and Vite and styled with the Shree/Warli visual language.

## Local development

From the repository root:

```bash
npm install --prefix shree_frontend
npm run dev --prefix shree_frontend
```

The Vite config reads the shared root `.env`. Set `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` there. Never put a Supabase service-role key, Gemini key, Exotel secret, or Sarvam key in this frontend.

## Manual entry

The dashboard includes a localized manual-entry option for Telugu, Hindi, and English. It accepts only:

- Income or expenditure
- Amount in INR
- Reason

The form creates a pending transaction proposal through `POST /financial/proposals`. The user must explicitly confirm the proposal before `POST /financial/proposals/{id}/confirm` creates the transaction. This preserves the project rule that no frontend or AI path writes directly to `transactions`.
