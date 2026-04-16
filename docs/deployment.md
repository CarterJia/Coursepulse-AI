# Railway Deployment Guide

This project is deployed on Railway as three services: `frontend`, `backend`, and a managed Postgres plugin.

## One-time setup

### 1. Provision Railway project

- Create a new Railway project.
- Add the **Postgres** plugin to the project. Railway will set `DATABASE_URL` automatically on the backend service once linked.

### 2. Backend service

- Deploy from the `backend/Dockerfile` in this repo (set the Root directory to `/`, Dockerfile path to `backend/Dockerfile`).
- Environment variables:
  - `DEEPSEEK_API_KEY` — your DeepSeek API key (used for default-quota requests)
  - `UPLOAD_QUOTA_PER_IP` — default `3`
  - `FILE_STORAGE_ROOT` — `/app/storage`
  - `SAMPLE_DOCUMENT_ID` — leave empty for now; populate after step 4

### 3. Frontend service

- Deploy from `frontend/Dockerfile`.
- Environment variables:
  - `NEXT_PUBLIC_API_BASE_URL` — the public URL of the backend service (e.g. `https://backend-production.up.railway.app`)

### 4. Populate the sample document

- Once both services are live, upload the sample PDF ONCE using your own API key so it bypasses quota:

```bash
curl -i -X POST \
  -H 'X-User-API-Key: YOUR_DEEPSEEK_KEY' \
  -F 'file=@path/to/sample.pdf' \
  https://backend-production.up.railway.app/api/documents/upload
```

- Copy the `document_id` from the response.
- Set `SAMPLE_DOCUMENT_ID` on the backend service to that UUID.
- Redeploy the backend. "Try the sample" on the homepage now routes to this document.

## Operational notes

- **Storage is ephemeral.** `scripts/cleanup_storage.sh` runs on container startup and deletes files older than 7 days from `storage/slides/`, `storage/assignments/`, and `storage/derived/`. This is intentional — the demo doesn't retain user uploads long term. Generated reports and glossary entries live in Postgres and persist across restarts.
- **Quota counter resets on restart.** The counter is in-memory. When the container is redeployed or restarted by Railway, all IPs get a fresh quota. Acceptable for a demo.
- **BYOK keys are never persisted.** They live only in the browser's localStorage and appear only on the single HTTP request they travel with. The backend never writes them to disk or logs.

## Costs

- Railway Hobby plan: $5/month (keeps containers warm, no cold start)
- DeepSeek API: estimated $5–30/month depending on traffic; capped by the per-IP quota
