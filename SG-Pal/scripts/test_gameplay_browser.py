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
    assert label in info(page)['choices'],(label,info(page))
    button=page.locator('#game-actions').get_by_role('button',name=label,exact=True)
    button.focus();button.press('Enter')



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
            start=page.locator('#game-actions').get_by_role('button',name='Start',exact=True)
            start.focus();start.press('ArrowRight');assert info(page)['focus']==1
            page.keyboard.press('ArrowLeft');assert info(page)['focus']==0
            for label in ['Start','otter','Choose','Reroll','Keep']:
                page.locator('#game-actions').get_by_role('button',name=label,exact=True).tap()
            screen(page,'04');assert info(page)['saved']['name']=='Pebble'
            choose(page,'Scan');page.locator('#photo').set_input_files(data/'orange.png');screen(page,'05photo')
            page.route('**/api/scan',lambda route:route.fulfill(status=502,content_type='application/json',body='{"detail":"TEST: AI service unavailable. Retry."}'))
            choose(page,'Analyse');screen(page,'live-request-error')
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
            choose(page,'Scan');page.locator('#photo').set_input_files(data/'orange.png');screen(page,'05photo');choose(page,'Analyse');screen(page,'live-candidate')
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
            page.locator('#game-actions').get_by_role('button',name='Save',exact=True).tap()
            screen(page,'live-commerce-result');assert info(page)['saved']['room']=={'window':'window_plant'}
            choose(page,'Home');screen(page,'04')
            page.screenshot(path=str(OUT/'decorated-room.png'))
            page.reload();screen(page,'04');assert info(page)['saved']['room']=={'window':'window_plant'}
            assert info(page)['saved']['coins']==7 and info(page)['saved']['inventory']==['window_plant']
            choose(page,'Menu');choose(page,'Shop')
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
            # Default responsive presentation: representative desktop, tablet,
            # phone portrait/landscape. These are emulated viewports, not devices.
            baseline=info(page)['saved']
            for label,width,height in [('desktop',1440,900),('wide',1920,1080),('laptop',1280,720),('tablet',768,1024),('phone',390,844),('small-phone',320,568),('landscape',844,390)]:
                page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),label
                shell=page.locator('#browser-shell').bounding_box()
                assert abs(shell['y']+shell['height']-height)<2,(label,shell)
                art=page.locator('#room-art').bounding_box()
                assert abs(art['width']/art['height']-320/168)<.01,(label,art)
                nav=page.locator('#game-nav').bounding_box()
                assert nav['y']+nav['height']<=height+1,(label,nav)
                if width>800:
                    assert art['y']>=0 and art['y']+art['height']<=height,(label,art)
                assert info(page)['saved']==baseline
                page.screenshot(path=str(OUT/('responsive-'+label+'.png')))
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#game-nav').get_by_role('button',name='Scan',exact=True).click();screen(page,'05')
            page.evaluate("()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(Object.assign(new Error('denied'),{name:'NotAllowedError'}))}")
            choose(page,'Camera');screen(page,'05error');assert page.locator('#game-actions').get_by_role('button',name='Upload',exact=True).is_visible()
            choose(page,'Back');choose(page,'Back');screen(page,'04')
            page.locator('#game-nav').get_by_role('button',name='Quests',exact=True).click();screen(page,'09')
            page.locator('#panel-close').click();screen(page,'04menu')
            page.locator('#game-nav').get_by_role('button',name='Home',exact=True).click();screen(page,'04')
            page.emulate_media(reduced_motion='reduce')
            assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
            assert page.locator('#game-actions button').first.evaluate("el=>getComputedStyle(el).transitionDuration")=='0s'
            page.set_viewport_size({'width':1440,'height':900})
            if page.locator('#fullscreen').is_visible():
                page.locator('#fullscreen').click()
                if page.evaluate('!!document.fullscreenElement'):
                    page.wait_for_function("document.getElementById('fullscreen').textContent==='Exit fullscreen'")
                    page.locator('#fullscreen').click()
                    page.wait_for_function('!document.fullscreenElement')
            # Browser gallery remains visibly isolated and cannot mutate progress.
            page.evaluate("SGPal.preview('11confirm')")
            assert page.locator('#mode').inner_text().startswith('DESIGN PREVIEW')
            page.evaluate('SGPal.press()');assert info(page)['saved']==baseline
            page.locator('#live').click();screen(page,'04');assert page.locator('#browser-shell').is_visible()
            # Unavailable fullscreen does not block normal windowed play.
            page.add_init_script("Object.defineProperty(document,'fullscreenEnabled',{get:()=>false})")
            page.reload();screen(page,'04');assert not page.locator('#fullscreen').is_visible()
            assert info(page)['saved']==baseline
            # Switching layout reads the same server progress.
            page.goto(url+'/?kiosk=1');screen(page,'04');assert info(page)['saved']==baseline
            assert page.locator('#screen').bounding_box()['width']==320
            page.screenshot(path=str(OUT/'responsive-compact.png'))
            assert not errors,errors
            browser.close()
            print('PASS: full UI flow, correction, lost-response reconciliation, persisted photos, Not yet, Done, failed-delivery retry across reload, exactly-once discovery/quest rewards, earned-coin purchases, cancel, insufficient funds, inventory, touch placement, replacement, reload, responsive desktop/tablet/phone portrait and landscape, fullscreen/fallback, compact switch, no JS errors. AI was an injected test fixture.')
    finally:
        proc.terminate();proc.wait(timeout=10)
