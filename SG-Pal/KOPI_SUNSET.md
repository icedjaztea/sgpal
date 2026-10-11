# SG Pal · Kopi Sunset hackathon build

## Run

From the repository root:

```bash
cd SG-Pal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-web.txt
SGPAL_DATA_DIR=./data/browser python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Preview: http://127.0.0.1:8000/ · Native kiosk: http://127.0.0.1:8000/?kiosk=1
Keep the terminal open. On subsequent starts, reuse the environment. On macOS,
`Start SG Pal.command` starts the server or opens an existing local preview.

A Pi browser, laptop and phone use the same FastAPI/Canvas game. For a trusted
LAN use `--host 0.0.0.0` and the host's LAN address. Everyone connected to that
server shares its device save. Phone camera access usually needs HTTPS; Upload
works on ordinary LAN HTTP. Default localhost is appropriate for a private demo.
No public deployment, accounts or multi-user isolation are included.

## Demo walkthrough

1. Choose Merlion, Otter or Mynah; keep or reroll its suggested name.
2. From the BTO, choose Scan, then Camera or Upload. JPEG, PNG and WebP are
   supported (6 MB / 24 megapixels maximum). Export HEIC as JPEG first.
3. Review the photo. Analyse explicitly sends it to OpenAI through the backend.
4. Read the short curated explanation and AI observation. Yes confirms a
   high-confidence catalogue match; Correct asks AI to independently reassess
   another catalogue item. Choosing a label alone cannot earn a discovery.
5. First confirmation stores the photo and Singapore timestamp, grants **10
   Culture XP + 5 Kopi Coins**, and assigns the relevant quest. Dex opens the
   explanation, record and saved photograph.
6. Quest → Answer asks **“Did you complete this quest?”**. Choose **“Yes, I did
   it”** or **“Not yet”**; Back is always available.
7. Yes records a **self-reported** completion and grants **25 Culture XP + 10
   Kopi Coins** once. Not yet keeps it open without penalty. Repeated completion,
   duplicate discovery and retries cannot increase the balances again.

Quests are honesty-based. No evidence photo, location check or AI verification is
required. This product decision supersedes the original handoff's quest-photo
screens. The reference artwork and original documents remain available under
`_handoff/`; their superseded behavior is not a requirement for the current game.
The design gallery uses isolated, labelled samples and never calls AI or saves
actual rewards. The three starter entries are chope, kopi ordering and tray
return; seven existing catalogue IDs remain supported so old saves are valid.
Activities are short, respectful and do not require purchases or photographing
people. Follow signs and ask for help when needed.

## Browser reward-to-decoration loop

After earning coins, open Menu → Shop. Browse with Next and choose Buy to preview
the price, current balance and item; Back cancels without changing progress.
Confirm submits the purchase to the backend. Each decoration can be owned once.

| Decoration | Kopi Coins | Art |
| --- | ---: | --- |
| Window plant | 8 | Reused approved plant primitive |
| Kopi cup | 5 | Simple palette-matched placeholder icon |
| Tile display | 12 | Shophouse-inspired placeholder tile icon |

A discovery and self-reported quest earn 15 coins, enough for the plant and cup.
Prices and compatibility come from `sgpal/commerce.py`. The browser cannot submit
a price, balance or ownership grant. SQLite commits the debit, ownership and
operation result together. Concurrent attempts cannot overdraw or charge twice;
an already-owned item costs nothing. Culture XP is never debited. Insufficient
funds produce a clear result without a charge; after earning more, make a new
purchase from the shop rather than replaying that old insufficient-funds result.

Open Items/Inventory, choose an owned decoration, then preview the Window or Door
slot with Next. Save places it; Back cancels. Menu → Decorate offers the same owned
item choices. Moving one item clears its previous slot. Replacing another item
keeps both owned. No sales, refunds, multiple copies or drag-and-drop are included.
The base room artwork is unchanged; some furniture in that background is baked
into the approved image and is not an inventory item.

Purchase/placement requests use durable operation IDs and share Status/Retry with
gameplay. Lost responses and reloads reconcile the original operation; replaying
an old placement cannot undo a later placement. New backend tables migrate from
schema 1/2 without resetting progress. Preview and sample gallery actions never
write purchases or room state. All new controls use the shared rotary/keyboard/
touch action path and fit the existing native 320 × 240 canvas.

This stage is browser-only. No Pi connections, GPIO configuration, driver
installation or kiosk-service changes were made. Auth and friends remain deferred.

## Recognition, rewards and failures

`core.recognise` reuses the configured `gpt-4.1-mini` Responses API with image
input, strict JSON schema, allowed catalogue IDs, `store:false`, verified HTTPS
and a 35-second timeout. Certifi supplies public CA roots alongside system roots.
API calls and reward amounts are backend-only. Camera capture, timers, uncertain
matches, malformed responses and failed requests cannot grant rewards. Correction
is an independent assessment, not an automatic override. AI confidence is not a
calibrated probability and does not establish a person's actions or location.

SQLite transactions combine record creation, unique reward events and balance
updates. Culture XP is cumulative; Kopi Coins are a separate future spending
balance. Pending operation IDs survive browser reload. Status reconciles a lost
response; Retry reuses its operation identity and stored discovery image or quest
answer. There are no automatic paid retries. A stale photo-request lease may be
reclaimed after 90 seconds; that timeout never produces a recognition or reward.

`POST /api/verify` is retired (410). Incomplete old verification attempts cannot
restart AI or award rewards. Completed historical operations remain readable and
reconcilable. New completion uses `/api/quests/answer`; `completion_method` is
`self_reported`. Legacy verified completions/photos remain preserved, never
reclassified as new self-reports or rewarded again. The older native `app.py`
entry point also uses an explicit honesty answer instead of photo verification.

Camera permission denial/device absence offers Upload, Retry and Back. Failed AI
and save requests show a retry/status screen. Unknown recognition does not become
a discovery. Failed photo loading leaves navigation available. Auth, friends,
cloud sync and social features remain deferred.

## Credentials and photo privacy

Reuse the existing Common Ground credential; never create a replacement merely
for this build. Presence can be checked at `/api/status` without returning its
value. If absent, from `SG-Pal/` run:

```bash
.venv/bin/python configure_key.py
```

Paste the existing secret only into that hidden Terminal prompt. It is stored in
`~/.config/sgpal/credentials.json` with owner-only permissions, outside Git.
Alternatively use a securely configured `OPENAI_API_KEY` environment variable.
Never paste a key in chat or frontend code. File credentials are read per request.

Discovery photos are normalized JPEG BLOBs in the local database, with EXIF
removed, not publicly hosted assets. UUID photo responses use private/no-store,
same-origin resource policy and nosniff headers. SQLite is owner-readable/writable
only. No friend sharing or cloud sync is enabled. A deliberate Analyse/correction
sends the photo to OpenAI; `store:false` does not promise zero provider retention.
LAN visitors to this single-device server share access to its save and photos;
keep the demo local or on a trusted network. This is not an authenticated service.

## Save compatibility

`SGPAL_DATA_DIR` defaults to `~/.local/share/sgpal`; startup above uses ignored
`data/browser/`. Back up that directory with the server stopped before moving it.

- `profile.json` retains adoption/name/species/sound.
- Original `progress.json` is imported once and preserved byte-for-byte.
- `gameplay.sqlite3` owns current progress, photos and durable operations. Schema
  2 adds quest answers; schema 3 adds inventory, room slots and durable purchase/
  placement operations. Both migrations preserve balances, photos and completions.
- Legacy XP is retained, with no retroactive coin awards. Historical entries with
  no stored photograph are explicitly labelled. Demo progress is never imported.

Corrupt or incompatible files fail closed without reset. If the old native app
changes the legacy JSON after migration, both saves are preserved and a conflict
is reported. Continue migrated progress through the shared FastAPI game; do not
run both runtimes against one migrated save. Credentials, virtual environments,
saves, logs, photos and test results are ignored by Git.

## Controls, design and hardware boundary

The approved room/Merlion/Otter/Mynah art is unchanged. The shared canvas is exactly
320 × 240 with integer enlargement, bitmap text and Kopi Sunset palette.
Keyboard arrows/Enter/Space/Escape, touch focus-then-activate, and rotary events
use one action system. No essential action needs a long press.

```javascript
window.dispatchEvent(new CustomEvent('sgpal:rotate', {detail:{delta:1}}));
window.dispatchEvent(new CustomEvent('sgpal:rotate', {detail:{delta:-1}}));
window.dispatchEvent(new Event('sgpal:press'));
```

Existing GPIO pin mappings, raw SPI display code and CSI adapter are retained.
Connecting those adapters to this renderer is pending; Chromium alone does not
connect to the raw SPI driver. No physical Pi, camera, encoder or iPhone Safari
validation is claimed. The old native runtime remains for hardware diagnostics.

## Tests

From `SG-Pal/` with the environment activated:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python scripts/test_browser.py
python scripts/test_gameplay_browser.py
```

