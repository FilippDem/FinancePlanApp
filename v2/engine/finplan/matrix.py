"""Scenario matrix: every life scenario (2 kids vs 3, move or stay, retire at 55 or 60 ...) tested
against every economic condition (as planned, weak or strong markets, high inflation, a crash at
retirement, a 1970s-style decade, real market history).

A life scenario is a whole plan. An economic condition is a set of primitive stress events (see
stress.py / engine.py `_stress`) or a Monte Carlo setting, applied on top of it. All cells use the
same random seed, so every scenario sees the same market paths inside a column and differences come
from the plans, not from luck.
"""
from __future__ import annotations

import copy

from .engine import monte_carlo, project
from .plan import normalize_plan

ECONOMIES: dict[str, dict] = {
    'plan': {'label': 'As planned', 'desc': 'Your own assumptions from the Assumptions page'},
    'weak': {'label': 'Weak markets', 'desc': 'Investment returns 2 points lower every year'},
    'strong': {'label': 'Strong markets', 'desc': 'Investment returns 2 points higher every year'},
    'inflation': {'label': 'High inflation', 'desc': 'Inflation 1.5 points higher every year; pay catches up half of that'},
    'crash': {'label': 'Crash at retirement', 'desc': 'Markets fall 35% in the year the first person retires'},
    'seventies': {'label': '1970s-style decade', 'desc': '8% inflation for 6 years from next year (pay catches up halfway) and returns 3 points lower for 10 years'},
    'history': {'label': 'Real market history', 'desc': 'Yearly returns drawn from actual S&P 500 years since 1928, in order'},
    'rolling': {'label': 'Every historical start', 'desc': 'The plan run once from every start year 1924–2023 with the actual S&P 500 returns in order; the cell shows the share of start years that never ran out'},
}
DEFAULT_ECONOMIES = ['plan', 'weak', 'strong', 'inflation', 'crash']


def _first_retirement_year(p: dict) -> int:
    cy = p['current_year']
    ys = [cy + max(0, p['parentX_retirement_age'] - p['parentX_age'])]
    if p.get('parent2_name') not in (None, '', 'N/A'):
        ys.append(cy + max(0, p['parentY_retirement_age'] - p['parentY_age']))
    return max(cy, min(ys))


def apply_economy(plan: dict, econ: str) -> dict:
    """A copy of the plan under an economic condition (unknown ids = as planned)."""
    p = normalize_plan(copy.deepcopy(plan))
    cy = p['current_year']
    ev = list(p.get('_stress') or [])
    base_infl = p['economic_params']['inflation_rate']
    if econ == 'weak':
        ev.append({'type': 'return_shift', 'shift': -0.02})
    elif econ == 'strong':
        ev.append({'type': 'return_shift', 'shift': 0.02})
    elif econ == 'inflation':
        ev.append({'type': 'inflation_spike', 'start_year': cy, 'years': 200, 'rate': base_infl + 0.015, 'wage_passthrough': 50})
    elif econ == 'crash':
        ev.append({'type': 'market_crash', 'year': _first_retirement_year(p), 'drop': -0.35})
    elif econ == 'seventies':
        ev.append({'type': 'inflation_spike', 'start_year': cy + 1, 'years': 6, 'rate': 0.08, 'wage_passthrough': 50})
        ev.append({'type': 'return_shift', 'shift': -0.03, 'start_year': cy + 1, 'years': 10})
    elif econ == 'history':
        p['mc_use_historical'] = True
        p['mc_historical_mode'] = 'sequential'
    if ev:
        p['_stress'] = ev
    return p


def _row_facts(plan: dict) -> dict:
    """Short description of a life scenario for the table."""
    p = normalize_plan(plan)
    kids = p.get('children_list') or []
    stl = p.get('state_timeline') or []
    places = []
    for e in stl:
        if not places or places[-1] != e['state']:
            places.append(e['state'])
    couple = p.get('parent2_name') not in (None, '', 'N/A')
    return {'kids': len(kids), 'places': places,
            'retire': [p['parentX_retirement_age']] + ([p['parentY_retirement_age']] if couple else []),
            'homes': len(p.get('houses') or [])}


