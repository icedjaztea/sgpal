# SG Pal - Kopi Sunset UI prototype

A runnable 320 x 240 screen-design prototype for the Raspberry Pi kiosk, laptop browser and phone browser. This is a portable integration candidate for your existing shared repository, not a replacement repository or the completed game.

## What works

- Choose Merlion, Otter or Mynah, cycle a suggested name, and persist adoption.
- Shared rotary focus logic, keyboard controls, touch selection and on-screen knob simulator.
- Native 320 x 240 Canvas renderer with integer enlargement, bitmap text and generated art assets.
- Home and menu navigation, local profile display and sound preference.
- Browser camera permission/capture and photo-file selection. Frames stay in memory; nothing is sent to AI.
- Design gallery covering all 18 planned screens, plus confirmation, empty, locked, duplicate, error and connection states. Sample data is isolated from your save.
- FastAPI serves the UI and atomically writes a single local device save. Standalone static preview uses browser localStorage.

## What is deliberately not implemented yet

AI recognition, evidence verification, reward grants, commerce, furniture persistence, GPIO input, the Pi camera adapter, authenticated cloud sync, accounts, friend requests and visits. Those controls show an explicit unconnected state. No simulated scan or timer awards XP or coins. No API key is needed for this UI-only version.

The images are approved concept assets sampled inside exact-resolution UI layouts. They are not a hand-cleaned sprite atlas. Animations described in the design specification are targets; the current Pal sprite is static. Test final legibility on the physical 2.8-inch display.

## Run on Mac, Linux or Raspberry Pi

Use Python 3.10 or newer. From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000 in your browser. The tests were run on Linux with Python3.12; the actual Pi and iPhone have not been tested here. Exact tested package versions are listed in `requirements-tested.txt`; `requirements.txt` keeps compatible ranges for installation on the Pi.

Windows activation, if needed: `.venv\Scripts\activate`.

### Phone or laptop visiting the Pi

On a trusted local network, run:

```bash
python -m uvicorn sgpal.server:app --host 0.0.0.0 --port 8000
```

Visit `http://<PI-IP>:8000` from the other device. Substitute the Pi's actual IP. This is one shared local-device save for everyone visiting that server; it is not user accounts or cloud sync. Do not expose this unauthenticated prototype to the public internet.

Live browser camera capture requires a secure context (normally HTTPS, or localhost on the same device). A phone opening the Pi's ordinary HTTP LAN URL may need **Upload** instead. Use HTTPS for the deployed browser version. A CSI Pi Camera must use a separate local camera adapter; the browser Camera button does not promise CSI support.

Reference: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

### Pi display

Once the display and Chromium are already working, open:

```text
http://localhost:8000/?kiosk=1
```

This removes the surrounding browser-preview controls and renders exactly320x240 CSS pixels. A typical launch command is:

```bash
chromium --kiosk 'http://localhost:8000/?kiosk=1'
```

Some OS images use `chromium-browser` instead. Display drivers, orientation, browser scaling, kiosk autostart and GPIO pin mapping depend on the actual hardware/OS and are not configured by this package.

### Without FastAPI (visual preview only)

```bash
python3 -m http.server 8000 --directory sgpal/web
```

Then open http://localhost:8000. This mode saves in that browser only. Do not open index.html directly as a file. The project currently has no service worker; initial loading still needs the local server. Internet is unnecessary for artwork/fonts after serving locally.

## Controls

- Encoder contract: `window.dispatchEvent(new CustomEvent('sgpal:rotate', {detail:{delta:1}}))` for clockwise, `delta:-1` for counterclockwise; `window.dispatchEvent(new Event('sgpal:press'))` for click. A Pi bridge must emit these in the kiosk browser, debounced once per detent/click.
- Keyboard: arrows to rotate, Enter/Space to select, Escape to Back. Focus the game canvas first if a browser form control has focus.
- Touch/mouse: first tap focuses; tap the same choice again to activate. External Turn/Press buttons offer direct rotary simulation.
- Menus expose Back. Home is the root and provides Settings via Menu.

## Save locations

FastAPI writes to `~/.local/share/sgpal/save.json`, or `SGPAL_DATA_DIR/save.json` if that environment variable is set. Updates use a temporary file and atomic replace. Use one server worker for this prototype. A corrupt save is preserved and reported, not deleted or overwritten.

Static preview uses localStorage key `sgpal-ui-v1`. Clearing site storage loses that browser-only save. There is no import/merge with the server save yet.

## Review screens

Expand **Review all screen designs** beneath the device. The visible DESIGN PREVIEW label means sample data. Return to my Pal exits without changing saved progress. Native PNGs and enlarged3x exports accompany this source package, along with per-screen interaction specifications.

## Integrating into the shared GitHub repo

1. Inspect that repo's README, AGENTS.md, existing backend/frontend and tests first.
2. Work on a feature branch. Do not overwrite existing scanning, culture data or persistence.
3. Map the shared renderer/components and input contract to the current routes and data model.
4. Replace the UI-only save adapter with the repo's persistence. Add migrations rather than resetting saves.
5. Integrate real scan/verification operations and their pending/error states. Only committed server operations grant rewards.
6. Validate Pi display and rotary input, then laptop Chrome and actual iPhone Safari.

No GitHub repository was opened or modified in producing this handoff; its URL was not yet provided.

## Tests

```bash
python -m pip install pytest httpx
python -m pytest tests
```

Backend tests cover adoption persistence, invalid species, repeat-adoption protection, corrupt-save preservation and unconnected AI endpoints granting no rewards. Browser QA covers all screen renders, navigation, native canvas dimensions, design/live separation and reload persistence.
