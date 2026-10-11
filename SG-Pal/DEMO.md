# Two-minute browser demo

This is the real FastAPI browser game. Discovery recognition uses OpenAI; quests
are self-reported. There is no simulated successful AI fallback. No Pi is needed.

## Start and preserve progress

From the shared repository's `SG-Pal` directory, with the existing environment:

```bash
SGPAL_DATA_DIR=./data/browser .venv/bin/python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ (responsive full-window browser game).
http://127.0.0.1:8000/?kiosk=1 is the exact 320 × 240 layout, without browser framing.
If the preview already runs, use it; do not start a second listener on that port.
For a new checkout, follow the environment installation in KOPI_SUNSET.md.

To rehearse onboarding without resetting anyone's saved game, start a separate
server with a new, unused data directory and port:

```bash
SGPAL_DATA_DIR=./data/rehearsal-01 .venv/bin/python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8001
```

Open http://127.0.0.1:8001/. This is a separate rehearsal save with **real AI and
real earned rewards**, not preloaded sample progress. Reuse that directory to
continue it. Choose a new unused directory for another fresh run; do not delete
actual saves. Clearing browser storage does not reset server progress. Keep the
same URL during a run so pending operation recovery stays in the same origin.

## Prepare

Bring your own clear JPEG/PNG/WebP photo of a Singapore kopi stall menu, ideally
showing kopi-O and kopi-C with the stall context. A plain coffee cup may be too
ambiguous. Keep it below 6 MB and 24 MP; export HEIC to JPEG first. Have that menu
available to read during the quest. Avoid faces and personal information.

Rehearse recognition with that exact photo in a separate save before presenting.
The model may be uncertain or identify another supported item. Confirm only a
correct suggestion. Correct triggers another real AI request and is not a way to
force rewards. This stage did not live-validate a cultural photo; no image is
bundled or guaranteed to be recognised.

## Timed script (target, not an AI latency guarantee)

| Time | Action and narration |
| --- | --- |
| 0:00–0:15 | Start → choose a Pal → Choose → Reroll if desired → Keep. “A Singapore companion with a little BTO home.” |
| 0:15–0:45 | Scan → Upload the prepared menu → Analyse. “This photo goes to real AI; only a supported, confirmed discovery earns rewards.” Read the explanation (scroll if needed); Yes only if correct. |
| 0:45–1:00 | Dex → Info, briefly show the saved entry/photo, then Quest. “Culture XP measures learning; Kopi Coins are spendable.” |
| 1:00–1:20 | Read the quest → Answer → Not yet. Show it remains active. Read the prepared menu, work out kopi-O or kopi-C, and practise the order. Answer → Yes, I did it. “Completion is self-reported, once.” |
| 1:20–1:40 | Home → Menu → Shop → Buy window plant → Confirm. First discovery + quest earn 15 coins; plant costs 8; 7 remain and XP stays 35. |
| 1:40–2:00 | Items → Window plant → Save in Window (Next selects Door). Home → reload. Show the Pal, plant, inventory and remaining balance persist. |

With an existing save, repeated discoveries/quests do not pay again and an owned
item cannot be bought twice. Use a fresh rehearsal save for the exact arithmetic.
Do not claim a quest completed just to advance the demo; actually do its action.

## Pre-demo checklist

- Start the intended save/server; keep its terminal running and laptop awake.
- Check `/api/status`: `ai_ready: true` means configured, not a guarantee of quota,
  network availability or model correctness. Never display the key or credential file.
- Rehearse the prepared image and controls: arrows turn, Enter/Space select,
  Escape returns; touch or click once to activate in the responsive browser. Compact mode uses
  focus-then-activate.
- Use the normal page on laptop/phone portrait. Selected choices are terracotta with visible keyboard focus
  (compact mode also has a pointer). Room art preserves its proportions with nearest-neighbour scaling.
- Check the saved photo and menu are locally available; prepare the internet fallback.
- Close the design gallery before live play. Gallery labels identify sample data.

## Failure fallback

Camera denied, unavailable or insecure: use Upload to select the prepared local
photo. Upload does not force the camera. Browser camera access requires permission
and a secure context: normally HTTPS, or localhost on the same device. Plain HTTP
to a laptop LAN IP is not the phone's localhost. See
[MDN getUserMedia security](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia#privacy_and_security).

AI/internet failure: show the honest error. Use Status to check a possibly saved
request, then Retry when connectivity returns. No timeout, capture or failure
awards anything. You can leave a pending request with Back; Home retains Status.
Confirmed late results refresh the balance without forcing navigation. Requests
time out after 60 seconds; allow extra time rather than promise instant AI.

If internet stays down, show already-earned CultureDex entries, honesty quests,
shop and room state on the local server. Say these are **previously saved results**.
Alternatively open “Review all screen designs” and say **design preview / sample
data, not live recognition**. The gallery cannot save rewards or purchases.
No prepared offline AI example or offline recognition has been added.

## Optional phone on the same trusted network

The inspected laptop address on 11 October 2026 was `172.20.10.3` (interface en0).
It can change when switching Wi-Fi/hotspots. Verify with `ipconfig getifaddr en0`.
The running port 8000 preview is loopback-only. For an isolated phone rehearsal:

```bash
SGPAL_DATA_DIR=./data/phone-rehearsal-01 .venv/bin/python -m uvicorn sgpal.server:app --host 172.20.10.3 --port 8001
```

Then open http://172.20.10.3:8001/ on the phone and laptop to share that rehearsal.
Stop any existing port 8001 rehearsal first. Use the phone's Upload action on this
HTTP address. A phone's `127.0.0.1` points to the phone, not this laptop.
Both devices must be on the same trusted network; allow Python through the local
firewall if prompted. Guest Wi-Fi/client isolation may block access. No physical
phone reachability was verified here. Stop the listener with Ctrl+C afterward.

Bind only the trusted LAN address. Do not port-forward, tunnel publicly or expose
this single-user server to the internet: visitors share access to its progress
and photos. No firewall changes, public hosting or Pi configuration were made.

## Validation for this stage

- 62 backend tests: reward/purchase idempotency, concurrency, insufficient funds,
  atomic rollback, ownership, migration, failure handling and persistence.
- Both Chrome browser suites: full journey with injected, visibly labelled test
  AI and temporary saves; correction, Not yet/Yes, lost responses, retry/reload,
  late purchase result after Back, inventory, replacement and touch placement.
- Camera permission denial, missing camera, unsupported upload, and capture from
  a synthetic browser stream. These are not physical camera tests.
- Three pet species, suggested names, keyboard/shared rotary actions, touch
  onboarding, Back navigation, 57 gallery states and sample isolation.
- Responsive phone/tablet/laptop viewports, including portrait and landscape;
  room proportions, canvas bounds, safe scrolling and text audit. This is browser emulation,
  not testing on a physical phone or Safari.
- No new live OpenAI call or physical Pi test. Actual photo recognition quality,
  internet latency, physical-phone camera/file picker and LAN reachability still
  need a rehearsal on the presentation devices.
