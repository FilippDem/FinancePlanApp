"""Stress tests: what happens to the plan if something goes wrong?

Each test is a dict added to plan['_stress'] (never saved). Types:
  market_crash    {year, drop}                       e.g. -0.30 in the retirement year
  income_loss     {person: 1|2|'both', start_year, years, pct}
  extra_cost      {name, amount (today's $/yr), start_year, years}   care for a child or parent, LTC
  inflation_spike {start_year, years, rate}
  early_death     {person, year, life_insurance}
"""
from __future__ import annotations

import copy

from .engine import project, monte_carlo
from .plan import normalize_plan


def default_tests(plan: dict) -> list[dict]:
    p = normalize_plan(plan)
    cy = p['current_year']
    ret_year = cy + max(1, min(p['parentX_retirement_age'] - p['parentX_age'], 60))
    single = p.get('parent2_name') in ('N/A', '')
    return [
        {'id': 'crash', 'type': 'market_crash', 'label': 'Market crash at retirement', 'year': ret_year, 'drop': -0.35},
        {'id': 'job', 'type': 'income_loss', 'label': 'Job loss for a year', 'person': 1, 'start_year': cy + 1, 'years': 1, 'pct': 100},
        {'id': 'care', 'type': 'extra_cost', 'label': 'Long-term care for a family member', 'name': 'Family care', 'amount': 40000,
         'start_year': cy + 5, 'years': 10},
        {'id': 'inflation', 'type': 'inflation_spike', 'label': '1970s-style inflation', 'start_year': cy + 2, 'years': 6, 'rate': 0.08},
        {'id': 'death', 'type': 'early_death', 'label': 'Early death of a partner' if not single else 'Early death',
         'person': 2 if not single else 1, 'year': cy + 3, 'life_insurance': 0},
    ]


def _summ(plan: dict, n: int) -> dict:
    pr = project(plan)
    mc = monte_carlo(plan, n, seed=11, normalized=False)
    s = pr['summary']
    rows = pr['rows']
    ret = next((r for r in rows if r['year'] == s['retirement_year']), rows[-1])
    last = rows[-1]
    return {
        'success_rate': mc['success_rate'],
        'depletion_year': s['depletion_year'],
        'net_worth_at_retirement': ret['net_worth'] / ret['infl_index'],
        'net_worth_end': last['net_worth'] / last['infl_index'],
        'investable': [r['investable'] / r['infl_index'] for r in rows],
        'years': [r['year'] for r in rows],
    }


def run(plan: dict, tests: list[dict] | None = None, n: int = 500) -> dict:
    base_plan = normalize_plan(plan)
    tests = tests or default_tests(base_plan)
    base = _summ(base_plan, n)
    out = []
    for t in tests:
        sp = copy.deepcopy(base_plan)
        sp['_stress'] = [t]
        r = _summ(sp, n)
        r.update(id=t.get('id'), label=t.get('label', t['type']), test=t,
                 delta_success=r['success_rate'] - base['success_rate'],
                 delta_end=r['net_worth_end'] - base['net_worth_end'])
        out.append(r)
    worst = min(out, key=lambda r: r['success_rate']) if out else None
    return {'base': base, 'results': out, 'worst': worst['id'] if worst else None}
