# Kopi Sunset gameplay integration — 11 October 2026

## Run

```bash
cd sgpal/SG-Pal
source .venv/bin/activate
python -m pip install -r requirements-web.txt
SGPAL_DATA_DIR=./data/browser python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Preview: http://127.0.0.1:8000/

Handheld: http://127.0.0.1:8000/?kiosk=1

On macOS, `Start SG Pal.command` starts this server (keep its Terminal open) or
opens the kiosk if the server is already running. For a phone on the same trusted
LAN, use `--host 0.0.0.0` and the computer's LAN IP. All visitors share this device's
save and photos; this is not an authenticated multi-user/cloud deployment. Camera
access on a phone generally needs HTTPS; use Upload on ordinary LAN HTTP.

## Existing Common Ground credential

The integration uses `OPENAI_API_KEY`, or the file selected by `SGPAL_KEY_FILE`,
defaulting to `~/.config/sgpal/credentials.json`. Nothing creates another key.
Use the existing local hidden-input helper:

```bash
.venv/bin/python configure_key.py
```

Enter the existing secret in that terminal prompt. It is saved outside the repo
with owner-only file permissions; never paste it in chat, JavaScript, or Git.
The running server reads the file per request, so configuring it needs no restart.
`GET /api/status` reveals presence only. Missing credentials produce an actionable
error with Retry. A key name alone is not a secret, and presence does not establish
model access, billing, network connectivity, or response quality.

The existing `gpt-4.1-mini` setting in `config.json` is retained. The backend uses
the Responses API with image input and strict structured output, `store: false`,
and a 35-second network timeout. There is no automatic paid retry. Provider keys
are never sent to the frontend or included in error text. API format references:
[images and vision](https://developers.openai.com/api/docs/guides/images-vision)
and [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

HTTPS uses Python's default trust context plus Certifi's public CA bundle. This
fixes missing default certificates in the macOS Python installation while keeping
certificate and hostname verification enabled and preserving system/custom roots.

## Real core flow

1. Adopt Merlion, Otter or Mynah, keep or reroll a suggested name, and enter the BTO.
2. Scan → Camera/Upload → review. Analyse explicitly sends the image to OpenAI.
3. The server normalizes JPEG/PNG/WebP, strips metadata, and assesses it against
   the existing ten-entry culture catalogue. Limit: 6 MB and 24 megapixels.
4. A high-confidence known item becomes a candidate, with no reward yet. Yes
   confirms it. Correct selects another catalogue item and runs a new independent
   assessment of the same image; selecting a label does not grant rewards.
5. The first confirmed discovery atomically saves the photo reference, record,
   quest assignment and **10 XP + 5 Kopi Coins**. A duplicate grants zero and keeps
   the original discovery photograph/time.
6. Dex opens the curated story, metadata and actual saved photograph. Timestamps
   are server receipt times displayed in Asia/Singapore, not claims about when
   an uploaded file was originally photographed.
7. Quest offers **Done**, **Not yet**, and **Back**. Done is the player's explicit
   declaration that the activity is finished; no evidence photo or AI check is
   required. Not yet keeps the quest open and awards nothing.
8. Done atomically saves a Singapore-time completion and **25 XP + 10 coins**.
   It is recorded as `self_reported`, never falsely described as AI verified.
   Concurrent/repeated answers and completed legacy quests cannot earn again.
   Failed requests and timers never decide completion. Lost responses can be
   reconciled through Status; a failed delivery can be retried after reload.

This follows the latest product instruction and supersedes the reference's quest
photo-check requirement. Real recognition and independent correction assessment
still gate discovery. The existing `/api/verify` route remains compatible for old
clients and saved operations, but the new UI does not request quest evidence.

Photos are normalized real JPEGs stored as SQLite BLOBs, not pixel-art substitutes.
Discovery and evidence files can be retrieved through UUID-based `/api/photos/`
URLs; the database is not served as a static file. Photos and operations remain
local until a deliberate Analyse/correction sends the relevant photo to OpenAI.
`store:false` is not a promise of zero provider retention. There is no photo
sharing, cloud sync, or social access.

XP and Kopi Coins are distinct integer balances. XP determines level using the
existing 50-XP rule. Coins are retained for future spending; no purchase endpoint
is enabled in this phase. Existing discovery/quest XP values are retained.

## Transactions, retry and migration

`sgpal/gameplay.py` owns SQLite persistence and reward rules. `sgpal/server.py`
validates API input and calls the existing `core.recognise` adapter. Each request
has an operation UUID. Reusing a UUID with different content is rejected. Pending
requests do not start another provider call. Failed requests can be deliberately
retried; completed results are returned from storage. The browser retains the
pending operation ID across reload and offers Status/Retry. The Home Status button
returns to an unfinished request. Retry after reload uses the persisted photo.
Photo requests use leases. A crashed worker's pending lease can be reclaimed after 90 seconds. An old worker
cannot commit after its lease has been replaced. This timer only releases a lock;
it never decides an AI result or awards anything.

Reward event IDs are unique per culture and reward type. Database transactions
include photo references where applicable, discovery/completion records, balance increments and
operation results. Interrupted transactions roll back together. Lost responses
can therefore be reconciled without adding a second reward. Distinct concurrent
requests for one culture also award once. Exact photo hashing deters accidental
reuse, but is not fraud-proof against crops or re-encoding; AI judgement also
requires real-world validation.

Files in `SGPAL_DATA_DIR` (default `~/.local/share/sgpal`):

- `profile.json`: existing versioned adoption/name/species/sound, unchanged format.
- `progress.json`: original XP/log/quest state, preserved byte-for-byte.
- `gameplay.sqlite3`: new authoritative gameplay, created on first game operation.
  Imports original XP, discoveries, active/completed quests and timestamps once.
  Schema 2 adds durable quest answers without changing schema-1 photos, balances,
  or completed records. Existing photo checks remain marked `photo_verified`;
  earlier imported completions remain `legacy`.
  Old records have no photo because the original app did not store them. Existing
  discoveries/completions cannot earn again; historical coins start at zero.
- `demo-progress.json`: original demo only; never imported into real gameplay.

The database stores a legacy snapshot. A later change to `progress.json` produces
an explicit conflict, preserving both saves rather than silently merging balances.
Continue migrated saves through the new server, not both game runtimes at once.
Back up the data directory with the server stopped before moving it to a Pi.
Corrupt/unsupported saves fail closed and are not reset.

## Shared UI and hardware boundary

All browser targets use the same approved Canvas at 320 × 240, integer enlargement,
bitmap text, Kopi Sunset palette and original PNG assets. Art is unchanged. Menus
have explicit Back/Cancel/Prev/Next controls and no required long press.
Keyboard arrows/Enter/Space/Escape, touch focus-then-activate, on-screen Turn/Press,
and these rotary events feed the same navigation functions:

```javascript
window.dispatchEvent(new CustomEvent('sgpal:rotate', {detail:{delta:1}}));
window.dispatchEvent(new CustomEvent('sgpal:rotate', {detail:{delta:-1}}));
window.dispatchEvent(new Event('sgpal:press'));
```

The 57 reference design states remain isolated, visibly labeled samples. They
cannot send AI requests or mutate real saves. `?storage=browser` remains an
explicit static visual preview; real gameplay requires FastAPI.

The original native app and hardware adapters are retained. Its verifier also now
requires a matching culture ID before granting quest XP. Wiring this browser UI
to the raw SPI display, GPIO encoder and CSI camera remains pending; launching
Chromium alone does not connect to this project's raw SPI display driver.

## Tests and validation limits

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python scripts/test_browser.py
python scripts/test_gameplay_browser.py
```

