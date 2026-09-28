"""Pensions & annuities, debts and 529 college plans (added 2026-09-28).

schedule_extras() fills deterministic schedule columns:
  pension1 / pension2        yearly pension or annuity income per person (survivor share after a death)
  pension_taxable            the taxable part (ordinary income)
  purchase_exp               annuity purchase price in its purchase year
  debt_pay / debt_balance    loan payments (fixed nominal) and year-end balances (also added to consumer_debt)
and returns the 529 plan descriptions used by simulate(), which grows each 529 with the portfolio return,
takes the contributions out of cash flow and pays the child's college costs (ages 18-21) from it.
"""
from __future__ import annotations

import numpy as np


def _person(p: dict, who: str):
    return ('X', 1) if who == 'Parent 1' else ('Y', 2)


def schedule_extras(p: dict, years: list, C: dict, details: list, events: list, ii_arr: list) -> list:
    cy = p['current_year']
    T = len(years)
    n1, n2 = p.get('parent1_name', 'Parent 1'), p.get('parent2_name', 'Parent 2')

    # ---- pensions & annuities ------------------------------------------------------
    for pen in p.get('pensions') or []:
        k, idx = _person(p, pen['person'])
        other = 2 if idx == 1 else 1
        age0 = p[f'parent{k}_age']
        t_start = pen['start_age'] - age0
        if pen['kind'] == 'annuity' and pen.get('purchase_year') and pen.get('purchase_amount'):
            ty = pen['purchase_year'] - cy
            if 0 <= ty < T:
                cost = pen['purchase_amount'] * ii_arr[ty]
                C['purchase_exp'][ty] += cost
                details[ty].setdefault('purchases', []).append({'name': f"{pen['name']} (annuity purchase)", 'amount': cost})
                events.append({'year': years[ty], 'type': 'purchase', 'label': f"Buy annuity: {pen['name']}", 'amount': cost})
        if pen['monthly'] <= 0:
            continue
        ts = max(t_start, 0)
        if ts >= T:
            continue
        # amount at the start: today's dollars grown with inflation to the start year, or as quoted
        start_amt = pen['monthly'] * 12 * (ii_arr[min(ts, T - 1)] if pen['todays_dollars'] else 1.0)
        started = False
        for t in range(ts, T):
            own_alive = bool(C[f'alive{idx}'][t])
            sp_alive = bool(C[f'alive{other}'][t])
            amt = start_amt * (1 + pen['cola_pct'] / 100) ** (t - ts)
            if own_alive:
                pay, to = amt, idx
            elif sp_alive and pen['survivor_pct'] > 0:
                pay, to = amt * pen['survivor_pct'] / 100, other
            else:
                continue
            C[f'pension{to}'][t] += pay
            C['pension_taxable'][t] += pay * pen['taxable_pct'] / 100
            details[t].setdefault('pensions', []).append({'name': pen['name'], 'amount': pay, 'to': n1 if to == 1 else n2})
            if not started:
                started = True
                if t_start >= 0:
                    events.append({'year': years[t], 'type': 'pension', 'label': f"{pen['name']} starts", 'amount': pay})

    # ---- debts (amortized with the payment you make; nominal) ----------------------
    for d in p.get('debts') or []:
        bal = d['balance']
        rate = d['rate'] / 100
        pay_y = (d['monthly_payment'] + d['extra_monthly']) * 12
        t0 = max(0, d['start_year'] - cy)
        paid_off = False
        for t in range(t0, T):
            if bal <= 0.005:
                break
            interest = bal * rate
            pay = min(pay_y, bal + interest)
            bal = bal + interest - pay
            C['debt_pay'][t] += pay
            C['debt_balance'][t] += max(bal, 0.0)
            C['consumer_debt'][t] += max(bal, 0.0)
            details[t].setdefault('debts', []).append({'name': d['name'], 'payment': pay, 'interest': interest, 'balance': max(bal, 0.0)})
            if bal <= 0.005 and not paid_off:
                paid_off = True
                events.append({'year': years[t], 'type': 'debt_paid', 'label': f"{d['name']} paid off"})
        if not paid_off and d['balance'] > 0 and pay_y <= d['balance'] * rate:
            events.append({'year': years[t0] if t0 < T else cy, 'type': 'warning',
                           'label': f"{d['name']}: the payment doesn't cover the interest"})

    # ---- 529 college plans -----------------------------------------------------------
    edu = []
    kids = {c['name']: c for c in p.get('children_list') or []}
    for pl in p.get('college_529') or []:
        ch = kids.get(pl['child'])
        if ch is None:
            continue
        contrib = np.zeros(T)
        cost = np.zeros(T)
        for t, y in enumerate(years):
            age = y - ch['birth_year']
            if 0 <= age < pl['until_age']:
                contrib[t] = pl['monthly'] * 12 * ii_arr[t]
            for cd in details[t].get('children') or []:
                if cd['name'] == ch['name'] and cd.get('in_college'):
                    cost[t] = cd['total']
        # the account closes the year the child turns 22
        close_t = next((t for t, y in enumerate(years) if y - ch['birth_year'] >= 22), None)
        edu.append({'child': ch['name'], 'birth_year': ch['birth_year'], 'balance': pl['balance'], 'contrib': contrib,
                    'cost': cost, 'close_t': close_t})
    # leftover money passes to the next younger sibling that has a 529 (else back to savings)
    order = sorted(range(len(edu)), key=lambda i: edu[i]['birth_year'])
    for j, i in enumerate(order):
        nxt = next((order[k] for k in range(j + 1, len(order)) if edu[order[k]]['birth_year'] >= edu[i]['birth_year']), None)
        edu[i]['next'] = nxt
    return edu


def contrib_529_total(edu: list, t: int) -> float:
    return float(sum(e['contrib'][t] for e in edu))
