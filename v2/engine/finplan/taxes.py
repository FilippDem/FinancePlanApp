"""Vectorized US tax calculations (numpy arrays in, arrays out).

Fixes vs v0.8:
  * brackets, standard deduction and SS wage base are indexed to inflation
    (2024 base year) instead of frozen at 2024 nominal values
  * FICA applied per earner (each has their own wage base)
  * rental income and pre-tax withdrawals are ordinary income (no FICA)
"""
from __future__ import annotations

import numpy as np

from .reference import location_tax_info

TAX_BASE_YEAR = 2024
MFJ = [(23200, .10), (94300, .12), (201050, .22), (383900, .24), (487450, .32), (731200, .35), (np.inf, .37)]
SINGLE = [(11600, .10), (47150, .12), (100525, .22), (191950, .24), (243725, .32), (609350, .35), (np.inf, .37)]
STD_DED = {'married': 29200.0, 'single': 14600.0}
SS_WAGE_BASE = 168600.0


def federal_income_tax(taxable, status: str, index: float):
    taxable = np.maximum(np.asarray(taxable, dtype=float), 0.0)
    return _bracket_tax(taxable, status, index)


def _bracket_tax(taxable, status, index):
    tax = np.zeros_like(taxable)
    prev = 0.0
    for limit, rate in (MFJ if status == 'married' else SINGLE):
        lim = limit * index
        width = np.clip(taxable - prev, 0, (lim - prev) if np.isfinite(lim) else np.inf)
        tax = tax + width * rate
        prev = lim
    return tax


def marginal_rate(taxable, status: str, index: float):
    taxable = np.asarray(taxable, dtype=float)
    rate = np.full_like(taxable, 0.10)
    prev = 0.0
    for limit, r in (MFJ if status == 'married' else SINGLE):
        rate = np.where(taxable > prev, r, rate)
        prev = limit * index
    return rate


def fica(wages, status: str, index: float):
    wages = np.maximum(np.asarray(wages, dtype=float), 0.0)
    ss = np.minimum(wages, SS_WAGE_BASE * index) * 0.062
    thr = 250000.0 if status == 'married' else 200000.0  # not indexed (by law)
    medicare = wages * 0.0145 + np.maximum(wages - thr, 0) * 0.009
    return ss + medicare


def taxable_ss(ss_income, other_income, status: str):
    """Provisional-income method (thresholds are not inflation-indexed by law)."""
    ss_income = np.asarray(ss_income, dtype=float)
    prov = other_income + 0.5 * ss_income
    t1, t2 = (32000.0, 44000.0) if status == 'married' else (25000.0, 34000.0)
    tier1 = np.minimum(np.maximum(prov - t1, 0), 0.5 * ss_income)
    tier1 = np.minimum(tier1, 0.5 * (t2 - t1))
    tier2 = 0.85 * np.maximum(prov - t2, 0)
    return np.minimum(tier1 + tier2, 0.85 * ss_income)


def total_taxes(wages1, wages2, ss_income, other_ordinary, pretax_deduction, year: int, inflation: float,
                location: str | None, status: str = 'married', state_rate_override: float | None = None):
    """Returns dict of arrays: federal, state, fica, foreign, total.

    other_ordinary: rental net income + pre-tax account withdrawals (no FICA).
    pretax_deduction: 401k contributions (reduce income tax, not FICA).
    """
    index = (1 + inflation) ** max(0, year - TAX_BASE_YEAR)
    w1 = np.asarray(wages1, dtype=float)
    w2 = np.asarray(wages2, dtype=float)
    wages = w1 + w2
    other = np.asarray(other_ordinary, dtype=float)
    ltype, info = location_tax_info(location)
    zeros = np.zeros(np.broadcast(wages, other, np.asarray(ss_income)).shape)
    fed = zeros.copy(); state = zeros.copy(); fic = zeros.copy(); foreign = zeros.copy()

    def us_federal():
        agi_wo_ss = np.maximum(wages - pretax_deduction, 0) + other
        tss = taxable_ss(ss_income, agi_wo_ss, status)
        taxable = np.maximum(agi_wo_ss + tss - STD_DED[status] * index, 0)
        return _bracket_tax(taxable, status, index), taxable

    if ltype == 'country' and info and info.get('type') != 'federal_state':
        rate = float(info.get('effective_rate', 0.35))
        foreign = (wages + other + np.asarray(ss_income, dtype=float)) * rate
        if info.get('has_fica', False):
            fic = fica(w1, status, index) + fica(w2, status, index)
    else:
        fed, taxable = us_federal()
        fic = fica(w1, status, index) + fica(w2, status, index)
        if ltype == 'us_state':
            state = taxable * float(info.get('rate', 0.0))
        elif ltype == 'country':  # "United States" without a state
            state = zeros
        else:
            state = taxable * (state_rate_override if state_rate_override is not None else 0.05)
    total = fed + state + fic + foreign
    return {'federal': fed, 'state': state, 'fica': fic, 'foreign': foreign, 'total': total}
