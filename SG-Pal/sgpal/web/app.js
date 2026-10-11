/* SG Pal shared browser UI. Approved Kopi Sunset renderer, native 320x240. */
(() => {
'use strict';
const C={paper:'#f7e8ca',ink:'#29334a',wood:'#a66d51',terra:'#d98169',jade:'#6f9e83',gold:'#e7ba62',cream:'#fff5df',muted:'#b7a78d'};
const canvas=document.getElementById('screen');let ctx=canvas.getContext('2d');
const compact=new URLSearchParams(location.search).get('kiosk')==='1';
let browserLines=[],browserBody=null,drawingControl=false;
ctx.imageSmoothingEnabled=false;
// Original compact bitmap alphabet: 5x7 glyphs at 2x = 10x14px, 12px advance.
const glyphs={
A:['01110','10001','10001','11111','10001','10001','10001'],B:['11110','10001','10001','11110','10001','10001','11110'],C:['01111','10000','10000','10000','10000','10000','01111'],D:['11110','10001','10001','10001','10001','10001','11110'],E:['11111','10000','10000','11110','10000','10000','11111'],F:['11111','10000','10000','11110','10000','10000','10000'],G:['01111','10000','10000','10111','10001','10001','01111'],H:['10001','10001','10001','11111','10001','10001','10001'],I:['11111','00100','00100','00100','00100','00100','11111'],J:['00111','00010','00010','00010','10010','10010','01100'],K:['10001','10010','10100','11000','10100','10010','10001'],L:['10000','10000','10000','10000','10000','10000','11111'],M:['10001','11011','10101','10101','10001','10001','10001'],N:['10001','11001','10101','10011','10001','10001','10001'],O:['01110','10001','10001','10001','10001','10001','01110'],P:['11110','10001','10001','11110','10000','10000','10000'],Q:['01110','10001','10001','10001','10101','10010','01101'],R:['11110','10001','10001','11110','10100','10010','10001'],S:['01111','10000','10000','01110','00001','00001','11110'],T:['11111','00100','00100','00100','00100','00100','00100'],U:['10001','10001','10001','10001','10001','10001','01110'],V:['10001','10001','10001','10001','10001','01010','00100'],W:['10001','10001','10001','10101','10101','10101','01010'],X:['10001','10001','01010','00100','01010','10001','10001'],Y:['10001','10001','01010','00100','00100','00100','00100'],Z:['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],'1':['00100','01100','00100','00100','00100','00100','01110'],'2':['01110','10001','00001','00010','00100','01000','11111'],'3':['11110','00001','00001','01110','00001','00001','11110'],'4':['00010','00110','01010','10010','11111','00010','00010'],'5':['11111','10000','10000','11110','00001','00001','11110'],'6':['01110','10000','10000','11110','10001','10001','01110'],'7':['11111','00001','00010','00100','01000','01000','01000'],'8':['01110','10001','10001','01110','10001','10001','01110'],'9':['01110','10001','10001','01111','00001','00001','01110'],
' ':['00000','00000','00000','00000','00000','00000','00000'],'.':['00000','00000','00000','00000','00000','00110','00110'],',':['00000','00000','00000','00000','00110','00110','00100'],':':['00000','00110','00110','00000','00110','00110','00000'],'!':['00100','00100','00100','00100','00100','00000','00100'],'?':['01110','10001','00001','00010','00100','00000','00100'],'-':['00000','00000','00000','11111','00000','00000','00000'],'/':['00001','00001','00010','00100','01000','10000','10000'],'+':['00000','00100','00100','11111','00100','00100','00000'],'#':['01010','11111','01010','01010','11111','01010','00000'],'<':['00010','00100','01000','10000','01000','00100','00010'],'>':['01000','00100','00010','00001','00010','00100','01000'],'(':['00010','00100','01000','01000','01000','00100','00010'],')':['01000','00100','00010','00010','00010','00100','01000'],"'":['00100','00100','00000','00000','00000','00000','00000']};
let hits=[],focus=0,current='01',gallery=false,backend=false,ready=false,stream=null,photo=null,mediaGeneration=0;
let candidate='merlion',nameIndex=0,lastCameraError='Camera unavailable.';
const names={merlion:['Kopi','Splash','Bubbles'],otter:['Kaya','Pebble','Puddle'],mynah:['Pip','Chirpy','Milo']};
const empty=()=>({version:1,adopted:false,species:'merlion',name:'Kopi',xp:0,coins:0,discoveries:[],quests:[],inventory:[],room:{},sound:false});
let shopItems=[],roomSlots=[],shopIndex=0,slotIndex=0,selectedDecor=null;
let saved=empty(),catalogue=[],menuPage=0,dexPage=0,questPage=0,detailPage=0,selectedEntry=null,saving=false;
const browserStorage=new URLSearchParams(location.search).get('storage')==='browser';
backend=!browserStorage;
const sample={...empty(),adopted:true,species:'merlion',name:'Kopi',xp:140,coins:80,discoveries:['001'],quests:['chope'],inventory:['plant']};
const state=()=>gallery?sample:saved;
const assets={};
const screens={};
const mainIds=['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18'];
const audit=[];
function rect(x,y,w,h,col){ctx.fillStyle=col;ctx.fillRect(x,y,w,h)}
function frame(x,y,w,h,fill=C.cream,border=C.ink){rect(x,y,w,h,border);rect(x+2,y+2,w-4,h-4,fill)}
function text(s,x,y,col=C.ink,scale=2){if(!drawingControl&&y>=24&&y<194)browserLines.push(String(s));s=String(s).toUpperCase();const w=s.length*6*scale-scale;if(x<0||x+w>320||y<0||y+7*scale>240)audit.push({screen:current,s,x,y,w});ctx.fillStyle=col;[...s].forEach((ch,i)=>(glyphs[ch]||glyphs['?']).forEach((row,ry)=>[...row].forEach((bit,rx)=>{if(bit==='1')ctx.fillRect(x+(i*6+rx)*scale,y+ry*scale,scale,scale)})))}
function center(s,y,col=C.ink,scale=2){text(s,Math.floor((320-(s.length*6-1)*scale)/2),y,col,scale)}
function lines(arr,x=16,y=48,col=C.ink){arr.forEach((v,i)=>text(v,x,y+i*22,col))}
function pointer(x,y){for(let i=0;i<5;i++)rect(x+i,y+i,1,9-i*2,C.ink)}
function header(title,right=''){rect(0,0,320,24,C.ink);text(title,8,5,C.paper);if(right)text(right,312-(right.length*12-2),5,C.paper)}
function footer(hint='TURN / PRESS'){rect(0,224,320,16,C.ink);center(hint,225,C.paper)}
function base(title,right=''){rect(0,0,320,240,C.paper);header(title,right);footer()}
function button(label,x,y,w,h,fn,{disabled=false}={}){const i=hits.length,sel=i===focus;hits.push({label,x,y,w,h,fn,disabled});frame(x,y,w,h,disabled?C.muted:sel?C.terra:C.cream);if(sel)pointer(x+5,y+Math.floor((h-9)/2));drawingControl=true;text(label,x+Math.floor((w-(label.length*12-2))/2)+(sel?3:0),y+Math.floor((h-14)/2));drawingControl=false;}
function rail(options){const gap=4,w=Math.floor((304-gap*(options.length-1))/options.length);options.forEach((o,i)=>button(o[0],8+i*(w+gap),194,w,28,o[1]));}
function row(label,y,fn,sub){button(label,12,y,296,30,fn);if(sub)text(sub,18,y+33,C.wood)}
function sprite(species,x,y,size=64){const a=assets[species];if(a){const r=Math.min(size/a.width,size/a.height);const w=Math.round(a.width*r),h=Math.round(a.height*r);ctx.drawImage(a,x+Math.floor((size-w)/2),y+Math.floor((size-h)/2),w,h)}}
function room(pal=true,arrangement=gallery?{}:saved.room){ctx.drawImage(assets.room,0,24,320,168);for(const [slotId,itemId] of Object.entries(arrangement||{})){const slot=roomSlots.find(s=>s.id===slotId),item=shopItems.find(i=>i.id===itemId);if(slot&&item)decoration(item.art,slot.x,slot.y)}if(pal)sprite(state().species,147,112,56)}
// Plant reuses approved primitive art. Cup/tile are simple palette-matched placeholders.
function decoration(art,x,y){
 if(art==='plant'){symbol('plant',x,y);return}
 if(art==='cup'){frame(x+1,y+15,28,25,C.cream);frame(x+27,y+20,9,13,C.cream);rect(x+29,y+23,4,7,C.wood);rect(x+4,y+18,22,5,C.wood);rect(x-2,y+43,38,4,C.paper);return}
 frame(x,y+7,34,34,C.cream);frame(x+4,y+11,26,26,C.jade);rect(x+13,y+14,8,20,C.terra);rect(x+7,y+20,20,8,C.terra);rect(x+13,y+20,8,8,C.gold);rect(x+6,y+44,24,4,C.wood);
}
function symbol(type,x,y){if(type==='coin'){frame(x+2,y,12,16,C.gold);rect(x,y+3,16,10,C.gold);rect(x+6,y+4,3,8,C.wood)}else if(type==='xp'){rect(x+6,y,4,16,C.cream);rect(x,y+6,16,4,C.cream)}else if(type==='lock'){frame(x+4,y,10,9,C.paper);frame(x,y+7,18,13,C.muted);rect(x+8,y+11,2,5,C.ink)}else if(type==='tissue'){frame(x,y+12,64,28,C.jade);rect(x+24,y+5,22,16,C.cream);rect(x+30,y,12,8,C.cream);rect(x+6,y+28,52,3,C.paper)}else if(type==='plant'){rect(x+14,y+12,4,23,C.wood);rect(x+2,y+8,15,10,C.jade);rect(x+17,y,16,13,C.jade);frame(x+4,y+32,28,21,C.terra)}}
function placeholderPhoto(x=20,y=40,w=280,h=116){frame(x,y,w,h,C.ink,C.wood);text('PHOTO AREA',x+Math.floor((w-118)/2),y+20,C.paper);text('NO SAMPLE PHOTO',x+Math.floor((w-178)/2),y+47,C.paper)}
function register(id,title,phase,draw,meta){screens[id]={id,title,phase,draw,...meta};}
function nav(id){stopCamera();current=id;focus=0;render();}
function goHome(){nav('04')}
function unavailable(title='Not connected'){nav('blocked');screens.blocked.context=title;render()}
async function api(path,body){
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),60000);
 try{const r=await fetch('/api/'+path,{signal:controller.signal,method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});if(!r.ok){let data;try{data=await r.json()}catch(_){}const error=Error(typeof data?.detail==='string'?data.detail:'Request failed. Check connection and retry.');error.status=r.status;throw error}return await r.json()}catch(e){if(e.name==='AbortError')throw Error('Request timed out. Use Status before retrying; the server may have saved it.');if(e instanceof TypeError)throw Error('Connection lost. Use Status or Retry when the server is reachable.');throw e}finally{clearTimeout(timeout)}
}
function localPersist(next){localStorage.setItem('sgpal-ui-v1',JSON.stringify(next));saved=next}
async function adopt(){
 if(gallery){nav('04');return}if(saving)return;saving=true;
 try{const body={species:candidate,name:names[candidate][nameIndex]};
  if(backend)saved=await api('adopt',body);else localPersist({...saved,...body,adopted:true});
  nav('04');
 }catch(e){
  // Reconcile a lost response or another browser's completed adoption.
  try{if(backend){const latest=await api('state');if(latest.adopted){saved=latest;nav('04');return}}}catch(_){}
  nav('saveerror');
 }finally{saving=false}
}
async function sound(){if(gallery){unavailable('Sample setting');return}if(saving)return;saving=true;try{const enabled=!saved.sound;if(backend)saved=await api('sound',{enabled});else localPersist({...saved,sound:enabled});render()}catch(e){nav('saveerror')}finally{saving=false}}
let audio;
function tick(){if(!saved.sound||gallery)return;try{audio=audio||new(window.AudioContext||window.webkitAudioContext)();audio.resume();const o=audio.createOscillator(),g=audio.createGain();o.type='square';o.frequency.value=440;g.gain.value=.018;o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+.035)}catch(e){}}
function rotate(delta){if(saving||!ready||!hits.length||!Number.isFinite(delta)||delta===0)return;focus=(focus+Math.sign(delta)+hits.length)%hits.length;tick();render()}
function press(){if(saving||!ready)return;const h=hits[focus];if(h&&!h.disabled){tick();h.fn()}}
function back(){if(saving)return;const h=hits.find(h=>h.label==='Back'||h.label==='Home'||h.label==='Leave'||h.label==='Cancel');if(h)h.fn();else if(current==='01')nav('help');else goHome()}
function stopCamera(){mediaGeneration++;if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}document.getElementById('camera').srcObject=null;}
async function camera(){if(gallery){nav('05live');return}if(!navigator.mediaDevices?.getUserMedia){lastCameraError='HTTPS or upload needed.';nav('05error');return}stopCamera();current='05starting';focus=0;render();const token=mediaGeneration;try{const s=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:640}},audio:false});if(token!==mediaGeneration){s.getTracks().forEach(t=>t.stop());return}stream=s;const v=document.getElementById('camera');v.srcObject=s;await v.play();if(token!==mediaGeneration){s.getTracks().forEach(t=>t.stop());return}current='05live';focus=0;render()}catch(e){if(token!==mediaGeneration)return;lastCameraError=e.name==='NotAllowedError'?'Permission not granted.':'Camera unavailable.';nav('05error')}}
function capture(){if(gallery){nav('06check');return}const v=document.getElementById('camera');if(!v.videoWidth){nav('05error');return}const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);const token=mediaGeneration,im=new Image();im.onload=()=>{if(token!==mediaGeneration)return;photo=im;photoPayload=im.src.split(',')[1];nav('05photo')};im.src=c.toDataURL('image/jpeg',.8)}
function choosePhoto(){document.getElementById('photo').click()}
function picture(){if(photo&&!gallery){ctx.save();ctx.imageSmoothingEnabled=true;const r=Math.min(280/photo.width,128/photo.height);let w=Math.round(photo.width*r),h=Math.round(photo.height*r);ctx.drawImage(photo,20+Math.floor((280-w)/2),34+Math.floor((128-h)/2),w,h);ctx.restore()}else placeholderPhoto()}
// Core flow. Screen examples always use isolated sample state.
register('01','Hello, Singapore',1,()=>{base('WELCOME');ctx.drawImage(assets.room,0,24,320,168);frame(24,40,272,148,C.paper);center('SG PAL',53,C.ink,3);sprite('merlion',34,90,60);sprite('otter',127,91,60);sprite('mynah',220,90,60);center('MAKE A LITTLE HOME.',170);rail([['Start',()=>nav('02')],['Help',()=>nav('help')],['Back',()=>nav('bootback')]])},{focus:'Start > Help > Back',click:'Start opens character selection. Returning adopted saves open Home instead.',back:'Back opens device options; it never erases a save.',layout:'Header 0,0 320x24; logo panel 24,40 272x148; portraits 60x60; action rail y194.',states:'Returning save bypasses onboarding. Unreadable server save shows Save error.',motion:'Optional brief logo reveal, then still. Reduced motion skips reveal.'});
register('02','Choose your Pal',1,()=>{base('CHOOSE YOUR PAL');['merlion','otter','mynah'].forEach((s,i)=>{button(s,8+i*104,36,96,116,()=>{candidate=s;nameIndex=0;nav('02confirm')});rect(12+i*104,40,88,76,focus===i?C.terra:C.cream);sprite(s,24+i*104,42,64);if(focus===i)pointer(16+i*104,46);text(s,12+i*104,127)});center('A FRIEND FOR THE ROAD.',170);rail([['Back',()=>nav('01')]])},{focus:'Merlion > Otter > Mynah > Back',click:'Press a species to open a confirmation. Adoption is not saved yet.',back:'Returns to Hello.',layout:'Three 96x116 cards at x8/112/216, y36; 64x64 portraits; description y170.',states:'Confirmation offers Choose or Back; selection survives Back.',motion:'Focused sprite can tilt or blink; no animation required to perceive focus.'});
register('02confirm','Confirm companion',1,()=>{base('YOUR NEW PAL?');sprite(candidate,120,31,80);center(candidate,121);center('YOUR ADVENTURE AWAITS.',153);rail([['Choose',()=>nav('03')],['Back',()=>{nav('02');focus=['merlion','otter','mynah'].indexOf(candidate);render()}]])},{focus:'Choose > Back',click:'Choose proceeds to suggested naming.',back:'Returns to species selection.',layout:'80x80 portrait at120,31; two-button rail.',states:'No saved-game mutation before naming confirmation.',motion:'Single happy reaction.'});
register('03','A name for your Pal',1,()=>{base('NAME YOUR PAL');sprite(candidate,23,38,64);text(names[candidate][nameIndex],104,61);lines(['KEEP THIS SUGGESTED NAME','OR TRY ANOTHER ONE.'],16,123);rail([['Keep',adopt],['Reroll',()=>{nameIndex=(nameIndex+1)%3;render()}],['Back',()=>nav('02confirm')]])},{focus:'Keep > Reroll > Back',click:'Keep commits adoption and opens Home; Reroll cycles three preset names.',back:'Returns to adoption confirmation.',layout:'Portrait23,38 64x64; name104,61; 2 dialogue lines; 3 actions.',states:'Save failure preserves previous save and offers Retry/Back. Phone naming belongs to phase3.',motion:'Name changes immediately; short success reaction after saved response.'});
register('04','My BTO',1,()=>{base('MY BTO','LV '+(gallery?3:(saved.level||1)));room();frame(240,30,72,24,C.paper);symbol('coin',245,34);text(state().coins,269,35);rail([['Pal',()=>nav('04pal')],['Scan',()=>startScan()],['Menu',()=>nav('04menu')]])},{focus:'Pal > Scan > Menu',click:'Pal opens interaction; Scan opens scanner; Menu opens scrolling menu.',back:'Root screen; Settings remains available via Menu.',layout:'Header24px; room0,24 320x168; 56x56 sprite container147,112; actions y194.',states:'Local save status appears in Settings. Offline play keeps local profile; no pending reward grants.',motion:'Target 4-frame idle at4fps, gentle fan 2-frame loop. Prototype remains still.'});
register('04pal','A moment with your Pal',1,()=>{base('HELLO, '+state().name);room();frame(12,131,296,57,C.paper);lines(['READY TO NOTICE SOMETHING','NEW AROUND SINGAPORE?'],22,140);rail([['Explore',()=>startScan()],['Back',goHome]])},{focus:'Explore > Back',click:'Explore opens scanner.',back:'Home.',layout:'Dialogue12,131 296x57 over room; two-button rail.',states:'No hunger, decay or daily-care penalty.',motion:'A brief greeting reaction; no currency for repeat interactions.'});
register('04menu','Pocket menu',1,()=>{base('POCKET MENU');const entries=[['CultureDex','07'],['Quests','09'],['Shop','11'],['Inventory','12'],['Decorate','13'],['Profile','14'],['Rooms','15'],['Friends','16'],['Settings','18'],['Back','04']];const page=Math.floor(focus/4);entries.forEach(([label,to],i)=>{const y=36+(i%4)*36;if(Math.floor(i/4)===page)button(label,12,y,296,30,()=>nav(to));else hits.push({label,x:0,y:-100,w:0,h:0,fn:()=>nav(to)})});center((page+1)+' / 3',196);},{focus:'CultureDex > Quests > Shop > Inventory > Decorate > Profile > Rooms > Friends > Settings > Back',click:'Press opens the focused destination; rotation scrolls four visible rows.',back:'Explicit Back is the final row.',layout:'Four296x30 rows at y36/72/108/144. Footer y224.',states:'Phase2-4 screens show empty/unconnected states in live mode.',motion:'No sliding transition; immediate page change avoids expensive redraw effects.'});
register('05','Camera scanner',1,()=>{base('CULTURE SCAN');frame(16,36,288,145,C.ink);center('NOTICE SOMETHING LOCAL?',56,C.paper);center('OPEN CAMERA OR UPLOAD',96,C.paper);center('A PHOTO TO BEGIN.',120,C.paper);rail([['Camera',camera],['Upload',choosePhoto],['Back',goHome]])},{focus:'Camera > Upload > Back',click:'Camera requests browser camera only after press; Upload opens system photo picker.',back:'Home. Stops active camera tracks.',layout:'Preview16,36 288x145; rail194. Photo pixels are not filtered as pixel art.',states:'No assumption of Pi camera. Permission or insecure-context error offers Upload/Retry/Back.',motion:'No camera frames until permission granted. Actual preview capped near10fps.'});
register('05starting','Camera permission',1,()=>{base('OPENING CAMERA');sprite(state().species,122,40,76);lines(['WAITING FOR CAMERA','PERMISSION...'],42,133);rail([['Cancel',()=>nav('05')]])},{focus:'Cancel',click:'Cancels pending request in app; late media streams are immediately stopped.',back:'Cancel returns to scanner.',layout:'76x76 portrait; centered status; one action.',states:'Browser permission dialog owns approval. No success while permission unresolved.',motion:'Optional two-frame thinking loop.'});
register('05live','Camera ready',1,()=>{base('CAMERA READY');if(stream){const v=document.getElementById('camera');ctx.save();ctx.imageSmoothingEnabled=true;const r=Math.min(288/v.videoWidth,152/v.videoHeight);ctx.drawImage(v,16+(288-v.videoWidth*r)/2,32+(152-v.videoHeight*r)/2,v.videoWidth*r,v.videoHeight*r);ctx.restore()}else{frame(16,32,288,152,C.ink);center('LIVE CAMERA AREA',82,C.paper);center('DESIGN PLACEHOLDER',108,C.paper)}rail([['Capture',capture],['Back',()=>nav('05')]])},{focus:'Capture > Back',click:'Capture freezes the real frame for review; no AI request is made in this prototype.',back:'Scanner and release camera.',layout:'Image16,32 288x152; fit/letterbox with normal photo interpolation.',states:'Gallery is explicitly a camera placeholder, not a fake photograph.',motion:'Live preview10fps; stop tracks on exit and page hide.'});
register('05photo','Review your photo',1,()=>{base('REVIEW PHOTO');picture();rail([['Analyse',()=>nav('05ai')],['Retry',()=>{photo=null;nav('05')}],['Back',()=>nav('05')]])},{focus:'Analyse > Retry > Back',click:'Analyse currently shows integration-needed state. It never saves a discovery.',back:'Scanner. Captured photo remains memory-only until replaced or page closes.',layout:'Fit photograph in20,34 280x128; three-action rail.',states:'Oversized/unsupported files rejected before decode. No upload to external services.',motion:'Still photograph, no artificial pixel filter.'});
register('05ai','AI not connected',1,()=>{base('AI NOT CONNECTED');sprite(state().species,126,31,68);lines(['YOUR PHOTO IS READY.','RECOGNITION NEEDS SETUP.','NO REWARDS WERE ADDED.'],10,119);rail([['Back',()=>nav('05photo')]])},{focus:'Back',click:'Returns to photo review.',back:'Review photo.',layout:'Status portrait; three14px lines; Back.',states:'Historical disconnected design sample; real discovery uses the backend.',motion:'Static integration-needed state.'});
register('05error','Camera unavailable',1,()=>{base('CAMERA UNAVAILABLE');symbol('lock',151,47);lines([lastCameraError,'TRY A PHOTO FROM YOUR','PHONE OR LAPTOP INSTEAD.'],16,95);rail([['Upload',choosePhoto],['Retry',camera],['Back',()=>nav('05')]])},{focus:'Upload > Retry > Back',click:'Upload uses picker; Retry requests permission again if browser allows.',back:'Scanner.',layout:'Icon and three lines; three actions.',states:'Distinct permission denial/insecure context/device absence message.',motion:'No indefinite loading spinner.'});
register('06check','Check the AI suggestion',1,()=>{base('IS THIS RIGHT?');symbol('tissue',24,42);text('#001',110,40);text('CHOPE',110,65);text('CULTURE',110,86);lines(['A TISSUE CAN RESERVE','A SEAT AT A HAWKER TABLE.','CHECK THE CONTEXT FIRST.'],16,121);rail([['Yes',()=>nav('06')],['No',()=>nav('06wrong')],['Back',()=>nav('05')]])},{focus:'Yes > No > Back',click:'In future integrated flow, Yes confirms a vetted ID; No retakes/corrects without reward. Gallery only here.',back:'Scanner/review.',layout:'64x40 item illustration24,42; title110,40; 3 lines at121.',states:'Uncertain/no cultural match must not auto-save. Correction UI offers retry; no free-text requirement.',motion:'Small thinking reaction before decision, not a reward animation.'});
register('06wrong','Try a clearer view',1,()=>{base('LET US TRY AGAIN');lines(['NO DISCOVERY SAVED.','TRY ANOTHER ANGLE OR','INCLUDE MORE CONTEXT.'],16,66);rail([['Retry',()=>nav('05')],['Back',()=>nav('06check')]])},{focus:'Retry > Back',click:'Retry opens scanner without granting anything.',back:'AI suggestion.',layout:'Three short lines and two actions.',states:'Future alternative candidates may replace retry when available.',motion:'Calm reaction; no punitive failure animation.'});
register('06','Discovery saved',1,()=>{base('NEW DISCOVERY!','#001');symbol('tissue',22,46);text('CHOPE',111,43);text('CULTURE',111,66);frame(12,108,296,38,C.jade);symbol('xp',25,119);text('+20 XP',50,120);symbol('coin',177,119);text('+5',203,120);text('NEW QUEST: CHOPE SPOTTER',16,161);rail([['Dex',()=>nav('08')],['Quest',()=>nav('09')],['Home',goHome]])},{focus:'Dex > Quest > Home',click:'Dex opens saved detail; Quest opens board. This is a sample success state only.',back:'Home.',layout:'Item64x40, title; reward strip12,108 296x38; quest alert y161.',states:'Show only after atomic save+reward commit in future backend. Duplicate uses06duplicate.',motion:'Target brief sparkle and one coin tick; reduced motion uses static reward strip.'});
register('06duplicate','Already discovered',1,()=>{base('SEEN THIS BEFORE');symbol('tissue',127,42);lines(['CHOPE IS IN YOUR DEX.','NO EXTRA XP OR COINS.','TRY YOUR ACTIVE QUEST.'],16,111);rail([['Dex',()=>nav('08')],['Quest',()=>nav('09')],['Home',goHome]])},{focus:'Dex > Quest > Home',click:'Open existing entry or quest; no reward transaction.',back:'Home.',layout:'Item art and three lines.',states:'Duplicate recognition must not create another reward event or overwrite original photo silently.',motion:'Gentle acknowledgement, no celebration.'});
register('07','CultureDex',1,()=>{base('CULTUREDEX',gallery?'1/5':'0/5');if(!gallery){lines(['YOUR STORY STARTS HERE.','SCAN A LOCAL DISCOVERY','TO FILL YOUR CULTUREDEX.'],16,61);rail([['Scan',()=>startScan()],['Back',()=>nav('04menu')]]);return}row('#001 CHOPE CULTURE',36,()=>nav('08'));row('#002 ???',72,()=>nav('08locked'));row('#003 ???',108,()=>nav('08locked'));row('#004 ???',144,()=>nav('08locked'));rail([['Next',()=>nav('07next')],['Back',()=>nav('04menu')]])},{focus:'Visible entries in numeric order > Next > Back',click:'Open entry; Next shows next catalogue page. Empty live state offers Scan.',back:'Pocket menu.',layout:'Four rows296x30 at36/72/108/144; 2 action buttons.',states:'Unknowns remain numbered with???; empty Dex uses invitation, not an empty grid.',motion:'Immediate focus move; no list bounce.'});
register('07next','CultureDex next page',1,()=>{base('CULTUREDEX','1/5');row('#005 ???',36,()=>nav('08locked'));rail([['Prev',()=>nav('07')],['Back',()=>nav('04menu')]])},{focus:'#005 > Prev > Back',click:'Unknown entry opens locked page.',back:'Pocket menu.',layout:'One row plus Prev/Back.',states:'Pages never contain fake unlocked entries.',motion:'None.'});
register('08','CultureDex story',1,()=>{base('#001 CHOPE','1/3');symbol('tissue',24,42);text('EVERYDAY LIFE',104,50);lines(['A TISSUE PACKET MAY MEAN','THIS SEAT IS RESERVED.','CHECK BEFORE YOU SIT.'],16,111);rail([['Next',()=>nav('08photo')],['Back',()=>nav('07')]])},{focus:'Next > Back',click:'Next opens Photo, then Quest metadata, then Story.',back:'Catalogue with previous focus restored in future implementation.',layout:'Title24px; illustration64x40; 3 lines; two actions.',states:'Explanation is curated example text. Actual approved recognition supplies entry ID.',motion:'Static reading page.'});
register('08photo','CultureDex photograph',1,()=>{base('#001 PHOTO','2/3');placeholderPhoto(20,34,280,108);text('11 OCT 2026 12:04 SGT',16,161);rail([['Next',()=>nav('08quest')],['Back',()=>nav('07')]])},{focus:'Next > Back',click:'Next opens quest metadata.',back:'Catalogue.',layout:'Photo20,34 280x108; timestamp16,161; two actions.',states:'Placeholder is explicitly not an actual scan. Real photo must display the captured timestamp in Asia/Singapore.',motion:'No pixel filter applied to photos.'});
register('08quest','CultureDex quest',1,()=>{base('#001 QUEST','3/3');lines(['CHOPE SPOTTER','STATUS: ACTIVE','DISCOVERY XP: 20','CATEGORY: EVERYDAY LIFE'],16,47);rail([['Story',()=>nav('08')],['Quest',()=>nav('10')],['Back',()=>nav('07')]])},{focus:'Story > Quest > Back',click:'Open story or associated quest detail.',back:'Catalogue.',layout:'Four metadata lines at47/69/91/113; 3 actions.',states:'XP shown belongs to discovery event; quest reward remains unclaimed.',motion:'None.'});
register('08locked','Unknown CultureDex entry',1,()=>{base('UNDISCOVERED');symbol('lock',150,48);lines(['A LITTLE MYSTERY FOR NOW.','KEEP EXPLORING TO REVEAL','THIS CULTUREDEX ENTRY.'],16,97);rail([['Scan',()=>startScan()],['Back',()=>nav('07')]])},{focus:'Scan > Back',click:'Scan opens camera selector.',back:'Catalogue.',layout:'Lock icon and three lines.',states:'Do not reveal private or undiscovered details.',motion:'Optional subtle question-mark idle.'});
register('09','Quest board',1,()=>{base('QUEST BOARD');if(gallery){row('ACTIVE: CHOPE SPOTTER',36,()=>nav('10'));row('COMPLETED QUESTS',78,()=>nav('09done'));row('LOCKED QUESTS',120,()=>nav('09locked'));rail([['Back',()=>nav('04menu')]])}else{lines(['NO QUESTS JUST YET.','DISCOVER LOCAL CULTURE','TO FIND YOUR FIRST QUEST.'],16,63);rail([['Scan',()=>startScan()],['Back',()=>nav('04menu')]])}},{focus:'Active quest > Completed > Locked > Back; empty: Scan > Back',click:'Open quest detail or selected status list.',back:'Pocket menu.',layout:'Three296x30 rows at36/78/120; Back below.',states:'Empty real save has no invented quest. Completed entry is non-claimable.',motion:'New quest can receive a brief marker, not constant flashing.'});
register('09done','Completed quest',1,()=>{base('COMPLETED');lines(['KOPI EXPLORER','DONE - REWARD CLAIMED','+30 XP / +10 COINS','SAMPLE COMPLETED QUEST'],16,53);rail([['Back',()=>nav('09')]])},{focus:'Back',click:'No claim action for completed quest.',back:'Quest board.',layout:'Four lines with claim status.',states:'Sample only; no additional reward on revisit.',motion:'No repeated celebration.'});
register('09locked','Locked quest',1,()=>{base('NOT QUITE YET');symbol('lock',150,43);lines(['HAWKER EXPLORER','DISCOVER A HAWKER CENTRE','TO UNLOCK THIS QUEST.'],16,98);rail([['Back',()=>nav('09')]])},{focus:'Back',click:'Read prerequisite.',back:'Quest board.',layout:'Lock and three lines.',states:'Prerequisite explicit; no selectable Verify.',motion:'None.'});
register('10','Honesty-based quest',1,()=>{base('CHOPE QUEST');lines(['NOTICE A RESERVED SEAT.','LEAVE BELONGINGS ALONE.','DID YOU COMPLETE IT?'],16,39);row('Yes, I did it',116,()=>nav('10pass'));row('Not yet',153,()=>nav('10fail'));rail([['Back',()=>nav('09')]])},{});
register('10wait','Saving quest answer',1,()=>{base('SAVING ANSWER');lines(['SAMPLE PENDING SAVE.','NO REWARD CONFIRMED.'],16,66);rail([['Back',()=>nav('10')]])},{});
register('10pass','Self-reported completion',1,()=>{base('QUEST COMPLETE!');lines(['SAMPLE: SELF-REPORTED','+25 XP / +10 COINS','NO REAL REWARD GRANTED.'],16,56);rail([['Done',()=>nav('09done')],['Home',goHome]])},{});
register('10fail','Quest still active',1,()=>{base('TAKE YOUR TIME');lines(['YOUR QUEST STAYS ACTIVE.','NO PENALTY.','COME BACK WHEN READY.'],16,56);rail([['Back',()=>nav('10')]])},{});
register('11','Kopi shop',2,()=>{base('KOPI SHOP',String(state().coins));symbol('plant',42,56);text('WINDOW PLANT',102,44);text('25 COINS',102,74);text(gallery?'YOU CAN AFFORD THIS.':'NEED 25 MORE COINS.',16,141);rail([['Buy',()=>nav(gallery?'11confirm':'11poor')],['Next',()=>nav('11unavailable')],['Back',()=>nav('04menu')]])},{focus:'Buy > Next > Back',click:'Buy opens confirmation only if affordable; actual purchase is not enabled in prototype.',back:'Pocket menu.',layout:'Item art40x60; label/price right; affordability line141.',states:'Insufficient coins and unavailable stock have separate states. Categories can reuse paged lists.',motion:'Focused item can rise1px; never jiggle disabled actions.'});
register('11confirm','Confirm purchase',2,()=>{base('BUY WINDOW PLANT?');symbol('plant',141,40);lines(['PRICE: 25 COINS','BALANCE AFTER: 55','OWNED AFTER PURCHASE: 1'],16,111);rail([['Confirm',()=>unavailable('Shop integration')],['Back',()=>nav('11')]])},{focus:'Confirm > Back',click:'Prototype reports not connected; future backend atomically debits25 and adds item.',back:'Shop, no purchase.',layout:'Item; price/balance/quantity; two actions.',states:'Recheck balance/owned state on server; reject duplicate transaction IDs.',motion:'Purchase reaction only after committed response.'});
register('11poor','Insufficient coins',2,()=>{base('SAVE A FEW MORE');lines(['WINDOW PLANT: 25 COINS','YOUR COINS: 0','DISCOVER CULTURE TO EARN','MORE KOPI COINS.'],16,49);rail([['Explore',()=>startScan()],['Back',()=>nav('11')]])},{focus:'Explore > Back',click:'Explore opens scanner; no negative balance.',back:'Shop.',layout:'Four lines plus two actions.',states:'Price and gap visible before confirmation.',motion:'None.'});
register('11unavailable','Shop item unavailable',2,()=>{base('KOPI SHOP');symbol('lock',150,43);lines(['MINI MRT DISPLAY','NOT AVAILABLE YET.','CHECK BACK ANOTHER TIME.'],16,97);rail([['Prev',()=>nav('11')],['Back',()=>nav('04menu')]])},{focus:'Prev > Back',click:'Browse available item or leave.',back:'Pocket menu.',layout:'Lock and three lines.',states:'No active Buy control when unavailable.',motion:'None.'});
register('12','Inventory',2,()=>{base('YOUR INVENTORY');if(gallery){row('FURNITURE: WINDOW PLANT',40,()=>nav('13'));row('ACCESSORIES: NONE',86,()=>unavailable('No accessories'));row('SPECIAL ITEMS: NONE',132,()=>unavailable('No special items'));rail([['Back',()=>nav('04menu')]])}else{lines(['A LITTLE ROOM TO GROW.','YOUR INVENTORY IS EMPTY.','FIND ITEMS IN THE SHOP.'],16,64);rail([['Shop',()=>nav('11')],['Back',()=>nav('04menu')]])}},{focus:'Furniture > Accessories > Special > Back; empty: Shop > Back',click:'Owned furniture opens placement. Empty categories give informative state.',back:'Pocket menu.',layout:'Three category rows, then Back.',states:'Show Owned/Placed/Equipped distinctions in future item list; no duplication.',motion:'None.'});
register('13','Decorate by slots',2,()=>{base('DECORATE');room(false);frame(238,86,62,64,C.paper,C.terra);symbol('plant',252,90);frame(12,151,214,36,C.paper);text('SLOT 1: WINDOW',23,163);rail([['Place',()=>nav('13confirm')],['Next',()=>nav('13slot')],['Back',()=>nav('12')]])},{focus:'Place > Next > Back',click:'Next cycles compatible fixed slots; Place opens confirmation, never drag-and-drop.',back:'Inventory.',layout:'Room;62x64 highlight at238,86;slot label12,151 214x36.',states:'Sample window plant only; live save has no item and cannot commit placement.',motion:'Solid slot outline; target brief before/after swap after save.'});
register('13slot','Alternate furniture slot',2,()=>{base('DECORATE');room(false);frame(14,78,48,64,C.paper,C.terra);symbol('plant',20,84);frame(12,151,214,36,C.paper);text('SLOT 2: DOOR',23,163);rail([['Place',()=>nav('13confirm')],['Next',()=>nav('13')],['Back',()=>nav('12')]])},{focus:'Place > Next > Back',click:'Select next compatible placement slot.',back:'Inventory.',layout:'48x64 highlight14,78; label below.',states:'Production save references stable slot IDs, not browser coordinates.',motion:'None.'});
register('13confirm','Confirm placement',2,()=>{base('PLACE WINDOW PLANT?');room(false);frame(16,120,288,68,C.paper);lines(['PLACE IN SELECTED SLOT?','YOUR ROOM SAVES LOCALLY.'],26,135);rail([['Save',()=>unavailable('Placement integration')],['Back',()=>nav('13')]])},{focus:'Save > Back',click:'Prototype shows integration needed. Future save validates ownership and slot.',back:'Placement.',layout:'Confirmation overlay16,120 288x68.',states:'Save failure must preserve original room and retryable edit.',motion:'Swap preview only; commit animation follows successful save.'});
register('14','Pal profile',1,()=>{base('PAL PROFILE');sprite(state().species,16,35,70);text(state().name,106,40);text(state().species,106,64);text('LEVEL '+(gallery?3:(saved.level||1)),106,88);frame(16,120,288,12,C.cream);rect(18,122,gallery?112:Math.floor((saved.xp%50)/50*284),8,C.jade);text('XP '+state().xp+' / '+(gallery?'200':String((saved.level||1)*50)),16,143);text('DISCOVERIES: '+state().discoveries.length,16,169);rail([['More',()=>nav('14more')],['Back',()=>nav('04menu')]])},{focus:'More > Back',click:'More shows accessories/personality/achievements.',back:'Pocket menu.',layout:'70x70 portrait, labels;288x12 XP bar; 2 metadata lines.',states:'Live level1/0XP; example level3 uses140/200. XP never spent.',motion:'Idle portrait; progress animates only on actual earned XP.'});
register('14more','Profile details',2,()=>{base('ABOUT YOUR PAL','2/2');lines(['CURIOUS AND CHEEKY','ACCESSORY: NONE','ACHIEVEMENTS: NONE','NO DAILY CARE REQUIRED.'],10,44);rail([['Back',()=>nav('14')]])},{focus:'Back',click:'Read profile details.',back:'Profile.',layout:'Four14px lines.',states:'Personality copy will vary by species. No invented unlocked achievements.',motion:'None.'});
register('15','Room expansion',2,()=>{base('YOUR BTO ROOMS');row('LIVING ROOM - OPEN',36,goHome);row('BEDROOM - LEVEL 5',78,()=>nav('15locked'));row('KITCHEN - LEVEL 8',120,()=>nav('15locked'));rail([['Back',()=>nav('04menu')]])},{focus:'Living room > Bedroom > Kitchen > Back',click:'Enter unlocked room; locked room explains milestone.',back:'Pocket menu.',layout:'Three room rows; short level requirement in each.',states:'Thresholds5/8 are proposed balancing, not committed economy. Study/balcony future pages.',motion:'Room transition as brief fade optional; reduced motion immediate.'});
register('15locked','Room milestone',2,()=>{base('MORE ROOM TO GROW');symbol('lock',151,42);lines(['EXPLORE TO LEVEL UP.','ROOMS UNLOCK WITH XP.','YOUR XP IS NEVER SPENT.'],10,96);rail([['Back',()=>nav('15')]])},{focus:'Back',click:'Return to room list.',back:'Rooms.',layout:'Lock and three lines.',states:'Use actual selected room requirement in production.',motion:'None.'});
register('16','Friends',4,()=>{base('FRIENDS');if(gallery){row('VISIT: KAYA',36,()=>nav('17'));row('REQUESTS: 1',78,()=>nav('16request'));row('ADD A FRIEND',120,()=>nav('16pair'));rail([['Back',()=>nav('04menu')]])}else{lines(['FRIENDS COME IN PHASE 4.','PAIRING AND SHARING','ARE NOT CONNECTED YET.'],16,63);rail([['Back',()=>nav('04menu')]])}},{focus:'Friend > Requests > Add > Back; live: Back',click:'Gallery previews asynchronous social UI. Live has no social calls.',back:'Pocket menu.',layout:'Three list rows or explicit unconnected state.',states:'Future friend rooms are private by default; authorised friends only.',motion:'Small status marker; no live-presence assumption.'});
register('16pair','Add friend by phone',4,()=>{base('ADD A FRIEND');frame(22,40,88,88,C.cream);text('QR',54,66);text('AREA',42,90);lines(['PAIR ON PHONE','TO ADD FRIENDS.'],128,53);text('PAIRING NOT CONNECTED.',16,148);rail([['Back',()=>nav('16')]])},{focus:'Back',click:'Production replaces labelled placeholder with actual short-lived server QR.',back:'Friends.',layout:'88x88 QR region plus2 lines. Real QR may need larger region after device tests.',states:'Never display decorative QR as usable code; no unauthorised room URL.',motion:'Pairing expiry shows Refresh, no polling when not paired.'});
register('16request','Friend request',4,()=>{base('FRIEND REQUEST');sprite('otter',120,36,80);center('KAYA WANTS TO VISIT.',136);rail([['Accept',()=>unavailable('Social integration')],['Decline',()=>unavailable('Social integration')],['Back',()=>nav('16')]])},{focus:'Accept > Decline > Back',click:'Future server-backed consent action; prototype does not change social state.',back:'Friends.',layout:'Portrait and single identity line.',states:'Show verified account identity in production, not only pet name.',motion:'No reward for accepting.'});
register('17','Visit a friend',4,()=>{base('KAYA\'S BTO','VISIT');room(false);sprite('otter',147,109,62);frame(12,153,296,34,C.paper);text('KAYA SAYS HELLO!',25,163);rail([['Greet',()=>nav('17greet')],['Leave',()=>nav('16')]])},{focus:'Greet > Leave',click:'Greet opens preset guestbook choices; no room editing.',back:'Leave returns to Friends.',layout:'Friend room snapshot; greeting overlay12,153 296x34.',states:'Sample house only. Real snapshot requires permission and excludes CultureDex scan photos.',motion:'Friend sprite can idle locally; does not imply real-time presence.'});
register('17greet','Leave a greeting',4,()=>{base('LEAVE A GREETING');row('LOVE YOUR LITTLE HOME!',38,()=>unavailable('Guestbook integration'));row('THANKS FOR HAVING ME!',82,()=>unavailable('Guestbook integration'));row('SEE YOU AROUND!',126,()=>unavailable('Guestbook integration'));rail([['Back',()=>nav('17')]])},{focus:'Three preset greetings > Back',click:'Future sends selected sticker/message once with confirmation. No unrestricted chat.',back:'Friend visit.',layout:'Three296x30 rows and Back.',states:'Sending must show pending, sent or failed. Prototype sends nothing.',motion:'One sticker pop only after successful send.'});
register('18','Settings and save',1,()=>{base('SETTINGS');row('SAVE AND CONNECTION',34,()=>nav('18status'));row('SOUND: '+(state().sound?'ON':'OFF'),70,sound);row('PAIRING AND PRIVACY',106,()=>nav('18pair'));row('ROTARY HELP',142,()=>nav('help'));rail([['Back',()=>nav('04menu')]])},{focus:'Save/status > Sound > Pairing/privacy > Help > Back',click:'Sound saves local preference. Other rows open details.',back:'Pocket menu.',layout:'Four296x30 rows; Back rail.',states:'Browser cannot reliably read Wi-Fi SSID. OS-managed network info shown explicitly.',motion:'Optional click sound only when enabled.'});
register('18status','Save and connection',1,()=>{base('SAVE AND CONNECTION');lines([backend?'SAVE: LOCAL SERVER':'SAVE: THIS BROWSER','CLOUD SYNC: NOT CONNECTED','NETWORK: '+(navigator.onLine?'BROWSER ONLINE':'OFFLINE'),'WI-FI: MANAGED IN OS'],16,47);rail([['Back',()=>nav('18')]])},{focus:'Back',click:'Read actual save adapter and browser network signal.',back:'Settings.',layout:'Four status lines.',states:'Browser online is not proof AI/cloud reachable. Remote unavailable never reported synced.',motion:'No perpetual sync indicator.'});
register('18pair','Pairing and privacy',3,()=>{base('PAIRING AND PRIVACY');lines(['PAIRING: NOT CONNECTED','PHOTOS STAY HERE.','NO PUBLIC ROOM SHARING','PHONE ACCOUNT SYNC: LATER'],16,46);rail([['Back',()=>nav('18')]])},{focus:'Back',click:'Informational until authenticated cloud service exists.',back:'Settings.',layout:'Four policy/status lines.',states:'Prototype photos remain memory only; no third-party upload. LAN access is not authenticated cloud pairing.',motion:'None.'});
register('18offline','Offline',3,()=>{base('YOU ARE OFFLINE');lines(['YOUR LOCAL SAVE IS SAFE.','EXPLORE YOUR BTO AND DEX.','SCANS NEED CONNECTION.','CLOUD SYNC IS NOT SET UP.'],16,44);rail([['Home',goHome],['Back',()=>nav('18')]])},{focus:'Home > Back',click:'Continue local experience.',back:'Settings.',layout:'Four lines.',states:'Future offline actions need durable operation IDs; no reward before validation.',motion:'Static offline icon, no error flashing.'});
register('18pending','Sync pending',3,()=>{base('SYNC PENDING');lines(['2 LOCAL CHANGES WAITING.','YOUR LOCAL COPY IS SAVED.','RETRY WHEN CONNECTED.','SAMPLE FUTURE SYNC STATE'],16,46);rail([['Retry',()=>unavailable('Sync integration')],['Back',()=>nav('18')]])},{focus:'Retry > Back',click:'Future retries operation queue; not implemented in this prototype.',back:'Settings.',layout:'Four status lines.',states:'Do not upload capture photos by default. Server deduplicates operation/reward IDs.',motion:'Brief spinner only during real retry.'});
register('18lost','Connection lost',3,()=>{base('CONNECTION LOST');lines(['REQUEST NOT FINISHED.','NO REWARD IS CONFIRMED.','RECONNECT TO CHECK STATUS.'],10,57);rail([['Retry',()=>unavailable('Status reconciliation')],['Back',()=>nav('18')]])},{focus:'Retry > Back',click:'Future checks request operation ID before repeating any mutation.',back:'Settings.',layout:'Three lines.',states:'Ambiguous completion must not be retried as a fresh reward grant.',motion:'Stop analysing animation when network is lost.'});
register('saveerror','Save could not finish',1,()=>{base('SAVE NEEDS ATTENTION');lines(['YOUR LAST SAVE IS KEPT.','CHECK DEVICE STORAGE','AND SERVER CONNECTION.','TRY YOUR ACTION AGAIN.'],16,47);rail([['Retry',()=>loadSaved()],['Back',()=>nav(saved.adopted?'04':'01')]])},{focus:'Retry > Back',click:'Returns to original profile/save action; never clears corrupt file automatically.',back:'Home or Hello according to adoption state.',layout:'Four lines and two actions.',states:'Corrupt server save results503. User must restore backup externally.',motion:'None.'});
register('help','Rotary help',1,()=>{base('ONE KNOB. LET US GO.');lines(['TURN TO MOVE THE POINTER.','PRESS TO CHOOSE.','FIND BACK TO GO BACK.','NO LONG PRESS NEEDED.'],16,46);rail([['Back',()=>nav(saved.adopted?'18':'01')]])},{focus:'Back',click:'Return to Settings or Hello.',back:'Context return.',layout:'Four short14px instructions.',states:'Keyboard and touch preserve the same ordered focus model.',motion:'Optional illustrated pointer move, not required to understand controls.'});
register('bootback','Device options',1,()=>{base('DEVICE OPTIONS');lines(['YOUR PAL IS WAITING.','PRESS START WHEN READY.'],16,67);rail([['Start',()=>nav('02')],['Back',()=>nav('01')]])},{focus:'Start > Back',click:'Start continues onboarding.',back:'Hello.',layout:'Two lines and two actions.',states:'No browser-exit or OS-shutdown action is simulated.',motion:'None.'});
register('blocked','Feature not connected',2,()=>{base('NOT CONNECTED YET');lines(['FEATURE PREVIEW ONLY.','NO CHANGES WERE SAVED.','RETURN TO YOUR HOME.'],10,63);rail([['Home',goHome],['Back',()=>nav('04menu')]])},{focus:'Home > Back',click:'Return safely without mutating sample or live state.',back:'Pocket menu.',layout:'Three lines, two actions.',states:'Used for deferred commerce, decoration and social mutations.',motion:'None.'});

