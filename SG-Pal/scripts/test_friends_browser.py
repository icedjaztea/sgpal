"""Focused two-account friends flow, MOCK email, real sessions and social database."""
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sgpal-game-test-') as temp:
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','scripts.gameplay_fixture:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'SGPAL_DATA_DIR':temp,'SGPAL_BROWSER_FIXTURE':'1','SGPAL_AUTH_FIXTURE':'1'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:urlopen(url+'/api/status',timeout=1);break
            except OSError:time.sleep(.1)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            a=browser.new_context(viewport={'width':1366,'height':900});b=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            p=a.new_page();q=b.new_page();errors=[]
            for page in (p,q):page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url);page.wait_for_function('window.SGPal && SGPal.inspect().current==="01"')
            def choose(page,label):page.locator('#game-actions').get_by_role('button',name=label,exact=True).click()
            for label in ['Start','otter','Choose','Keep']:choose(p,label)
            p.wait_for_function('SGPal.inspect().saved.adopted')
            owner=p.evaluate('SGPal.inspect().saved.owner_id')
            def login(page,email,conflict=False):
                # Only test fixture clock reset, never a production endpoint.
                import sqlite3
                with sqlite3.connect(Path(temp)/'accounts.sqlite3') as db:db.execute('DELETE FROM limits')
                page.locator('#settings-open').click();page.locator('#account-open').click();page.locator('#login-email').fill(email)
                page.locator('#account-email-form button').click()

                try:page.wait_for_function('document.querySelector("#account-message").textContent.includes("Request accepted")',timeout=10000)
                except Exception:print('Email UI:',page.locator('#account-message').inner_text());raise
                token=hashlib.sha256(email.encode()).hexdigest()
                page.goto(url+'/#token_hash='+token+'&type=email')
                if email=='alice@example.test' and not conflict:
                    page.goto(url+'/#token_hash='+('x'*64)+'&type=email')
                    page.locator('#confirm-email-link').click()
                    page.locator('#account-email-form').wait_for(state='visible')
                    assert not page.evaluate('SGPalAccount.session.signed_in')
                    page.goto(url+'/#token_hash='+token+'&type=email')
                page.locator('#confirm-email-link').click()
                if conflict:page.locator('#use-account').wait_for(state='visible')
                else:page.wait_for_function('window.SGPalAccount?.session?.signed_in===true')
            login(p,'alice@example.test')
            for label in ['Start','mynah','Choose','Keep']:choose(q,label)
            q.wait_for_function('SGPal.inspect().saved.adopted')
            login(q,'bob@example.test')
            p.locator('#game-nav [data-destination="16"]').click();q.locator('#game-nav [data-destination="16"]').click()
            p.locator('#friend-code-input').wait_for();q.locator('#friend-code-input').wait_for()
            bc=q.locator('#friends-content code').first.inner_text()
            own=p.evaluate('SGPal.inspect().saved')
            denied=p.evaluate("async code=>(await fetch('/api/friends/'+code+'/room')).status",bc)
            assert denied==403
            p.locator('#friend-code-input').fill(bc)
            p.locator('#friends-content').get_by_role('button',name='Send request').click()
            p.wait_for_function("document.querySelector('#friends-message').textContent==='Friend request sent.'")
            q.locator('#friends-content').get_by_role('button',name='Refresh',exact=True).click()
            q.locator('#friends-content').get_by_role('button',name='Accept',exact=True).click()
            q.wait_for_function("document.querySelector('#friends-message').textContent==='Friend request accepted.'")
            p.locator('#friends-content').get_by_role('button',name='Refresh',exact=True).click()
            p.locator('#friends-content').get_by_role('button',name='Visit room').click()
            p.locator('#visit-banner').wait_for(state='visible')
            p.screenshot(path=str(OUT/'friends-desktop.png'))
            assert p.evaluate('SGPal.inspect().saved')==own
            p.locator('#return-home').click()
            p.wait_for_function("SGPal.inspect().current==='04'")
            q.locator('#friends-content').get_by_role('button',name='Visit room').click()
            q.locator('#visit-banner').wait_for(state='visible')
            q.screenshot(path=str(OUT/'friends-phone.png'))
            assert q.evaluate('document.documentElement.scrollWidth<=innerWidth')
            p.locator('#game-nav [data-destination="16"]').click()
            p.locator('#friends-content').get_by_role('button',name='Remove friend').click()
            p.wait_for_function("document.querySelector('#friends-message').textContent.includes('revoked')")
            assert p.evaluate("async code=>(await fetch('/api/friends/'+code+'/room')).status",bc)==403
            assert not errors,errors
            browser.close()
            print('PASS: request, accept, saved-room visit, return, remove, denied non-friend/revoked access; desktop 1366x900 and phone 390x844. Mock email, no physical phone.')
    finally:proc.terminate();proc.wait(timeout=10)
