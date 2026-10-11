"""Full browser→FastAPI→SQLite flow with an explicitly injected test AI.
No live model quality claim; no secrets or real player data are used.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)


def info(page):return page.evaluate('SGPal.inspect()')
def screen(page,name):page.wait_for_function('(name)=>SGPal.inspect().current===name',arg=name)
def choose(page,label):
    for _ in range(20):
        state=info(page)
        assert label in state['choices'],(label,state)
        if state['choices'][state['focus']]==label:
            page.keyboard.press('Enter');return
        page.keyboard.press('ArrowRight')
    raise AssertionError('Focus not found')


with tempfile.TemporaryDirectory(prefix='sgpal-game-test-') as temp:
    data=Path(temp)
    for name in ['orange','blue','green']:
        Image.new('RGB',(300,200),name).save(data/(name+'.png'))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    env={**os.environ,'SGPAL_DATA_DIR':temp,'SGPAL_BROWSER_FIXTURE':'1'}
    command=[sys.executable,'-m','uvicorn','scripts.gameplay_fixture:app','--host','127.0.0.1','--port',str(port)]
    proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(url+'/api/status',timeout=1):break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Fixture did not start')
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel=os.environ.get('SGPAL_BROWSER_CHANNEL','chrome'),headless=True)
            context=browser.new_context(viewport={'width':390,'height':844},has_touch=True)
            page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url);screen(page,'01');assert page.locator('#photo').get_attribute('capture') is None;page.locator('#screen').focus()
            choose(page,'Start');choose(page,'otter');choose(page,'Choose');choose(page,'Keep');screen(page,'04')
            choose(page,'Scan');page.locator('#photo').set_input_files(data/'orange.png');screen(page,'05photo')
            page.route('**/api/scan',lambda route:route.fulfill(status=502,content_type='application/json',body='{"detail":"TEST: AI service unavailable. Retry."}'))
            page.locator('#screen').focus();choose(page,'Analyse');screen(page,'live-request-error')
            assert info(page)['saved']['xp']==0 and info(page)['saved']['coins']==0
            page.unroute('**/api/scan');choose(page,'Retry');screen(page,'live-candidate')
            assert info(page)['saved']['xp']==0
            choose(page,'Correct');screen(page,'live-correction');choose(page,'Kaya toast');screen(page,'live-candidate')
            # Persist candidate across reload, then confirm. Simulate a committed
            # confirmation whose HTTP response is lost before reaching the client.
            page.reload();screen(page,'live-candidate');page.locator('#screen').focus()
            def lose_response(route):route.fetch();route.abort()
            page.route('**/api/confirm',lose_response)
            choose(page,'Yes');screen(page,'live-request-error')
            page.unroute('**/api/confirm');choose(page,'Status');screen(page,'live-reward')
            assert info(page)['saved']['xp']==10 and info(page)['saved']['coins']==5
            choose(page,'Dex');screen(page,'live-story');choose(page,'Info');screen(page,'live-info')
            choose(page,'Photo');screen(page,'live-photo');page.screenshot(path=str(OUT/'game-photo.png'))
            choose(page,'Back');choose(page,'Quest');screen(page,'live-quest')
            choose(page,'Answer');screen(page,'live-quest-answer')
            page.screenshot(path=str(OUT/'quest-answer.png'))
            choose(page,'Not yet');screen(page,'live-quest')
            assert info(page)['saved']['xp']==10 and info(page)['saved']['coins']==5
            assert info(page)['saved']['completed']==[]
            # Failed delivery before commit: reload must retain the explicit answer for retry.
            page.route('**/api/quests/answer',lambda route:route.abort())
            choose(page,'Answer');screen(page,'live-quest-answer');choose(page,'Yes, I did it');screen(page,'live-request-error')
            assert info(page)['saved']['coins']==5
            page.reload();screen(page,'live-request-error');page.locator('#screen').focus()
            page.unroute('**/api/quests/answer')
            # Retry commits but its response is lost; Status retrieves exactly that result.
            page.route('**/api/quests/answer',lose_response)
            choose(page,'Retry');screen(page,'live-request-error')
            page.unroute('**/api/quests/answer');choose(page,'Status');screen(page,'live-reward')
            assert info(page)['saved']['xp']==35 and info(page)['saved']['coins']==15
            assert info(page)['saved']['quest_details']['kaya']['completion_method']=='self_reported'
            page.screenshot(path=str(OUT/'game-complete.png'))
            choose(page,'Quest');screen(page,'live-quest');assert 'Answer' not in info(page)['choices']
            # Reload reads committed reward and persisted photos.
            page.reload();screen(page,'04');assert info(page)['saved']['coins']==15
            page.locator('#screen').focus();choose(page,'Scan');page.locator('#photo').set_input_files(data/'orange.png');screen(page,'05photo');page.locator('#screen').focus();choose(page,'Analyse');screen(page,'live-candidate')
            choose(page,'Correct');choose(page,'Kaya toast');screen(page,'live-candidate');choose(page,'Yes');screen(page,'live-reward')
            assert info(page)['saved']['xp']==35 and info(page)['saved']['coins']==15
            assert info(page)['saved']['completed']==['kaya']
            # Earned coins -> purchase -> inventory -> room. No wallet seeding.
            choose(page,'Home');choose(page,'Menu');choose(page,'Shop');screen(page,'11')
            choose(page,'Buy');screen(page,'11confirm');choose(page,'Back');screen(page,'11')
            assert info(page)['saved']['coins']==15 and info(page)['saved']['inventory']==[]
            choose(page,'Buy');page.route('**/api/shop/purchase',lose_response)
            choose(page,'Confirm');screen(page,'live-request-error')
            page.unroute('**/api/shop/purchase')
            page.reload();screen(page,'live-commerce-result');page.locator('#screen').focus()
            assert info(page)['saved']['coins']==7 and info(page)['saved']['xp']==35
            choose(page,'Shop');screen(page,'11');assert 'Owned' in info(page)['choices']
            choose(page,'Owned');screen(page,'12');choose(page,'Window plant');screen(page,'live-placement')
            assert info(page)['saved']['room']=={}
            choose(page,'Back');screen(page,'12');assert info(page)['saved']['room']=={}
            choose(page,'Window plant');screen(page,'live-placement')
            # Touch uses the same Save action as keyboard/rotary.
            box=page.locator('#screen').bounding_box();scale=box['width']/320
            page.touchscreen.tap(box['x']+45*scale,box['y']+208*scale)
            screen(page,'live-commerce-result');assert info(page)['saved']['room']=={'window':'window_plant'}
            page.locator('#screen').focus();choose(page,'Home');screen(page,'04')
            page.screenshot(path=str(OUT/'decorated-room.png'))
            page.reload();screen(page,'04');assert info(page)['saved']['room']=={'window':'window_plant'}
            assert info(page)['saved']['coins']==7 and info(page)['saved']['inventory']==['window_plant']
            page.locator('#screen').focus();choose(page,'Menu');choose(page,'Shop')
            choose(page,'Next');choose(page,'Next');choose(page,'Buy');choose(page,'Confirm');screen(page,'live-commerce-result')
            assert info(page)['saved']['coins']==7 and info(page)['saved']['inventory']==['window_plant']
            page.screenshot(path=str(OUT/'shop-insufficient.png'))
            choose(page,'Shop');choose(page,'Next');choose(page,'Next');choose(page,'Buy')
            # Leave a slow committed purchase. The result must refresh the wallet
            # without forcing the user away from Home; Status retains the receipt.
            held=[]
            page.route('**/api/shop/purchase',lambda route:held.append((route,route.fetch())))
            choose(page,'Confirm');screen(page,'live-working')
            page.wait_for_timeout(200)
            assert len(held)==1
            choose(page,'Back');screen(page,'04')
            assert info(page)['saved']['coins']==7
            held[0][0].fulfill(response=held[0][1])
            page.unroute('**/api/shop/purchase')
            page.wait_for_function('SGPal.inspect().saved.coins===2')
            screen(page,'04');choose(page,'Status');screen(page,'live-commerce-result')
            assert info(page)['saved']['coins']==2
            choose(page,'Items');choose(page,'Kopi cup');screen(page,'live-placement');choose(page,'Save');screen(page,'live-commerce-result')
            assert info(page)['saved']['room']=={'window':'kopi_cup'}
            assert set(info(page)['saved']['inventory'])=={'window_plant','kopi_cup'}
            choose(page,'Home');page.reload();screen(page,'04')
            assert info(page)['saved']['coins']==2 and info(page)['saved']['xp']==35
            assert info(page)['saved']['room']=={'window':'kopi_cup'}
            assert page.evaluate('SGPal.audit()')==[]
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not errors,errors
            browser.close()
            print('PASS: full UI flow, correction, lost-response reconciliation, persisted photos, Not yet, Done, failed-delivery retry across reload, exactly-once discovery/quest rewards, earned-coin purchases, cancel, insufficient funds, inventory, touch placement, replacement, reload, 390px layout, no JS errors. AI was an injected test fixture.')
    finally:
        proc.terminate();proc.wait(timeout=10)
