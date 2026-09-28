"""Goals and milestones with progress (added 2026-09-28).

A goal is a dict in plan['goals']:
  fi              "Work optional" by a year: savings reach 25x the yearly spending not covered by
                  Social Security and pensions (or `amount` if given)
  net_worth       net worth of `amount` (today's $) by `year`
  savings         cash & investments (outside retirement accounts) of `amount` by `year`
  emergency_fund  `months` of spending in cash & investments (now)
  college         a child's college costs (`child`) covered, by 529 money or savings
  house_paid_off  the mortgage on `house` is paid off by `year`
  debt_free       every loan in `debts` is paid off by `year`
Amounts are today's dollars. evaluate() compares each goal with the projection (and Monte Carlo paths when
given) and returns progress, the projected value and a status: on_track / at_risk / off_track.
"""
from __future__ import annotations

import numpy as np

TYPES = {
    'fi': 'Work optional',
    'net_worth': 'Net worth target',
    'savings': 'Savings target',
    'emergency_fund': 'Emergency fund',
    'college': 'College funded',
    'house_paid_off': 'House paid off',
    'debt_free': 'Debt free',
}


def _num(v, d=0.0):
    try:
        return float(v) if v not in (None, '') else d
    except (TypeError, ValueError):
        return d


def normalize(goals, p: dict) -> list:
    cy = p.get('current_year') or 2026
    out = []
    for i, g in enumerate(goals or []):
        if not isinstance(g, dict) or g.get('type') not in TYPES:
            continue
        x = {'id': str(g.get('id') or f'goal{i + 1}'), 'type': g['type'], 'name': g.get('name') or TYPES[g['type']],
             'year': int(_num(g.get('year'), cy + 10)), 'amount': _num(g.get('amount')), 'months': _num(g.get('months'), 6),
             'child': g.get('child') or '', 'house': g.get('house') or ''}
        out.append(x)
    return out


def _status(ratio: float, prob: float | None = None) -> str:
    if prob is not None:
        return 'on_track' if prob >= 0.75 else 'at_risk' if prob >= 0.5 else 'off_track'
    return 'on_track' if ratio >= 1 else 'at_risk' if ratio >= 0.8 else 'off_track'


def targets(p: dict, rows: list) -> list:
    """(goal, metric, year index, target in today's $) for goals Monte Carlo can score."""
    cy = p['current_year']
    out = []
    for g in p.get('goals') or []:
        t = max(0, min(g['year'] - cy, len(rows) - 1))
        if g['type'] == 'net_worth' and g['amount'] > 0:
            out.append((g, 'net_worth', t, g['amount']))
        elif g['type'] == 'savings' and g['amount'] > 0:
            out.append((g, 'liquid', t, g['amount']))
        elif g['type'] == 'fi':
            out.append((g, 'investable', t, fi_target(p, rows, g)))
    return out


def fi_target(p: dict, rows: list, g: dict) -> float:
    if g.get('amount'):
        return g['amount']
    cy = p['current_year']
    t = max(0, min(g['year'] - cy, len(rows) - 1))
    r = rows[t]
    # spending that year without work-related saving, less guaranteed income, in today's dollars
    spend = r['total_expenses'] - r.get('down_payment', 0) - r.get('exp_purchases', 0)
    guaranteed = r.get('ss_income', 0) + r.get('pension_income', 0) + r.get('rent_income', 0)
    # Social Security may start later: use the income at 67 when it's bigger
    later = next((x for x in rows if x['age1'] >= 67), None)
    if later:
        guaranteed = max(guaranteed, (later.get('ss_income', 0) + later.get('pension_income', 0)) * r['infl_index'] / later['infl_index'] * 0.6)
    return max(0.0, (spend - guaranteed) / r['infl_index']) * 25