// Live projections use the existing culture catalogue and progress, never gallery data.
function liveView(id,draw){const sampleDraw=screens[id].draw;screens[id].draw=()=>gallery?sampleDraw():draw()}
function wrapWords(value,width=24){const result=[];let line='';for(const word of String(value).toUpperCase().split(/\s+/).flatMap(w=>w.match(new RegExp('.{1,'+width+'}','g'))||[])){if((line+' '+word).trim().length>width&&line){result.push(line);line=''}line+=(line?' ':'')+word}if(line)result.push(line);return result}
function readPage(title,body,backTo,extra=[]){
 browserBody=body;
 const all=wrapWords(body),pages=Math.max(1,Math.ceil(all.length/6));detailPage%=pages;
 base(title.slice(0,20),pages>1?(detailPage+1)+'/'+pages:'');lines(all.slice(detailPage*6,detailPage*6+6),16,38);
 rail([...(pages>1?[['Next',()=>{detailPage=(detailPage+1)%pages;render()}]]:[]),...extra,['Back',()=>nav(backTo)]]);
}
function openEntry(item){selectedEntry=item;detailPage=0;nav(saved.discoveries.includes(item.id)?'live-story':'08locked')}
function pagedRows(title,entries,page,setPage,backTo){
 const pages=Math.max(1,Math.ceil(entries.length/4));page%=pages;base(title,(page+1)+'/'+pages);
 entries.slice(page*4,page*4+4).forEach(([label,fn],i)=>row(label,36+i*36,fn));
 rail([['Prev',()=>{setPage((page+pages-1)%pages);focus=0;render()}],['Next',()=>{setPage((page+1)%pages);focus=0;render()}],['Back',()=>nav(backTo)]]);
}
liveView('04menu',()=>{
 const entries=[['CultureDex','07'],['Quests','09'],['Shop','11'],['Inventory','12'],['Decorate','13'],['Profile','14'],['Rooms','15'],['Friends','16'],['Settings','18']];
 pagedRows('POCKET MENU',entries.map(([label,id])=>[label,()=>nav(id)]),menuPage,p=>menuPage=p,'04');
});
liveView('07',()=>{
 if(!saved.discoveries.length){base('CULTUREDEX','0/'+catalogue.length);lines(['YOUR STORY STARTS HERE.','SCAN A LOCAL DISCOVERY','TO FILL YOUR CULTUREDEX.'],16,61);rail([['Scan',()=>startScan()],['Back',()=>nav('04menu')]]);return}
 const entries=catalogue.map((item,i)=>['#'+String(i+1).padStart(3,'0')+' '+(saved.discoveries.includes(item.id)?item.title.toUpperCase():'???'),()=>openEntry(item)]);
 pagedRows('CULTUREDEX',entries,dexPage,p=>dexPage=p,'04menu');
});
register('live-story','Saved CultureDex story',1,()=>{
 const item=selectedEntry;if(!item){nav('07');return}
 readPage(item.title,item.fact,'07',[['Info',()=>nav('live-info')]]);
},{});
register('live-info','Saved discovery details',1,()=>{
 const item=selectedEntry,record=saved.log?.[item?.id];if(!record){nav('07');return}
 base('DISCOVERY RECORD');
 const stamp=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Singapore',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(record.time*1000)).replace(',','');
 lines([stamp+' SGT','CULTURE XP: '+(record.xp||10),record.photo_url?'PHOTO SAVED ON DEVICE.':'LEGACY: NO PHOTO SAVED.','KOPI COINS: '+(record.coins||0)],10,48);
 if(record.photo_url)button('Photo',112,157,96,28,()=>showStoredPhoto(record.photo_url));
 rail([['Story',()=>nav('live-story')],['Quest',()=>{detailPage=0;nav('live-quest')}],['Back',()=>nav('07')]]);
},{});
liveView('09',()=>{
 const entries=catalogue.filter(c=>saved.discoveries.includes(c.id)).map(item=>{
  const status=(saved.completed||[]).includes(item.id)?'DONE':saved.active===item.id?'ACTIVE':'OPEN';
  return [status+': '+item.title.slice(0,16),()=>{selectedEntry=item;detailPage=0;nav('live-quest')}];
 });
 if(entries.length){pagedRows('QUEST BOARD',entries,questPage,p=>questPage=p,'04menu');return}
 base('QUEST BOARD');lines(['NO QUESTS JUST YET.','DISCOVER LOCAL CULTURE','TO FIND YOUR FIRST QUEST.'],16,63);rail([['Scan',()=>startScan()],['Back',()=>nav('04menu')]]);
});
register('live-quest','Saved culture quest',1,()=>{
 const item=selectedEntry;if(!item){nav('09');return}
 const done=(saved.completed||[]).includes(item.id);
 gameRead(done?'QUEST COMPLETED':'CULTURE QUEST',item.quest+(done?' Completed. Reward already claimed.':' Reward: 25 XP and 10 Kopi Coins. Answer when you are ready. No proof needed.'),[...(done?[]:[['Answer',()=>nav('live-quest-answer')]]),['Back',()=>nav('09')]]);
},{});
register('live-quest-answer','Honesty-based quest answer',1,()=>{
 if(!selectedEntry){nav('09');return}
 base('YOUR QUEST');lines(['DID YOU COMPLETE','THIS QUEST?'],16,36);
 row('Yes, I did it',94,()=>answerQuest(true));
 row('Not yet',136,()=>answerQuest(false));
 rail([['Back',()=>nav('live-quest')]]);
},{});

