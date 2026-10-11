"""Browser acceptance test. Uses temporary saves; never touches player progress.
Run: .venv/bin/python scripts/test_browser.py (installed Chrome), or set
SGPAL_BROWSER_CHANNEL=chromium after `python -m playwright install chromium`.
"""
import json
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
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)


def inspect(page):
    return page.evaluate('SGPal.inspect()')


def choose(page, label):
    state = inspect(page)
    assert label in state['choices'], (label, state)
    for _ in range(len(state['choices'])):
        state = inspect(page)
        if state['choices'][state['focus']] == label:
            page.evaluate("window.dispatchEvent(new Event('sgpal:press'))")
            return
        page.evaluate("window.dispatchEvent(new CustomEvent('sgpal:rotate',{detail:{delta:1}}))")
    raise AssertionError(label)


def screen(page, current):
    page.wait_for_function('(s)=>SGPal.inspect().current===s', arg=current)


def boot(page, url):
    page.goto(url)
    page.wait_for_function('window.SGPal?.inspect().ready')
    screen(page, '01')


def tap(page, x, y):
    box = page.locator('#screen').bounding_box()
    page.touchscreen.tap(box['x'] + x * box['width'] / 320, box['y'] + y * box['height'] / 240)


with tempfile.TemporaryDirectory(prefix='sgpal-browser-') as folder:
    data = Path(folder)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'sgpal.server:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env={**os.environ, 'SGPAL_DATA_DIR': folder, 'OPENAI_API_KEY': '', 'SGPAL_KEY_FILE': str(data / 'absent-credential.json')}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(url + '/api/status', timeout=1) as response:
                    assert response.status == 200
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Test server did not start')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=os.environ.get('SGPAL_BROWSER_CHANNEL', 'chrome'), headless=True)
            errors = []
            for species, name in [('merlion', 'Splash'), ('otter', 'Pebble'), ('mynah', 'Chirpy')]:
                context = browser.new_context(viewport={'width': 1100, 'height': 1100})
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                boot(page, url)
                choose(page, 'Start'); choose(page, species)
                choose(page, 'Back')
                assert inspect(page)['choices'][inspect(page)['focus']] == species
                choose(page, species); choose(page, 'Choose'); choose(page, 'Reroll')
                assert not (data / 'profile.json').exists()
                choose(page, 'Keep'); screen(page, '04')
                assert inspect(page)['saved']['name'] == name
                page.reload(); screen(page, '04')
                assert inspect(page)['saved']['species'] == species
                if species == 'otter':
                    page.screenshot(path=str(OUT / 'desktop.png'))
                    before = (data / 'profile.json').read_bytes()
                    ids = page.evaluate("SGPal.manifest().filter(s=>!s.id.startsWith('live-')).map(s=>s.id)")
                    for ident in ids:
                        page.evaluate('(id)=>SGPal.preview(id)', ident)
                        assert inspect(page)['gallery'] is True
                    assert page.evaluate('SGPal.audit()') == [], page.evaluate('SGPal.audit()')
                    page.evaluate("SGPal.preview('18')")
                    choose(page, 'SOUND: OFF')
                    for ident, label in [('03', 'Keep'), ('06check', 'Yes'), ('10pass', 'Done'), ('11confirm', 'Confirm'), ('13confirm', 'Save'), ('16request', 'Accept')]:
                        page.evaluate('(id)=>SGPal.preview(id)', ident); choose(page, label)
                    assert (data / 'profile.json').read_bytes() == before
                    assert not (data / 'progress.json').exists()
                    page.evaluate('SGPal.live()'); screen(page, '04')
                    # Shared keyboard adapter: focus canvas, arrow moves, Enter activates, Escape returns.
                    page.locator('#screen').focus(); page.keyboard.press('ArrowRight'); page.keyboard.press('Enter'); screen(page, '05')
                    page.keyboard.press('Escape'); screen(page, '04')
                    # Every live menu destination and explicit Back.
                    for label in ['CultureDex', 'Quests', 'Shop', 'Inventory', 'Decorate', 'Profile', 'Rooms', 'Friends', 'Settings']:
                        page.evaluate('SGPal.live()'); choose(page, 'Menu')
                        for _ in range(3):
                            if label in inspect(page)['choices']: break
                            choose(page, 'Next')
                        choose(page, label)
                        assert 'Back' in inspect(page)['choices']
                        choose(page, 'Back'); screen(page, '04menu')
                    page.evaluate('SGPal.live()'); choose(page, 'Scan')
                    page.evaluate("()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(Object.assign(new Error('denied'),{name:'NotAllowedError'}))}")
                    choose(page, 'Camera'); screen(page, '05error'); choose(page, 'Back')
                    page.locator('#photo').set_input_files(str(ROOT / 'sgpal/web/assets/otter.png'))
                    screen(page, '05photo'); choose(page, 'Analyse'); screen(page, 'live-request-error')
                    assert inspect(page)['saved']['xp'] == 0
                    assert inspect(page)['saved']['coins'] == 0
                    choose(page, 'Back'); screen(page, '04')
                    # Server error must never silently change save storage.
                    page.route('**/api/state', lambda route: route.abort())
                    page.reload(); screen(page, 'saveerror')
                    assert inspect(page)['backend'] is True
                    assert page.evaluate("localStorage.getItem('sgpal-ui-v1')") is None
                    page.unroute('**/api/state'); choose(page, 'Retry'); screen(page, '04')
                    # Simulate a lost adoption response on a fresh profile; recover committed save.
                    (data / 'profile.json').unlink()
                    page.reload(); screen(page, '01'); choose(page, 'Start'); choose(page, 'otter'); choose(page, 'Choose')
                    def lose_response(route):
                        route.fetch()
                        route.abort()
                    page.route('**/api/adopt', lose_response)
                    choose(page, 'Keep'); screen(page, '04')
                    assert inspect(page)['saved']['name'] == 'Kaya'
                context.close()
                (data / 'profile.json').unlink()
            # Touch-only onboarding and menu paging at phone dimensions.
            context = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, device_scale_factor=3)
            page = context.new_page(); page.on('pageerror', lambda e: errors.append(str(e)))
            boot(page, url)
            tap(page, 60, 208); screen(page, '02')
            tap(page, 264, 80); tap(page, 264, 80); screen(page, '02confirm')
            tap(page, 80, 208); screen(page, '03')
            tap(page, 160, 208); tap(page, 160, 208)
            tap(page, 60, 208); tap(page, 60, 208); screen(page, '04')
            assert inspect(page)['saved']['name'] == 'Chirpy'
            page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
            tap(page, 260, 208); tap(page, 260, 208); screen(page, '04menu')
            for _ in range(2):
                tap(page, 160, 208); tap(page, 160, 208)
            assert 'Settings' in inspect(page)['choices']
            tap(page, 160, 50); screen(page, '18')
            tap(page, 160, 84); tap(page, 160, 84)
            page.wait_for_function('SGPal.inspect().saved.sound===true')
            page.reload(); screen(page, '04')
            assert inspect(page)['saved']['sound'] is True
            for width in [320, 360, 375, 390, 768, 1100]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                bounds=page.locator('#screen').bounding_box()
                assert bounds['width'] % 320 == 0 and bounds['height'] % 240 == 0
            page.goto(url+'/?kiosk=1'); screen(page, '04')
            bounds=page.locator('#screen').bounding_box()
            assert bounds['width']==320 and bounds['height']==240 and bounds['x']==0 and bounds['y']==0
            page.screenshot(path=str(OUT/'kiosk.png'))
            context.close()
            # Read existing real catalogue/progress, with an unrelated isolated demo save.
            (data/'progress.json').write_text(json.dumps({'xp':85,'log':{'chope':{'time':1791684000,'hash':'old'},'kopi':{'time':1791685000,'hash':'other'}},'completed':['chope'],'active':'kopi'}))
            (data/'demo-progress.json').write_text(json.dumps({'xp':999,'log':{},'completed':[],'active':None}))
            before=(data/'progress.json').read_bytes()
            page=browser.new_page();page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(url); screen(page,'04'); assert inspect(page)['saved']['xp']==85
            choose(page,'Menu'); choose(page,'CultureDex'); choose(page,'#001 CHOPE CULTURE'); screen(page,'live-story')
            choose(page,'Info'); screen(page,'live-info'); choose(page,'Quest'); screen(page,'live-quest')
            choose(page,'Back'); screen(page,'09'); choose(page,'ACTIVE: Kopi time'); screen(page,'live-quest')
            assert page.evaluate('SGPal.audit()')==[]
            assert (data/'progress.json').read_bytes()==before
            assert not errors, errors
            browser.close()
            print(f'PASS: 3 species, rotary/keyboard/touch onboarding, reload, 9 menu destinations, {len(ids)} gallery states, photo/error handling, save reconciliation, mobile widths 320–1100, kiosk 320x240, legacy progress and sample isolation. No JS errors.')
    finally:
        proc.terminate(); proc.wait(timeout=10)
