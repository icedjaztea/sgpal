"""Real recovery credentials/sessions/stores. Only discovery AI is mocked."""
import hashlib
import pytest
from sgpal import accounts, server
from session_client import SessionClient
from test_accounts import clients, adopt
from test_gameplay import discover


def save(c):
    r=c.post('/api/auth/recovery/save');assert r.status_code==200,r.text
    return r.json()['code']

def restore(c,code):return c.post('/api/auth/recovery/restore',json={'code':code})


def test_recovery_progress_isolation_and_friend_visit(clients):
    a,b,path=clients;adopt(a);found=discover(a);before=a.get('/api/state').json();code=save(a)
    assert len(code)==68 and code.startswith('SGP-')
    assert a.get('/api/state').json()==before
    assert a.get('/api/auth/session').json()['recovery_enabled']
    with accounts.Sessions(path).db() as db:
        assert db.execute('SELECT hash FROM recovery').fetchone()[0]==hashlib.sha256(code.encode()).hexdigest()
    assert code.encode() not in (path/'accounts.sqlite3').read_bytes()
    old=b.cookies.get(accounts.COOKIE)
    assert restore(b,code).status_code==200
    assert b.cookies.get(accounts.COOKIE)!=old
    assert b.get('/api/state').json()==before
    revoked=SessionClient(server.app);revoked.cookies.set(accounts.COOKIE,old)
    assert not revoked.get('/api/state').json()['adopted']
    c=SessionClient(server.app);adopt(c,'Friend');save(c)
    assert c.get(found['state']['log']['kopi']['photo_url']).status_code==404
    assert c.get('/api/operations/'+found['operation_id']).status_code==404
    ac=a.get('/api/friends').json()['code'];cc=c.get('/api/friends').json()['code']
    assert restore(c,ac).status_code==401
    assert c.get('/api/friends/'+ac+'/room').status_code==403
    assert a.post('/api/friends',json={'code':cc,'action':'request'}).status_code==200
    assert c.post('/api/friends',json={'code':ac,'action':'accept'}).status_code==200
    room=c.get('/api/friends/'+ac+'/room').json()
    assert room['name']=='Kaya' and 'email' not in room and 'coins' not in room
    assert b.get('/api/friends').json()['friends'][0]['code']==cc
    assert b.post('/api/auth/logout').status_code==200
    assert not b.get('/api/state').json()['adopted']
    assert a.get('/api/state').json()==before


def test_unsaved_guest_cancel_and_failure_limit(clients):
    a,b,path=clients;adopt(a);code=save(a);adopt(b,'Other');before=b.get('/api/state').json()
    assert restore(b,code).status_code==409
    assert b.post('/api/auth/logout').status_code==409
    assert b.get('/api/state').json()==before
    other=save(b);assert restore(b,code).status_code==200
    assert restore(b,other).status_code==200
    assert b.get('/api/state').json()==before
    assert b.post('/api/auth/recovery/save').status_code==409
    c=SessionClient(server.app)
    for _ in range(5):assert restore(c,'invalid').status_code==401
    # Fresh Sessions objects read the same durable limit, no in-memory bypass.
    assert restore(c,code).status_code==429
    with accounts.Sessions(path).db() as db:
        assert db.execute('SELECT max(failures) FROM recovery_limits').fetchone()[0]>=5


def test_https_origin_cookie_and_csrf(clients,monkeypatch):
    _,_,path=clients;monkeypatch.setenv('SGPAL_PUBLIC_URL','https://sgpal.example')
    c=SessionClient(server.app,base_url='https://sgpal.example')
    response=c.get('/api/auth/session')
    assert 'Secure' in response.headers['set-cookie'] and 'HttpOnly' in response.headers['set-cookie']
    assert c.post('/api/auth/recovery/save',headers={'Origin':'https://evil.test'}).status_code==403
    assert c.post('/api/auth/recovery/save',headers={'X-SGPal-CSRF':'wrong'}).status_code==403
    assert c.post('/api/auth/recovery/save',headers={'Origin':'https://sgpal.example'}).status_code==200
    assert c.get('/api/state',headers={'Host':'evil.test'}).status_code==400
    assert c.get('/healthz').status_code==200