liveView('14more',()=>{base('ABOUT YOUR PAL');const personality={merlion:'CURIOUS AND BRAVE',otter:'PLAYFUL AND SOCIABLE',mynah:'BRIGHT AND CHATTY'};lines([personality[saved.species],'ACCESSORY: NONE','ACHIEVEMENTS: NONE','NO DAILY CARE REQUIRED.'],10,44);rail([['Back',()=>nav('14')]])});

// Real game requests. Gallery never reaches these paths. Only the server can
// change progress; pending IDs survive reload so lost responses can be checked.
let photoPayload=null,activeRequest=null,gameResult=null,gameMessage='',gameBusy=false,requestView=0,correctionPage=0,storedPhoto=null;
const pendingKey='sgpal-pending-operation-v1';
const newId=()=>crypto.randomUUID ? crypto.randomUUID() : '10000000-1000-4000-8000-100000000000'.replace(/[018]/g,c=>(Number(c)^crypto.getRandomValues(new Uint8Array(1))[0]&15>>Number(c)/4).toString(16));
function startScan(){photo=null;photoPayload=null;activeRequest=null;nav('05')}
function rememberRequest(){try{localStorage.setItem(pendingKey,JSON.stringify({id:activeRequest.body.operation_id,path:activeRequest.path,...(['quests/answer','shop/purchase','room/place'].includes(activeRequest.path)?{body:activeRequest.body}:{})}))}catch(_){}}
function forgetRequest(){try{localStorage.removeItem(pendingKey)}catch(_){}}
function acceptResult(result){
 if(result.state)saved=result.state;gameResult=result;
 if(result.kind==='verify'&&!['verified','duplicate'].includes(result.status)){forgetRequest();selectedEntry=catalogue.find(c=>c.id===result.quest_id);nav('live-quest');return}
 if(result.culture_id)selectedEntry=catalogue.find(c=>c.id===result.culture_id)||null;
 detailPage=0;
 if(result.status==='pending'){gameMessage='Still checking. No reward is confirmed. Check status shortly.';nav('live-request-error');return}
 if(result.status==='candidate'){
  if(!photo&&result.photo_url){const im=new Image();im.onload=()=>{if(gameResult?.operation_id===result.operation_id){photo=im;if(current==='05photo')render()}};im.src=result.photo_url}
  nav('live-candidate');return
 }
 if(result.status==='failed'){gameMessage=result.message||'Request failed. No rewards added.';nav('live-request-error');return}
 forgetRequest();
 if(['purchase','place'].includes(result.kind)){selectedDecor=shopItems.find(i=>i.id===result.item_id);nav('live-commerce-result');return}
 if(result.status==='not_done'){nav('live-quest');return}
 if(['confirmed','verified','completed','duplicate'].includes(result.status))nav('live-reward');
 else nav('live-uncertain');
}
async function runGameRequest(){
 if(gallery||gameBusy)return;if(!backend){unavailable('Run the FastAPI server');return}
 gameBusy=true;const token=++requestView;nav('live-working');rememberRequest();
 try{const result=await api(activeRequest.path,activeRequest.body);if(token===requestView&&!gallery)acceptResult(result);else if(result.state){saved=result.state;render()}}
 catch(e){if(token===requestView&&!gallery){gameMessage=e.message;detailPage=0;nav('live-request-error')}}
 finally{gameBusy=false}
}
async function analysePhoto(){
 if(gameBusy)return;
 if(!photoPayload&&gameResult?.status==='candidate'){nav('live-candidate');return}
 if(!photoPayload){gameMessage='Choose a photo before analysis.';nav('live-request-error');return}
 activeRequest={path:'scan',body:{operation_id:newId(),image:photoPayload}};
 await runGameRequest();
}
async function retryRequest(){
 if(activeRequest){await runGameRequest();return}
 let pending;try{pending=JSON.parse(localStorage.getItem(pendingKey))}catch(_){}
 if(!pending){startScan();return}
 activeRequest=['quests/answer','shop/purchase','room/place'].includes(pending.path)&&pending.body?{path:pending.path,body:pending.body}:{path:'retry',body:{operation_id:pending.id}};await runGameRequest();
}
async function checkRequest(){
 if(gameBusy)return;let pending;
 try{pending=activeRequest?{id:activeRequest.body.operation_id,path:activeRequest.path}:JSON.parse(localStorage.getItem(pendingKey))}catch(_){}
 if(!pending){nav('05');return}
 try{const result=await api('operations/'+pending.id);if(result.status==='pending'&&result.retryable&&activeRequest){await runGameRequest();return}acceptResult(result)}
 catch(e){gameMessage=e.message;detailPage=0;nav('live-request-error')}
}
async function confirmDiscovery(){
 if(gallery||gameBusy||!gameResult)return;
 activeRequest={path:'confirm',body:{operation_id:gameResult.operation_id}};await runGameRequest();
}
async function correctTo(item){
 if(gallery||gameBusy)return;
 activeRequest={path:'correct',body:{operation_id:newId(),source_operation_id:gameResult.operation_id,culture_id:item.id}};
 await runGameRequest();
}
async function answerQuest(done){
 if(gallery||gameBusy||!selectedEntry)return;
 activeRequest={path:'quests/answer',body:{operation_id:newId(),culture_id:selectedEntry.id,done}};
 await runGameRequest();
}
function closeRequest(){requestView++;nav('04')}
async function resumeRequest(){
 if(!backend)return false;
 let pending;try{pending=JSON.parse(localStorage.getItem(pendingKey))}catch(_){}
 if(!pending)return false;
 try{const result=await api('operations/'+pending.id);acceptResult(result);return true}
 catch(e){if(e.status===404&&!['quests/answer','shop/purchase','room/place'].includes(pending.path)){forgetRequest();return false}gameMessage=e.message;nav('live-request-error');return true}
}
function showStoredPhoto(url){
 storedPhoto=null;nav('live-photo');const im=new Image();
 im.onload=()=>{storedPhoto=im;if(current==='live-photo')render()};
 im.onerror=()=>{storedPhoto=null;gameMessage='Photo could not load. Check the server and retry.';if(current==='live-photo')render()};
 im.src=url;
}
function photoImage(im){ctx.save();ctx.imageSmoothingEnabled=true;const ratio=Math.min(280/im.width,128/im.height);const w=Math.round(im.width*ratio),h=Math.round(im.height*ratio);ctx.drawImage(im,20+Math.floor((280-w)/2),32+Math.floor((128-h)/2),w,h);ctx.restore()}
function gameRead(title,message,actions){
 browserBody=message;
 const all=wrapWords(message),count=Math.max(1,Math.ceil(all.length/6));detailPage%=count;
 base(title.slice(0,20),count>1?(detailPage+1)+'/'+count:'');lines(all.slice(detailPage*6,detailPage*6+6),16,37);
 // Up to 3 actions fit the approved bottom rail. Text paging has a compact,
 // separately focusable control above it when needed.
 if(count>1)button('Read',222,166,90,25,()=>{detailPage=(detailPage+1)%count;render()});
 rail(actions);
}
liveView('04',()=>{
 base('MY BTO','LV '+(saved.level||1));room();frame(240,30,72,24,C.paper);symbol('coin',245,34);text(saved.coins,269,35);
 rail([['Pal',()=>nav('04pal')],['Scan',()=>startScan()],['Menu',()=>nav('04menu')]]);
 try{if(localStorage.getItem(pendingKey))button('Status',8,30,96,24,checkRequest)}catch(_){}
});
liveView('05',()=>{
 base('CULTURE SCAN');frame(16,36,288,145,C.ink);
 center('OPEN CAMERA OR UPLOAD',56,C.paper);center('REVIEW BEFORE SENDING',96,C.paper);center('TO OPENAI FOR CHECKING.',120,C.paper);
 rail([['Camera',camera],['Upload',choosePhoto],['Back',goHome]]);
});
liveView('05photo',()=>{base('REVIEW PHOTO');picture();text('ANALYSE SENDS TO OPENAI',16,169);rail([['Analyse',analysePhoto],['Retry',()=>startScan()],['Back',()=>nav('05')]])});
register('live-working','Saving or checking',1,()=>{const answering=['quests/answer','shop/purchase','room/place'].includes(activeRequest?.path);base(answering?'SAVING YOUR CHOICE':'CHECKING PHOTO');sprite(saved.species,120,32,80);lines([answering?'WAITING FOR SAVE.':'WAITING FOR AI RESPONSE.','NO REWARD CONFIRMED.','BACK KEEPS REQUEST ID.'],16,121);rail([['Back',closeRequest]])},{});
register('live-candidate','Confirm culture suggestion',1,()=>{
 gameRead('IS THIS RIGHT?',(selectedEntry?.title||'Unknown')+'. '+(selectedEntry?.fact||'')+' AI saw: '+gameResult.observation+' Confirm only if this matches your photo.',[['Yes',confirmDiscovery],['Correct',()=>{correctionPage=0;nav('live-correction')}],['Back',()=>nav('05photo')]]);
},{});
register('live-correction','Correct the suggestion',1,()=>{
 const entries=catalogue.map(c=>[c.title,()=>correctTo(c)]);
 pagedRows('CHECK ANOTHER ITEM',entries,correctionPage,p=>correctionPage=p,gameResult?.status==='candidate'?'live-candidate':'live-uncertain');
},{});
register('live-uncertain','Photo needs another look',1,()=>{
 gameRead('NOT SURE YET',(gameResult?.observation||'Try a clearer photo with more context.')+' No rewards were added.',[['Retry',()=>startScan()],['Correct',()=>nav('live-correction')],['Back',goHome]]);
},{});
register('live-request-error','Request needs attention',1,()=>{
 gameRead('CHECK NOT FINISHED',gameMessage,[['Retry',retryRequest],['Status',checkRequest],['Back',closeRequest]]);
},{});
register('live-reward','Saved game result',1,()=>{
 const reward=gameResult.reward||{xp:0,coins:0},quest=['verify','complete'].includes(gameResult.kind);
 base(gameResult.status==='duplicate'?'ALREADY RECORDED':quest?'QUEST COMPLETE!':'DISCOVERY SAVED!');
 sprite(saved.species,126,32,68);center((selectedEntry?.title||'SAVED').slice(0,24),111);
 frame(12,140,296,38,C.jade);text('+'+reward.xp+' XP / +'+reward.coins+' COINS',24,152);
 rail([['Dex',()=>{detailPage=0;nav('live-story')}],['Quest',()=>{detailPage=0;nav('live-quest')}],['Home',goHome]]);
},{});
register('live-photo','Your saved photograph',1,()=>{
 base('SAVED PHOTO');if(storedPhoto)photoImage(storedPhoto);else lines(['LOADING PHOTO...','BACK AND RETRY IF NEEDED.'],16,70);
 const record=saved.log[selectedEntry?.id];
 if(record)text(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Singapore',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(record.time*1000)).replace(',','')+' SGT',10,167);
 rail([['Back',()=>nav('live-info')]]);
},{});
liveView('11',()=>{
 const item=shopItems[shopIndex%shopItems.length];if(!item){base('KOPI SHOP');lines(['SHOP NEEDS THE SERVER.'],16,70);rail([['Back',()=>nav('04menu')]]);return}
 base('KOPI SHOP',String(saved.coins));decoration(item.art,30,48);
 text(item.title.toUpperCase(),82,43);text(item.price+' COINS',82,72);
 const owned=saved.inventory.includes(item.id);
 text(owned?'ALREADY OWNED':saved.coins<item.price?'NEED '+(item.price-saved.coins)+' MORE COINS':'YOU CAN AFFORD THIS.',16,108);
 lines(wrapWords(item.description).slice(0,2),16,138);
 rail([[owned?'Owned':'Buy',()=>{selectedDecor=item;nav(owned?'12':'11confirm')}],['Next',()=>{shopIndex=(shopIndex+1)%shopItems.length;nav('11')}],['Back',()=>nav('04menu')]]);
});
liveView('11confirm',()=>{
 if(!selectedDecor){nav('11');return}
 base('CONFIRM PURCHASE');decoration(selectedDecor.art,140,30);
 lines([selectedDecor.title.toUpperCase(),'PRICE: '+selectedDecor.price+' COINS','YOUR COINS: '+saved.coins],16,95);
 rail([['Confirm',purchaseDecor],['Back',()=>nav('11')]]);
});
function inventoryView(title){
 base(title);
 const items=shopItems.filter(i=>saved.inventory.includes(i.id));
 if(!items.length){lines(['NO DECORATIONS YET.','VISIT THE KOPI SHOP.'],16,65);rail([['Shop',()=>nav('11')],['Back',()=>nav('04menu')]]);return}
 items.forEach((item,i)=>row(item.title,36+i*40,()=>{selectedDecor=item;slotIndex=0;nav('live-placement')}));
 rail([['Shop',()=>nav('11')],['Back',()=>nav('04menu')]]);
}
liveView('12',()=>inventoryView('YOUR INVENTORY'));
liveView('13',()=>inventoryView('CHOOSE DECORATION'));
register('live-placement','Preview room placement',2,()=>{
 const item=selectedDecor,slots=roomSlots.filter(s=>item?.slots.includes(s.id)),slot=slots[slotIndex%slots.length];
 if(!item||!slot){nav('12');return}
 const preview={...saved.room};for(const id of Object.keys(preview))if(preview[id]===item.id)delete preview[id];preview[slot.id]=item.id;
 base('PREVIEW ONLY');room(false,preview);ctx.strokeStyle=C.terra;ctx.lineWidth=2;ctx.strokeRect(slot.x-5,slot.y-3,46,59);
 frame(8,151,304,38,C.paper);text(slot.title.toUpperCase()+' SLOT',16,158);text(saved.room[slot.id]&&saved.room[slot.id]!==item.id?'BOTH ITEMS STAY OWNED':'SAVE TO KEEP THIS HERE',16,174);
 rail([['Save',placeDecor],['Next',()=>{slotIndex=(slotIndex+1)%slots.length;render()}],['Back',()=>nav('12')]]);
},{});
async function purchaseDecor(){
 if(gallery||gameBusy||!selectedDecor)return;
 activeRequest={path:'shop/purchase',body:{operation_id:newId(),item_id:selectedDecor.id}};await runGameRequest();
}
async function placeDecor(){
 if(gallery||gameBusy||!selectedDecor)return;
 const slots=roomSlots.filter(s=>selectedDecor.slots.includes(s.id));
 activeRequest={path:'room/place',body:{operation_id:newId(),item_id:selectedDecor.id,slot_id:slots[slotIndex%slots.length].id}};await runGameRequest();
}
register('live-commerce-result','Decoration saved result',2,()=>{
 const status=gameResult.status;
 base({purchased:'PURCHASE SAVED!',owned:'ALREADY OWNED',insufficient:'NOT ENOUGH COINS',placed:'ROOM SAVED!'}[status]||'SAVED');
 if(selectedDecor)decoration(selectedDecor.art,140,34);
 lines([selectedDecor?.title.toUpperCase()||'DECORATION',status==='insufficient'?'NEED '+gameResult.needed+' MORE COINS':status==='purchased'?'PAID '+gameResult.charged+' KOPI COINS':status==='owned'?'NO EXTRA CHARGE.':'ITEMS STAY IN INVENTORY.','YOUR COINS: '+saved.coins],16,105);
 rail([['Items',()=>nav('12')],['Shop',()=>nav('11')],['Home',goHome]]);
},{});

liveView('18pair',()=>{base('PHOTOS AND PRIVACY');lines(['ANALYSE SENDS TO OPENAI.','PHOTOS SAVE ON THIS','DEVICE. NO CLOUD SYNC.','NO FRIEND SHARING YET.'],16,46);rail([['Back',()=>nav('18')]])});

function render(){if(!ready)return;browserLines=[];browserBody=null;hits=[];ctx.imageSmoothingEnabled=false;screens[current].draw();if(focus>=hits.length){focus=0;hits=[];screens[current].draw()}if(!compact&&!gallery&&browserBody){hits=hits.filter(h=>!['Read','Next'].includes(h.label));focus=Math.min(focus,Math.max(0,hits.length-1))}document.getElementById('mode').textContent=gallery?'DESIGN PREVIEW · sample data · no save changes':(backend?'PLAY · saved on this server':'PLAY · saved in this browser');document.getElementById('accessible').textContent=screens[current].title+'. '+hits.map((h,i)=>(i===focus?'Selected: ':'')+h.label).join('. ');if(!compact&&!gallery)renderBrowser();}
// Browser presentation consumes these same screen choices and state. It never
// calculates rewards, writes saves, or implements a second gameplay flow.
function renderBrowser(){
 const target=document.getElementById('room-art'),original=ctx;
 try{ctx=target.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,320,168);ctx.save();ctx.translate(0,-24);
  let arrangement=saved.room;
  if(current==='live-placement'&&selectedDecor){const slots=roomSlots.filter(s=>selectedDecor.slots.includes(s.id)),slot=slots[slotIndex%slots.length];arrangement={...saved.room};for(const id of Object.keys(arrangement))if(arrangement[id]===selectedDecor.id)delete arrangement[id];if(slot)arrangement[slot.id]=selectedDecor.id}
  room(saved.adopted,arrangement);ctx.restore();
 }finally{ctx=original}
 window.SGPalBrowser.render({screen:current,title:screens[current].title,lines:browserLines,body:browserBody,choices:hits.map(({label,disabled})=>({label,disabled})),focus,saved,candidate,name:names[candidate][nameIndex],item:selectedDecor||shopItems[shopIndex%shopItems.length],shopItem:shopItems[shopIndex%shopItems.length],entry:selectedEntry,result:gameResult,photo:current==='live-photo'?storedPhoto:photo,stream,backend,busy:gameBusy||saving}, {
  activate(i){focus=i;press()},select(i){focus=i;render()},
  navigate(id){if(saving)return;if(gameBusy)requestView++;gallery=false;id==='05'?startScan():nav(id)},back,
  paintItem(target,art){const old=ctx;try{ctx=target.getContext('2d');ctx.imageSmoothingEnabled=false;decoration(art,8,2)}finally{ctx=old}}
 });
}
function resize(){const top=canvas.getBoundingClientRect().top+scrollY;const byHeight=Math.floor((innerHeight-top-24)/240);document.documentElement.style.setProperty('--scale',String(Math.max(1,Math.min(3,Math.floor((innerWidth-60)/320),byHeight))))}
document.getElementById('left').onclick=()=>{canvas.focus();rotate(-1)};document.getElementById('right').onclick=()=>{canvas.focus();rotate(1)};document.getElementById('press').onclick=()=>{canvas.focus();press()};
window.addEventListener('keydown',e=>{if(['SELECT','INPUT','TEXTAREA','SUMMARY','BUTTON'].includes(e.target.tagName))return;if(['ArrowLeft','ArrowUp','ArrowRight','ArrowDown','Enter',' ','Escape'].includes(e.key)){e.preventDefault();if(e.repeat&&['Enter',' '].includes(e.key))return;if(e.key==='Escape')back();else if(e.key==='Enter'||e.key===' ')press();else rotate(['ArrowLeft','ArrowUp'].includes(e.key)?-1:1)}});
canvas.addEventListener('click',e=>{const b=canvas.getBoundingClientRect(),x=(e.clientX-b.left)*320/b.width,y=(e.clientY-b.top)*240/b.height;const i=hits.findIndex(h=>x>=h.x&&x<h.x+h.w&&y>=h.y&&y<h.y+h.h);if(i>=0){if(i===focus)press();else{focus=i;render()}}});
// Hardware adapter contract: one signed step per debounced encoder detent.
window.addEventListener('sgpal:rotate',e=>rotate(Number(e.detail?.delta)||0));window.addEventListener('sgpal:press',press);
document.getElementById('scene').onchange=e=>{requestView++;gallery=true;nav(e.target.value)};
document.getElementById('live').onclick=()=>{document.body.classList.remove('design-gallery');gallery=false;photo=null;nav(saved.adopted?'04':'01')};
document.getElementById('photo').onchange=e=>{const f=e.target.files[0];e.target.value='';if(!f)return;if(f.size>6*1024*1024||!['image/jpeg','image/png','image/webp'].includes(f.type)){lastCameraError='JPG/PNG/WEBP, MAX 6MB.';nav('05error');return}const token=mediaGeneration,url=URL.createObjectURL(f),im=new Image();im.onload=()=>{if(token!==mediaGeneration){URL.revokeObjectURL(url);return}if(im.width*im.height>24000000){URL.revokeObjectURL(url);lastCameraError='PHOTO TOO LARGE: MAX 24MP';nav('05error');return}const reader=new FileReader();reader.onload=()=>{if(token!==mediaGeneration)return;photo=im;photoPayload=String(reader.result).split(',')[1];nav('05photo')};reader.onerror=()=>{lastCameraError='PHOTO COULD NOT BE READ.';nav('05error')};reader.readAsDataURL(f);URL.revokeObjectURL(url)};im.onerror=()=>{URL.revokeObjectURL(url);if(token!==mediaGeneration)return;lastCameraError='PHOTO COULD NOT BE READ.';nav('05error')};im.src=url};
window.addEventListener('resize',resize);window.addEventListener('pagehide',stopCamera);document.addEventListener('visibilitychange',()=>{if(document.hidden&&stream){stopCamera();current='05';focus=0;render()}});
if(compact)document.body.classList.add('kiosk');else{document.body.classList.add('browser-game');document.getElementById('browser-shell').hidden=false;canvas.tabIndex=-1;}
setInterval(()=>{if(ready&&stream&&current==='05live'&&!document.hidden)render()},100);
window.SGPal={rotate,press,back,preview(id){document.body.classList.add('design-gallery');document.getElementById('review').open=true;if(!screens[id])throw Error('Unknown screen');gallery=true;nav(id)},live(){document.body.classList.remove('design-gallery');gallery=false;nav(saved.adopted?'04':'01')},manifest:()=>Object.values(screens).sort((a,b)=>(parseInt(a.id)||999)-(parseInt(b.id)||999)||a.id.localeCompare(b.id)).map(({draw,...s})=>({...s,main:mainIds.includes(s.id)})),audit:()=>audit,inspect:()=>({current,focus,choices:hits.map(h=>h.label),saved:{...saved},gallery,backend,ready}),native:()=>canvas.toDataURL('image/png')};
async function loadSaved(){
 try{
  if(backend){saved=await api('state');catalogue=await api('catalogue');const shop=await api('shop');shopItems=shop.items;roomSlots=shop.slots}
  else{const raw=localStorage.getItem('sgpal-ui-v1');saved=raw?{...empty(),...JSON.parse(raw)}:empty();if(!names[saved.species]||typeof saved.adopted!=='boolean')throw Error('Invalid save')}
  if(!(saved.adopted&&await resumeRequest()))nav(saved.adopted?'04':'01');
 }catch(e){nav('saveerror')}
}
async function init(){
 resize();for(const key of ['room','merlion','otter','mynah']){assets[key]=await new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src='assets/'+key+'.png'})}
 Object.values(screens).filter(s=>!s.id.startsWith('live-')).sort((a,b)=>(parseInt(a.id)||999)-(parseInt(b.id)||999)||a.id.localeCompare(b.id)).forEach(s=>{const op=document.createElement('option');op.value=s.id;op.textContent=s.id+' · '+s.title+' (phase '+s.phase+')';document.getElementById('scene').append(op)});
 ready=true;await loadSaved();
}
init().catch(()=>{ctx.fillStyle=C.paper;ctx.fillRect(0,0,320,240);text('ASSETS COULD NOT LOAD',16,80);text('USE THE LOCAL WEB SERVER',16,110);if(!compact){document.getElementById('panel-title').textContent='The room could not load.';document.getElementById('panel-copy').textContent='Check the local server and try again. Your saved progress has not been changed.';const retry=document.createElement('button');retry.textContent='Retry loading';retry.onclick=()=>location.reload();document.getElementById('game-actions').replaceChildren(retry)}});
})();
