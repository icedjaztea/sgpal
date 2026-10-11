"""Focused social permissions: mocked identity provider, real database/sessions."""
from sgpal import accounts
from test_accounts import clients,login,adopt
from test_gameplay import discover,answer
from test_commerce import request

def code(c):return c.get('/api/friends').json()['code']
def action(c,code,verb):return c.post('/api/friends',json={'code':code,'action':verb})
def clear_rate(path):
    with accounts.Sessions(path).db() as db:db.execute("DELETE FROM limits WHERE key LIKE 'friend-request:%'")

def test_complete_flow_and_private_snapshot(clients):
    a,b,path=clients;adopt(a);adopt(b,'Pebble');login(a,path);login(b,path,'bob')
    ac,bc=code(a),code(b);assert ac!=bc and code(a)==ac
    room='/api/friends/'+bc+'/room';assert a.get(room).status_code==403
    assert action(a,bc,'request').status_code==200
    clear_rate(path);assert action(a,bc,'request').status_code==200
    assert len(b.get('/api/friends').json()['incoming'])==1
    assert a.get(room).status_code==403
    assert action(a,bc,'accept').status_code==409
    assert action(b,ac,'accept').status_code==200
    discover(b);b.post('/api/quests/answer',json=answer());b.post('/api/shop/purchase',json=request())
    b.post('/api/room/place',json=request(slot_id='window'))
    snapshots=[c.get('/api/state').json() for c in (a,b)]
    response=a.get(room);assert response.status_code==200
    public=response.json();assert set(public)=={'name','species','adopted','room','code','read_only'}
    assert public['room']=={'window':'window_plant'} and public['read_only']
    assert [c.get('/api/state').json() for c in (a,b)]==snapshots
    assert a.get(snapshots[1]['log']['kopi']['photo_url']).status_code==404
    assert 'email' not in a.get('/api/friends').text and '@' not in a.get('/api/friends').text
    assert action(a,bc,'remove').status_code==200
    assert a.get(room).status_code==403 and b.get('/api/friends/'+ac+'/room').status_code==403
    assert not b.get('/api/friends').json()['friends']
    assert action(a,bc,'remove').status_code==200

def test_auth_self_decline_and_rate(clients):
    a,b,path=clients
    assert a.get('/api/friends').status_code==401
    assert action(a,'A'*12,'request').status_code==401
    assert a.get('/api/friends/'+'A'*12+'/room').status_code==401
    login(a,path);login(b,path,'bob');ac,bc=code(a),code(b)
    assert action(a,ac,'request').status_code==400
    assert action(a,bc,'request').status_code==429
    clear_rate(path);assert action(a,bc,'request').status_code==200
    assert action(b,ac,'decline').status_code==200
    assert not a.get('/api/friends').json()['outgoing']
    assert a.get('/api/friends/'+bc+'/room').status_code==403
    assert action(b,ac,'accept').status_code==409
