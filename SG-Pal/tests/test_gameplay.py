"""Real routes/storage with an injected recognizer. Never calls a paid provider."""
import base64
import io
import json
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from PIL import Image
from session_client import SessionClient as TestClient
from core import Store, normalise
from sgpal import server
from sgpal.gameplay import GameStore


def photo(color='orange', format='PNG'):
    out=io.BytesIO(); Image.new('RGB',(160,120),color).save(out,format)
    return base64.b64encode(out.getvalue()).decode()


def body(color='orange', **extra):
    return {'operation_id':str(uuid.uuid4()), 'image':photo(color), **extra}


def result(cid='kopi', confidence='high', verified=False):
    return {'culture_id':cid,'confidence':confidence,'verified':verified,'observation':'A readable kopi-C menu is visible.'}


@pytest.fixture
def game(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'data_dir',lambda:tmp_path)
    monkeypatch.setattr(server,'credential_present',lambda:True)
    monkeypatch.setattr(server,'recognise',lambda image,quest=None,correction=None: result(quest['id'] if quest else correction['id'] if correction else 'kopi',verified=bool(quest)))
    client=TestClient(server.app)
    client.post('/api/adopt',json={'species':'otter','name':'Kaya'})
    return client,tmp_path


def discover(client, color='orange'):
    scan=client.post('/api/scan',json=body(color)).json()
    assert scan['status']=='candidate'
    return client.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()


def test_complete_flow_photos_and_reload(game):
    c,path=game
    request=body();scan=c.post('/api/scan',json=request).json()
    assert scan['status']=='candidate' and scan['state']['xp']==0 and scan['state']['coins']==0
    found=c.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()
    assert found['reward']=={'xp':10,'coins':5}
    assert found['state']['active']=='kopi'
    record=found['state']['log']['kopi']
    assert record['timestamp_sgt'].endswith('+08:00')
    image=c.get(record['photo_url']);assert image.status_code==200
    assert image.content==normalise(base64.b64decode(request['image']))
    evidence=answer()
    verified=c.post('/api/quests/answer',json=evidence).json()
    assert verified['status']=='completed' and verified['reward']=={'xp':25,'coins':10}
    assert verified['state']['xp']==35 and verified['state']['coins']==15
    assert verified['state']['completed']==['kopi']
    quest=verified['state']['quest_details']['kopi']
    assert quest['completed_sgt'].endswith('+08:00')
    assert quest['evidence_url'] is None and quest['completion_method']=='self_reported'
    assert GameStore(path).state()['xp']==35
    assert c.get('/api/operations/'+evidence['operation_id']).json()['status']=='completed'
    for _ in range(3):
        assert c.post('/api/quests/answer',json=evidence).json()['state']['xp']==35
        assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()['state']['coins']==15
    assert discover(c,'green')['status']=='duplicate'
    assert c.post('/api/quests/answer',json=answer()).json()['status']=='duplicate'
    with sqlite3.connect(path/'gameplay.sqlite3') as db:
        assert db.execute('SELECT count(*) FROM rewards').fetchone()[0]==2


@pytest.mark.parametrize('confidence,cid', [('low','kopi'),('medium','kopi'),('high','unknown')])
def test_uncertain_never_confirmed(game,monkeypatch,confidence,cid):
    c,_=game;monkeypatch.setattr(server,'recognise',lambda *args:result(cid,confidence))
    scan=c.post('/api/scan',json=body()).json()
    assert scan['status']=='uncertain'
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).status_code==409
    assert c.get('/api/state').json()['xp']==0


def test_catalogue_validation_and_correction_reassessed(game,monkeypatch):
    c,_=game
    scan=c.post('/api/scan',json=body()).json()
    correction={'operation_id':str(uuid.uuid4()),'source_operation_id':scan['operation_id'],'culture_id':'kaya'}
    calls=[]
    def recognise(image,quest,alternative):
        calls.append(alternative['id']);return result('kaya')
    monkeypatch.setattr(server,'recognise',recognise)
    corrected=c.post('/api/correct',json=correction).json()
    assert calls==['kaya'] and corrected['status']=='candidate'
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).status_code==409
    assert c.get('/api/state').json()['xp']==0
    assert c.post('/api/confirm',json={'operation_id':corrected['operation_id']}).json()['state']['discoveries']==['kaya']
    assert c.post('/api/correct',json={**correction,'culture_id':'invented'}).status_code==422
    monkeypatch.setattr(server,'recognise',lambda *args:result('invented'))
    assert c.post('/api/scan',json=body('black')).status_code==502
    assert c.get('/api/state').json()['xp']==10


