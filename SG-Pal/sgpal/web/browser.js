/* Responsive presentation only. Actions are supplied by the shared game. */
(() => {
'use strict';
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el};
const picture=(species,cls='pal-portrait')=>{const im=node('img',undefined,cls);im.src='assets/'+species+'.png';im.alt=species+' Pal';return im};
const readable=text=>String(text).replace(/^[A-Z\s.,!?]+$/,s=>s.charAt(0)+s.slice(1).toLowerCase());
let previous='',signature='',actions;
function fitRoom(){
 const stage=document.querySelector('.room-stage'),art=document.querySelector('.room-art');
 document.documentElement.style.setProperty('--usable-height',(window.visualViewport?.height||innerHeight)+'px');
 const w=stage.clientWidth,h=stage.clientHeight;
 // Uniform camera scale: whole room on wide screens, centre crop on portrait.
 const canvas=$('room-art'),ratio=canvas.width/canvas.height;
 art.style.width=Math.round(Math.max(w,Math.min(h*ratio,w*2.8)))+'px';
}
window.addEventListener('resize',fitRoom);
window.visualViewport?.addEventListener('resize',fitRoom);
const navItems=[['Home','04','⌂'],['Scan','05','◎'],['CultureDex','07','▤'],['Quests','09','✓'],['Shop','11','◇'],['Inventory','12','▣'],['Friends','16','♧']];
const activeSection=id=>id==='12'?'12':id==='16'?'16':id.startsWith('05')||['live-candidate','live-correction','live-uncertain'].includes(id)?'05':id==='07'||['live-story','live-info','live-photo','08locked'].includes(id)?'07':id==='09'||id.startsWith('live-quest')?'09':['11','11confirm','12','13','live-placement','live-commerce-result'].includes(id)?'11':'04';
function fullscreenState(){const b=$('fullscreen');b.hidden=!document.fullscreenEnabled&&!document.fullscreenElement;b.textContent=document.fullscreenElement?'Exit fullscreen':'Fullscreen';b.setAttribute('aria-label',b.textContent);b.dataset.active=String(!!document.fullscreenElement)}
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch(_){$('browser-status').textContent='Fullscreen unavailable. You can keep playing in this window.'}};
document.addEventListener('fullscreenchange',fullscreenState);fullscreenState();
$('panel-close').onclick=()=>{window.SGPal.live();restoreToolbar()};
let returnFocus=null;
function restoreToolbar(){(returnFocus?.isConnected?returnFocus:$('game-nav').querySelector('button'))?.focus()}
$('return-home').onclick=()=>{SGPal.live();restoreToolbar()};
$('settings-open').onclick=()=>{$('settings-dialog').showModal()};
$('settings-close').onclick=()=>$('settings-dialog').close();
$('settings-dialog').addEventListener('close',()=> $('settings-open').focus());
$('account-dialog').addEventListener('close',()=> $('settings-open').focus());
for(const [id,screen] of [['pal-open','04pal'],['profile-open','14'],['game-settings-open','18'],['decorate-open','13'],['pocket-open','04menu']])$(id).onclick=()=>{$('settings-dialog').close();actions.navigate(screen)};
$('game-actions').addEventListener('focusin',e=>{for(const b of $('game-actions').children)b.classList.toggle('selected',b===e.target)});
$('account-open').addEventListener('click',()=> $('settings-dialog').close());
// Keyboard navigation is presentation-only; inputs retain normal cursor editing.
window.addEventListener('keydown',e=>{
 if(!document.body.classList.contains('browser-game')||document.body.classList.contains('design-gallery')||e.target.closest('input,textarea,select,[contenteditable="true"]'))return;
 const modal=document.querySelector('dialog[open]');
 if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Enter','Escape'].includes(e.key))return;
 if(e.key==='Escape'){
  e.preventDefault();e.stopImmediatePropagation();
  if(modal){if(modal.id==='friends-dialog')$('friends-close').click();else if(modal.id==='account-dialog')$('account-close').click();else modal.close()}
  else if(!$('visit-banner').hidden){SGPal.live();restoreToolbar()}
  else if(previous!=='04'){actions.back();if(previous==='04')restoreToolbar()}
  else $('settings-open').click();return;
 }
 const panel=$('game-panel'),inWindow=previous!=='04';
 const scope=modal|| (inWindow?panel:$('browser-shell'));
 const controls=[...scope.querySelectorAll('button:not(:disabled),summary,a[href],input')].filter(n=>n.getClientRects().length&&!n.closest('[hidden]'));
 if(!controls.length)return;
 const at=controls.indexOf(document.activeElement);
 e.preventDefault();e.stopImmediatePropagation();
 if(e.key==='Enter'){if(!e.repeat)(at>=0?controls[at]:controls[0]).click();return}
 const step=['ArrowLeft','ArrowUp'].includes(e.key)?-1:1;
 controls[(at<0?0:(at+step+controls.length)%controls.length)].focus();
},true);
window.SGPalBrowser={render(data,controls){
 actions=controls;const {screen,saved,choices}=data;
 const changed=screen!==previous;
 const requestIndex=screen==='04'?choices.findIndex(c=>c.label==='Status'):-1;
 $('request-status').hidden=requestIndex<0;$('settings-open').dataset.pending=String(requestIndex>=0);
 $('request-status').onclick=()=>{$('settings-dialog').close();controls.activate(requestIndex)};
 $('hud-pet').src='assets/'+(saved.adopted?saved.species:data.candidate)+'.png';
 $('hud-name').textContent=saved.adopted?saved.name:'Meet your Pal';
 $('hud-level').textContent=saved.adopted?'Level '+(saved.level||1)+' · '+saved.species:'A friend for the road';
 $('hud-mobile-level').textContent='Level '+(saved.level||1);$('hud-xp').textContent=saved.xp;$('hud-coins').textContent=saved.coins;$('hud-progress').value=saved.xp%50;
 $('visit-banner').hidden=!data.visiting;
 $('visit-label').textContent=data.visiting?'Visiting '+data.visiting.name:'';
 $('game-nav').hidden=!saved.adopted;
 if(!$('game-nav').children.length)for(const [label,id,icon] of navItems){const b=node('button');b.type='button';b.setAttribute('aria-label',label);b.dataset.destination=id;const caption=node('span',label,'nav-label');caption.dataset.short=({CultureDex:'Dex',Inventory:'Items'})[label]||label;b.append(node('span',icon,'nav-icon'),caption);b.onclick=()=>{returnFocus=b;id==='16'?window.SGPalFriends.open():actions.navigate(id)};$('game-nav').append(b)}
 for(const b of $('game-nav').children){if(b.dataset.destination===activeSection(screen))b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')}
 $('browser-shell').dataset.screen=screen;
 $('browser-shell').classList.toggle('at-home',screen==='04');
 $('browser-shell').classList.toggle('onboarding',!saved.adopted);
 $('panel-close').hidden=['01','04','live-working'].includes(screen);
 const celebrating=screen==='live-reward'&&(data.result?.reward?.xp||data.result?.reward?.coins)||screen==='live-commerce-result'&&['purchased','placed'].includes(data.result?.status);
 $('panel-kicker').textContent=celebrating?'A LITTLE MOMENT TO CELEBRATE':screen.startsWith('05')?'NOTICE SOMETHING LOCAL':screen==='11'?'LITTLE THINGS, LOVELY HOME':saved.adopted?'YOUR SINGAPORE STORY':'WELCOME, NEIGHBOUR';
 const titles={'01':'Hello, Singapore.','02':'Who’s coming along?','02confirm':'Your new companion?','03':'What shall we call you?','04':'Make yourself at home.','05':'What caught your eye?','05photo':'Take a closer look.','11':'The Kopi Shop','12':'Your little collection','13':'Make it your own','live-placement':'Find its happy place.','live-candidate':'Does this look right?','live-quest-answer':'Did you complete this quest?','live-request-error':'Let’s try that again.','live-working':'One moment…'};
 if(screen==='live-reward')titles[screen]=data.result?.status==='duplicate'?'Already part of your story.':data.result?.kind==='complete'?'Quest complete!':'Discovery saved!';
 if(screen==='live-commerce-result')titles[screen]=({purchased:'A little joy for home.',placed:'Looking more like home.',owned:'Already yours.',insufficient:'A few more coins…'})[data.result?.status]||data.title;
 $('panel-title').textContent=titles[screen]||data.title;
 const key=JSON.stringify([screen,data.lines,data.body,saved,data.name,data.item,data.shopItem,data.result,data.photo?.src,!!data.stream]);
 if(key!==signature){
  const copy=$('panel-copy'),media=$('panel-media');copy.replaceChildren();media.replaceChildren();
  let body=data.body||[...new Set(data.lines)].map(readable).join(' ');
  if(screen==='01'){body='Meet a little companion. Discover everyday Singapore together, collect its stories, and make this BTO your own.';for(const species of ['merlion','otter','mynah'])media.append(picture(species,'welcome-pal'))}
  if(screen==='02')body='A brave Merlion, a playful Otter, or a chatty Mynah. Who feels like your kind of neighbour?';
  if(['02confirm','03'].includes(screen)){media.append(picture(data.candidate));body=screen==='03'?'How about '+data.name+'? Keep this name, or try another suggestion.':'A little '+data.candidate+', ready for a big Singapore adventure.'}
  if(screen==='04'){body='Your next story is just around the corner. Notice something local, learn its story, and bring a little joy back home.';const note=node('div',undefined,'home-note');note.append(node('span','YOUR JOURNEY'),node('strong',saved.discoveries.length+' '+(saved.discoveries.length===1?'discovery':'discoveries')+' · '+(saved.completed||[]).length+' '+((saved.completed||[]).length===1?'quest':'quests')+' completed'));copy.append(note)}
  if(screen==='05')body='A kopi menu, a tray-return station, a familiar local ritual. Capture or upload a photo to discover its story. You choose when to send it to OpenAI.';
  if(screen==='05error')body=data.lines.map(readable).join(' ')+' Camera access needs permission and HTTPS or device-local localhost. Upload a saved photo instead.';
  if(screen==='05live'&&data.stream){const v=node('video');v.autoplay=true;v.muted=true;v.playsInline=true;v.srcObject=data.stream;v.play().catch(()=>{});media.append(v);body='Frame the cultural item and capture when you’re ready.'}
  if(['05photo','live-photo'].includes(screen)&&data.photo){const im=node('img');im.src=data.photo.src;im.alt=screen==='live-photo'?'Your saved cultural discovery':'Photo ready for recognition';media.append(im)}
  if(screen==='05photo')body='Happy with this photo? Analyse sends it to OpenAI. A photo alone never grants a reward.';
  if(['11','11confirm','live-commerce-result'].includes(screen)){const item=screen==='11'?data.shopItem:data.item;if(item){const art=node('canvas',undefined,'item-art');art.width=52;art.height=60;controls.paintItem(art,item.art);media.append(art);if(screen==='11'){const owned=saved.inventory.includes(item.id);body=item.description;copy.append(node('h3',item.title),node('p',item.price+' Kopi Coins','item-price'),node('p',owned?'Already yours. Find it in your inventory.':saved.coins<item.price?'You need '+(item.price-saved.coins)+' more coins.':'A little treat within reach.','ownership'))}}}
  if(screen==='live-quest-answer')body='This one is on trust. Choose “Yes, I did it” when you’ve actually finished. “Not yet” keeps it active, with no penalty and no proof needed.';
  if(screen==='live-reward'){const reward=data.result?.reward||{xp:0,coins:0};media.append(picture(saved.species));body=data.result.status==='duplicate'?'Already part of your story. No extra rewards were added.':data.result.kind==='complete'?'Quest complete — recorded as self-reported. Nicely done.':'A new Singapore story, saved to your CultureDex.';const badge=node('div',undefined,'reward-badge');badge.append(node('strong','+'+reward.xp+' Culture XP'),node('span','+'+reward.coins+' Kopi Coins'));copy.append(badge)}
  if(screen==='help')body='Tap or click a choice to select it. Use Tab and Enter, or arrow keys to move through the game choices. Escape goes back. Compact mode also supports rotary turn and press.';
  copy.append(node('p',body,'story-copy'));
  if(screen==='live-working')copy.prepend(node('div','Saving / checking your request','loading-note'));
  signature=key;
 }
 const oldFocus=document.activeElement?.dataset.action;
 const actionBox=$('game-actions');actionBox.replaceChildren();
 choices.forEach((choice,i)=>{
  if(data.body&&['Read','Next'].includes(choice.label))return; // Browser text scrolls in full.
  const label=screen==='01'&&choice.label==='Start'?'Play now':choice.label;const b=node('button',label);b.type='button';b.setAttribute('aria-label',label);b.dataset.action=String(i);b.disabled=!!choice.disabled;b.classList.toggle('selected',i===data.focus);b.classList.toggle('quiet',['Back','Home','Next','Prev','Retry'].includes(choice.label));
  if(screen==='02'&&['merlion','otter','mynah'].includes(choice.label)){b.prepend(picture(choice.label,'choice-pal'));b.classList.add('pet-choice')}
  b.onclick=()=>controls.activate(i);
  b.onkeydown=e=>{if(['ArrowLeft','ArrowUp','ArrowRight','ArrowDown'].includes(e.key)){e.preventDefault();const visible=[...actionBox.children].map(el=>Number(el.dataset.action)),at=visible.indexOf(i),step=['ArrowLeft','ArrowUp'].includes(e.key)?-1:1;controls.select(visible[(at+step+visible.length)%visible.length]);actionBox.querySelector('[data-action="'+visible[(at+step+visible.length)%visible.length]+'"]').focus()}else if(e.key==='Escape'){e.preventDefault();controls.back()}};
  actionBox.append(b);
 });
 actionBox.classList.toggle('pet-choices',screen==='02');
 $('browser-status').textContent=data.backend?'Progress saved on this server · private local play':'Browser-only preview · AI requires the server';
 if(changed){$('game-panel').scrollTop=0;document.querySelector('.game-workspace').scrollTop=0;requestAnimationFrame(()=>{if(screen==='04')restoreToolbar();else $('game-actions button:not(:disabled)')?.focus({preventScroll:true})});if(screen==='live-reward'){$('game-panel').classList.remove('reward-arrival');void $('game-panel').offsetWidth;$('game-panel').classList.add('reward-arrival')}}
 else if(oldFocus!==undefined)actionBox.querySelector('[data-action="'+oldFocus+'"]')?.focus({preventScroll:true});
 previous=screen;requestAnimationFrame(fitRoom);
}};
})();
