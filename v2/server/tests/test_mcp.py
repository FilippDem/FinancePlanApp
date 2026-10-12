import json, subprocess, sys
from pathlib import Path

import pytest

V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2)); sys.path.insert(0, str(V2 / 'engine'))


@pytest.fixture()
def mcp(tmp_path, monkeypatch):
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    import importlib
    import server.mcp_server as M
    importlib.reload(M)
    from server import storage as S
    hid = S.create_household('Demo', 'a@b.c')
    S.save_plan(hid, {'parent1_name': 'A', 'parent2_name': 'B', 'parentX_income': 100000,
                      'parentX_career_phases': [], 'parentY_career_phases': []}, 'a@b.c')
    return M, S, hid, tmp_path


def call(M, tool, **args):
    r = M.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': tool, 'arguments': args}})
    res = r['result']
    return res['isError'], (res['content'][0]['text'] if res['isError'] else json.loads(res['content'][0]['text']))


def test_protocol_handshake_and_tools(mcp):
    M, *_ = mcp
    init = M.handle({'jsonrpc': '2.0', 'id': 0, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}})
    assert init['result']['serverInfo']['name'] == 'financial-planner'
    assert M.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) is None
    names = {t['name'] for t in M.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})['result']['tools']}
    assert {'get_plan', 'propose_changes', 'apply_changes', 'run_scenarios', 'save_scenario'} <= names


def test_propose_writes_nothing_and_apply_saves_with_backup(mcp):
    M, S, hid, tmp = mcp
    err, plan = call(M, 'get_plan', household='Demo')
    assert not err and plan['summary']['people'][0]['income'] == 100000
    before = json.loads((tmp / 'households' / f'{hid}.json').read_text())
    err, prop = call(M, 'propose_changes', changes={'parentX_income': 150000, 'children_list': [{'name': 'Kid', 'birth_year': 2028}]})
    assert not err and prop['proposal_id']
    assert {'field': 'parentX_income', 'from': 100000.0, 'to': 150000.0} in prop['changes']
    assert 'success_rate' in prop['before'] and 'success_rate' in prop['after']
    assert json.loads((tmp / 'households' / f'{hid}.json').read_text()) == before        # nothing written yet
    err, ok = call(M, 'apply_changes', proposal_id=prop['proposal_id'])
    assert not err
    saved = S.load_plan(hid)
    assert saved['parentX_income'] == 150000 and saved['children_list'][0]['name'] == 'Kid'
    assert any(f.name.startswith(hid) for f in (tmp / 'backups').iterdir())
    err, again = call(M, 'apply_changes', proposal_id=prop['proposal_id'])
    assert err                                                                              # one use only


def test_stale_proposal_is_refused(mcp):
    M, S, hid, _ = mcp
    _, prop = call(M, 'propose_changes', changes={'parentX_income': 1})
    S.save_plan(hid, {'parentY_income': 5}, 'someone@else')
    err, msg = call(M, 'apply_changes', proposal_id=prop['proposal_id'])
    assert err and 'saved since' in msg
    assert S.load_plan(hid)['parentX_income'] == 100000


def test_merge_patch_and_scenarios(mcp):
    M, S, hid, _ = mcp
    assert M.merge_patch({'a': {'b': 1, 'c': 2}, 'l': [1]}, {'a': {'b': None, 'd': 3}, 'l': [2, 3]}) == {'a': {'c': 2, 'd': 3}, 'l': [2, 3]}
    err, res = call(M, 'save_scenario', name='Retire at 55', changes={'parentX_retirement_age': 55})
    assert not err and S.load_scenarios(hid)['Retire at 55']['parentX_retirement_age'] == 55
    err, mx = call(M, 'run_scenarios', economies=['plan', 'weak'], n=60)
    assert not err and [r['scenario'] for r in mx['scenarios']] == ['Current plan', 'Retire at 55']


def test_stdio_roundtrip(tmp_path):
    env = {**__import__('os').environ, 'DATA_DIR': str(tmp_path)}
    msgs = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'list_households', 'arguments': {}}}]
    p = subprocess.run([sys.executable, str(V2 / 'server' / 'mcp_server.py')], input='\n'.join(json.dumps(m) for m in msgs) + '\n',
                       capture_output=True, text=True, env=env, timeout=120)
    lines = [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
    assert [l['id'] for l in lines] == [1, 2] and lines[1]['result']['content'][0]['text'].strip() == '[]'