@pytest.mark.parametrize('cid', ['kopi', 'kaya', 'invented'])
def test_quest_photo_route_retired_without_ai_or_rewards(game,monkeypatch,cid):
    c,_=game;discover(c)
    monkeypatch.setattr(server,'recognise',lambda *args:pytest.fail('No quest AI call'))
    assert c.post('/api/verify',json=body('blue',quest_id=cid)).status_code==410
    assert c.get('/api/state').json()['xp']==10


def test_provider_failure_retry_and_id_conflict(game,monkeypatch):
    c,_=game;request=body()
    def fail(*args): raise RuntimeError('Could not reach AI. Check connection and retry.')
    monkeypatch.setattr(server,'recognise',fail)
    assert c.post('/api/scan',json=request).status_code==502
    assert c.get('/api/operations/'+request['operation_id']).json()['status']=='failed'
    assert c.get('/api/state').json()['xp']==0
    calls=[]
    monkeypatch.setattr(server,'recognise',lambda *args:calls.append(1) or result())
    assert c.post('/api/scan',json=request).json()['status']=='candidate'
    assert c.post('/api/scan',json=request).json()['status']=='candidate'
    assert calls==[1]
    assert c.post('/api/scan',json={**request,'image':photo('blue')}).status_code==409


def test_pending_request_does_not_make_second_provider_call(game,monkeypatch):
    c,_=game;entered=threading.Event();release=threading.Event();request=body()
    def recognise(*args):entered.set();release.wait(5);return result()
    monkeypatch.setattr(server,'recognise',recognise)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(c.post,'/api/scan',json=request)
        assert entered.wait(3)
        try:
            assert c.post('/api/scan',json=request).json()['status']=='pending'
            assert c.get('/api/state').json()['xp']==0
        finally:release.set()
        assert first.result().json()['status']=='candidate'


def test_concurrent_confirm_and_answers_award_once(game):
    c,path=game
    ids=[c.post('/api/scan',json=body(color)).json()['operation_id'] for color in ['orange','green']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda oid:c.post('/api/confirm',json={'operation_id':oid}).json(),ids))
    assert sorted(o['status'] for o in outcomes)==['confirmed','duplicate']
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda color:c.post('/api/quests/answer',json=answer()).json(),['blue','purple']))
    assert sorted(o['status'] for o in outcomes)==['completed','duplicate']
    assert GameStore(path).state()['coins']==15


def test_migration_preserves_legacy_progress_and_demo(game):
    c,path=game
    old=Store(path/'progress.json');old.discover('chope','old');old.activate('chope');old.finish('chope','evidence');old.discover('kopi','old2');old.activate('kopi')
    old_bytes=old.path.read_bytes()
    (path/'demo-progress.json').write_text('{"xp":9999}')
    scan=c.post('/api/scan',json=body()).json()
    assert scan['state']['xp']==45 and scan['state']['coins']==0
    assert scan['state']['completed']==['chope'] and scan['state']['active']=='kopi'
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()['status']=='duplicate'
    assert old.path.read_bytes()==old_bytes
    assert c.get('/api/state').json()['coins']==0
    assert GameStore(path).state()['xp']==45


def test_corrupt_migration_and_missing_key_fail_closed(game,monkeypatch):
    c,path=game
    monkeypatch.setattr(server,'credential_present',lambda:False)
    assert c.post('/api/scan',json=body()).status_code==503
    assert not (path/'gameplay.sqlite3').exists()
    (path/'progress.json').write_text('{broken')
    monkeypatch.setattr(server,'credential_present',lambda:True)
    assert c.post('/api/scan',json=body()).status_code==503
    assert (path/'progress.json').read_text()=='{broken'


@pytest.mark.parametrize('image', ['not base64',base64.b64encode(b'not an image').decode(),photo('orange','GIF')])
def test_invalid_images_no_rewards(game,image):
    c,_=game
    assert c.post('/api/scan',json={'operation_id':str(uuid.uuid4()),'image':image}).status_code==422
    assert c.get('/api/state').json()['xp']==0


def test_reward_commit_failure_rolls_back_everything(game,monkeypatch):
    c,path=game;scan=c.post('/api/scan',json=body()).json()
    original=GameStore.reward
    def fail(db,event,xp,coins):
        original(db,event,xp,coins)
        raise sqlite3.OperationalError('simulated disk failure before commit')
    monkeypatch.setattr(GameStore,'reward',staticmethod(fail))
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).status_code==503
    state=c.get('/api/state').json()
    assert state['xp']==0 and state['coins']==0 and state['discoveries']==[]
    assert c.get('/api/operations/'+scan['operation_id']).json()['status']=='candidate'
    monkeypatch.setattr(GameStore,'reward',staticmethod(original))
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()['state']['coins']==5


