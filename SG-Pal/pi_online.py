"""Hardware-only Chromium bridge for the verified raw SPI panel. No game DB/API key.
CDP binds to loopback; the dedicated browser profile and runtime files are private.
"""
import argparse
import base64
import fcntl
import getpass
import io
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import tempfile
import time
from urllib.request import urlopen
from urllib.parse import urlparse

URL='https://sgpal.onrender.com/?kiosk=1'
HOME=Path.home()
PROFILE=HOME/'.local/share/sgpal-online/chromium'
CONFIG=HOME/'.config/sgpal-online.json'
RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR',str(HOME/'.local/share/sgpal-online')))

class CDP:
    def __init__(self):
        import websocket
        port=int((PROFILE/'DevToolsActivePort').read_text().splitlines()[0])
        with urlopen(f'http://127.0.0.1:{port}/json',timeout=5) as response:tabs=json.load(response)
        tab=next(t for t in tabs if t['type']=='page' and urlparse(t['url']).hostname=='sgpal.onrender.com')
        self.ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=15,suppress_origin=True)
        self.sequence=0;self.events=[]
    def call(self,method,params=None):
        self.sequence+=1;identifier=self.sequence
        self.ws.send(json.dumps({'id':identifier,'method':method,'params':params or {}}))
        while True:
            message=json.loads(self.ws.recv())
            if message.get('id')==identifier:
                if 'error' in message:raise RuntimeError('Browser command failed')
                return message.get('result',{})
            if message.get('method')=='Page.fileChooserOpened':self.events.append(message['params'])
    def evaluate(self,expression):
        result=self.call('Runtime.evaluate',{'expression':expression,'awaitPromise':True,'returnByValue':True})
        if 'exceptionDetails' in result:raise RuntimeError('Browser action failed')
        return result.get('result',{}).get('value')
    def key(self,name):
        codes={'ArrowLeft':37,'ArrowRight':39,'Enter':13,'Escape':27,'Tab':9}
        for kind in ('keyDown','keyUp'):
            self.call('Input.dispatchKeyEvent',{'type':kind,'key':name,'code':name,'windowsVirtualKeyCode':codes[name],'nativeVirtualKeyCode':codes[name]})
    def close(self):self.ws.close()


def panel():
    # Same controller setup/pins as jaz's sgpal-hardware-tests/screen_test.py.
    # Preserve that file and its driver configuration. No kernel overlay changes.
    from hardware import Display
    from PIL import Image
    class SPIBrowserDisplay(Display):
        def show(self,image):
            image=image.transpose(Image.Transpose.ROTATE_90)
            pixels=bytearray()
            for r,g,b in image.convert('RGB').getdata():
                value=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
                pixels.extend((value>>8,value&255))
            self.command(0x2A,[0,0,0,239]);self.command(0x2B,[0,0,1,63]);self.command(0x2C)
            self.dc.on()
            for start in range(0,len(pixels),4096):self.spi.writebytes(list(pixels[start:start+4096]))
    return SPIBrowserDisplay({'spi_hz':8000000,'rotate_180':False,'swap_red_blue':False})


