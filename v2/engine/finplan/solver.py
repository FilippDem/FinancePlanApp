"""'What would it take?' — the smallest change to one lever that reaches a target success rate.

Each lever is searched on its own (the others unchanged) with a fixed Monte Carlo seed, so every
candidate sees the same market paths and the search is stable. When the plan already beats the
target, the same search runs the other way and reports the headroom (retire earlier / spend more).
"""
from __future__ import annotations

import copy

from .engine import monte_carlo
from .plan import normalize_plan, is_single

HOUSING = {'Mortgage/Rent', 'Property Tax', 'Home Insurance'}
# 2026 employee 401(k) limit per person under 50 (IRS; see data/sources.json irs_401k_2026)
LIMIT_401K = 24500

LEVERS = {
    'retire_later': {'label': 'Retire later', 'unit': 'years', 'hi': 10, 'step': 1, 'headroom': 'retire_earlier'},
    'spend_less': {'label': 'Spend less', 'unit': '%', 'hi': 40, 'step': 1, 'headroom': 'spend_more'},
    # (money you don't spend is already saved in this model, so "save more" = "spend less"; not a separate lever)
    'claim_later': {'label': 'Claim Social Security later', 'unit': 'years', 'hi': 8, 'step': 1, 'headroom': None},
}


def _working(p: dict) -> list[str]:
    out = []
    for w in ('X',) + (() if is_single(p) else ('Y',)):
        if p[f'parent{w}_age'] < p[f'parent{w}_retirement_age']:
            out.append(w)
    return out


def apply(plan: dict, lever: str, x: float) -> dict:
    """A copy of the plan with the lever moved by x (negative = the other direction)."""
    p = copy.deepcopy(plan)
    if lever in ('retire_later', 'retire_earlier'):
        d = int(round(x if lever == 'retire_later' else -x))
        for w in _working(p) or ['X']:
            ret = p[f'parent{w}_retirement_age'] + d
            p[f'parent{w}_retirement_age'] = int(max(p[f'parent{w}_age'] + (0 if d < 0 else 1), min(ret, p[f'parent{w}_death_age'] - 1)))
    elif lever in ('spend_less', 'spend_more'):
        k = 1 - x / 100 if lever == 'spend_less' else 1 + x / 100
        r10 = lambda v: round(v * k / 10) * 10
        for key in ('parentX_expenses', 'parentY_expenses'):
            p[key] = {c: r10(v) for c, v in (p.get(key) or {}).items()}
        p['family_shared_expenses'] = {c: (v if c in HOUSING else r10(v)) for c, v in (p.get('family_shared_expenses') or {}).items()}
        for r in p.get('recurring_expenses') or []:
            r['amount'] = r10(r['amount'])
    elif lever == 'claim_later':
        for w in ('X',) + (() if is_single(p) else ('Y',)):
            cur = p.get(f'parent{w}_ss_claim_age') or min(max(p[f'parent{w}_retirement_age'], 62), 70)
            p[f'parent{w}_ss_claim_age'] = int(min(70, max(62, round(cur + x))))
    elif lever == 'combined':
        # x in [0, 100]: a bit of everything, scaled together
        for sub, amt in combo_parts(plan, x).items():
            if amt:
                p = apply(p, sub, amt)
    return p


def combo_parts(plan: dict, x: float) -> dict:
    f = max(0.0, min(x, 100.0)) / 100
    working = _working(plan)
    return {'retire_later': int(round(5 * f)) if working else 0, 'spend_less': int(round(25 * f)),
            'claim_later': int(round(3 * f))}


def patch(plan: dict, lever: str, x: float) -> dict:
    """Only the keys that change, for the UI to apply."""
    p = apply(plan, lever, x)
    keys = {'retire_later': ('parentX_retirement_age', 'parentY_retirement_age'),
            'retire_earlier': ('parentX_retirement_age', 'parentY_retirement_age'),
            'spend_less': ('parentX_expenses', 'parentY_expenses', 'family_shared_expenses', 'recurring_expenses'),
            'spend_more': ('parentX_expenses', 'parentY_expenses', 'family_shared_expenses', 'recurring_expenses'),
            'claim_later': ('parentX_ss_claim_age', 'parentY_ss_claim_age'),
            'combined': ('parentX_retirement_age', 'parentY_retirement_age', 'parentX_expenses', 'parentY_expenses',
                         'family_shared_expenses', 'recurring_expenses', 'parentX_ss_claim_age', 'parentY_ss_claim_age')}[lever]
    return {k: p[k] for k in keys if k in p}


def _succ(p: dict, n: int, seed: int) -> float:
    return monte_carlo(p, n, seed=seed)['success_rate']


def _min_to_reach(p, lever, hi, step, target, n, seed):
    """Smallest multiple of step in (0, hi] reaching target, or None."""
    top = _succ(apply(p, lever, hi), n, seed)
    if top < target:
        return None, top
    lo_i, hi_i = 0, int(round(hi / step))
    best = top
    while hi_i - lo_i > 1:
        mid = (lo_i + hi_i) // 2
        s = _succ(apply(p, lever, mid * step), n, seed)
        if s >= target:
            hi_i, best = mid, s
        else:
            lo_i = mid
    return hi_i * step, best


def _max_keeping(p, lever, hi, step, target, n, seed):
    """Largest multiple of step in [0, hi] that still keeps success >= target."""
    lo_i, hi_i = 0, int(round(hi / step))
    if _succ(apply(p, lever, hi), n, seed) >= target:
        return hi, None
    while hi_i - lo_i > 1:
        mid = (lo_i + hi_i) // 2
        if _succ(apply(p, lever, mid * step), n, seed) >= target:
            lo_i = mid
        else:
            hi_i = mid
    return lo_i * step, None