def test_retry_after_reload_uses_persisted_photo(game,monkeypatch):
    c,_=game;request=body()
    monkeypatch.setattr(server,'recognise',lambda *args:(_ for _ in ()).throw(RuntimeError('Network unavailable.')))
    assert c.post('/api/scan',json=request).status_code==502
    monkeypatch.setattr(server,'recognise',lambda *args:result())
    retry=c.post('/api/retry',json={'operation_id':request['operation_id']}).json()
    assert retry['status']=='candidate' and retry['state']['xp']==0
    assert c.post('/api/confirm',json={'operation_id':request['operation_id']}).json()['state']['xp']==10


def test_expired_pending_reclaims_lease_and_ignores_old_worker(game):
    c,path=game;store=GameStore(path);oid=str(uuid.uuid4());image=normalise(base64.b64decode(photo()))
    _,old_lease=store.begin(oid,'scan',image)
    with sqlite3.connect(store.path) as db:db.execute('UPDATE operations SET started=0 WHERE id=?',(oid,))
    _,new_lease=store.begin(oid,'scan',image)
    assert old_lease!=new_lease
    assert store.finish(oid,old_lease,result())['status']=='pending'
    assert store.finish(oid,new_lease,result())['status']=='candidate'
    assert store.state()['xp']==0


def test_legacy_changes_after_migration_are_not_silently_lost(game):
    c,path=game;discover(c)
    (path/'progress.json').write_text(json.dumps({'xp':99,'log':{},'completed':[],'active':None}))
    response=c.get('/api/state')
    assert response.status_code==503
    assert 'Both saves are preserved' in response.json()['detail']
    assert json.loads((path/'progress.json').read_text())['xp']==99


def test_missing_credential_still_allows_reconciling_committed_result(game,monkeypatch):
    c,_=game;request=body();c.post('/api/scan',json=request)
    c.post('/api/confirm',json={'operation_id':request['operation_id']})
    monkeypatch.setattr(server,'credential_present',lambda:False)
    assert c.post('/api/scan',json=request).json()['status']=='confirmed'
    assert c.get('/api/operations/'+request['operation_id']).json()['state']['coins']==5


def test_old_pending_verification_cannot_restart_ai(game,monkeypatch):
    c,path=game;discover(c);store=GameStore(path)
    oid=str(uuid.uuid4())
    store.begin(oid,'verify',normalise(base64.b64decode(photo('blue'))),'kopi')
    monkeypatch.setattr(server,'recognise',lambda *args:pytest.fail('Retired verification must not call AI'))
    assert c.post('/api/retry',json={'operation_id':oid}).status_code==410
    assert c.post('/api/quests/answer',json=answer()).json()['state']['xp']==35


def test_legacy_verifier_also_requires_matching_catalogue_id(tmp_path):
    from app import App
    app=App(data_dir=tmp_path);app.store.discover('chope','old');app.store.activate('chope');app.quest_mode=True;app.photo=b'new'
    app.handle('recognised',result('kopi',verified=True))
    assert app.store.data['xp']==10 and app.store.data['completed']==[]