def capture(cdp,event):
    # Only runs after the player deliberately chooses Upload. No HTTP camera API.
    with tempfile.TemporaryDirectory(prefix='sgpal-photo-',dir=RUNTIME) as folder:
        photo=Path(folder)/'capture.jpg'
        cdp.evaluate("document.getElementById('accessible').textContent='Capturing CSI photo…'")
        try:
            subprocess.run(['rpicam-still','--nopreview','--timeout','1000','--width','1280','--height','960','--encoding','jpg','--output',str(photo)],check=True,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            os.chmod(photo,0o600)
            cdp.call('DOM.setFileInputFiles',{'files':[str(photo)],'backendNodeId':event['backendNodeId']})
            # The shared file reader must finish before deleting its temporary input.
            end=time.monotonic()+5
            while time.monotonic()<end:
                if cdp.evaluate("SGPal.inspect().current==='05photo'"):break
                time.sleep(.1)
        except (subprocess.SubprocessError,OSError):
            cdp.evaluate("SGPal.cameraFailure('CSI CAPTURE FAILED. TRY UPLOAD AGAIN.')")


def run(args):
    from PIL import Image
    PROFILE.mkdir(parents=True,exist_ok=True,mode=0o700);PROFILE.chmod(0o700)
    RUNTIME.mkdir(parents=True,exist_ok=True)
    lock=open(RUNTIME/'sgpal-online.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    browser=None;display=None;controls=None;cdp=None
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        active=PROFILE/'DevToolsActivePort'
        if active.exists():active.unlink()
        browser=subprocess.Popen(['chromium','--headless=new','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--password-store=basic','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--window-size=320,240','--user-data-dir='+str(PROFILE),URL],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline and not stopped:
            if browser.poll() is not None:raise RuntimeError('Chromium stopped during startup')
            try:cdp=CDP();break
            except (OSError,ValueError,IndexError,StopIteration):time.sleep(.5)
        if cdp is None:raise RuntimeError('Chromium startup timed out')
        cdp.call('Emulation.setDeviceMetricsOverride',{'width':320,'height':240,'deviceScaleFactor':1,'mobile':False})
        cdp.call('Page.enable')
        if args.camera:cdp.call('Page.setInterceptFileChooserDialog',{'enabled':True})
        display=panel();events=queue.Queue()
        if args.controls:
            from hardware import Controls
            required=('rotary_a','rotary_b','rotary_press')
            if not all(isinstance(config.get(k),int) for k in required):raise RuntimeError('Confirmed rotary pins required in private config')
            controls=Controls({**config,'back_button':config.get('back_button'),'scan_button':config.get('scan_button')},events)
        print('Hosted game connected; SPI display active. Controls='+str(args.controls)+' CSI upload='+str(args.camera),flush=True)
        while not stopped:
            if browser.poll() is not None:raise RuntimeError('Chromium stopped')
            while not events.empty():
                action,_=events.get()
                if action=='scan':cdp.evaluate("SGPal.live();SGPal.rotate(1);SGPal.press()")
                else:cdp.key({'prev':'ArrowLeft','next':'ArrowRight','select':'Enter','back':'Escape'}[action])
                print('Input: '+action,flush=True)
            frame=cdp.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
            display.show(Image.open(io.BytesIO(base64.b64decode(frame['data']))))
            if args.camera and cdp.events:capture(cdp,cdp.events.pop(0))
            time.sleep(.12)
    finally:
        if controls:controls.close()
        if display:display.close()
        if cdp:cdp.close()
        if browser:
            browser.terminate()
            try:browser.wait(timeout=10)
            except subprocess.TimeoutExpired:browser.kill();browser.wait()
        lock.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['run','restore','key','status'])
    parser.add_argument('key',nargs='?',choices=['ArrowLeft','ArrowRight','Enter','Escape','Tab'])
    parser.add_argument('--controls',action='store_true');parser.add_argument('--camera',action='store_true')
    args=parser.parse_args()
    if args.action=='run':run(args);return
    cdp=CDP()
    try:
        if args.action=='key':cdp.key(args.key or 'Enter')
        elif args.action=='status':
            print(json.dumps(cdp.evaluate("({screen:window.SGPal?.inspect().current,ready:window.SGPal?.inspect().ready,adopted:window.SGPal?.inspect().saved.adopted,signed_in:window.SGPalAccount?.session?.signed_in})")))
        else:
            code=getpass.getpass('Private recovery code (hidden; never logged): ')
            # Same authenticated, CSRF-protected recovery API as the browser UI.
            expression="(async()=>{const r=await fetch('/api/auth/recovery/restore',{method:'POST',headers:{'Content-Type':'application/json',...SGPalAccount.headers()},body:JSON.stringify({code:"+json.dumps(code)+"})});if(r.ok){return {ok:true}}const body=await r.json();return {ok:false,message:body.detail}})()"
            result=cdp.evaluate(expression);code='';expression=''
            if not result or not result.get('ok'):raise RuntimeError((result or {}).get('message','Restore failed'))
            cdp.call('Page.reload')
            print('Restored. The private session is saved in the dedicated browser profile.')
    finally:cdp.close()

if __name__=='__main__':main()