Browser tests use installed Chrome and temporary saves. For Playwright Chromium,
run `python -m playwright install chromium`, then set `SGPAL_BROWSER_CHANNEL=chromium`.
Tests cover onboarding, reload, nine menu routes, 57 isolated gallery states,
320–1100px viewports, exact kiosk geometry, all input adapters, correction, AI
failure, Not yet, Yes, repeated claims, migration, concurrency and failed saves.
The browser fixture is explicitly labelled simulated AI; it refuses normal data
folders. Automated tests do not spend API credits.

Optional live check (one paid recognition call, temporary progress):

```bash
python scripts/test_live_gameplay.py /absolute/path/to/menu.jpg --expected-id kopi --allow-live
```

It refuses to call without `--allow-live`. A missing/uncertain/unexpected match
stops without rewards. It checks saved image bytes, Singapore timestamps, Not yet,
self-reported Yes, duplicates and reload. The tested input was a synthetic kopi-O
menu, not a field photograph: successful live API access is not camera-accuracy
validation. Reports and screenshots stay under ignored `test-results/`.

## Curated content references

Kopi terminology follows [Singapore Tourism Board's kopi guide](https://www.visitsingapore.com/ko_kr/things-to-do/dining/local-food-and-drinks/order-coffee-like-a-local/).
Tray-return guidance follows [NEA's Clean Tables campaign](https://www.nea.gov.sg/our-services/public-cleanliness/clean-tables).
Chope is presented as a contextual practice, never inferred confidently from an
isolated tissue packet. These short activities avoid claims about every Singaporean.

Shop-stage validation: 62 backend tests pass, including earned-coin purchases,
insufficient funds, forged prices, concurrent duplicates, competing purchases,
rollback, ownership/slot validation, idempotent placement and schema-2 migration.
The complete browser test extends the labelled AI fixture through cancellation,
lost purchase response/reload, touch placement, insufficient funds, replacement
and saved room reload. Existing onboarding/mobile/gallery checks also pass.
No new live AI test was needed for this stage: recognition code is unchanged,
and test coins come from discovery/quest transactions with injected recognition.
