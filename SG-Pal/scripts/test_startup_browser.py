"""Exercise temporary deployment failures against a real, isolated server."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sgpal-startup-') as folder:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'sgpal.server:app', '--host', '127.0.0.1', '--port', str(port)],
        cwd=ROOT, env={**os.environ, 'SGPAL_DATA_DIR': folder, 'SGPAL_PUBLIC_URL': url},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                urlopen(url + '/healthz', timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Test server did not start')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=os.getenv('SGPAL_BROWSER_CHANNEL', 'chrome'), headless=True)
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # Each dependency fails once, like a page opened during a disk-backed deploy.
            paths = ['/friends.js', '/accounts.js', '/browser.js', '/app.js', '/assets/room.png', '/api/state']
            attempts = dict.fromkeys(paths, 0)
            def temporary(route):
                path = route.request.url.removeprefix(url)
                if path in attempts:
                    attempts[path] += 1
                    if attempts[path] == 1:
                        route.fulfill(status=502, body='Deploying')
                        return
                route.continue_()
            page.route('**/*', temporary)
            page.goto(url)
            page.get_by_role('button', name='Play now', exact=True).wait_for(timeout=30000)
            assert all(count >= 2 for count in attempts.values()), attempts
            page.get_by_role('button', name='Play now', exact=True).click()
            page.get_by_role('button', name='otter', exact=True).click()
            page.get_by_role('button', name='Choose', exact=True).click()
            page.get_by_role('button', name='Keep', exact=True).click()
            page.wait_for_function("SGPal.inspect().current === '04'")
            saved = page.evaluate('SGPal.inspect().saved')
            page.reload()
            page.wait_for_function("window.SGPal?.inspect().current === '04'")
            assert page.evaluate('SGPal.inspect().saved') == saved
            assert not errors, errors
            page.close()
            for query in ('', '?kiosk=1'):
                page = browser.new_page(viewport={'width': 320, 'height': 240} if query else {'width': 1280, 'height': 720})
                count = [0]
                def unavailable(route):
                    count[0] += 1
                    route.fulfill(status=502, body='Unavailable')
                page.route('**/assets/room.png', unavailable)
                page.goto(url + '/' + query)
                # Compact mode has its own visible retry beside the canvas.
                visible_button = page.locator('#mode button' if query else '#game-actions button')
                visible_button.wait_for(state='visible', timeout=20000)
                assert count[0] == 4, count
                if query:
                    box = visible_button.bounding_box()
                    assert box and 0 <= box['y'] < 240
                page.unroute('**/assets/room.png', unavailable)
                visible_button.click()
                page.wait_for_function('window.SGPal?.inspect().ready && SGPal.inspect().choices.length > 0')
                page.close()
            browser.close()
        print('PASS: transient script/artwork/API 502 recovery, adoption/reload persistence, bounded permanent failure and manual retry in desktop + compact mode.')
    finally:
        proc.terminate()
        proc.wait(timeout=10)
