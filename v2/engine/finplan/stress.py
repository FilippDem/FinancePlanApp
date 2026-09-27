"""Stress tests: what happens to the plan if something goes wrong?

A test is a dict. Primitive event types (the engine applies them via plan['_stress'],
which is never saved):
  market_crash    {year, drop}                       portfolio falls by `drop` (e.g. -0.5) in that year
  income_loss     {person: 1|2|'both', start_year, years, pct}
  extra_cost      {name, amount (today's $/yr), start_year, years}
  inflation_spike {start_year, years, rate, wage_passthrough (% of the extra inflation that raises pay, default 50)}
  early_death     {person, year, life_insurance}
Composite types (expanded here):
  disabled_child  {child, person, extra_cost, years_cost}  one parent stops working for good when the
                  child is born (v0.8 test), optionally plus a yearly care cost
  compound        {events: [tests...]}                 several events together (v0.8 compound test)
Any test can set  when: 'worst'  to search for the worst start year (v0.8 behaviour); otherwise the
year fields are used as given. Results report success rate, the per-percentile stoplight
(v0.8's 10/25/50/75/90 ✅/❌ table) and final net worth percentiles.
"""
from __future__ import annotations

import copy

import numpy as np

from .engine import project, monte_carlo
from .plan import normalize_plan, is_single

PCT_NAMES = (10, 25, 50, 75, 90)
_YEAR_KEYS = {'market_crash': 'year', 'income_loss': 'start_year', 'extra_cost': 'start_year',
              'inflation_spike': 'start_year', 'early_death': 'year'}


def _duration(t: dict) -> int:
    if t['type'] in ('income_loss', 'extra_cost', 'inflation_spike'):
        return int(t.get('years', 1))
    if t['type'] == 'compound':
        return max([_duration(e) for e in t.get('events', [])] + [1])
    return 1


def _names(p):
    return p.get('parent1_name', 'Person 1'), p.get('parent2_name', 'Person 2')


def default_tests(plan: dict) -> list[dict]:
    """The v0.8 stress-test set (worst-year search) plus the v2 additions."""
    p = normalize_plan(plan)
    cy = p['current_year']
    single = is_single(p)
    n1, n2 = _names(p)
    ret_year = cy + max(1, min(p['parentX_retirement_age'] - p['parentX_age'], 60))
    tests = [
        {'id': 'crash', 'type': 'market_crash', 'label': '50% market crash at the worst time', 'year': ret_year, 'drop': -0.50,
         'when': 'worst', 'group': 'v08'},
        {'id': 'hyperinflation', 'type': 'inflation_spike', 'label': 'Hyperinflation: 15% for 5 years', 'start_year': cy + 2,
         'years': 5, 'rate': 0.15, 'wage_passthrough': 50, 'when': 'worst', 'group': 'v08'},
    ]
    for i, ch in enumerate(p['children_list']):
        # v0.8: parent 2 retires immediately to care for the child (parent 1 if single)
        tests.append({'id': f'disabled_{i}', 'type': 'disabled_child', 'label': f"Disabled child: {ch['name']} (a parent stops working)",
                      'child': ch['name'], 'person': 1 if single else 2, 'extra_cost': 0, 'years_cost': 30, 'group': 'v08'})
    people = [(1, n1)] + ([] if single else [(2, n2)])
    for who, nm in people:
        tests.append({'id': f'unemployed_{who}', 'type': 'income_loss', 'label': f'{nm} unemployed for 3 years', 'person': who,
                      'start_year': cy + 1, 'years': 3, 'pct': 100, 'when': 'worst', 'group': 'v08'})
    tests += [
        {'id': 'care', 'type': 'extra_cost', 'label': 'Long-term care for a family member', 'name': 'Family care', 'amount': 40000,
         'start_year': cy + 5, 'years': 10, 'group': 'v2'},
        {'id': 'death', 'type': 'early_death', 'label': 'Early death of a partner' if not single else 'Early death',
         'person': 2 if not single else 1, 'year': cy + 3, 'life_insurance': 0, 'group': 'v2'},
    ]
    return tests


def expand(t: dict, p: dict, start: int | None = None) -> list[dict]:
    """Turn a test (optionally shifted to `start`) into primitive engine events."""
    t = copy.deepcopy(t)
    kind = t['type']
    if kind == 'compound':
        out = []
        for e in t.get('events', []):
            out += expand(e, p, start)
        return out
    if kind == 'disabled_child':
        ch = next((c for c in p['children_list'] if c['name'] == t.get('child')), None)
        if ch is None:
            return []
        s = max(p['current_year'], int(ch['birth_year']))
        ev = [{'type': 'income_loss', 'person': t.get('person', 2), 'start_year': s, 'years': 200, 'pct': 100}]
        if t.get('extra_cost'):
            ev.append({'type': 'extra_cost', 'name': f"Care for {ch['name']}", 'amount': t['extra_cost'], 'start_year': s,
                       'years': int(t.get('years_cost', 30))})
        return ev
    if start is not None and kind in _YEAR_KEYS:
        t[_YEAR_KEYS[kind]] = start
    return [t]


def _mc_summary(p: dict, n: int, seed: int = 11) -> dict:
    mc = monte_carlo(p, n, seed=seed, normalized=True)
    fail = 1 - mc['success_rate']
    fin = mc['final']
    return {'success_rate': mc['success_rate'],
            'stoplight': {str(q): bool(fail < q / 100) for q in PCT_NAMES},
            'final_nw': {str(q): mc['net_worth'][str(q)][-1] for q in PCT_NAMES},
            'final_median': fin['median'], 'depletion_year_median': mc['depletion_year_median']}


