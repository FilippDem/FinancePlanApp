"""Check-in scoring and plan roll-forward (docs/CHECKINS.md §4–5)."""
from __future__ import annotations

import copy
from datetime import date

from .engine import project, monte_carlo, PCTS
from .mortgage import sync_legacy_fields
from .plan import normalize_plan

STATUS = [(75, 'ahead'), (25, 'on_track'), (10, 'behind'), (-1, 'off_track')]


def _interp(start: float, rows_by_year: dict, cy: int, d: date) -> float:
    """Value at date d from end-of-year values (row[y] = value at Dec 31 of y)."""
    f = (d.timetuple().tm_yday - 1) / 365.0
    y = d.year
    prev = start if y <= cy else rows_by_year.get(y - 1, start)
    cur = rows_by_year.get(y, prev)
    if y < cy:
        return start
    return prev + f * (cur - prev)


def percentile_rank(value: float, points: dict) -> float:
    qs = sorted(points)
    xs = [points[q] for q in qs]
    if value <= xs[0]:
        return max(1.0, qs[0] / 2)
    if value >= xs[-1]:
        return min(99.0, (qs[-1] + 100) / 2)
    for (q0, x0), (q1, x1) in zip(zip(qs, xs), zip(qs[1:], xs[1:])):
        if x0 <= value <= x1:
            return q0 + (q1 - q0) * ((value - x0) / (x1 - x0) if x1 > x0 else 0.5)
    return 50.0


def status_for(pctl: float) -> str:
    for cut, name in STATUS:
        if pctl >= cut:
            return name
    return 'off_track'


def evaluate(plan: dict, on: date, investable: float, net_worth: float | None = None, n: int = 1000) -> dict:
    """Compare actual balances on a date with what the plan expected."""
    p = normalize_plan(plan)
    cy = p['current_year']
    pr = project(p)
    rows = {r['year']: r for r in pr['rows']}
    s = pr['summary']
    start_inv = s['investable_now'] + p.get('hsa_balance', 0.0)
    start_nw = s['net_worth_now'] + p.get('hsa_balance', 0.0)
    exp_inv = _interp(start_inv, {y: r['investable'] for y, r in rows.items()}, cy, on)
    exp_nw = _interp(start_nw, {y: r['net_worth'] for y, r in rows.items()}, cy, on)
    mc = monte_carlo(p, n, seed=7, normalized=False)
    band = {}
    for q in PCTS:
        by_year = dict(zip(mc['years'], mc['investable'][str(q)]))
        band[q] = _interp(start_inv, by_year, cy, on)
    pctl = percentile_rank(investable, band)
    out = {
        'expected': {'investable': exp_inv, 'net_worth': exp_nw, **{f'p{q}': v for q, v in band.items()},
                     'success_rate': mc['success_rate']},
        'percentile': round(pctl, 1), 'status': status_for(pctl),
        'gap': investable - exp_inv,
    }
    if net_worth is not None:
        out['gap_net_worth'] = net_worth - exp_nw
    return out


def rebase(plan: dict, balances: dict, on: date) -> dict:
    """Roll the plan forward to reality. Returns a new (normalized) plan.

    balances = {'p1': {'liquid', 'pretax', 'separate_liquid'?, 'separate_pretax'?}, 'p2': {...},
                'homes': [{'name','value','mortgage'}], 'other_debts'}
    """
    p = normalize_plan(copy.deepcopy(plan))
    delta = max(0, on.year - p['current_year'])
    own = p.get('ownership_tracking') or {}
    if own.get('enabled'):
        # keep "who owns what" when rolling forward: carry the projected separate balances,
        # unless the check-in says how much of each balance is separate
        today = copy.deepcopy(own.get('today') or {})
        if delta:
            from .engine import project
            rows = project(plan)['rows']
            row = next((r for r in rows if r['year'] == on.year - 1), None)
            if row and row.get('ownership'):
                o = row['ownership']
                today = {'p1': {'liquid': max(o['liquid']['s1'], 0), 'pretax': max(o['pretax']['s1'], 0)},
                         'p2': {'liquid': max(o['liquid']['s2'], 0), 'pretax': max(o['pretax']['s2'], 0)}}
        for who in ('p1', 'p2'):
            bx = balances.get(who) or {}
            for k in ('liquid', 'pretax'):
                if bx.get(f'separate_{k}') is not None:
                    today.setdefault(who, {})[k] = float(bx[f'separate_{k}'] or 0)
        p['ownership_tracking'] = {**own, 'today': today}
    if delta:
        p['current_year'] += delta
        p['parentX_age'] += delta
        p['parentY_age'] += delta
    debts = float(balances.get('other_debts') or 0)
    b1, b2 = balances.get('p1') or {}, balances.get('p2') or {}
    liq1, liq2 = float(b1.get('liquid') or 0), float(b2.get('liquid') or 0)
    tot = liq1 + liq2
    share1 = liq1 / tot if tot > 0 else (1.0 if not b2 else 0.5)
    if b1:
        pre1 = float(b1.get('pretax') or 0)
        ro1 = float(b1.get('roth') or 0) if b1.get('roth') is not None else None
        p['parentX_net_worth'] = liq1 + pre1 + (ro1 or 0) - debts * share1
        p['parentX_pretax_balance'] = pre1
        if ro1 is not None:
            p['parentX_roth_balance'] = ro1
    if b2:
        pre2 = float(b2.get('pretax') or 0)
        ro2 = float(b2.get('roth') or 0) if b2.get('roth') is not None else None
        p['parentY_net_worth'] = liq2 + pre2 + (ro2 or 0) - debts * (1 - share1)
        p['parentY_pretax_balance'] = pre2
        if ro2 is not None:
            p['parentY_roth_balance'] = ro2
    by_name = {h['name']: h for h in p['houses']}
    for hb in balances.get('homes') or []:
        h = by_name.get(hb.get('name'))
        if not h:
            continue
        if h.get('mortgage_mode') == 'estimate':
            sync_legacy_fields(h, p['current_year'])  # remaining years as of the new current year
        elif delta:
            h['mortgage_years_left'] = max(0, h['mortgage_years_left'] - delta)
        h['mortgage_mode'] = 'actual'
        if hb.get('value') is not None:
            h['current_value'] = float(hb['value'])
        if hb.get('mortgage') is not None:
            h['mortgage_balance'] = float(hb['mortgage'])
            if h['mortgage_balance'] <= 0:
                h['mortgage_years_left'] = 0
    p['last_rebased'] = on.isoformat()
    return normalize_plan(p)
