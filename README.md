# SG Pal · Kopi Sunset

One repository for Raspberry Pi, laptop and phone. The shared game is in
`SG-Pal/`: FastAPI serves the approved native 320 × 240 HTML/CSS/JavaScript UI.
The existing native Pi application and hardware configuration are retained.

## Run from this repository root

```bash
cd SG-Pal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-web.txt
SGPAL_DATA_DIR=./data/browser python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ or http://127.0.0.1:8000/?kiosk=1.
Keep the terminal open. Reuse the environment on subsequent starts.
For a trusted LAN, bind `--host 0.0.0.0` and open the host's LAN address on a phone.
Every visitor shares that server's save. Phone capture generally needs HTTPS;
Upload works on ordinary LAN HTTP. This is not an authenticated public service.

Reuse an existing OpenAI key with `python configure_key.py` at its hidden Terminal
prompt. Credentials remain outside the repository. Never paste secrets into chat,
frontend code or Git. The model is configured in `SG-Pal/config.json`.

Working: three-Pal adoption, suggested names, BTO, shared controls, persisted
reload, real recognition/correction, confirmed CultureDex discoveries with saved
photos and Singapore timestamps, separate XP/coins and exactly-once rewards.
Quests now use the requested “Yes, I did it” / “Not yet” choice, explicitly player-reported.
The labelled design gallery is isolated from actual progress. Auth, friends and
shop spending remain deferred. Raw SPI/GPIO/CSI integration with the new renderer
and physical Pi/iPhone validation remain pending.

## Validate

From `SG-Pal/` with the environment activated:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python scripts/test_browser.py
python scripts/test_gameplay_browser.py
```

Browser scripts use installed Chrome, temporary servers and saves; model results
are injected only in a labelled test fixture. To use Playwright Chromium instead,
install it with `python -m playwright install chromium` and set
`SGPAL_BROWSER_CHANNEL=chromium`. Automated tests never spend API credits.

See [integration and migration notes](SG-Pal/KOPI_SUNSET.md),
[application setup and original hardware instructions](SG-Pal/README.md), and the
[approved handoff](_handoff/sgpal-kopi-sunset-ui/CODEX_HANDOFF.md).
Schema upgrades preserve existing progress; back up the data directory with the
server stopped before moving it between devices. Do not run old and new game
runtimes against a migrated save simultaneously.