def evaluate(p: dict, proj: dict, mc: dict | None = None) -> list:
    rows = proj['rows']
    cy = p['current_year']
    r0 = rows[0]
    probs = (mc or {}).get('goal_probs') or {}
    out = []
    for g in p.get('goals') or []:
        t = max(0, min(g['year'] - cy, len(rows) - 1))
        r = rows[t]
        ii = r['infl_index']
        res = {**g, 'label': TYPES[g['type']], 'target': 0.0, 'projected': 0.0, 'now': 0.0, 'progress': 0.0,
               'status': 'off_track', 'probability': probs.get(g['id']), 'note': ''}
        if g['type'] == 'fi':
            tgt = fi_target(p, rows, g)
            res.update(target=tgt, now=r0['investable'], projected=r['investable'] / ii,
                       note='25× the yearly spending not covered by Social Security, pensions or rent' if not g.get('amount') else '')
        elif g['type'] in ('net_worth', 'savings'):
            key = 'net_worth' if g['type'] == 'net_worth' else 'liquid'
            res.update(target=g['amount'], now=r0[key], projected=r[key] / ii)
        elif g['type'] == 'emergency_fund':
            monthly = (r0['total_expenses'] - r0.get('down_payment', 0) - r0.get('exp_purchases', 0)) / 12
            tgt = monthly * (g['months'] or 6)
            res.update(target=tgt, now=r0['liquid'], projected=r0['liquid'], year=cy,
                       note=f"{int(g['months'] or 6)} months of spending (about ${monthly:,.0f}/month) in cash and investments")
        elif g['type'] == 'college':
            costs = paid = 0.0
            yrs = []
            for x in rows:
                for cd in (x['details'].get('children') or []):
                    if cd['name'] == g['child'] and cd.get('in_college'):
                        costs += cd['total'] / x['infl_index']
                        yrs.append(x['year'])
                for e in x['details'].get('edu529') or []:
                    if e['child'] == g['child']:
                        paid += e['paid'] / x['infl_index']
            solvent = all(x['investable'] >= 0 for x in rows if x['year'] in yrs) if yrs else True
            res.update(target=costs, now=next((e['balance'] for e in (r0['details'].get('edu529') or []) if e['child'] == g['child']), 0.0),
                       projected=paid, year=yrs[-1] if yrs else g['year'])
            if costs <= 0:
                res.update(status='on_track', progress=1.0, note='No college costs in the plan for this child')
                out.append(res)
                continue
            share = paid / costs
            res['note'] = (f"529 covers {share * 100:.0f}% of about ${costs:,.0f} (today's $)"
                           + ('; the rest comes from savings' if share < 0.999 and solvent else '; savings run short in those years' if not solvent else ''))
            res['progress'] = min(1.0, share)
            res['status'] = 'on_track' if share >= 0.999 or solvent else 'off_track'
            if share < 0.999 and solvent:
                res['status'] = 'on_track' if share >= 0.5 else 'at_risk'
            out.append(res)
            continue
        elif g['type'] == 'house_paid_off':
            def bal(x):
                return next((h.get('balance', 0.0) for h in x['details'].get('houses') or [] if h['name'] == g['house']), None)
            b0, bt = bal(r0), bal(r)
            if bt is None:
                res.update(status='off_track', note='That home is not owned in that year')
                out.append(res)
                continue
            hist = [bal(x) for x in rows if bal(x) is not None]
            start = max([b for b in hist if b is not None] + [b0 or 0, 1])
            paid_year = next((x['year'] for x in rows if bal(x) is not None and bal(x) <= 1 and x['year'] >= cy), None)
            res.update(target=0.0, now=b0 or 0.0, projected=bt, progress=1 - (b0 or 0) / start if start else 1.0,
                       status='on_track' if bt <= 1 else 'off_track',
                       note=f"Paid off in {paid_year}" if paid_year else 'Not paid off within the plan')
            out.append(res)
            continue
        elif g['type'] == 'debt_free':
            orig = sum(d['balance'] for d in p.get('debts') or []) or 0.0
            b0 = sum(d['balance'] for d in p.get('debts') or [] if d['start_year'] <= cy)
            bt = r.get('debt_balance', 0.0)
            free_year = next((x['year'] for x in rows if x.get('debt_balance', 0.0) <= 1 and x['year'] >= max([d['start_year'] for d in p.get('debts') or []] + [cy])), None)
            res.update(target=0.0, now=b0, projected=bt, progress=1.0 if orig <= 1 else max(0.0, 1 - b0 / orig),
                       status='on_track' if bt <= 1 else 'off_track',
                       note=f"All loans paid off in {free_year}" if free_year else 'Loans are not paid off within the plan')
            out.append(res)
            continue
        tgt = res['target']
        res['progress'] = min(1.0, res['now'] / tgt) if tgt > 0 else 1.0
        ratio = res['projected'] / tgt if tgt > 0 else 1.0
        res['status'] = _status(ratio, res['probability'])
        out.append(res)
    return out


def mc_probs(p: dict, rows: list, paths: dict, infl_index, normalized: bool) -> dict:
    """Share of Monte Carlo paths meeting each scorable goal."""
    out = {}
    for g, metric, t, tgt in targets(p, rows):
        arr = paths[metric][t]
        vals = arr if normalized else arr / infl_index[t]
        out[g['id']] = float(np.mean(vals >= tgt)) if tgt > 0 else 1.0
    return out
