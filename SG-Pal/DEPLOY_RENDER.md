# Render MVP: one service, one persistent disk

This is the recovery-code deployment. Supabase, SMTP, Postgres and Pi services are not required. Existing local saves are not uploaded by a Git deployment. Legacy account tables/files remain intact; legacy migration tooling is outside this MVP.

## Dashboard setup

1. In Render, choose **New → Web Service**, connect `icedjaztea/sgpal`, branch `main`. Choose Python 3, region Singapore, root directory `SG-Pal`.
2. Choose **Starter**, exactly one instance. Build: `pip install -r requirements-web.txt`. Start:
   ```sh
   python -m uvicorn sgpal.server:app --host 0.0.0.0 --port $PORT --workers 1 --no-proxy-headers
   ```
   The `:app` is required. Health check: `/healthz`. No pre-deploy command or Pi dependencies.
3. Attach a **1 GB persistent disk** at `/var/data` before play. Set these server environment variables:
   - `SGPAL_DATA_DIR=/var/data/sgpal`
   - `SGPAL_PUBLIC_URL=https://YOUR-SERVICE.onrender.com` (the exact assigned URL, no path)
   - `OPENAI_API_KEY`: enter the existing Common Ground key privately in Render, never Git or chat.
   - `PYTHON_VERSION=3.13.12` (also declared in the Blueprint).
4. Deploy the latest merged commit. Alternatively create a Blueprint from the root `render.yaml`; supply the two `sync: false` environment values in Render. Do not create both a manual and Blueprint service.
5. Open the HTTPS URL, Play now, adopt, then ☰ → Save my Pal. Keep the private recovery code. Restore it in a separate browser, then restart the Render service and check the same Pal loads. Camera permission requires HTTPS; upload remains available.

Pricing checked 11 October 2026: Starter $7/month plus 1 GB disk $0.25/month = **US$7.25/month**, excluding taxes, OpenAI and usage overages. Hobby includes 5 GB outbound bandwidth, then $0.15/GB. Confirm the checkout estimate before provisioning. Sources: https://render.com/pricing and https://render.com/docs/new-workspace-plans .

## Persistence and security

Everything player-owned lives beneath `SGPAL_DATA_DIR`: `accounts.sqlite3` (sessions, account links, recovery hashes, limits, friendships) and `players/<opaque-owner>/` (profile, gameplay DB, private photos, operation state). Keep the disk attached on redeploy. Do not scale to multiple instances or workers; do not serve this directory as static files. Disk-backed deployment has brief downtime; this is not a high-availability service. Watch the 1 GB usage as photos accumulate.

Render terminates HTTPS. Uvicorn ignores forwarded headers; the application uses `SGPAL_PUBLIC_URL` as its canonical origin, validates Host and write Origin, and sets Secure/HttpOnly/SameSite cookies. CSRF and owner preconditions remain mandatory. Health checks need no player session. Use only the configured public hostname; changing domains requires updating `SGPAL_PUBLIC_URL`. All app API URLs are relative. Never enable request-body logging for recovery endpoints.

Recovery codes contain 256 random bits and only their SHA-256 hash is persisted. Codes are shown once, not stored in browser storage, URLs, logs or public profiles. Possession gives access to the profile. A lost code cannot be recovered; if the issuing response is lost, retain the signed-in browser session. There is no rotation UI in this MVP. Sign-out revokes the current session and starts a fresh guest. Restore rotates the session; unrelated active sessions remain valid. No balance merging occurs.

Failed restores are persisted and limited to 5 per session and 60 per connecting proxy/IP per 15 minutes. The aggregate proxy limit is intentionally conservative on this single-server MVP; it does not trust caller-supplied X-Forwarded-For. Existing guest progress must be saved before switching profiles.

## Checks

```sh
.venv/bin/python -m pytest tests/test_recovery.py tests/test_accounts.py tests/test_friends.py -q
.venv/bin/python scripts/test_recovery_browser.py
```

The browser check starts a real server with temporary saves, uses real recovery credentials, and restarts the process to verify persistence. It does not call OpenAI or email providers. The privacy test injects AI results only to create a private discovery photo. Public deployment verification requires an actual Render URL; local passing tests are not proof of deployment.
