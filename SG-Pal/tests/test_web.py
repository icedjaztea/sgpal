"""Integration contracts: UI adoption must never rewrite existing game progress."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from core import Store
from sgpal import server


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'DATA', tmp_path)
    return TestClient(server.app)


@pytest.mark.parametrize('species,name', [('merlion', 'Splash'), ('otter', 'Pebble'), ('mynah', 'Milo')])
def test_adoption_reload_and_repeat(client, tmp_path, species, name):
    assert not client.get('/api/state').json()['adopted']
    response = client.post('/api/adopt', json={'species': species, 'name': name})
    assert response.status_code == 200
    assert server.read_state()['name'] == name
    assert server.read_state()['species'] == species
    assert client.post('/api/adopt', json={'species': 'mynah', 'name': 'Pip'}).status_code == 409
    assert client.post('/api/sound', json={'enabled': True}).json()['sound'] is True
    assert json.loads((tmp_path / 'profile.json').read_text())['sound'] is True
    assert not (tmp_path / 'progress.json').exists()


@pytest.mark.parametrize('body', [
    {'species': 'cat', 'name': 'Kopi'}, {'species': 'otter', 'name': '   '},
    {'species': 'otter', 'name': 'Kopi', 'xp': 999},
    {'species': 'mynah', 'name': '<script>'},
])
def test_invalid_adoption_cannot_write(client, tmp_path, body):
    assert client.post('/api/adopt', json=body).status_code == 422
    assert not (tmp_path / 'profile.json').exists()


def test_preserve_existing_progress_and_ignore_demo(client, tmp_path):
    store = Store(tmp_path / 'progress.json')
    store.discover('chope', 'photo1')
    store.activate('chope')
    store.finish('chope', 'photo2')
    store.discover('kopi', 'photo3')
    store.activate('kopi')
    demo = Store(tmp_path / 'demo-progress.json')
    demo.discover('hawker', 'sample')
    paths = [store.path, demo.path]
    before = [p.read_bytes() for p in paths]
    state = client.post('/api/adopt', json={'species': 'otter', 'name': 'Kaya'}).json()
    assert state['xp'] == 45
    assert state['discoveries'] == ['chope', 'kopi']
    assert state['completed'] == ['chope'] and state['active'] == 'kopi'
    client.post('/api/sound', json={'enabled': True})
    for _ in range(2):
        for route in ('scan', 'verify'):
            assert client.post('/api/' + route, json={'verified': True, 'xp': 999}).status_code == 422
    assert [p.read_bytes() for p in paths] == before
    assert client.get('/api/state').json()['coins'] == 0


@pytest.mark.parametrize('filename,content', [
    ('profile.json', '{broken'), ('profile.json', '{"version":2}'),
    ('progress.json', '{broken'), ('progress.json', '{"xp":100}'),
])
def test_unreadable_saves_preserved(client, tmp_path, filename, content):
    path = tmp_path / filename
    path.write_text(content)
    assert client.get('/api/state').status_code == 503
    assert client.post('/api/adopt', json={'species': 'merlion', 'name': 'Kopi'}).status_code == 503
    assert client.post('/api/sound', json={'enabled': True}).status_code == 503
    assert path.read_text() == content


def test_failed_write_preserves_profile(client, tmp_path, monkeypatch):
    client.post('/api/adopt', json={'species': 'merlion', 'name': 'Kopi'})
    before = (tmp_path / 'profile.json').read_bytes()
    def fail(*args):
        raise OSError('Disk full')
    monkeypatch.setattr(server, 'atomic_json', fail)
    assert client.post('/api/sound', json={'enabled': True}).status_code == 503
    assert (tmp_path / 'profile.json').read_bytes() == before


def test_concurrent_adoption_has_one_winner(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda name: client.post('/api/adopt', json={'species': 'otter', 'name': name}), ['Kaya', 'Pebble']))
    assert sorted(r.status_code for r in responses) == [200, 409]


def test_origin_and_shared_catalogue(client):
    assert client.post('/api/adopt', headers={'Origin': 'https://elsewhere.example'}, json={'species': 'mynah', 'name': 'Pip'}).status_code == 403
    assert len(client.get('/api/catalogue').json()) == 10
    assert client.get('/').status_code == 200
    assert client.get('/assets/otter.png').status_code == 200
    assert client.get('/api/state').headers['cache-control'] == 'no-store'
