/* Private recovery credentials exist only in form memory; never URLs or storage. */
(() => {
'use strict';
const $=id=>document.getElementById(id),dialog=$('account-dialog');
let session=null,busy=false;
if(location.hash)history.replaceState(null,'',location.pathname+location.search);
const channel=typeof BroadcastChannel==='function'?new BroadcastChannel('sgpal-auth'):null;
function clearAndReload(broadcast=true){
 try{for(const key of Object.keys(localStorage))if(key.startsWith('sgpal-pending'))localStorage.removeItem(key);
 if(broadcast){channel?.postMessage('changed');localStorage.setItem('sgpal-auth-change',String(Date.now()))}
 }catch(_){}
 document.body.style.visibility='hidden';location.replace(location.pathname+location.search);
}
channel?.addEventListener('message',()=>clearAndReload(false));
window.addEventListener('storage',e=>{if(e.key==='sgpal-auth-change')clearAndReload(false)});
window.addEventListener('pageshow',e=>{if(e.persisted)clearAndReload(false)});
function clearPrivate(){ $('recovery-code').textContent='';$('recovery-input').value='';$('recovery-issued').hidden=true;$('restore-form').hidden=true;$('guest-warning').hidden=true; }
function close(){if(busy)return;if(!$('recovery-issued').hidden){$('account-message').textContent='Keep your code, then choose “I saved my code”.';return}dialog.close()}
$('account-close').onclick=close;
dialog.addEventListener('cancel',e=>{e.preventDefault();close()});
dialog.addEventListener('close',clearPrivate);
function display(){
 $('account-open').textContent=session?.signed_in?'My account':'Save my Pal';
 $('account-label').textContent=session?.signed_in?(session.recovery_enabled?'Recovery account · private save':'Legacy account · private save'):'Guest · saved in this browser session';
 $('account-heading').textContent='Your Pal, saved';
 $('account-description').textContent='Play now as a guest. Save my Pal gives you a private recovery code for this profile. Restore it on another browser using this same site. No email is needed.';
 $('save-pal').hidden=!!session?.recovery_enabled;
 $('sign-out').hidden=!session?.signed_in;
}
async function boot(){
 const r=await fetch('/api/auth/session',{cache:'no-store',signal:AbortSignal.timeout(20000)});if(!r.ok)throw Error('Session unavailable. Reload to try again.');session=await r.json();display();return session;
}
function headers(){return session?{'X-SGPal-CSRF':session.csrf,'X-SGPal-Owner':session.owner_id}:{}}
async function post(path,body={}){
 const r=await fetch('/api/auth/'+path,{method:'POST',signal:AbortSignal.timeout(20000),headers:{'Content-Type':'application/json',...headers()},body:JSON.stringify(body)});
 let value;try{value=await r.json()}catch(_){}
 if(!r.ok)throw Error(typeof value?.detail==='string'?value.detail:'Account request failed. Please retry.');return value;
}
async function run(fn){if(busy)return;busy=true;$('account-message').textContent='Working…';try{await fn()}catch(e){$('account-message').textContent=e.message||'Connection failed. Try again.'}finally{busy=false}}
async function save(){
 const out=await post('recovery/save');
 // Show immediately: a later session-refresh failure must not hide the only copy.
 $('guest-warning').hidden=true;$('restore-form').hidden=true;
 $('recovery-code').textContent=out.code;$('recovery-issued').hidden=false;
 $('save-pal').hidden=true;$('restore-open').hidden=true;$('sign-out').hidden=true;
 $('account-message').textContent='Progress preserved. Copy and keep your private code now.';$('copy-recovery').focus();
}
$('account-open').onclick=()=>{display();dialog.showModal();run(async()=>{await boot();$('account-message').textContent=session.recovery_enabled?'Recovery access is enabled. Use your saved private code on another browser.':''})};
$('save-pal').onclick=()=>run(save);$('guest-save').onclick=()=>run(save);
$('copy-recovery').onclick=()=>run(async()=>{try{await navigator.clipboard.writeText($('recovery-code').textContent);$('account-message').textContent='Copied. Keep it private and save it somewhere safe.'}catch(_){$('account-message').textContent='Copy unavailable. Select the code above and copy it manually.'}});
$('recovery-kept').onclick=()=>run(async()=>{clearPrivate();$('restore-open').hidden=false;await boot();$('account-message').textContent='Recovery access saved. You can now restore another Pal or continue playing.'});
$('restore-open').onclick=()=>run(async()=>{
 await boot();$('account-message').textContent='';
 if(session.unsaved_progress){$('guest-warning').hidden=false;$('guest-save').focus();return}
 $('restore-form').hidden=false;$('recovery-input').focus();
});
$('guest-cancel').onclick=()=>{$('guest-warning').hidden=true;$('account-message').textContent='Your guest progress is unchanged.'};
$('restore-cancel').onclick=()=>{$('restore-form').hidden=true;$('recovery-input').value=''};
$('restore-form').onsubmit=e=>{e.preventDefault();run(async()=>{const code=$('recovery-input').value.trim();$('recovery-input').value='';await post('recovery/restore',{code});clearAndReload()})};
$('sign-out').onclick=()=>run(async()=>{await post('logout');clearAndReload()});
$('refresh-progress').onclick=()=>window.dispatchEvent(new Event('sgpal:refresh'));
window.addEventListener('sgpal:save-status',e=>{$('save-status').textContent=e.detail});
window.SGPalAccount={boot,headers,changed:()=>clearAndReload(false),get session(){return session}};
})();