def test_real_provider_request_uses_image_schema_and_correction(monkeypatch):
    import core
    captured={}
    monkeypatch.setattr(core,'api_key',lambda:'test-only-placeholder')
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return json.dumps({'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result('kaya'))}]}]}).encode()
    def open_request(request,timeout,context):
        import ssl
        assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
        assert context.cert_store_stats()['x509_ca'] > 0
        captured.update(json.loads(request.data));assert request.full_url=='https://api.openai.com/v1/responses';assert timeout==35
        return Response()
    monkeypatch.setattr(core,'urlopen',open_request)
    assert core.recognise(b'image',None,core.BY_ID['kaya'])['culture_id']=='kaya'
    assert captured['store'] is False
    assert captured['text']['format']['strict'] is True
    assert captured['text']['format']['schema']['properties']['culture_id']['enum']==[*core.BY_ID,'unknown']
    content=captured['input'][0]['content']
    assert json.loads(content[0]['text'])['suggested_correction']['id']=='kaya'
    assert content[1]['type']=='input_image'


def answer(cid='kopi', done=True, oid=None):
    return {'operation_id':oid or str(uuid.uuid4()),'culture_id':cid,'done':done}


def test_quest_done_not_yet_and_reload_without_ai(game,monkeypatch):
    c,path=game;discover(c)
    monkeypatch.setattr(server,'recognise',lambda *args:pytest.fail('Quest answer must not call AI'))
    monkeypatch.setattr(server,'credential_present',lambda:False)
    later=c.post('/api/quests/answer',json=answer(done=False)).json()
    assert later['status']=='not_done' and later['state']['xp']==10 and later['state']['coins']==5
    assert later['state']['active']=='kopi' and later['state']['completed']==[]
    request=answer();done=c.post('/api/quests/answer',json=request).json()
    assert done['status']=='completed' and done['reward']=={'xp':25,'coins':10}
    detail=done['state']['quest_details']['kopi']
    assert detail['completion_method']=='self_reported' and detail['evidence_url'] is None
    assert detail['completed_sgt'].endswith('+08:00')
    assert done['state']['active'] is None
    assert c.get('/api/operations/'+request['operation_id']).json()['status']=='completed'
    assert c.post('/api/retry',json={'operation_id':request['operation_id']}).json()['state']['coins']==15
    assert c.post('/api/quests/answer',json=request).json()['state']['xp']==35
    for value in [True,False]:
        duplicate=c.post('/api/quests/answer',json=answer(done=value)).json()
        assert duplicate['status']=='duplicate' and duplicate['reward']=={'xp':0,'coins':0}
    assert GameStore(path).state()['xp']==35
    with sqlite3.connect(path/'gameplay.sqlite3') as db:
        assert db.execute('SELECT count(*) FROM rewards').fetchone()[0]==2


def test_quest_answer_validation_and_identity_conflict(game):
    c,_=game
    assert c.post('/api/quests/answer',json=answer()).status_code==409
    assert c.post('/api/quests/answer',json=answer('invented')).status_code==422
    assert c.post('/api/quests/answer',json=answer(done='false')).status_code==422
    scan=c.post('/api/scan',json=body()).json()
    assert c.post('/api/quests/answer',json=answer()).status_code==409
    c.post('/api/confirm',json={'operation_id':scan['operation_id']})
    assert c.post('/api/quests/answer',json=answer(oid=scan['operation_id'])).status_code==409
    request=answer(done=False);c.post('/api/quests/answer',json=request)
    assert c.post('/api/quests/answer',json={**request,'done':True}).status_code==409
    assert c.post('/api/scan',json={**body(),'operation_id':request['operation_id']}).status_code==409


def test_concurrent_quest_answers_reward_once(game):
    c,_=game;discover(c)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:c.post('/api/quests/answer',json=answer()).json(),range(4)))
    assert sorted(r['status'] for r in results)==['completed','duplicate','duplicate','duplicate']
    assert c.get('/api/state').json()['coins']==15


def test_quest_answer_rollback_then_retry(game,monkeypatch):
    c,path=game;discover(c);reward=GameStore.reward
    def fail(db,*args):
        reward(db,*args)
        raise sqlite3.OperationalError('test write failure')
    request=answer()
    with monkeypatch.context() as patch:
        patch.setattr(GameStore,'reward',staticmethod(fail))
        assert c.post('/api/quests/answer',json=request).status_code==503
    state=GameStore(path).state()
    assert state['xp']==10 and state['completed']==[]
    assert c.get('/api/operations/'+request['operation_id']).status_code==404
    assert c.post('/api/quests/answer',json=request).json()['state']['coins']==15


def test_v1_save_migration_preserves_verified_rewards_and_photos(game):
    c,path=game;discover(c)
    store=GameStore(path);oid=str(uuid.uuid4())
    _,lease=store.begin(oid,'verify',normalise(base64.b64decode(photo('blue'))),'kopi')
    store.finish(oid,lease,result('kopi',verified=True))  # Historical schema-1 record, not a live route.
    before=c.get('/api/state').json()
    with sqlite3.connect(path/'gameplay.sqlite3') as db:
        for table in ('room','inventory','commerce_operations','quest_answers'):
            db.execute('DROP TABLE '+table)
        db.execute("UPDATE meta SET value='1' WHERE key='version'")
    after=c.get('/api/state').json()
    assert after==before
    assert after['quest_details']['kopi']['completion_method']=='photo_verified'
    assert c.get(after['log']['kopi']['photo_url']).status_code==200
    assert c.post('/api/quests/answer',json=answer()).json()['reward']=={'xp':0,'coins':0}
    with sqlite3.connect(path/'gameplay.sqlite3') as db:
        assert db.execute("SELECT value FROM meta WHERE key='version'").fetchone()[0]=='3'


