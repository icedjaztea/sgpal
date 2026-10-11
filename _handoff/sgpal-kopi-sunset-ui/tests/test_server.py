from fastapi.testclient import TestClient
from sgpal import server


def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DATA", tmp_path)
    return TestClient(server.app)


def test_adoption_persists_and_cannot_reset_rewards(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch)
    assert c.get('/api/state').json()['adopted'] is False
    r = c.post('/api/adopt', json={'species': 'otter', 'name': 'Kaya'})
    assert r.status_code == 200
    assert server.read_save()['name'] == 'Kaya'
    assert c.post('/api/adopt', json={'species': 'mynah', 'name': 'Pip'}).status_code == 409
    assert c.get('/api/state').json()['species'] == 'otter'


def test_invalid_species_or_blank_name_never_creates_save(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch)
    assert c.post('/api/adopt', json={'species': '../bad', 'name': 'Kopi'}).status_code == 422
    assert c.post('/api/adopt', json={'species': 'otter', 'name': '   '}).status_code == 422
    assert not (tmp_path/'save.json').exists()


def test_unconnected_ai_cannot_grant_rewards(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch)
    before = c.get('/api/state').json()
    for route in ['/api/scan', '/api/verify']:
        assert c.post(route, json={'verified': True, 'xp': 999}).status_code == 501
    assert c.get('/api/state').json() == before


def test_corrupt_save_is_preserved(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch)
    path = tmp_path/'save.json'
    path.write_text('{broken')
    assert c.get('/api/state').status_code == 503
    assert c.post('/api/adopt', json={'species': 'merlion', 'name': 'Kopi'}).status_code == 503
    assert path.read_text() == '{broken'
