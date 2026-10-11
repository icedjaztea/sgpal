#!/bin/bash
# Double-click on macOS, or run with bash from any working directory.
cd "$(dirname "$0")" || exit 1
export SGPAL_DATA_DIR="${SGPAL_DATA_DIR:-$PWD/data/browser}"
PYTHON="$PWD/.venv/bin/python"
if [ ! -x "$PYTHON" ] || ! "$PYTHON" -c 'import fastapi, uvicorn' 2>/dev/null; then
  echo 'First run these commands in this folder:'
  echo 'python3 -m venv .venv'
  echo '.venv/bin/python -m pip install -r requirements-web.txt'
  read -r -p 'Press Enter to close.'
  exit 1
fi

echo 'SG Pal: http://127.0.0.1:8000/'
echo '320 x 240 kiosk: http://127.0.0.1:8000/?kiosk=1'

# Reuse an already running SG Pal server; never stop another process.
if "$PYTHON" - <<'PY'
import json
from urllib.request import urlopen
try:
    with urlopen('http://127.0.0.1:8000/api/status', timeout=2) as response:
        assert json.load(response).get('mode') == 'local-browser'
except Exception:
    raise SystemExit(1)
PY
then
  if [ "$(uname)" = Darwin ]; then open 'http://127.0.0.1:8000/?kiosk=1'; fi
  exit 0
fi

echo 'Keep this Terminal window open while playing. Ctrl+C stops the server.'
"$PYTHON" -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
result=$?
if [ "$result" -ne 0 ]; then read -r -p 'Server could not start. Read the error above, then press Enter.'; fi
exit "$result"
