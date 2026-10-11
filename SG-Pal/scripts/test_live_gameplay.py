"""Opt-in real recognition → confirmed discovery → player-reported quest completion.
Uses temporary progress, never the running server's save. One paid image request.
"""
import argparse
import base64
import json
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from core import BY_ID, normalise
from sgpal import server
from sgpal.gameplay import GameStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--expected-id', required=True, choices=BY_ID)
    parser.add_argument('--allow-live', action='store_true', help='Explicitly allow one paid OpenAI request')
    args = parser.parse_args()
    if not args.allow_live:
        parser.error('Pass --allow-live to send this image to OpenAI using your configured credential.')
    if not server.credential_present():
        parser.error('Configure the existing key securely with python configure_key.py first.')
    raw = args.image.read_bytes()
    normalized = normalise(raw)
    with tempfile.TemporaryDirectory(prefix='sgpal-live-test-') as directory:
        server.DATA = Path(directory)
        client = TestClient(server.app)
        def post(route, body):
            response = client.post('/api/'+route, json=body)
            if response.status_code != 200:
                raise RuntimeError(f"{route}: HTTP {response.status_code}: {response.json().get('detail')}")
            return response.json()
        post('adopt', {'species':'otter', 'name':'LiveTest'})
        oid = str(uuid.uuid4())
        scan = post('scan', {'operation_id':oid,'image':base64.b64encode(raw).decode()})
        assert scan['state']['xp'] == 0 and scan['state']['coins'] == 0
        if scan['status'] != 'candidate' or scan['culture_id'] != args.expected_id:
            print('No expected confident match. No discovery confirmed and no rewards granted.')
            return 2
        found = post('confirm', {'operation_id':oid})
        assert found['reward'] == {'xp':10,'coins':5}
        cid = args.expected_id
        record = found['state']['log'][cid]
        assert record['timestamp_sgt'].endswith('+08:00')
        assert client.get(record['photo_url']).content == normalized
        assert found['state']['active'] == cid
        def answer(done):
            return {'operation_id':str(uuid.uuid4()), 'culture_id':cid, 'done':done}
        later = post('quests/answer', answer(False))
        assert later['status']=='not_done' and later['state']['xp']==10
        request = answer(True)
        completed = post('quests/answer', request)
        assert completed['reward']=={'xp':25,'coins':10}
        assert completed['state']['quest_details'][cid]['completion_method']=='self_reported'
        assert completed['state']['quest_details'][cid]['completed_sgt'].endswith('+08:00')
        post('confirm', {'operation_id':oid})
        post('quests/answer', request)
        assert post('quests/answer', answer(True))['reward']=={'xp':0,'coins':0}
        persisted = GameStore(directory).state()
        assert persisted['xp']==35 and persisted['coins']==15
        report = {'passed':True,'recognition':'live OpenAI','input_file':args.image.name,
                  'quest_completion':'explicit player Done; no AI verification',
                  'xp':35,'coins':15,'user_save_modified':False}
        output = Path(__file__).resolve().parents[1]/'test-results'
        output.mkdir(exist_ok=True)
        (output/'live-api-validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