def evaluate(plan: dict, economies: list[str] | None = None, n: int = 300, seed: int = 11,
             target: float = 0.85) -> dict:
    """One life scenario across economic conditions."""
    econs = [e for e in (economies or DEFAULT_ECONOMIES) if e in ECONOMIES] or ['plan']
    n = max(50, min(int(n), 2000))
    cells = {}
    for e in econs:
        p = apply_economy(plan, e)
        if e == 'rolling':
            from .backtest import run as _bt
            bt = _bt(p)
            pr = project(p)
            rows, s = pr['rows'], pr['summary']
            last = rows[-1]
            low = min(rows, key=lambda r: r['investable'] / r['infl_index'])
            cells[e] = {'success': bt['success_rate'], 'ok': bt['success_rate'] >= target,
                        'final_median': bt['median_final'], 'final_p10': bt['p10_final'],
                        'depletion_year': s['depletion_year'], 'end_net_worth': last['net_worth'] / last['infl_index'],
                        'lowest_savings': low['investable'] / low['infl_index'], 'lowest_year': low['year'],
                        'median_path': bt['median_path'], 'years': bt['years'],
                        'worst_starts': [w['year'] for w in bt['worst'] if not w['ok']]}
            continue
        mc = monte_carlo(p, n, seed=seed, normalized=True)
        pr = project(p)
        rows, s = pr['rows'], pr['summary']
        last = rows[-1]
        low = min(rows, key=lambda r: r['investable'] / r['infl_index'])
        cells[e] = {'success': mc['success_rate'], 'ok': mc['success_rate'] >= target,
                    'final_median': mc['final']['median'], 'final_p10': mc['final']['p10'],
                    'depletion_year': s['depletion_year'],
                    'end_net_worth': last['net_worth'] / last['infl_index'],
                    'lowest_savings': low['investable'] / low['infl_index'], 'lowest_year': low['year'],
                    'median_path': mc['net_worth']['50'], 'years': mc['years']}
    passed = [e for e in econs if cells[e]['ok']]
    base_ok = cells[econs[0]]['ok'] if 'plan' not in cells else cells['plan']['ok']
    if len(passed) == len(econs):
        verdict = 'robust'
    elif base_ok:
        verdict = 'fragile'
    else:
        verdict = 'fails'
    return {'cells': cells, 'economies': econs, 'target': target, 'passed': len(passed), 'total': len(econs),
            'worst': min(econs, key=lambda e: cells[e]['success']), 'verdict': verdict, 'facts': _row_facts(plan)}


# ── variant builder: make a life scenario from the current plan ──────────────────────────────
def build_variant(plan: dict, changes: dict) -> dict:
    """Apply simple life changes to a copy of the plan.

    changes keys (all optional):
      kids: target number of children (adds children born from `kid_years` or 2 years apart from next
            year; removes the youngest ones when lower)
      kid_years: [birth years for added children]
      move: {location, year, lifestyle?}   add a move (replaces moves on or after that year)
      retire_x / retire_y: retirement ages
      lifestyle: spending lifestyle label for every period (Conservative / Average / High-end ...)
    """
    p = copy.deepcopy(plan)
    cy = int(p.get('current_year') or normalize_plan(p)['current_year'])
    kids = list(p.get('children_list') or [])
    loc0 = ((p.get('state_timeline') or [{}])[0] or {}).get('state', 'Seattle')
    if changes.get('kids') is not None:
        want = max(0, int(changes['kids']))
        if want < len(kids):
            kids = sorted(kids, key=lambda c: c.get('birth_year', 0))[:want]
        years = list(changes.get('kid_years') or [])
        last_birth = max([int(c.get('birth_year', cy)) for c in kids] + [cy - 1])
        names = {c.get('name') for c in kids}
        while len(kids) < want:
            by = int(years.pop(0)) if years else max(cy + 1, last_birth + 2)
            last_birth = by
            k = len(kids) + 1
            nm = f'Child {k}'
            while nm in names:
                k += 1
                nm = f'Child {k}'
            names.add(nm)
            kids.append({'name': nm, 'birth_year': by, 'use_template': True, 'template_state': loc0,
                         'template_strategy': 'Average', 'school_type': 'Public', 'college_type': 'Public',
                         'college_location': loc0})
        p['children_list'] = kids
    mv = changes.get('move')
    if mv and mv.get('location') and mv.get('year'):
        stl = [e for e in (p.get('state_timeline') or []) if int(e['year']) < int(mv['year'])]
        prev = stl[-1] if stl else {'spending_strategy': 'Average'}
        stl.append({'year': int(mv['year']), 'state': mv['location'],
                    'spending_strategy': mv.get('lifestyle') or prev.get('spending_strategy', 'Average')})
        p['state_timeline'] = stl
    for w in ('x', 'y'):
        v = changes.get(f'retire_{w}')
        if v is not None:
            p[f'parent{w.upper()}_retirement_age'] = int(v)
    if changes.get('lifestyle'):
        for e in p.get('state_timeline') or []:
            e['spending_strategy'] = changes['lifestyle']
    return p
