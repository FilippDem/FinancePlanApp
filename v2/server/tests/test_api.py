import json, os, sys, importlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2)); sys.path.insert(0, str(V2 / 'engine'))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    import server.app as appmod
    importlib.reload(appmod)
    return TestClient(appmod.app), tmp_path


def v08_household(tmp, hid='abc12345', email='filippdem@gmail.com'):
    (tmp / 'households').mkdir(parents=True, exist_ok=True)
    (tmp / 'households_index.json').write_text(json.dumps({hid: {'name': 'Home', 'members': [email]}}))
    plan = {'parent1_name': 'Filipp', 'parentX_age': 36, 'parentX_net_worth': 100000.0,
            'houses': [], 'future_v09_field': [1, 2, 3]}
    (tmp / 'households' / f'{hid}.json').write_text(json.dumps(
        {'household_name': 'Home', 'plan_data': plan, 'scenarios': {'Base': plan}, 'actuals': {'2025': {'x': 1}}}))
    return hid


def test_login_select_load_merge_save(client):
    c, tmp = client
    hid = v08_household(tmp)
    assert c.get('/api/me').json()['email'] is None
    c.post('/api/login', json={'email': 'FilippDem@gmail.com'})
    me = c.get('/api/me').json()
    assert me['email'] == 'filippdem@gmail.com' and me['households'][0]['id'] == hid
    assert c.get('/api/plan').status_code == 409
    c.post('/api/households/select', json={'id': hid})
    plan = c.get('/api/plan').json()['plan']
    assert plan['parent1_name'] == 'Filipp' and plan['future_v09_field'] == [1, 2, 3]
    # partial save must not drop other keys, scenarios or actuals
    r = c.put('/api/plan', json={'plan': {'parentX_age': 37}})
    assert r.status_code == 200
    stored = json.loads((tmp / 'households' / f'{hid}.json').read_text())
    assert stored['plan_data']['parentX_age'] == 37
    assert stored['plan_data']['future_v09_field'] == [1, 2, 3]
    assert stored['scenarios']['Base']['parent1_name'] == 'Filipp'
    assert stored['actuals'] == {'2025': {'x': 1}}
    assert list((tmp / 'backups').glob(f'{hid}_*.json')), 'backup must be written before save'


def test_non_member_cannot_select(client):
    c, tmp = client
    hid = v08_household(tmp)
    c.post('/api/login', json={'email': 'stranger@example.com'})
    assert c.post('/api/households/select', json={'id': hid}).status_code == 403


def test_cloudflare_header_identity(client):
    c, tmp = client
    hid = v08_household(tmp)
    h = {'Cf-Access-Authenticated-User-Email': 'filippdem@gmail.com'}
    assert c.get('/api/me', headers=h).json()['email'] == 'filippdem@gmail.com'
    assert c.post('/api/login', json={'email': 'x@y.z'}, headers=h).status_code == 400


def test_encrypted_household_compatible_with_v08(client):
    c, tmp = client
    from server import storage as S
    hid = 'enc00001'
    (tmp / 'households').mkdir(parents=True, exist_ok=True)
    (tmp / 'households_index.json').write_text(json.dumps({hid: {'name': 'E', 'members': ['a@b.c'], 'encrypted': True}}))
    enc = S.encrypt(json.dumps({'parent1_name': 'Secret'}), 'pw')
    (tmp / 'households' / f'{hid}.json').write_text(json.dumps({'household_name': 'E', 'encrypted': True, 'plan_data_encrypted': enc}))
    c.post('/api/login', json={'email': 'a@b.c'})
    assert c.post('/api/households/select', json={'id': hid, 'passphrase': 'bad'}).status_code == 403
    c.post('/api/households/select', json={'id': hid, 'passphrase': 'pw'})
    assert c.get('/api/plan').json()['plan']['parent1_name'] == 'Secret'
    c.put('/api/plan', json={'plan': {'parentX_age': 50}})
    stored = json.loads((tmp / 'households' / f'{hid}.json').read_text())
    assert 'plan_data' not in stored and 'plan_data_encrypted' in stored


def test_scenarios_and_engine_endpoints(client):
    c, tmp = client
    c.post('/api/login', json={'email': 'a@b.c'})
    hid = c.post('/api/households', json={'name': 'New'}).json()['id']
    plan = c.get('/api/plan').json()
    assert plan['is_new']
    c.post('/api/scenarios', json={'name': 'A', 'plan': plan['plan']})
    assert 'A' in c.get('/api/scenarios').json()['scenarios']
    c.post('/api/scenarios/rename', json={'name': 'A', 'new_name': 'B'})
    assert list(c.get('/api/scenarios').json()['scenarios']) == ['B']
    c.delete('/api/scenarios/B')
    assert c.get('/api/scenarios').json()['scenarios'] == {}
    pr = c.post('/api/project', json={'plan': plan['plan']}).json()
    assert pr['rows'] and pr['summary']
    mc = c.post('/api/montecarlo', json={'plan': plan['plan'], 'n': 200}).json()
    assert 0 <= mc['success_rate'] <= 1
    assert c.get('/api/demos').json()['demos']
    ref = c.get('/api/reference').json()
    assert 'Seattle' in ref['locations']
    t = c.post('/api/templates/children', json={'location': 'Seattle', 'strategy': 'Average'}).json()
    assert all(len(v) == 31 for v in t.values()) and t
