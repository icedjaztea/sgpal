#!/usr/bin/env python3
import argparse, io, json, queue, signal, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core import Store, CONFIG, CULTURE, BY_ID, ROOT, normalise, recognise, digest
from ui import render, wrapped

HTML='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>SG Pal preview</title>
<style>body{margin:0;background:#e7ebdf;color:#233f3b;font:16px system-ui;display:grid;place-items:center;min-height:100vh}main{max-width:760px;padding:24px}small{letter-spacing:2px}h1{font-size:32px;margin:8px 0}img{width:min(640px,90vw);image-rendering:pixelated;border:12px solid #233f3b;border-radius:18px;box-sizing:border-box}button,label{display:inline-block;background:#233f3b;color:#fff8e6;border:0;border-radius:12px;padding:12px 16px;margin:5px;cursor:pointer}p{line-height:1.5}input{display:none}</style>
<main><small>COMMON GROUND / SG PAL</small><h1>A little local adventure.</h1><p>The actual 320 × 240 device screen, enlarged.</p><img id="screen" alt="SG Pal device screen"><div>
<button onclick="act('prev')">← Previous</button><button onclick="act('select')">Select</button><button onclick="act('next')">Next →</button><button onclick="act('back')">Back</button><button onclick="act('scan')">Scan</button></div>
<label>Choose photo <input id="file" type="file" accept="image/jpeg,image/png,image/webp"></label><p>Arrow keys: browse · Enter: select · Escape: back · S: scan.<br>Photos stay local until you confirm “analyse”. DEMO never calls AI.</p><p id="status"></p></main>
<script>
async function act(action,value=null){let r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,value})});if(!r.ok)document.querySelector('#status').textContent='Request rejected. Reload this page.';}
let screen=document.querySelector('#screen');setInterval(()=>{screen.src='/screen.png?t='+Date.now()},250);
screen.onclick=e=>{let r=screen.getBoundingClientRect();let b=12;act('tap',[Math.round((e.clientX-r.left-b)*320/(r.width-2*b)),Math.round((e.clientY-r.top-b)*240/(r.height-2*b))]);};
document.onkeydown=e=>{let a={ArrowLeft:'prev',ArrowUp:'prev',ArrowRight:'next',ArrowDown:'next',Enter:'select',Escape:'back',s:'scan'}[e.key];if(a){e.preventDefault();act(a);}};
document.querySelector('#file').onchange=e=>{let f=e.target.files[0];if(!f)return;if(f.size>6*1024*1024){alert('Choose a photo under 6 MB.');return;}let r=new FileReader();r.onload=()=>act('upload',r.result.split(',')[1]);r.readAsDataURL(f);};
</script>'''

class App:
    def __init__(self,demo=False,pi=False,data_dir=None):
        self.demo=demo; self.pi=pi
        base=Path(data_dir) if data_dir else Path.home()/'.local/share/sgpal'
        self.store=Store(base/('demo-progress.json' if demo else 'progress.json'))
        self.events=queue.Queue(maxsize=64); self.screen='home'; self.index=0; self.page=0
        self.photo=None; self.result=None; self.cid=None; self.error=''; self.note=''
        self.quest_mode=False; self.busy_label='Looking closely...'; self.hits=[]; self.effects=None
        self.png=b''; self.running=True

    def set_screen(self,name): self.screen=name; self.page=0; self.index=0

    def content(self):
        if self.screen=='error': return 'Let us try again',self.error,'Press or Back: home'
        if self.screen=='capture_help': return 'Choose a photo','Use Choose photo below the preview, then press Select to send it for analysis.','Back: home'
        if self.screen=='result':
            if self.cid:
                item=BY_ID[self.cid]
                return item['title'], self.note+' '+item['fact']+' '+self.result.get('observation',''),'Turn: read  /  Press: quest  /  Back'
            return 'Not sure yet',self.result['observation']+' Try a clearer photo with more context.','Press or Back: home'
        if self.screen=='detail':
            c=BY_ID[self.cid]; return c['title'],c['fact'],'Turn: read  /  Press: quest  /  Back'
        if self.screen=='quest':
            cid=self.store.data['active']
            if cid:
                c=BY_ID[cid]; return 'Your next discovery',c['quest'],'Turn: read  /  Press: take photo'
            return 'A quest awaits','Scan something new, then choose its quest. Complete a photo challenge for 25 XP.','Back: home'
        if self.screen=='verified': return 'Quest check',self.note,'Press or Back: home'
        return 'SG Pal','','Back: home'

    def worker(self,fn,kind):
        self.set_screen('busy')
        def run():
            try: self.events.put((kind,fn()))
            except Exception as exc:
                msg=str(exc) if isinstance(exc,(RuntimeError,ValueError)) else 'Unexpected error. Check hardware and retry.'
                self.events.put(('error',msg))
        threading.Thread(target=run,daemon=True).start()

    def start_capture(self):
        self.quest_mode=bool(self.store.data['active']) and (self.screen=='quest' or (self.screen in ('photo','capture_help') and self.quest_mode))
        if self.demo:
            from PIL import Image,ImageDraw
            im=Image.new('RGB',(320,240),'#E6DCC6'); d=ImageDraw.Draw(im)
            d.rectangle((60,100,250,190),fill='#B27E56'); d.rectangle((115,105,180,133),fill='white')
            d.text((35,40),'DEMO SCENE - NOT A REAL SCAN',fill='black')
            # Distinct demo quest photo so duplicate guard still exercises the flow.
            if self.quest_mode: d.rectangle((185,80,205,128),fill='#66AABB')
            out=io.BytesIO(); im.save(out,'JPEG'); self.photo=out.getvalue(); self.set_screen('photo')
        elif self.pi:
            from hardware import capture
            self.busy_label='Taking a photo...'; self.worker(lambda:normalise(capture()),'captured')
        else: self.set_screen('capture_help')

    def analyse(self):
        quest=BY_ID[self.store.data['active']] if self.quest_mode and self.store.data['active'] else None
        if quest and digest(self.photo)==self.store.data['log'][quest['id']]['hash']:
            self.error='This is the discovery photo again. Take a new photo showing the quest evidence.'; self.set_screen('error'); return
        self.busy_label='Checking your quest...' if quest else 'Looking closely...'
        if self.demo:
            def fake():
                time.sleep(.5)
                return {'culture_id':quest['id'] if quest else 'chope','confidence':'high',
                        'observation':'Demo result only; this scene has not been assessed by AI.','verified':bool(quest)}
            self.worker(fake,'recognised')
        else: self.worker(lambda:recognise(self.photo,quest),'recognised')

    def handle(self,action,value=None):
        if action=='error': self.error=value; self.set_screen('error'); return
        if action=='captured': self.photo=value; self.set_screen('photo'); return
        if action=='recognised':
            self.result=value
            high=value['confidence']=='high'
            if self.quest_mode:
                cid=self.store.data['active']
                success=bool(cid and high and value['verified'] and self.store.finish(cid,digest(self.photo)))
                self.note=('Quest complete! +25 XP. ' if success else 'Not verified yet. Try a clearer photo of the quest requirement. ')+value['observation']
                self.set_screen('verified')
            else:
                self.cid=value['culture_id'] if high and value['culture_id'] in BY_ID else None
                success=bool(self.cid)
                fresh=self.store.discover(self.cid,digest(self.photo)) if self.cid else False
                self.note='+10 XP! New discovery.' if fresh else 'Already in your culture log.'
                self.set_screen('result')
            if self.effects: self.effects.signal(success)
            return
        if self.screen=='busy': return
        if action=='upload':
            if self.pi or self.demo: return
            import base64
            try:
                self.quest_mode=self.screen=='quest' or (self.screen=='capture_help' and self.quest_mode)
                self.photo=normalise(base64.b64decode(value,validate=True)); self.set_screen('photo')
            except Exception: self.error='Could not open photo. Use JPEG, PNG or WebP under 6 MB.'; self.set_screen('error')
            return
        if action=='tap':
            for bounds,event in self.hits:
                if bounds[0]<=value[0]<=bounds[2] and bounds[1]<=value[1]<=bounds[3]: self.handle(*event); break
            return
        if action in ('menu','logitem'):
            self.index=value; self.handle('select'); return
        if action=='back': self.photo=None; self.quest_mode=False; self.set_screen('home'); return
        if action in ('next','prev'):
            delta=1 if action=='next' else -1
            if self.screen=='home': self.index=(self.index+delta)%4
            elif self.screen=='log': self.index=(self.index+delta)%max(1,len(self.store.data['log']))
            else:
                pages=max(1,(len(wrapped(self.content()[1],292))+6)//7)
                self.page=(self.page+delta)%pages
            return
        if action=='scan': self.start_capture(); return
        if action=='select':
            if self.screen=='home':
                if self.index==0: self.start_capture()
                else: self.set_screen(['home','log','quest','pal'][self.index])
            elif self.screen=='photo': self.analyse()
            elif self.screen=='quest':
                if self.store.data['active']: self.start_capture()
            elif self.screen=='log':
                ids=list(self.store.data['log'])
                if ids: self.cid=ids[self.index%len(ids)]; self.set_screen('detail')
            elif self.screen in ('detail','result') and self.cid:
                if self.store.activate(self.cid): self.set_screen('quest')
                else: self.note='You have already completed this quest. Scan another cultural cue.'; self.set_screen('verified')
            elif self.screen in ('error','result','verified'): self.set_screen('home')


def server_for(app,port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,status,data,kind):
            self.send_response(status); self.send_header('Content-Type',kind)
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError): pass
        def do_GET(self):
            if self.path=='/': self.reply(200,HTML.encode(),'text/html; charset=utf-8')
            elif self.path.startswith('/screen.png'): self.reply(200,app.png,'image/png')
            else: self.reply(404,b'Not found','text/plain')
        def do_POST(self):
            allowed={f'localhost:{port}',f'127.0.0.1:{port}'}
            origin=self.headers.get('Origin','')
            if self.path!='/action' or self.headers.get('Host') not in allowed or origin not in {'http://'+h for h in allowed}:
                self.reply(403,b'Forbidden','text/plain'); return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>8500000: raise ValueError()
                data=json.loads(self.rfile.read(size)); a=data['action']; v=data.get('value')
                if a not in ('next','prev','select','back','scan','upload','tap'): raise ValueError()
                if a=='tap' and (not isinstance(v,list) or len(v)!=2 or not all(type(x) is int for x in v)): raise ValueError()
                if a=='upload' and not isinstance(v,str): raise ValueError()
                app.events.put_nowait((a,v)); self.reply(200,b'OK','text/plain')
            except (ValueError,KeyError,TypeError,queue.Full): self.reply(400,b'Bad request','text/plain')
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--pi',action='store_true'); p.add_argument('--demo',action='store_true')
    p.add_argument('--no-controls',action='store_true'); p.add_argument('--port',type=int,default=8765)
    p.add_argument('--data-dir'); p.add_argument('--screenshot'); args=p.parse_args()
    app=App(args.demo,args.pi,args.data_dir)
    if args.screenshot: render(app).save(args.screenshot); return
    devices=[]; display=None; touch=None; server=None
    try:
        if args.pi:
            from hardware import Display,Controls,Effects,Touch
            display=Display(CONFIG); devices.append(display)
            if not args.no_controls: devices.append(Controls(CONFIG,app.events))
            app.effects=Effects(CONFIG); devices.append(app.effects)
            if CONFIG['touch']: touch=Touch(CONFIG,app.events); devices.append(touch)
        server=server_for(app,args.port); threading.Thread(target=server.serve_forever,daemon=True).start()
        print(f'SG Pal {"DEMO" if args.demo else "LIVE"}: http://127.0.0.1:{args.port}',flush=True)
        def stop(*_): app.running=False
        signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
        while app.running:
            for _ in range(20):
                try: app.handle(*app.events.get_nowait())
                except queue.Empty: break
            if touch:
                try: touch.poll()
                except OSError: print('Touch I2C error; continuing with controls.',flush=True); touch.close(); devices.remove(touch); touch=None
            frame=render(app)
            buf=io.BytesIO(); frame.save(buf,'PNG'); app.png=buf.getvalue()
            if display: display.show(frame)
            time.sleep(.12)
    finally:
        if server: server.shutdown(); server.server_close()
        for device in reversed(devices): device.close()

if __name__=='__main__': main()