def _det_summary(p: dict) -> dict:
    pr = project(p)
    s = pr['summary']
    rows = pr['rows']
    ret = next((r for r in rows if r['year'] == s['retirement_year']), rows[-1])
    last = rows[-1]
    return {'depletion_year': s['depletion_year'],
            'net_worth_at_retirement': ret['net_worth'] / ret['infl_index'],
            'net_worth_end': last['net_worth'] / last['infl_index'],
            'investable': [r['investable'] / r['infl_index'] for r in rows],
            'years': [r['year'] for r in rows]}


def _with(p: dict, events: list) -> dict:
    sp = copy.deepcopy(p)
    sp['_stress'] = events
    return sp


def _candidates(t: dict, p: dict) -> list[int]:
    cy = p['current_year']
    end = cy + max(p['parentX_death_age'] - p['parentX_age'],
                   0 if is_single(p) else p['parentY_death_age'] - p['parentY_age'])
    dur = _duration(t)
    last = end - dur
    kinds = {e['type'] for e in (t.get('events') or [t])}
    if kinds <= {'income_loss'} or (t['type'] == 'income_loss'):
        who = t.get('person', 1) if t['type'] == 'income_loss' else 1
        ages = [p['parentX_retirement_age'] - p['parentX_age']]
        if not is_single(p):
            ages.append(p['parentY_retirement_age'] - p['parentY_age'])
        work_end = cy + (max(ages) if who == 'both' else ages[0] if int(who) == 1 else ages[-1])
        last = min(last, work_end - 1)
    return list(range(cy, max(cy, last) + 1))


def find_worst_year(t: dict, p: dict, n: int = 120) -> tuple[int | None, list]:
    """Search start years (coarse, then refine) for the lowest success rate."""
    cands = _candidates(t, p)
    if not cands:
        return None, []
    step = 1 if len(cands) <= 15 else 3 if len(cands) <= 60 else 4
    scored = {}

    def score(y):
        if y not in scored:
            sp = _with(p, expand(t, p, y))
            mc = monte_carlo(sp, n, seed=7, normalized=True)
            scored[y] = (mc['success_rate'], mc['final']['median'])
        return scored[y]
    for y in cands[::step]:
        score(y)
    best = min(scored, key=lambda y: scored[y])
    for y in range(best - step + 1, best + step):
        if y in cands:
            score(y)
    best = min(scored, key=lambda y: scored[y])
    curve = [{'year': y, 'success_rate': scored[y][0]} for y in sorted(scored)]
    return best, curve


WORST_CHILD = '__worst__'


def worst_child(t: dict, p: dict, n: int = 150) -> str | None:
    """v0.8 find_worst_case_disabled_child: the child whose disability hurts the plan most."""
    best, score = None, None
    for ch in p['children_list']:
        sp = _with(p, expand({**t, 'child': ch['name']}, p))
        mc = monte_carlo(sp, n, seed=5, normalized=True)
        sc = (mc['success_rate'], mc['final']['median'])
        if score is None or sc < score:
            best, score = ch['name'], sc
    return best


def resolve_children(t: dict, p: dict) -> dict:
    """Replace 'worst case' child placeholders (also inside compound tests) with a concrete child."""
    t = copy.deepcopy(t)
    if t['type'] == 'disabled_child' and (t.get('child') in (None, '', WORST_CHILD)):
        t['child'] = worst_child(t, p)
        t['auto_child'] = True
    if t['type'] == 'compound':
        t['events'] = [resolve_children(e, p) for e in t.get('events', [])]
    return t


def run(plan: dict, tests: list[dict] | None = None, n: int = 500) -> dict:
    base_plan = normalize_plan(plan)
    tests = tests if tests is not None else default_tests(base_plan)
    base = {**_det_summary(base_plan), **_mc_summary(base_plan, n)}
    out = []
    for t in tests:
        t = resolve_children(t, base_plan)
        worst_year, curve = (None, [])
        if t.get('when') == 'worst':
            worst_year, curve = find_worst_year(t, base_plan)
        elif t['type'] == 'compound' and t.get('start_year'):
            worst_year = int(t['start_year'])  # "pick the year": every event starts that year
        events = expand(t, base_plan, worst_year)
        sp = _with(base_plan, events)
        r = {**_det_summary(sp), **_mc_summary(sp, n)}
        r.update(id=t.get('id'), label=t.get('label', t['type']), test=t, events=events,
                 worst_year=worst_year, search=curve,
                 delta_success=r['success_rate'] - base['success_rate'],
                 delta_end=r['net_worth_end'] - base['net_worth_end'])
        out.append(r)
    worst = min(out, key=lambda r: r['success_rate']) if out else None
    total = len(out) * len(PCT_NAMES)
    passed = sum(sum(1 for v in r['stoplight'].values() if v) for r in out)
    rate = passed / total if total else 1.0
    verdict = ('excellent' if rate >= 0.8 else 'good' if rate >= 0.6 else 'moderate' if rate >= 0.4 else 'high_risk')
    return {'base': base, 'results': out, 'worst': worst['id'] if worst else None,
            'summary': {'total': total, 'passed': passed, 'rate': rate, 'verdict': verdict}}
