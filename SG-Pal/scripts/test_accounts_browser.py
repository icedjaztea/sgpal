"""Browser account transitions against real storage, MOCK email/AI, isolated temp saves."""
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
            assert p.evaluate('SGPal.inspect().saved.owner_id')==owner
            login(q,'alice@example.test',True)
            q.screenshot(path=str(OUT/'accounts-phone.png'))
            q.locator('#use-guest').click();q.wait_for_function('window.SGPalAccount?.session?.conflict===false')
            assert not q.evaluate('SGPalAccount.session.signed_in')
            login(q,'alice@example.test',True);q.locator('#use-account').click()
            q.wait_for_function('window.SGPal?.inspect().saved.adopted===true')
            assert q.evaluate('SGPal.inspect().saved.owner_id')==owner
            q.reload();q.wait_for_function('window.SGPal?.inspect().saved.adopted===true')
            p.locator('#settings-open').click();p.locator('#account-open').click();p.screenshot(path=str(OUT/'accounts-desktop.png'))
            q.locator('#settings-open').click();q.locator('#account-open').click();q.locator('#sign-out').click()
            q.wait_for_function('window.SGPal?.inspect().current==="01"')
            assert not q.evaluate('SGPalAccount.session.signed_in')
            assert p.evaluate('SGPalAccount.session.signed_in')
            login(q,'bob@example.test')
            assert q.evaluate('SGPalAccount.session.owner_id')!=owner
            assert not q.evaluate('SGPal.inspect().saved.adopted')
            assert q.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
            browser.close()
            print('PASS: two browser contexts, two users, new-account guest migration, existing-account choices, cross-session reload, sign-out isolation, phone modal. Email/AI mocked; no physical phone test.')
    finally:proc.terminate();proc.wait(timeout=10)
