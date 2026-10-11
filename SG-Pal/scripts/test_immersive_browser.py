"""Focused presentation acceptance. Mock email/AI, real sessions and saves; no Pi."""
import hashlib
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)

def screen(p,name):p.wait_for_function('(n)=>window.SGPal?.inspect().current===n && SGPal.inspect().choices.length>0',arg=name)
def key(p,label):
    for _ in range(30):
        if p.evaluate('document.activeElement?.textContent.trim()')==label:
            p.keyboard.press('Enter');return
        p.keyboard.press('ArrowRight')
    raise AssertionError('Keyboard cannot reach '+label)

with tempfile.TemporaryDirectory(prefix='sgpal-game-test-') as temp:
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}';photo=Path(temp)/'kopi.png';Image.new('RGB',(300,200),'orange').save(photo)
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','scripts.gameplay_fixture:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'SGPAL_DATA_DIR':temp,'SGPAL_BROWSER_FIXTURE':'1','SGPAL_AUTH_FIXTURE':'1'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:urlopen(url+'/api/status',timeout=1);break
            except OSError:time.sleep(.1)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            a=browser.new_context(viewport={'width':1366,'height':900});b=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            p=a.new_page();q=b.new_page();errors=[]
            for page,species in [(p,'otter'),(q,'mynah')]:
                page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url);screen(page,'01')
                for label in ['Start',species,'Choose','Keep']:key(page,label)
                screen(page,'04')
            # Mouse-free home -> feature -> action -> Back; camera denial is emulated.
            p.evaluate("()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(Object.assign(new Error('denied'),{name:'NotAllowedError'}))}")
            p.keyboard.press('ArrowRight');p.keyboard.press('Enter');screen(p,'05')
            key(p,'Camera');screen(p,'05error');p.keyboard.press('Escape');screen(p,'05');p.keyboard.press('Escape');screen(p,'04')
            assert p.locator('#game-nav [data-destination="05"]').evaluate('(n)=>n===document.activeElement')
            p.keyboard.press('Enter');screen(p,'05');p.locator('#photo').set_input_files(photo);screen(p,'05photo')
            key(p,'Analyse');screen(p,'live-candidate')
            def lose_confirmation(route):route.fetch();route.abort()
            p.route('**/api/confirm',lose_confirmation);key(p,'Yes');screen(p,'live-request-error')
            p.unroute('**/api/confirm');key(p,'Back');screen(p,'04')
            p.locator('#settings-open').click();p.locator('#request-status').click();screen(p,'live-reward')
            p.locator('#panel-close').click();screen(p,'04');p.reload();screen(p,'04')
            assert p.evaluate('SGPal.inspect().saved.coins')==5
            for page,file in [(p,'immersive-desktop.png'),(q,'immersive-phone.png')]:
                page.screenshot(path=str(OUT/file))
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight')
                assert not page.locator('#game-panel').is_visible()
                bounds=page.locator('#room-art').bounding_box();assert abs(bounds['width']/bounds['height']-320/168)<.01
            q.locator('#game-nav [data-destination="11"]').click();screen(q,'11')
            q.screenshot(path=str(OUT/'immersive-phone-window.png'));q.locator('#panel-close').click();screen(q,'04')
            # Existing mocked email fixture only; no production auth bypass.
            def login(page,email):
                with sqlite3.connect(Path(temp)/'accounts.sqlite3') as db:db.execute('DELETE FROM limits')
                page.locator('#settings-open').click();page.locator('#account-open').click()
                page.locator('#login-email').fill(email)
                page.keyboard.press('ArrowLeft');assert page.locator('#login-email').evaluate('(n)=>n===document.activeElement') # input keeps native editing
                page.locator('#account-email-form button').click()
                page.wait_for_function("document.querySelector('#account-message').textContent.includes('Request accepted')")
                page.goto(url+'/#token_hash='+hashlib.sha256(email.encode()).hexdigest())
                page.locator('#confirm-email-link').click();page.wait_for_function('window.SGPalAccount?.session?.signed_in===true');screen(page,'04')
            login(p,'alice@example.test');login(q,'bob@example.test')
            for page in (p,q):page.locator('#game-nav [data-destination="16"]').click();page.locator('#friend-code-input').wait_for()
            code=q.locator('#friends-content code').first.inner_text()
            p.locator('#friend-code-input').fill(code);p.locator('#friends-content').get_by_role('button',name='Send request').click()
            p.wait_for_function("document.querySelector('#friends-message').textContent==='Friend request sent.'")
            q.locator('#friends-content').get_by_role('button',name='Refresh',exact=True).click();q.locator('#friends-content').get_by_role('button',name='Accept',exact=True).click()
            q.wait_for_function("document.querySelector('#friends-message').textContent==='Friend request accepted.'")
            p.locator('#friends-content').get_by_role('button',name='Refresh',exact=True).click();p.locator('#friends-content').get_by_role('button',name='Visit room').click()
            p.locator('#visit-banner').wait_for(state='visible');assert not p.locator('#friends-dialog').is_visible()
            assert 'Pip' in p.locator('#visit-label').inner_text()
            p.screenshot(path=str(OUT/'immersive-visit.png'))
            p.keyboard.press('Escape');assert not p.locator('#visit-banner').is_visible()
            assert p.evaluate('SGPal.inspect().saved.coins')==5
            p.goto(url+'/?kiosk=1');screen(p,'04');bounds=p.locator('#screen').bounding_box();assert bounds['width']==320 and bounds['height']==240
            p.locator('#screen').focus();p.keyboard.press('ArrowRight');p.keyboard.press('Enter');screen(p,'05');p.keyboard.press('Escape');screen(p,'04')
            assert not errors,errors
            browser.close();print('PASS: keyboard onboarding/navigation/Back/focus, saved discovery/reload and lost-response recovery (mock AI), desktop + phone scenes, real saved-room visit with mocked email auth, compact rendering/navigation. No physical devices tested.')
    finally:proc.terminate();proc.wait(timeout=10)
