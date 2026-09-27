"""Linked accounts: SnapTrade signing/sync (mocked transport) and CSV import."""
import base64
import hashlib
import hmac
import json
import os

os.environ.setdefault('DISABLE_LINKED_SYNC', '1')

from server import linked as LK
from server.tests.test_api import client, v08_household  # noqa: F401  (fixture)

FIDELITY_CSV = '''Account Number,Account Name,Symbol,Description,Quantity,Last Price,Last Price Change,Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent,Total Gain/Loss Dollar,Total Gain/Loss Percent,Percent Of Account,Cost Basis Total,Average Cost Basis,Type
Z12345678,Individual,SPAXX**,HELD IN MONEY MARKET,,,,"$1,234.56",,,,,1.2%,,,Cash,
Z12345678,Individual,FXAIX,FIDELITY 500 INDEX FUND,100,$200.00,+$1.00,"$20,000.00",+$100.00,+0.50%,+$5000.00,+33.3%,98.8%,"$15,000.00",$150.00,Cash,
238765432,ROTH IRA,FSKAX,FIDELITY TOTAL MARKET INDEX,50,$150.00,,"$7,500.00",,,,,100%,,,Cash,
Z12345678,Individual,Pending Activity,,,,,-$34.56,,,,,,,,,

"The data and information in this spreadsheet is provided to you solely for your use and is not for distribution."
"Date downloaded 09/27/2026 10:00 AM ET"
'''


def test_signature_matches_documented_algorithm():
    pq = '/accounts?clientId=ABC&timestamp=1700000000'
    sig = LK.sign(pq, 'secret-key', None)
    obj = json.dumps({'content': None, 'path': '/api/v1/accounts', 'query': 'clientId=ABC&timestamp=1700000000'},
                     separators=(',', ':'), sort_keys=True)
    want = base64.b64encode(hmac.new(b'secret-key', obj.encode(), hashlib.sha256).digest()).decode()
    assert sig == want


def test_parse_fidelity_csv():
    accts = {a['number']: a for a in LK.parse_csv(FIDELITY_CSV)}
    assert abs(accts['Z12345678']['balance'] - 21200.00) < 0.01
    assert accts['238765432']['balance'] == 7500 and accts['238765432']['name'] == 'ROTH IRA'
    assert LK.guess_kind('ROTH IRA') == 'roth' and LK.guess_kind('Rollover IRA') == 'retirement' and LK.guess_kind('Individual') == 'liquid' and LK.guess_kind('Health Savings Account') == 'hsa'
    gen = LK.parse_csv('Account,Balance\nChecking,"$5,000"\nSavings,12000\n')
    assert {a['name']: a['balance'] for a in gen} == {'Checking': 5000, 'Savings': 12000}


def _fake_snaptrade(disabled=False):
    calls = []

    def transport(method, url, headers, body):
        calls.append((method, url, headers, body))
        assert 'Signature' in headers and 'clientId=' in url
        if '/authorizations' in url and method == 'GET':
            return 200, json.dumps([{'id': 'auth-1', 'disabled': disabled, 'brokerage': {'name': 'Fidelity', 'slug': 'FIDELITY'}}]).encode()
        if url.split('?')[0].endswith('/accounts'):
            return 200, json.dumps([
                {'id': 'acc-1', 'brokerage_authorization': 'auth-1', 'name': 'Individual', 'number': 'Z12345678', 'institution_name': 'Fidelity',
                 'raw_type': 'INDIVIDUAL', 'balance': {'total': {'amount': 150000.0, 'currency': 'USD'}}},
                {'id': 'acc-2', 'brokerage_authorization': 'auth-1', 'name': 'Traditional IRA', 'number': '111222333', 'institution_name': 'Fidelity',
                 'raw_type': 'IRA', 'balance': {'total': {'amount': 90000.0, 'currency': 'USD'}}}]).encode()
        if url.split('?')[0].endswith('/snapTrade/login'):
            assert json.loads(body)['connectionType'] == 'read'
            return 200, json.dumps({'redirectURI': 'https://app.snaptrade.com/connect?x=1', 'sessionId': 's'}).encode()
        return 404, b'{"detail":"nope"}'
    return transport, calls


def _login(c, tmp):
    hid = v08_household(tmp)
    c.post('/api/login', json={'email': 'filippdem@gmail.com'})
    c.post('/api/households/select', json={'id': hid})
    return hid


def test_linked_flow(client, monkeypatch):
    c, tmp = client
    hid = _login(c, tmp)
    transport, calls = _fake_snaptrade()
    monkeypatch.setattr(LK, '_urllib_transport', transport)
    # works without any setup: CSV import
    r = c.post('/api/linked/csv?institution=Fidelity&filename=pos.csv', content=FIDELITY_CSV.encode())
    assert r.status_code == 200 and len(r.json()['imported']) == 2
    assert not r.json()['snaptrade']['configured']
    # optional SnapTrade: keys are checked, stored server-side, never returned
    r = c.put('/api/linked/snaptrade', json={'client_id': 'CLIENT123', 'consumer_key': 'KEY-SECRET'})
    assert r.status_code == 200 and r.json()['snaptrade']['configured'] and 'KEY-SECRET' not in r.text
    stored = json.loads((tmp / 'households' / f'{hid}.json').read_text())
    assert stored['integrations']['snaptrade']['consumer_key'] == 'KEY-SECRET'
    assert stored['scenarios']['Base']['parent1_name'] == 'Filipp'      # merge-save kept everything else
    assert c.post('/api/linked/snaptrade/portal', json={}).json()['url'].startswith('https://')
    r = c.post('/api/linked/sync').json()
    snap = [a for a in r['accounts'] if a['source'] == 'snaptrade']
    assert len(snap) == 2 and r['last_error'] is None
    ira = next(a for a in snap if a['name'] == 'Traditional IRA')
    assert ira['kind'] == 'retirement' and ira['number'] == '…2333'
    # personal keys: no userId/userSecret on the wire
    assert all('userSecret' not in u for _, u, _, _ in calls)
    # map an account to person 2 and mark it separate
    r = c.patch(f"/api/linked/accounts/{ira['key']}", json={'owner': 'p2', 'separate': True}).json()
    t = r['totals']
    assert t['p2']['pretax'] == 90000 and t['p2']['separate_pretax'] == 90000
    assert t['p1']['liquid'] >= 150000
    # a broken connection keeps the last balances and is flagged
    transport2, _ = _fake_snaptrade(disabled=True)
    monkeypatch.setattr(LK, '_urllib_transport', transport2)
    r = c.post('/api/linked/sync').json()
    assert r['connections'][0]['disabled'] and any(a.get('disabled') for a in r['accounts'])
    # remove the keys: imported accounts stay
    r = c.delete('/api/linked/snaptrade').json()
    assert not r['snaptrade']['configured'] and len(r['accounts']) == 4


def test_bad_keys_rejected(client, monkeypatch):
    c, tmp = client
    _login(c, tmp)
    monkeypatch.setattr(LK, '_urllib_transport', lambda *a: (401, b'{"detail":"Invalid signature"}'))
    r = c.put('/api/linked/snaptrade', json={'client_id': 'X', 'consumer_key': 'bad'})
    assert r.status_code == 400 and 'Invalid signature' in r.text


def test_linked_needs_confirmation_before_driving_checkins():
    st = LK.empty_state()
    assert st['covers_all'] is None     # not asked yet: check-ins only show linked totals as a hint
    LK.apply_csv(st, LK.parse_csv(FIDELITY_CSV), 'Fidelity')
    t = LK.totals(st)
    assert t['accounts'] == 2 and not t['p1']['any_separate']
