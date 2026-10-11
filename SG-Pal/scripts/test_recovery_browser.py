"""Focused real recovery flow, no email/AI mocks or external calls. Temporary saves."""
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

def screen(p,n):p.wait_for_function('(n)=>window.SGPal?.inspect().current===n',arg=n)
def adopt(p,name='Kaya'):
    screen(p,'01');p.get_by_role('button',name='Play now',exact=True).click();screen(p,'02')
    p.locator('#game-actions').get_by_role('button',name='otter',exact=True).click()
    p.locator('#game-actions').get_by_role('button',name='Choose',exact=True).click()
    screen(p,'03');p.locator('#game-actions').get_by_role('button',name='Keep',exact=True).click();screen(p,'04')
def account(p):
    p.locator('#settings-open').click();p.locator('#account-open').click()
    p.wait_for_function("document.querySelector('#account-message').textContent!=='Working…'")
def save(p):
    p.locator('#save-pal').click();p.locator('#recovery-issued').wait_for(state='visible')
    code=p.locator('#recovery-code').inner_text();assert len(code)==68
    p.keyboard.press('Escape');assert p.locator('#recovery-issued').is_visible()
    p.locator('#recovery-kept').click();p.wait_for_function('SGPalAccount.session.recovery_enabled')
    return code
def restore(p,code):
    p.locator('#restore-open').click();p.locator('#recovery-input').fill(code)
    p.locator('#restore-form button[type=submit]').click();p.wait_for_function('SGPalAccount.session.signed_in');screen(p,'04')
def api(p,path,body=None):
    return p.evaluate('''async ({path,body})=>{const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json',...SGPalAccount.headers()},body:body?JSON.stringify(body):undefined});return {status:r.status,data:await r.json()}}''',{'path':path,'body':body})

with tempfile.TemporaryDirectory(prefix='sgpal-recovery-test-') as temp:
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    env={**os.environ,'SGPAL_DATA_DIR':temp,'SGPAL_PUBLIC_URL':url}
    for key in ('SUPABASE_URL','SUPABASE_PUBLISHABLE_KEY'):env.pop(key,None)
    def start():
        proc=subprocess.Popen([sys.executable,'-m','uvicorn','sgpal.server:app','--host','127.0.0.1','--port',str(port),'--workers','1','--no-proxy-headers'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:urlopen(url+'/healthz',timeout=1);return proc
            except OSError:time.sleep(.1)
        proc.terminate();raise AssertionError('Server did not start')
    proc=start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            a=browser.new_context();b=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            p=a.new_page();q=b.new_page();errors=[]
            for page in (p,q):page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url)
            adopt(p);before=api(p,'/api/state')['data'];account(p);code=save(p)
            assert api(p,'/api/state')['data']==before
            account(q);q.locator('#restore-open').click();q.locator('#recovery-input').fill('invalid');q.locator('#restore-form button[type=submit]').click()
            q.wait_for_function("document.querySelector('#account-message').textContent.includes('not recognised')")
            restore(q,code);assert api(q,'/api/state')['data']==before
            # Fresh server process keeps sessions and progress on the same disk.
            proc.terminate();proc.wait(timeout=10);proc=start()
            for page in (p,q):page.reload();screen(page,'04');assert api(page,'/api/state')['data']==before
            # Unsaved guest cannot be abandoned; Save/Cancel are explicit choices.
            c=browser.new_context();r=c.new_page();r.goto(url);adopt(r);account(r)
            r.locator('#restore-open').click();r.locator('#guest-warning').wait_for(state='visible');r.locator('#guest-cancel').click()
            assert api(r,'/api/state')['data']['adopted'];other=save(r);r.locator('#account-close').click()
            ac=api(p,'/api/friends')['data']['code'];cc=api(r,'/api/friends')['data']['code']
            assert api(r,'/api/auth/recovery/restore',{'code':ac})['status']==401
            assert api(r,'/api/friends/'+ac+'/room')['status']==403
            assert api(p,'/api/friends',{'code':cc,'action':'request'})['status']==200
            assert api(r,'/api/friends',{'code':ac,'action':'accept'})['status']==200
            q.locator('#game-nav [data-destination="16"]').click()
            q.get_by_role('button',name='Visit room',exact=True).click();q.locator('#visit-banner').wait_for(state='visible')
            q.locator('#return-home').click();assert not q.locator('#visit-banner').is_visible()
            account(q);q.locator('#sign-out').click();screen(q,'01');assert not api(q,'/api/state')['data']['adopted']
            assert api(p,'/api/state')['data']==before
            assert not errors,errors
            browser.close()
        print('PASS: real guest/save/restore across browser sessions, invalid/public codes, unsaved guest guard, friend visit/return, sign-out isolation and fresh-process persistence. No external auth, AI calls or physical devices.')
    finally:proc.terminate();proc.wait(timeout=10)