def test_discovery_photo_not_publicly_cached_or_embeddable(game):
    import stat
    c,path=game;found=discover(c)
    response=c.get(found['state']['log']['kopi']['photo_url'])
    assert response.headers['cache-control']=='private, no-store'
    assert response.headers['cross-origin-resource-policy']=='same-origin'
    assert response.headers['x-content-type-options']=='nosniff'
    assert stat.S_IMODE((path/'gameplay.sqlite3').stat().st_mode)==0o600


def test_correction_disagreement_is_not_confirmation(game,monkeypatch):
    c,_=game;scan=c.post('/api/scan',json=body()).json()
    monkeypatch.setattr(server,'recognise',lambda *args:result('kopi'))
    corrected=c.post('/api/correct',json={'operation_id':str(uuid.uuid4()),'source_operation_id':scan['operation_id'],'culture_id':'tray'}).json()
    assert corrected['status']=='uncertain'
    assert c.post('/api/confirm',json={'operation_id':corrected['operation_id']}).status_code==409
    assert c.get('/api/state').json()['coins']==0


def test_catalogue_quests_never_require_proof():
    from core import CULTURE, recognise
    assert [item['id'] for item in CULTURE[:3]]==['chope','kopi','tray']
    for item in CULTURE:
        assert not any(word in item['quest'].lower() for word in ['photo','verify','location check','proof'])
    with pytest.raises(RuntimeError,match='retired'):
        recognise(b'unused',CULTURE[0])


def test_native_answer_failure_preserves_memory_and_disk(tmp_path,monkeypatch):
    import core
    store=Store(tmp_path/'progress.json');store.discover('kopi','old');store.activate('kopi')
    before=store.path.read_bytes()
    assert not store.finish_self_reported(None)
    def fail(*args):raise OSError('test storage failure')
    monkeypatch.setattr(core,'atomic_json',fail)
    with pytest.raises(OSError):store.finish_self_reported('kopi')
    assert store.data['xp']==10 and store.data['completed']==[]
    assert store.path.read_bytes()==before


def test_general_local_context_has_no_catalogue_reward(game, monkeypatch):
    c,_ = game
    observation = 'A bicycle is visible. In Singapore, park connectors offer cycling routes; the photo does not establish its location.'
    monkeypatch.setattr(server, 'recognise', lambda *args, **kwargs: {**result('unknown', 'high'), 'observation': observation})
    scan = c.post('/api/scan', json=body()).json()
    assert scan['observation'] == observation
    assert scan['reward'] == {'xp': 0, 'coins': 0}
    assert c.post('/api/confirm', json={'operation_id': scan['operation_id']}).status_code == 409


def test_local_find_rewards_once_and_persists(game, monkeypatch):
    c,path = game
    def local(*args, **kwargs):
        return {**result('unknown','high'), 'singapore_related':True, 'discovery_key':'electric-fan', 'discovery_title':'A cooling companion', 'observation':'A floor fan. Singapore connection: Useful in humid weather.'}
    monkeypatch.setattr(server,'recognise',local)
    scan=c.post('/api/scan',json=body()).json()
    assert scan['status']=='candidate' and scan['reward']['coins']==0
    confirmed=c.post('/api/confirm',json={'operation_id':scan['operation_id']}).json()
    assert confirmed['reward']=={'xp':10,'coins':5}
    c.post('/api/confirm',json={'operation_id':scan['operation_id']})
    second=c.post('/api/scan',json=body('blue')).json()
    assert c.post('/api/confirm',json={'operation_id':second['operation_id']}).json()['status']=='duplicate'
    # Same photo cannot earn again under another AI-generated item key.
    monkeypatch.setattr(server,'recognise',lambda *a,**k:{**local(),'discovery_key':'standing-fan'})
    third=c.post('/api/scan',json=body()).json()
    assert c.post('/api/confirm',json={'operation_id':third['operation_id']}).json()['reward']['coins']==0
    state=c.get('/api/state').json()
    assert state['coins']==5 and state['xp']==10
    assert state['local_finds'][0]['item_key']=='electric-fan'
    assert not state['quests']


@pytest.mark.parametrize('fields', [dict(confidence='low'),dict(singapore_related=False),dict(discovery_key='../invalid'),dict(discovery_title='')])
def test_local_find_uncertain_or_invalid_never_rewards(game,monkeypatch,fields):
    c,_=game
    monkeypatch.setattr(server,'recognise',lambda *a,**k:{**result('unknown','high'),'singapore_related':True,'discovery_key':'fan','discovery_title':'Fan',**fields})
    scan=c.post('/api/scan',json=body()).json()
    assert scan['status']=='uncertain'
    assert c.post('/api/confirm',json={'operation_id':scan['operation_id']}).status_code==409
    assert c.get('/api/state').json()['coins']==0