def solve(plan: dict, target: float = 0.85, n: int = 600, seed: int = 11) -> dict:
    p = normalize_plan(plan)
    base = _succ(p, n, seed)
    working = _working(p)
    out = {'target': target, 'success': base, 'reached': base >= target, 'levers': []}
    if base < target:
        for lev, cfg in LEVERS.items():
            if lev == 'retire_later' and not working:
                out['levers'].append({'id': lev, 'label': cfg['label'], 'unit': cfg['unit'], 'applicable': False,
                                      'note': 'Everyone is already retired'})
                continue
            hi = cfg['hi']
            if lev == 'claim_later':
                claims = [p.get(f'parent{w}_ss_claim_age') or min(max(p[f'parent{w}_retirement_age'], 62), 70)
                          for w in ('X',) + (() if is_single(p) else ('Y',))]
                hi = int(70 - min(claims))
                ages_now = [p[f'parent{w}_age'] for w in ('X',) + (() if is_single(p) else ('Y',))]
                if hi <= 0 or min(claims) <= max(ages_now):
                    out['levers'].append({'id': lev, 'label': cfg['label'], 'unit': cfg['unit'], 'applicable': False,
                                          'note': 'Already claiming at 70' if hi <= 0 else 'Benefits have already started'})
                    continue
            x, s = _min_to_reach(p, lev, hi, cfg['step'], target, n, seed)
            item = {'id': lev, 'label': cfg['label'], 'unit': cfg['unit'], 'applicable': True, 'feasible': x is not None,
                    'amount': x, 'success_after': s, 'max_tried': hi}
            if x is not None:
                item['patch'] = patch(p, lev, x)
            out['levers'].append(item)
        # no single change is enough (or even if one is): a smaller mix of all three
        x, s = _min_to_reach(p, 'combined', 100, 5, target, n, seed)
        item = {'id': 'combined', 'label': 'A mix of all three', 'unit': 'mix', 'applicable': True, 'feasible': x is not None,
                'amount': x, 'success_after': s, 'max_tried': 100, 'parts': combo_parts(p, x if x is not None else 100)}
        if x is not None:
            item['patch'] = patch(p, 'combined', x)
        out['levers'].append(item)
    else:
        for lev, label, hi, step in (('retire_earlier', 'Retire earlier', 10, 1), ('spend_more', 'Spend more', 50, 1)):
            if lev == 'retire_earlier' and not working:
                continue
            if lev == 'retire_earlier':
                hi = min(hi, min(p[f'parent{w}_retirement_age'] - p[f'parent{w}_age'] for w in working) - 1)
                if hi < 1:
                    continue
            x, _ = _max_keeping(p, lev, hi, step, target, n, seed)
            item = {'id': lev, 'label': label, 'unit': 'years' if lev == 'retire_earlier' else '%', 'applicable': True,
                    'feasible': x > 0, 'amount': x, 'success_after': _succ(apply(p, lev, x), n, seed) if x else base}
            if x:
                item['patch'] = patch(p, lev, x)
            out['levers'].append(item)
    return out


# ── safe spending (2026-09-28) ─────────────────────────────────────────────
def _scale_spending(plan: dict, k: float) -> dict:
    """Everyday, household (not housing) and recurring spending times k."""
    p = copy.deepcopy(plan)
    for key in ('parentX_expenses', 'parentY_expenses'):
        p[key] = {c: v * k for c, v in (p.get(key) or {}).items()}
    p['family_shared_expenses'] = {c: (v if c in HOUSING else v * k) for c, v in (p.get('family_shared_expenses') or {}).items()}
    for r in p.get('recurring_expenses') or []:
        r['amount'] = r['amount'] * k
    return p


def flexible_spending(p: dict) -> float:
    """This year's flexible spending in today's dollars (what safe spending scales)."""
    s = sum((p.get('parentX_expenses') or {}).values())
    if not is_single(p):
        s += sum((p.get('parentY_expenses') or {}).values())
    s += sum(v for c, v in (p.get('family_shared_expenses') or {}).items() if c not in HOUSING)
    cy = p['current_year']
    s += sum(r['amount'] / max(r['frequency_years'], 1) for r in p.get('recurring_expenses') or []
             if r['start_year'] <= cy and (r['end_year'] is None or r['end_year'] >= cy))
    return float(s)


def safe_spending(plan: dict, target: float = 0.85, n: int = 500, seed: int = 11) -> dict:
    """The most you can spend on flexible items (as a multiple of today's plan) and still reach `target`."""
    p = normalize_plan(plan)
    base = _succ(p, n, seed)
    cur = flexible_spending(p)
    lo, hi = 0.3, 3.0
    s_lo = _succ(_scale_spending(p, lo), n, seed)
    if s_lo < target:
        k, s_k = None, s_lo
    elif _succ(_scale_spending(p, hi), n, seed) >= target:
        k, s_k = hi, None
    else:
        for _ in range(12):
            mid = (lo + hi) / 2
            if _succ(_scale_spending(p, mid), n, seed) >= target:
                lo = mid
            else:
                hi = mid
        k = lo
        s_k = _succ(_scale_spending(p, k), n, seed)
    out = {'target': target, 'success': base, 'current': cur, 'multiplier': k,
           'safe': cur * k if k is not None else None, 'success_at_safe': s_k}
    if k is not None:
        out['delta_year'] = cur * (k - 1)
        out['delta_month'] = cur * (k - 1) / 12
        out['patch'] = {kk: v for kk, v in _scale_spending(p, k).items()
                        if kk in ('parentX_expenses', 'parentY_expenses', 'family_shared_expenses', 'recurring_expenses')}
    return out
