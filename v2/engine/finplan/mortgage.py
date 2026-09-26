"""Mortgage math for homes (Redfin-style calculator + actual-loan mode).

Two ways to describe a home loan (house['mortgage_mode']):

* 'estimate' - like a listing calculator: purchase price, down payment %,
  loan term and interest rate. The loan starts in the purchase year; for a
  home bought in the past, today's balance is derived by amortizing it.
* 'actual'  - what's on your statement today: current balance, rate, years
  left and (optionally) the actual monthly principal & interest you pay
  (mortgage_payment_override). A higher payment than required = extra
  principal, so the loan pays off sooner.

Legacy keys (mortgage_balance / mortgage_years_left) are always kept in sync
so v0.8 can still read the file.
"""
from __future__ import annotations

from functools import lru_cache


def monthly_payment(principal: float, annual_rate: float, years: float) -> float:
    if principal <= 0 or years <= 0:
        return 0.0
    n = round(years * 12)
    r = annual_rate / 12
    if r <= 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def loan_terms(h: dict, current_year: int) -> dict:
    """Normalize a house's loan into (start_year, principal, rate, monthly payment)."""
    rate = float(h.get('mortgage_rate') or 0.0)
    price = float(h.get('purchase_price') or 0.0)
    if h.get('mortgage_mode') == 'estimate':
        dp = float(h.get('down_payment_pct', 20.0) or 0.0)
        principal = max(price * (1 - dp / 100), 0.0)
        term = float(h.get('loan_term_years') or 30)
        start = int(h['purchase_year'])
        pmt = monthly_payment(principal, rate, term)
        down = price * dp / 100
        original = principal
    else:
        principal = float(h.get('mortgage_balance') or 0.0)
        years = float(h.get('mortgage_years_left') or 0)
        start = max(int(current_year), int(h['purchase_year']))
        req = monthly_payment(principal, rate, years)
        ov = h.get('mortgage_payment_override')
        pmt = float(ov) if ov not in (None, '', 0) and float(ov) > 0 else req
        down = max(price - principal, 0.0)
        original = float(h.get('original_loan_amount') or 0.0) or principal
    return {'start': start, 'principal': principal, 'rate': rate, 'pmt': pmt, 'down': down,
            'original': original, 'price': price}


@lru_cache(maxsize=512)
def _schedule(principal: float, rate: float, pmt: float) -> tuple:
    """Month-end balances until payoff (max 60 years). Index 0 = start balance."""
    bal = [principal]
    b = principal
    r = rate / 12
    for _ in range(720):
        if b <= 0.005:
            break
        interest = b * r
        pay = min(pmt, b + interest)
        if pay <= interest:          # payment doesn't cover interest: cap growth, stop
            bal.append(b)
            break
        b = b + interest - pay
        bal.append(max(b, 0.0))
    return tuple(bal)


def year_flows(terms: dict, year: int) -> dict:
    """Payments during calendar `year` and balances at its start/end."""
    zero = {'bal_start': 0.0, 'bal_end': 0.0, 'paid': 0.0, 'interest': 0.0, 'principal': 0.0}
    if terms['principal'] <= 0 or terms['pmt'] <= 0:
        return zero
    k = 12 * (year - terms['start'])
    if k < 0:
        return {**zero, 'bal_start': terms['principal'], 'bal_end': terms['principal']}
    sched = _schedule(round(terms['principal'], 2), terms['rate'], round(terms['pmt'], 4))
    last = len(sched) - 1
    b0 = sched[min(k, last)]
    b1 = sched[min(k + 12, last)]
    months = max(0, min(k + 12, last) - min(k, last))
    if months == 0:
        return {**zero, 'bal_start': b0, 'bal_end': b1}
    principal_paid = b0 - b1
    # interest actually accrued over those months
    r = terms['rate'] / 12
    interest = sum(sched[i] * r for i in range(min(k, last), min(k + 12, last)))
    return {'bal_start': b0, 'bal_end': b1, 'paid': principal_paid + interest,
            'interest': interest, 'principal': principal_paid}


def balance_at(terms: dict, year: int) -> float:
    """Balance at the START of `year`."""
    return year_flows(terms, year)['bal_start']


def payoff_year(terms: dict) -> int | None:
    if terms['principal'] <= 0 or terms['pmt'] <= 0:
        return None
    sched = _schedule(round(terms['principal'], 2), terms['rate'], round(terms['pmt'], 4))
    if sched[-1] > 0.005:
        return None
    return terms['start'] + (len(sched) - 2) // 12


def sync_legacy_fields(h: dict, current_year: int) -> None:
    """Keep mortgage_balance / mortgage_years_left meaningful for v0.8."""
    if h.get('mortgage_mode') != 'estimate':
        return
    t = loan_terms(h, current_year)
    y = max(current_year, int(h['purchase_year']))
    bal = balance_at(t, y)
    po = payoff_year(t)
    h['mortgage_balance'] = round(bal, 2)
    h['mortgage_years_left'] = max(0, (po + 1 - y) if po is not None else int(h.get('loan_term_years') or 30))
