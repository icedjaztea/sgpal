> **Current MVP uses private recovery codes:** see [DEPLOY_RENDER.md](DEPLOY_RENDER.md). Guest → Save my Pal preserves the current player. Restore my Pal opens it on another browser. Public friend codes never authenticate. Email configuration below is retained only for legacy accounts; no email address alone grants access.

# Browser accounts and private progress

SG Pal uses **Supabase Auth** for maintained, managed email magic-link authentication. FastAPI owns opaque HttpOnly sessions, gameplay and rewards. Supabase receives email addresses, not discovery photos or gameplay saves. There is no mock login in the normal application.

Guests can play immediately. Each browser receives a random private session, with a separate player directory. Sessions last seven days; clearing cookies or letting a guest session expire loses browser access to that guest save. Use **Save my progress** to retain access through an account. Signing out revokes that browser session and starts a fresh guest. Other signed-in devices remain signed in.

## Setup

1. Create or reuse a Supabase project. Enable **Authentication → Providers → Email**, email confirmations and email sign-in. Configure a real SMTP sender for recipients beyond Supabase's development email restrictions.
2. Set **Authentication → URL Configuration → Site URL** to the application's exact origin, without a trailing slash. For local development use `http://127.0.0.1:8000`. A shared laptop/phone deployment must use the same HTTPS origin.
3. In **both Magic Link and Confirm Signup email templates**, use this link:

   ```html
   <a href="{{ .SiteURL }}/#token_hash={{ .TokenHash }}&amp;type=email">Continue to SG Pal</a>
   ```

   Do not use the default confirmation URL: this app exchanges the token on its backend. The fragment keeps the token out of HTTP request URLs and access logs. SG Pal removes it from browser history immediately and asks the player to confirm. Request and open the email link in the **same browser**, within 15 minutes. On another device, request a new link there.
4. In a local editor, create the ignored `SG-Pal/.env.accounts` file (never paste values into chat or commit it):

   ```sh
   export SUPABASE_URL='https://YOUR_PROJECT.supabase.co'
   export SUPABASE_PUBLISHABLE_KEY='YOUR_PROJECT_PUBLISHABLE_KEY'
   export SGPAL_PUBLIC_URL='http://127.0.0.1:8000'
   ```

   Use the project's publishable key, **not** a service-role/secret key. All three values are read only by the backend. Keep the existing OpenAI configuration unchanged.
5. From the repository's `SG-Pal` directory:

   ```sh
   chmod 600 .env.accounts
   .venv/bin/python -m pip install -r requirements-web.txt
   source .env.accounts
   SGPAL_DATA_DIR="$PWD/data/browser" .venv/bin/python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
   ```

Without these variables, guest play works and email requests return an honest configuration error. Variable presence is not proof of working email delivery. Test delivery, expired links and both new/existing users after configuring the provider.

Provider references: [passwordless email](https://supabase.com/docs/guides/auth/auth-email-passwordless), [email templates](https://supabase.com/docs/guides/auth/auth-email-templates).

## Cross-browser synchronization and hosting

Both devices must access **one persistent FastAPI deployment and data directory**. Signing in against two independent local servers does not synchronize their SQLite files. Deploy behind an HTTPS reverse proxy with a persistent disk and backups of the entire data directory, including `accounts.sqlite3` and `players/`. Set `SGPAL_PUBLIC_URL` to that HTTPS origin and update the Supabase Site URL/templates. Secure cookies require HTTPS there. Only trust proxy headers from the actual reverse proxy. Do not log cookies, authorization headers, request bodies or email token fragments.

Do not expose the development server publicly. Phone `localhost` means the phone, not the laptop. A production HTTPS host is required for secure remote account use; this change does not provision hosting, DNS, TLS, SMTP or a cloud database. SQLite supports this small single-host application, not replicas with independent disks or ephemeral serverless filesystems. Browser camera access requires HTTPS (or laptop localhost); upload remains available.

Changes save on the server immediately. The HUD reports saving, saved, or an unconfirmed save; **Refresh progress**, tab return and periodic home/menu refresh load newer changes. There is no offline write queue. Old room/preference/adoption writes return a conflict instead of overwriting newer state. Reward and purchase transactions are idempotent across tabs/devices; XP is never spent.

## Guest/account conflicts

A new account keeps the current guest's owner and all progress, including private photos. An existing account prompts **Use account** or **Keep guest** before switching. Neither option combines coins or overwrites the account. Use account leaves the old guest files archived on the server but removes access from this browser; there is no self-service archive recovery UI. Keep guest cancels sign-in and retains the guest save. Sign out starts an empty guest, so the next player does not inherit account data.

## Import the previous shared save safely

Old versions had one server-wide save. It is never automatically given to the first visitor. The original files remain untouched. A trusted local operator can explicitly assign a **copy**:

1. Stop the server and back up the whole data directory.
2. From `SG-Pal`, run:

   ```sh
   .venv/bin/python -m sgpal.accounts --data "$PWD/data/browser" --output "$PWD/data/legacy-import-key.txt"
   ```

3. Restart the server. In a fresh guest browser, open **Save my progress → Import an existing local save** and select that key file. Do not upload the save/photo/database itself. The private key is single-use and readable only by its local owner. Never share or commit it.
4. Confirm the imported pet/progress, then create an account to preserve access. An existing account still requires the explicit conflict decision and cannot silently absorb this save. Delete the consumed key file when finished. Demo files are excluded. The optional `?storage=browser` prototype remains separate, with its original browser-local save; it does not synchronize or authenticate and is not imported into account currency.

## Validation and limits

Run `.venv/bin/python -m pytest tests -q`, plus `scripts/test_browser.py`, `scripts/test_gameplay_browser.py` and `scripts/test_accounts_browser.py` with that Python interpreter and Chrome installed. Account browser tests use a guarded temporary fixture with a clearly mocked email provider; production startup cannot enable it. Gameplay browser tests mock AI. Live SMTP/Supabase login must be validated after external configuration. No physical phone or Pi validation is implied.

Email requests are rate-limited per email/IP. Sessions, claim keys and CSRF values are stored privately; cookie/claim tokens are hashed in the database. Every private route resolves its owner from the session, never from a client owner ID. Operational limits: guest/session cleanup, account deletion/export and multi-host storage are not implemented. Protect and back up the data directory; it contains private photos and email addresses.

## Friends (saved rooms)

Open **Friends** after email sign-in. Copy your stable 12-character code, send a request using another account's code, and use Refresh to see incoming requests. Accept or decline; accepted friends can visit the latest saved room. Return to my room leaves gameplay unchanged. Remove friend immediately denies subsequent room fetches in both directions. A previously downloaded snapshot cannot be recalled; visits are not live multiplayer.

Account identities, friend codes and friendships share `accounts.sqlite3`, independent of browser or future device type. Existing per-player gameplay storage is unchanged. Shared profiles contain only pet name/species/adoption, friend code and decoration slots; emails, balances, CultureDex photos and credentials remain private. Sending requests is limited to one every three seconds per account, including invalid guesses. No chat, gifts, trades, presence, notifications or Pi pairing.

Focused validation: `python -m pytest tests/test_friends.py tests/test_accounts.py -q` and `python scripts/test_friends_browser.py`. Browser validation uses the existing guarded mock-email fixture, not a production login bypass. Real friends require the Supabase email/SMTP configuration and the same persistent backend described above.
