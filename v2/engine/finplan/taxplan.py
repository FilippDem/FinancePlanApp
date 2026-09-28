"""Tax planning helpers (2026-09-28): Roth conversion strategies compared side by side, and the
ordinary-income bracket tops in today's dollars for the bracket chart."""
from __future__ import annotations

import copy

from .engine import project, monte_carlo
from .plan import normalize_plan, is_single
from .taxes import MFJ, SINGLE, STD_DED, TAX_BASE_YEAR

HEIR_TAX = 0.25   # pre-tax money left at the end is worth ~75% to heirs (they pay income tax on it)

STRATEGIES = [
    ('off', 'No conversions', {'mode': 'off'}),
    ('fill_12', 'Fill the 12% bracket', {'mode': 'fill_bracket', 'bracket': 0.12}),
    ('fill_22', 'Fill the 22% bracket', {'mode': 'fill_bracket', 'bracket': 0.22}),
    ('fill_24', 'Fill the 24% bracket', {'mode': 'fill_bracket', 'bracket': 0.24}),
    ('fill_32', 'Fill the 32% bracket', {'mode': 'fill_bracket', 'bracket': 0.32}),
]


def brackets(plan: dict) -> dict:
    p = normalize_plan(plan)
    infl = p['economic_params']['inflation_rate']
    k = (1 + infl) ** max(0, p['current_year'] - TAX_BASE_YEAR)
    status = 'single' if (is_single(p) or p.get('tax_filing_status') == 'single') else 'married'
    table = MFJ if status == 'married' else SINGLE
    return {'status': status, 'std_deduction': STD_DED[status] * k,
            'tops': [{'rate': r, 'top': (lim * k if lim != float('inf') else None)} for lim, r in table]}


def _score(p: dict, n: int, seed: int) -> dict:
    pr = project(p)
    rows, s = pr['rows'], pr['summary']
    last = rows[-1]
    ii = last['infl_index']
    after_tax_end = (last['net_worth'] - last['pretax'] * HEIR_TAX) / ii
    mc = monte_carlo(p, n, seed=seed, normalized=True)
    return {'lifetime_taxes': s['lifetime_taxes'], 'lifetime_irmaa': s['lifetime_irmaa'],
            'lifetime_conversions': s['lifetime_conversions'], 'after_tax_end': after_tax_end,
            'end_pretax': last['pretax'] / ii, 'end_roth': last['roth'] / ii,
            'success': mc['success_rate'], 'irmaa_years': len(s['irmaa_years']),
            'conversions_by_year': [[r['year'], r['roth_conversion'] / r['infl_index']] for r in rows if r['roth_conversion'] > 1]}


def compare(plan: dict, n: int = 300, seed: int = 11) -> dict:
    p = normalize_plan(plan)
    rc = p['roth_conversion']
    out = []
    for sid, label, cfg in STRATEGIES:
        q = copy.deepcopy(p)
        q['roth_conversion'] = {**rc, **cfg}
        out.append({'id': sid, 'label': label, 'settings': q['roth_conversion'], **_score(q, n, seed)})
    cur_id = 'off' if rc['mode'] == 'off' else (f"fill_{int(round(rc['bracket'] * 100))}" if rc['mode'] == 'fill_bracket' else 'current')
    if cur_id not in {x['id'] for x in out}:
        out.append({'id': 'current', 'label': f"Yours: ${rc['amount']:,.0f} a year", 'settings': rc, **_score(p, n, seed)})
        cur_id = 'current'
    best = max(out, key=lambda x: (round(x['after_tax_end'], -3), x['success']))
    base = next(x for x in out if x['id'] == 'off')
    for x in out:
        x['vs_none'] = x['after_tax_end'] - base['after_tax_end']
    return {'strategies': out, 'best': best['id'], 'current': cur_id, 'heir_tax': HEIR_TAX,
            'has_pretax': (p['parentX_pretax_balance'] + p['parentY_pretax_balance'] + p['pretax_401k']) > 0}
