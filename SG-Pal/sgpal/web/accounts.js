/* Optional account UI. Provider API credentials and access tokens stay on the server. */
(() => {
'use strict';
const $=id=>document.getElementById(id);
let session=null,linkToken=new URLSearchParams(location.hash.slice(1)).get('token_hash');
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
const dialog=$('account-dialog');
window.addEventListener('hashchange',()=>{linkToken=new URLSearchParams(location.hash.slice(1)).get('token_hash');history.replaceState(null,'',location.pathname+location.search);if(linkToken){display();if(!dialog.open)dialog.showModal()}});
dialog.addEventListener('keydown',e=>{if(e.key==='Escape')e.stopPropagation()});
$('account-close').onclick=()=>dialog.close();
function display(){
 $('account-open').textContent=session?.signed_in?'Account':'Save my progress';
 $('account-label').textContent=session?.signed_in?'Signed in · '+session.email:'Guest · this browser’s private save';
 $('account-heading').textContent=session?.signed_in?'Your progress, together.':'Save your Singapore story.';
 $('account-email-form').hidden=!!session?.signed_in||!!session?.conflict||!!linkToken;
 $('account-conflict').hidden=!session?.conflict;
 $('confirm-email-link').hidden=!linkToken;
 $('sign-out').hidden=!session?.signed_in;
 $('account-import').hidden=!!session?.signed_in;
 $('account-description').textContent=session?.signed_in?'Sign in on another browser using the same server address to continue this pet. Sign out starts a fresh guest session here.':'Guest play needs no registration. Email sign-in saves this guest’s progress to a new account. Existing accounts require an explicit choice; balances are never combined.';
 if(!session?.configured&&!session?.signed_in)$('account-message').textContent='Email login is not configured on this server yet. Guest play and private saves work. See ACCOUNTS.md for setup.';
}
async function boot(){
 const r=await fetch('/api/auth/session',{cache:'no-store',signal:AbortSignal.timeout(20000)});if(!r.ok)throw Error('Session unavailable. Reload to try again.');session=await r.json();display();
 if((linkToken||session.conflict)&&!dialog.open)dialog.showModal();
 return session;
}
async function post(path,body){
 const r=await fetch('/api/auth/'+path,{method:'POST',signal:AbortSignal.timeout(20000),headers:{'Content-Type':'application/json',...headers()},body:JSON.stringify(body||{})});
 let value;try{value=await r.json()}catch(_){}
 if(!r.ok)throw Error(typeof value?.detail==='string'?value.detail:'Account request failed. Please retry.');return value;
}
function headers(){return session?{'X-SGPal-CSRF':session.csrf,'X-SGPal-Owner':session.owner_id}:{}}
let busy=false;
async function run(fn){if(busy)return;busy=true;$('account-message').textContent='Working… No sign-in is confirmed yet.';try{await fn()}catch(e){$('account-message').textContent=e.message||'Connection failed. Try again.'}finally{busy=false}}
$('account-open').onclick=()=>{display();dialog.showModal()};
$('account-email-form').onsubmit=e=>{e.preventDefault();run(async()=>{const out=await post('email',{email:$('login-email').value});$('account-message').textContent=out.message})};
$('confirm-email-link').onclick=()=>run(async()=>{
 try{const result=await post('complete',{token_hash:linkToken});linkToken=null;if(result.signed_in)clearAndReload();else{await boot();$('account-message').textContent='Existing account found. Choose which save to continue. Neither save has been changed.'}}
 catch(e){linkToken=null;display();throw e}
});
for(const choice of ['account','guest'])$('use-'+choice).onclick=()=>run(async()=>{await post('decision',{choice});clearAndReload()});
$('sign-out').onclick=()=>run(async()=>{await post('logout');clearAndReload()});
$('legacy-key').onchange=e=>run(async()=>{const file=e.target.files[0];e.target.value='';if(!file)return;if(file.size>128)throw Error('Choose the one-time import key file, not a save or photo.');await post('import',{key:(await file.text()).trim()});clearAndReload()});
$('refresh-progress').onclick=()=>window.dispatchEvent(new Event('sgpal:refresh'));
window.addEventListener('sgpal:save-status',e=>{$('save-status').textContent=e.detail});
window.SGPalAccount={boot,headers,changed:()=>clearAndReload(false),get session(){return session}};
})();
