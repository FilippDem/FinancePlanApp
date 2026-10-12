"""MCP server: lets Claude (Claude Desktop / Claude Code) read and edit household plans.

Runs over stdio with the plain MCP JSON-RPC protocol, so it needs nothing beyond the planner itself:

    python server/mcp_server.py            (from v2/, or app/ in the installed folder)

Data: DATA_DIR, else the installed layout's ../../data next to app/, else ./data.

Editing is always two steps. `propose_changes` validates a change, shows every field that would change
and its effect on the results, and writes nothing. `apply_changes` writes a proposal through the normal
storage path (timestamped backup, load-then-merge, version history). A proposal is refused if the plan was
saved by anyone else since it was made. Encrypted households need FINPLAN_PASSPHRASE.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # v2/ (repo) or app/ (installed)
sys.path[:0] = [str(ROOT), str(ROOT / 'engine')]
if 'DATA_DIR' not in os.environ:
    installed = ROOT.parent / 'data'                 # FinancialPlanner/app/server -> FinancialPlanner/data
    if (ROOT.parent / 'launcher').exists() and installed.exists():
        os.environ['DATA_DIR'] = str(installed)

from server import storage as S                      # noqa: E402
from finplan.plan import normalize_plan              # noqa: E402
from finplan.engine import project, monte_carlo      # noqa: E402

PROTOCOL = '2025-06-18'
USER = os.environ.get('FINPLAN_USER', 'Claude (MCP)')
PASSPHRASE = os.environ.get('FINPLAN_PASSPHRASE') or None
_proposals: dict[str, dict] = {}


# ── helpers ──────────────────────────────────────────────────────────────────────────────────
def _households() -> dict:
    return {hid: info for hid, info in S.load_index().items() if not hid.startswith(S.TEST_PREFIX)}


def _hid(household: str | None) -> str:
    hh = _households()
    if not hh:
        raise ValueError('No households yet. Create one in the planner first.')
    if not household:
        if len(hh) == 1:
            return next(iter(hh))
        raise ValueError('Several households exist; pass household (id or name): ' +
                         ', '.join(f"{i['name']} ({h})" for h, i in hh.items()))
    for hid, info in hh.items():
        if household in (hid, info.get('name')) or household.lower() == str(info.get('name', '')).lower():
            return hid
    raise ValueError(f'Unknown household {household!r}')


def _plan(hid: str) -> dict:
    return normalize_plan(S.load_plan(hid, PASSPHRASE) or {})


def merge_patch(target, patch):
    """RFC 7386 JSON merge patch: objects merge, null removes a key, anything else (lists too) replaces."""
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    out = copy.deepcopy(target) if isinstance(target, dict) else {}
    for k, v in patch.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = merge_patch(out.get(k), v)
    return out


def _flat(obj, prefix=''):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(_flat(v, f'{prefix}.{k}' if prefix else str(k)))
        return out
    if isinstance(obj, list):
        if all(not isinstance(x, (dict, list)) for x in obj):
            return {prefix: obj}
        out = {}
        for i, v in enumerate(obj):
            out.update(_flat(v, f'{prefix}[{i}]'))
        if not obj:
            out[prefix] = []
        return out
    return {prefix: obj}


def diff(a: dict, b: dict) -> list:
    fa, fb = _flat(a), _flat(b)
    return [{'field': k, 'from': fa.get(k), 'to': fb.get(k)}
            for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]


def outcome(p: dict, n: int = 400) -> dict:
    pr = project(p)
    s, last = pr['summary'], pr['rows'][-1]
    mc = monte_carlo(p, n, seed=11, normalized=True)
    return {'success_rate': round(mc['success_rate'], 3),
            'net_worth_end_todays_dollars': round(last['net_worth'] / last['infl_index']),
            'net_worth_at_retirement': round(s['net_worth_at_retirement'] or 0),
            'retirement_year': s['retirement_year'], 'runs_out_year': s['depletion_year'],
            'lifetime_taxes': round(s['lifetime_taxes'])}


def summary(p: dict) -> dict:
    pr = project(p)
    r0 = pr['rows'][0]
    people = [{'name': p.get('parent1_name') or 'Parent 1', 'age': p['parentX_age'], 'retire_at': p['parentX_retirement_age'],
               'savings': p['parentX_net_worth'], 'income': r0['wages1']}]
    if p.get('parent2_name') not in (None, '', 'N/A'):
        people.append({'name': p['parent2_name'], 'age': p['parentY_age'], 'retire_at': p['parentY_retirement_age'],
                       'savings': p['parentY_net_worth'], 'income': r0['wages2']})
    return {'year': p['current_year'], 'people': people,
            'kids': [{'name': c['name'], 'born': c['birth_year']} for c in p['children_list']],
            'homes': [{'name': h['name'], 'value': h['current_value'], 'mortgage': h['mortgage_balance']} for h in p['houses']],
            'places': [{'from': e['year'], 'where': e['state'], 'lifestyle': e['spending_strategy']} for e in p['state_timeline']],
            'this_year': {k: round(r0[k]) for k in ('total_income', 'taxes', 'total_expenses', 'cashflow', 'investable', 'net_worth')}}


# ── tools ────────────────────────────────────────────────────────────────────────────────────
def t_list_households(_):
    return [{'id': h, 'name': i.get('name'), 'members': i.get('members', []), 'encrypted': i.get('encrypted', False)}
            for h, i in _households().items()]


def t_get_plan(a):
    hid = _hid(a.get('household'))
    p = _plan(hid)
    out = {'household': hid, 'summary': summary(p), 'last_saved': S.household_info(hid).get('last_saved')}
    if a.get('full', True):
        out['plan'] = p
    return out


def t_run_analysis(a):
    hid = _hid(a.get('household'))
    p = _plan(hid)
    from finplan.solver import solve, safe_spending
    target = float(a.get('target', 0.85))
    res = {'household': hid, 'outcome': outcome(p, 500)}
    sol = solve(p, target=target, n=400)
    res['what_would_it_take'] = {'target': target, 'success': sol['success'], 'reached': sol['reached'],
                                 'levers': [{k: v for k, v in l.items() if k != 'patch'} for l in sol.get('levers', [])]}
    ss = safe_spending(p, target=target, n=300)
    res['safe_spending'] = {k: v for k, v in ss.items() if not isinstance(v, list)}
    return res


def t_run_scenarios(a):
    from finplan.matrix import evaluate, ECONOMIES
    hid = _hid(a.get('household'))
    econs = a.get('economies') or list(ECONOMIES)
    plans = {'Current plan': _plan(hid)}
    for name, sc in S.load_scenarios(hid).items():
        plans[name] = normalize_plan(json.loads(sc) if isinstance(sc, str) else sc)
    rows = []
    for name, pl in plans.items():
        ev = evaluate(pl, econs, n=int(a.get('n', 300)))
        rows.append({'scenario': name, 'verdict': ev['verdict'], 'passed': f"{ev['passed']}/{ev['total']}",
                     'success_by_economy': {ECONOMIES[e]['label']: round(c['success'] * 100) for e, c in ev['cells'].items()}})
    return {'household': hid, 'target': 0.85, 'scenarios': rows}


def t_propose_changes(a):
    hid = _hid(a.get('household'))
    changes = a.get('changes')
    if not isinstance(changes, dict) or not changes:
        raise ValueError('changes must be a non-empty object (JSON merge patch over the plan)')
    before = _plan(hid)
    after = normalize_plan(merge_patch(before, changes))
    d = diff(before, after)
    if not d:
        return {'proposal_id': None, 'message': 'Nothing would change.'}
    pid = uuid.uuid4().hex[:8]
    _proposals[pid] = {'household': hid, 'plan': after, 'note': a.get('note', ''),
                       'base_saved': S.household_info(hid).get('last_saved')}
    return {'proposal_id': pid, 'household': hid, 'changes': d[:200], 'changed_fields': len(d),
            'before': outcome(before), 'after': outcome(after),
            'next': 'Show these changes to the user. Only call apply_changes after they confirm.'}


def t_apply_changes(a):
    pr = _proposals.get(a.get('proposal_id') or '')
    if not pr:
        raise ValueError('Unknown or already applied proposal_id; call propose_changes first')
    hid = pr['household']
    if S.household_info(hid).get('last_saved') != pr['base_saved']:
        _proposals.pop(a['proposal_id'], None)
        raise ValueError('The plan was saved since this proposal was made; propose the change again')
    ts = S.save_plan(hid, pr['plan'], USER, PASSPHRASE)
    _proposals.pop(a['proposal_id'], None)
    return {'saved': ts, 'household': hid,
            'note': 'Saved with a backup (version history can restore it). Reload the planner window to see it.'}


def t_save_scenario(a):
    hid = _hid(a.get('household'))
    name = (a.get('name') or '').strip()
    if not name:
        raise ValueError('name is required')
    p = normalize_plan(merge_patch(_plan(hid), a.get('changes') or {}))
    sc = S.load_scenarios(hid)
    existed = name in sc
    sc[name] = p
    S.save_scenarios(hid, sc)
    return {'saved_scenario': name, 'replaced': existed, 'outcome': outcome(p)}


_H = {'type': 'string', 'description': 'Household id or name (optional when there is only one)'}
TOOLS = {
    'list_households': (t_list_households, 'List the households (plans) stored by the Financial Planner.',
                        {'type': 'object', 'properties': {}}),
    'get_plan': (t_get_plan, 'Read a household plan: a short summary plus the full plan JSON (the same keys the '
                 'app saves, e.g. parentX_income, parentX_job_changes, children_list, houses, state_timeline).',
                 {'type': 'object', 'properties': {'household': _H, 'full': {'type': 'boolean', 'default': True}}}),
    'run_analysis': (t_run_analysis, 'Results for the saved plan: Monte Carlo success rate, end net worth, what it '
                     'would take to reach a target success rate (or headroom above it), and safe spending.',
                     {'type': 'object', 'properties': {'household': _H, 'target': {'type': 'number', 'default': 0.85}}}),
    'run_scenarios': (t_run_scenarios, 'Scenario matrix: the current plan and every saved scenario under each '
                      'economic condition (as planned, weak/strong markets, high inflation, crash at retirement, '
                      '1970s, real history, every historical start).',
                      {'type': 'object', 'properties': {'household': _H, 'economies': {'type': 'array', 'items': {'type': 'string'}},
                                                        'n': {'type': 'integer', 'default': 300}}}),
    'propose_changes': (t_propose_changes, 'Propose an edit to the plan as a JSON merge patch (objects merge, null '
                        'removes, lists replace whole). Writes nothing: returns every changed field and the effect '
                        'on results. Show it to the user and apply only after they agree.',
                        {'type': 'object', 'required': ['changes'],
                         'properties': {'household': _H, 'changes': {'type': 'object'}, 'note': {'type': 'string'}}}),
    'apply_changes': (t_apply_changes, 'Save a proposal the user has confirmed (backed up, undoable from version history).',
                      {'type': 'object', 'required': ['proposal_id'], 'properties': {'proposal_id': {'type': 'string'}}}),
    'save_scenario': (t_save_scenario, 'Save a what-if copy of the plan (current plan + merge patch) to the scenario '
                      'library without changing the plan itself.',
                      {'type': 'object', 'required': ['name'],
                       'properties': {'household': _H, 'name': {'type': 'string'}, 'changes': {'type': 'object'}}}),
}


# ── JSON-RPC over stdio ──────────────────────────────────────────────────────────────────────
def handle(msg: dict) -> dict | None:
    mid, method, params = msg.get('id'), msg.get('method'), msg.get('params') or {}
    if mid is None:                                  # notification (e.g. notifications/initialized)
        return None
    try:
        if method == 'initialize':
            result = {'protocolVersion': params.get('protocolVersion') or PROTOCOL,
                      'capabilities': {'tools': {}},
                      'serverInfo': {'name': 'financial-planner', 'version': '2.0'},
                      'instructions': 'Household financial plans. Read with get_plan; edit only via propose_changes, '
                                      'show the diff, and apply_changes after the user confirms.'}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools': [{'name': n, 'description': d, 'inputSchema': s} for n, (_, d, s) in TOOLS.items()]}
        elif method == 'tools/call':
            fn = TOOLS.get(params.get('name'), (None,))[0]
            if fn is None:
                return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32602, 'message': f"Unknown tool {params.get('name')}"}}
            try:
                data = fn(params.get('arguments') or {})
                result = {'content': [{'type': 'text', 'text': json.dumps(data, default=str, indent=1)}], 'isError': False}
            except Exception as e:                   # tool errors go back to the model, not the protocol
                result = {'content': [{'type': 'text', 'text': f'Error: {e}'}], 'isError': True}
        else:
            return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}
        return {'jsonrpc': '2.0', 'id': mid, 'result': result}
    except Exception as e:
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32603, 'message': str(e)}}


def main():
    out = sys.stdout
    sys.stdout = sys.stderr                          # stray prints must never corrupt the protocol stream
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(msg)
        if reply is not None:
            out.write(json.dumps(reply, default=str) + '\n')
            out.flush()


if __name__ == '__main__':
    main()