Browser tests use installed Chrome, temporary server/save directories and isolated
browser profiles. `test_browser.py` disables credentials. The complete gameplay
browser test runs `scripts/gameplay_fixture.py`, an explicitly labeled test-only
recognizer; it cannot run against a normal data directory. No production route or
configuration enables that fixture. For installed Playwright Chromium instead of
Chrome, set `SGPAL_BROWSER_CHANNEL=chromium` after installing that browser.

Validated: complete API/database and browser flows; correction assessment; no
reward before confirmation; real photo byte persistence and Singapore timestamps;
legacy migration; uncertainty/failure/wrong-ID rejection; repeated and concurrent
claims; simulated save rollback; stale-worker lease protection; lost response
reconciliation; retry after reload; all three species; keyboard/rotary/touch input;
all nine menus; gallery isolation; mobile widths 320–1100; exact kiosk geometry.
Screenshots are under ignored `test-results/`. Unit tests inject provider results,
and the provider-contract test intercepts the HTTP request without sending it.
These tests verify application behavior, not real model accuracy.

After the existing Common Ground credential was configured locally, live OpenAI
validation passed on 11 October 2026 with two synthetic menu images and temporary
progress: kopi-O recognition, explicit confirmation, saved photo retrieval,
Singapore timestamps, quest assignment, kopi-C evidence verification, persisted
reload, replay and new-operation reward deduplication. Exactly two reward events
produced 35 XP and 15 coins. An earlier unclear sample returned unknown and could
not be confirmed or rewarded. Reports and input images are in ignored
`test-results/live-api-validation.json`, `live-api-uncertain-validation.json`,
`live-discovery-menu.png` and `live-evidence-menu.png`.

