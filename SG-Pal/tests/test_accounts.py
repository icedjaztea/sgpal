"""Real sessions and stores, explicitly mocked email provider and AI; no live email."""
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from sgpal import accounts, server
from session_client import SessionClient
from test_gameplay import discover, answer, result

class FakeProvider:
    ready=True
    def send(self,email): pass
    def verify(self,token):
        if token=='x'*32: raise HTTPException(401,'Invalid link')
        email=token.replace('_','@')+'.test'
        return str(uuid.uuid5(uuid.NAMESPACE_DNS,email)),email

@pytest.fixture
def clients(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(accounts,'provider',FakeProvider())
    monkeypatch.setattr(server,'credential_present',lambda:True)
    monkeypatch.setattr(server,'recognise',lambda *a,**kw:result())
    return SessionClient(server.app),SessionClient(server.app),tmp_path

def login(c,path,name='alice',existing=False):
    # Clear test rate-limit clocks; production has no bypass.
    with accounts.Sessions(path).db() as db: db.execute('DELETE FROM limits')
    token=name+'_examplelongdomain123456789'
    assert c.post('/api/auth/email',json={'email':token.replace('_','@')+'.test'}).status_code==200
    r=c.post('/api/auth/complete',json={'token_hash':token})
    assert r.status_code==200,r.text
    assert r.json()['conflict']==existing
    return r

def adopt(c,name='Kaya'):
    assert c.post('/api/adopt',json={'species':'otter','name':name}).status_code==200

def test_guest_isolation_and_security(clients):
    a,b,path=clients;adopt(a);adopt(b,'Pip');found=discover(a)
    assert b.get('/api/state').json()['coins']==0
    assert b.get(found['state']['log']['kopi']['photo_url']).status_code==404
    assert b.get('/api/operations/'+found['operation_id']).status_code==404
    identity=a.get('/api/auth/session').json()
    assert a.post('/api/sound',json={'enabled':True},headers={'X-SGPal-CSRF':'wrong'}).status_code==403
    assert b.post('/api/sound',json={'enabled':True},headers={'X-SGPal-Owner':identity['owner_id']}).status_code==409
    assert a.post('/api/sound',json={'enabled':True},headers={'Origin':'https://evil.test'}).status_code==403
    assert 'no-store' in a.get('/api/state').headers['cache-control']

def test_migration_conflict_cross_session_logout(clients):
    a,b,path=clients;adopt(a);discover(a);before=a.get('/api/state').json();old=a.cookies.get(accounts.COOKIE)
    login(a,path)
    assert a.cookies.get(accounts.COOKIE)!=old
    assert a.get('/api/state').json()==before
    adopt(b,'Other');discover(b);guest=b.get('/api/state').json()
    login(b,path,existing=True)
    assert b.get('/api/state').json()==guest
    assert b.post('/api/auth/decision',json={'choice':'guest'}).status_code==200
    assert b.get('/api/state').json()==guest
    login(b,path,existing=True)
    assert b.post('/api/auth/decision',json={'choice':'account'}).status_code==200
    assert b.get('/api/state').json()==before
    assert b.post('/api/auth/logout').status_code==200
    assert not b.get('/api/state').json()['adopted']
    assert a.get('/api/state').json()==before
    assert not b.get('/api/auth/session').json()['signed_in']
    login(b,path,'bob');adopt(b,'Bob')
    assert b.get('/api/state').json()['coins']==0
    assert a.get('/api/state').json()['coins']==5

def test_concurrent_rewards_and_stale_writes(clients):
    a,b,path=clients;adopt(a);discover(a);login(a,path);login(b,path,existing=True)
    b.post('/api/auth/decision',json={'choice':'account'})
    revision=a.get('/api/state').json()['revision']
    with ThreadPoolExecutor(2) as pool:
        responses=list(pool.map(lambda c:c.post('/api/quests/answer',json=answer()),[a,b]))
    assert all(r.status_code==200 for r in responses)
    assert sum(r.json()['reward']['coins'] for r in responses)==10
    assert a.get('/api/state').json()['coins']==15
    assert a.post('/api/sound',json={'enabled':True},headers={'If-Match':revision}).status_code==409
    assert a.get('/api/state').json()==b.get('/api/state').json()

def test_invalid_missing_and_wrong_email(clients,monkeypatch):
    a,b,path=clients;adopt(a)
    assert a.post('/api/auth/complete',json={'token_hash':'x'*32}).status_code==409
    a.post('/api/auth/email',json={'email':'alice@example.test'})
    assert a.post('/api/auth/complete',json={'token_hash':'x'*32}).status_code==401
    assert a.post('/api/auth/complete',json={'token_hash':'bob_examplelongdomain123456789'}).status_code==401
    assert not a.get('/api/auth/session').json()['signed_in']
    assert a.post('/api/auth/email',json={'email':'alice@example.test'}).status_code==429
    monkeypatch.setattr(accounts,'provider',accounts.Provider())
    for key in ('SUPABASE_URL','SUPABASE_PUBLISHABLE_KEY','SGPAL_PUBLIC_URL'):monkeypatch.delenv(key,raising=False)
    assert not b.get('/api/auth/session').json()['configured']
    with accounts.Sessions(path).db() as db:db.execute('DELETE FROM limits')
    assert b.post('/api/auth/email',json={'email':'nobody@example.test'}).status_code==503
    assert not b.get('/api/auth/session').json()['signed_in']

def test_legacy_import_is_explicit_one_time(clients,tmp_path):
    a,b,path=clients
    (path/'profile.json').write_text('{"version":1,"species":"otter","name":"Legacy","adopted":true,"sound":false}')
    original=(path/'profile.json').read_bytes()
    key=path/'private-key.txt';accounts.prepare_legacy(path,key)
    assert not a.get('/api/state').json()['adopted']
    assert a.post('/api/auth/import',json={'key':key.read_text()}).status_code==200
    assert a.get('/api/state').json()['name']=='Legacy'
    assert b.post('/api/auth/import',json={'key':key.read_text()}).status_code==404
    assert (path/'profile.json').read_bytes()==original

def test_cross_device_commerce_and_revoked_cookie(clients):
    from test_commerce import request
    a,b,path=clients;adopt(a);discover(a);a.post('/api/quests/answer',json=answer());login(a,path)
    login(b,path,existing=True);b.post('/api/auth/decision',json={'choice':'account'})
    with ThreadPoolExecutor(2) as pool:
        purchases=list(pool.map(lambda c:c.post('/api/shop/purchase',json=request()).json(),[a,b]))
    assert sum(p['charged'] for p in purchases)==8
    placement=request(slot_id='window');old=a.get('/api/state').json()['revision']
    assert a.post('/api/room/place',json=placement).status_code==200
    assert b.post('/api/room/place',json=request(slot_id='door'),headers={'If-Match':old}).status_code==409
    assert b.post('/api/room/place',json=placement,headers={'If-Match':old}).status_code==200
    assert a.get('/api/state').json()==b.get('/api/state').json()
    assert b.get('/api/state').json()['room']=={'window':'window_plant'}
    token=b.cookies.get(accounts.COOKIE);b.post('/api/auth/logout')
    c=SessionClient(server.app);c.cookies.set(accounts.COOKIE,token)
    assert not c.get('/api/state').json()['adopted']


def test_expired_flow_and_secure_cookie(clients,monkeypatch):
    a,b,path=clients
    a.post('/api/auth/email',json={'email':'alice@example.test'})
    with accounts.Sessions(path).db() as db:db.execute('UPDATE sessions SET deadline=0')
    assert a.post('/api/auth/complete',json={'token_hash':'alice_examplelongdomain123456789'}).status_code==409
    monkeypatch.setenv('SGPAL_PUBLIC_URL','https://sgpal.example')
    c=SessionClient(server.app,base_url='https://sgpal.example')
    response=c.get('/api/auth/session')
    header=response.headers['set-cookie'].lower()
    assert 'secure' in header and 'httponly' in header and 'samesite=lax' in header

def test_supabase_adapter_contract(monkeypatch):
    import httpx
    monkeypatch.setenv('SUPABASE_URL','https://project.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY','test-publishable-not-a-secret')
    monkeypatch.setenv('SGPAL_PUBLIC_URL','http://127.0.0.1:8000')
    calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs))
        return httpx.Response(200,json={'user':{'id':str(uuid.uuid4()),'email':'Alice@example.test','email_confirmed_at':'2026-10-11T00:00:00Z'},'access_token':'must-not-return','refresh_token':'must-not-return'})
    monkeypatch.setattr(accounts.httpx,'post',post)
    provider=accounts.Provider();provider.send('alice@example.test')
    subject,email=provider.verify('a'*64)
    assert email=='alice@example.test'
    assert calls[0][1]['json']=={'email':'alice@example.test','create_user':True}
    assert calls[1][1]['json']=={'token_hash':'a'*64,'type':'email'}
    assert calls[1][1]['follow_redirects'] is False
    monkeypatch.setattr(accounts.httpx,'post',lambda *a,**kw:httpx.Response(200,json={'user':{'id':subject,'email':email}}))
    with pytest.raises(HTTPException) as exc:provider.verify('a'*64)
    assert exc.value.status_code==401
    def unavailable(*a,**kw):raise httpx.ConnectError('internal provider details')
    monkeypatch.setattr(accounts.httpx,'post',unavailable)
    with pytest.raises(HTTPException) as exc:provider.send(email)
    assert exc.value.status_code==503 and 'internal' not in exc.value.detail


def test_mutation_returns_current_revision(clients):
    a,_,_=clients
    result=a.post('/api/adopt',json={'species':'otter','name':'Kaya'}).json()
    assert result==a.get('/api/state').json()
    for enabled in (True,False):
        response=a.post('/api/sound',json={'enabled':enabled},headers={'If-Match':result['revision']})
        assert response.status_code==200
        result=response.json()
        assert result==a.get('/api/state').json()
