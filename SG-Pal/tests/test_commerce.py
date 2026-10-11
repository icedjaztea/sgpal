"""Earn through real game transactions with injected recognition; never seed coins."""
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_gameplay import game, discover, answer, body
from sgpal.gameplay import GameStore


def request(item='window_plant', **extra):
    return {'operation_id':str(uuid.uuid4()),'item_id':item,**extra}


def earn(c):
    discover(c)
    return c.post('/api/quests/answer',json=answer()).json()['state']


def buy(c,item='window_plant'):
    response=c.post('/api/shop/purchase',json=request(item));assert response.status_code==200
    return response.json()


def test_earn_buy_place_replace_reload(game):
    c,path=game;assert earn(c)['coins']==15
    before=c.get('/api/state').json()
    c.get('/api/shop')  # Previewing the catalogue has no effect.
    assert c.get('/api/state').json()==before
    result=buy(c)
    assert result['status']=='purchased' and result['charged']==8
    assert result['state']['coins']==7 and result['state']['xp']==35
    assert result['state']['inventory']==['window_plant']
    assert buy(c,'kopi_cup')['state']['coins']==2
    for item in ['window_plant','kopi_cup']:
        placed=c.post('/api/room/place',json=request(item,slot_id='window')).json()
        assert placed['status']=='placed' and placed['state']['room']=={'window':item}
    assert set(placed['state']['inventory'])=={'window_plant','kopi_cup'}
    c.post('/api/room/place',json=request('kopi_cup',slot_id='door'))
    state=GameStore(path).state()
    assert state['room']=={'door':'kopi_cup'} and state['coins']==2 and state['xp']==35
    assert set(state['inventory'])=={'window_plant','kopi_cup'}


def test_insufficient_and_owned_no_charges(game):
    c,_=game
    failed=buy(c);assert failed['status']=='insufficient' and failed['state']['coins']==0
    earn(c);buy(c)
    duplicate=buy(c);assert duplicate['status']=='owned' and duplicate['charged']==0
    assert duplicate['state']['coins']==7
    assert buy(c,'tile_display')['status']=='insufficient'
    assert c.get('/api/state').json()['inventory']==['window_plant']


def test_purchase_retry_and_concurrent_duplicates(game):
    c,_=game;earn(c);req=request()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:c.post('/api/shop/purchase',json=req).json(),range(4)))
    assert all(r['state']['coins']==7 for r in results)
    assert c.get('/api/operations/'+req['operation_id']).json()['status']=='purchased'
    assert c.post('/api/retry',json={'operation_id':req['operation_id']}).json()['state']['coins']==7
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:buy(c),range(4)))
    assert all(r['status']=='owned' and r['state']['coins']==7 for r in results)


def test_competing_items_never_overdraw(game):
    c,_=game;earn(c)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda item:buy(c,item),['window_plant','tile_display']))
    assert sorted(r['status'] for r in results)==['insufficient','purchased']
    assert c.get('/api/state').json()['coins'] in (3,7)
    assert c.get('/api/state').json()['xp']==35


def test_server_rejects_forged_prices_and_unowned_placement(game):
    c,_=game;earn(c)
    assert c.post('/api/shop/purchase',json=request(price=0,coins=999)).status_code==422
    assert c.post('/api/shop/purchase',json=request('invented')).status_code==422
    assert c.post('/api/room/place',json=request(slot_id='window')).status_code==409
    buy(c)
    assert c.post('/api/room/place',json=request(slot_id='ceiling')).status_code==422
    assert c.get('/api/state').json()['room']=={}


def test_operation_identity_across_actions_and_stale_placement(game):
    c,_=game;earn(c);req=request();c.post('/api/shop/purchase',json=req)
    assert c.post('/api/shop/purchase',json={**req,'item_id':'kopi_cup'}).status_code==409
    assert c.post('/api/room/place',json={**req,'slot_id':'window'}).status_code==409
    assert c.post('/api/scan',json={**body(),'operation_id':req['operation_id']}).status_code==409
    assert c.post('/api/quests/answer',json=answer(oid=req['operation_id'])).status_code==409
    buy(c,'kopi_cup');first=request(slot_id='window')
    c.post('/api/room/place',json=first)
    c.post('/api/room/place',json=request('kopi_cup',slot_id='window'))
    replay=c.post('/api/room/place',json=first).json()
    assert replay['state']['room']=={'window':'kopi_cup'}  # Old retry cannot undo newer placement.


def test_purchase_rollback_keeps_balance_and_inventory(game):
    c,path=game;earn(c);dbpath=path/'gameplay.sqlite3'
    with sqlite3.connect(dbpath) as db:
        db.execute("CREATE TRIGGER fail_purchase BEFORE INSERT ON commerce_operations BEGIN SELECT RAISE(ABORT,'test failure'); END")
    req=request();assert c.post('/api/shop/purchase',json=req).status_code==503
    state=c.get('/api/state').json();assert state['coins']==15 and state['inventory']==[]
    with sqlite3.connect(dbpath) as db:db.execute('DROP TRIGGER fail_purchase')
    assert c.post('/api/shop/purchase',json=req).json()['state']['coins']==7


def test_schema2_migration_preserves_all_game_progress(game):
    c,path=game;earn(c);before=c.get('/api/state').json()
    with sqlite3.connect(path/'gameplay.sqlite3') as db:
        for table in ('room','inventory','commerce_operations'):db.execute('DROP TABLE '+table)
        db.execute("UPDATE meta SET value='2' WHERE key='version'")
    assert c.get('/api/state').json()==before
    assert c.get(before['log']['kopi']['photo_url']).status_code==200
    assert buy(c)['state']['coins']==7