These calls verified credential/model access and the live API/database flow;
synthetic menus do not establish real-world camera accuracy. The complete browser
flow uses the separate simulated provider described above. No new credential was
created and the user's save was untouched. All 51 automated tests passed in the shared checkout, including migration,
concurrent Done answers, strict input checks and rollback. The complete browser
test now covers Not yet, Done, failed delivery across reload and lost responses. Physical Pi display/camera/encoder, actual iPhone Safari and
camera hardware remain untested. Auth, friends, full shop, decoration and sync
remain deferred.

## Current Done / Not yet live check

The shared checkout passed the updated end-to-end API flow with a real OpenAI
recognition request on a synthetic kopi-O menu: confirm, retrieve the actual
stored image, check Singapore time, Not yet (zero reward), Done (25 XP/10 coins),
replay, duplicate completion and persisted reload. Final balance: 35 XP/15 coins.
This test used temporary progress and did not alter the player's save. It does
not establish real camera accuracy and performs no quest AI verification.

To deliberately repeat with your own photo (one paid image request), from `SG-Pal/`:

```bash
python scripts/test_live_gameplay.py /absolute/path/to/menu.jpg --expected-id kopi --allow-live
```

Without `--allow-live`, the script refuses to call the provider. A nonmatching or
uncertain result stops without confirmation or rewards. Output is ignored under
`test-results/`; the credential is never printed.

## Shared repository and review

The implementation lives in `SG-Pal/` in https://github.com/icedjaztea/sgpal.git,
with the approved reference preserved at `_handoff/sgpal-kopi-sunset-ui/`.
Branch `feat/sgpal-kopi-sunset` starts at origin/main commit
`6fcad08b85bf00c3eb02e80b3412e0c2c2043e7c`. The sprint branch pointed at that
same commit during inspection. No applicable AGENTS.md was present.

The earlier Downloads folder had no commits or remote. It remains intact beside
the separate `shared-repository/` checkout; its files were compared with main
before integrating the reviewed differences. Hardware configuration, original
catalogue, artwork/font licence and original six tests are preserved. Existing
Python/Pillow hardware entry points remain available for compatibility, while the
new shared FastAPI/Canvas game is the supported cross-device implementation.
Credentials, virtual environments, runtime saves, photos, logs and test output
are ignored. No key or local progress is part of the branch.
