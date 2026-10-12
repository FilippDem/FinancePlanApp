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

    agi = [None]

    def us_federal():
        agi_wo_ss = np.maximum(wages - pretax_deduction, 0) + other
        tss = taxable_ss(ss_income, agi_wo_ss, status)
        agi[0] = agi_wo_ss + tss
        taxable = np.maximum(agi_wo_ss + tss - STD_DED[status] * index, 0)
        return _bracket_tax(taxable, status, index), taxable

    taxable = zeros.copy()
    if ltype == 'country' and info and info.get('type') != 'federal_state':
        rate = float(info.get('effective_rate', 0.35))
        foreign = (wages + other + np.asarray(ss_income, dtype=float)) * rate
        agi[0] = wages + other + np.asarray(ss_income, dtype=float)
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
    return {'federal': fed, 'state': state, 'fica': fic, 'foreign': foreign, 'total': total,
            'taxable': taxable, 'agi': agi[0] if agi[0] is not None else zeros}


# ── capital gains, IRMAA, ACA (added 2026-09-28; see data/sources.json) ─────────────────────
# Long-term capital-gains brackets, 2024 (IRS Rev. Proc. 2023-34), indexed like the ordinary brackets.
LTCG = {'married': (94050.0, 583750.0), 'single': (47025.0, 518900.0)}
NIIT_THRESHOLD = {'married': 250000.0, 'single': 200000.0}   # 3.8% net investment income tax; not indexed by law


def state_rate(location: str | None, override: float | None = None) -> tuple[str, float]:
    """(kind, flat rate) used for gains: US state rate, a country's effective rate, or the override/5% guess."""
    ltype, info = location_tax_info(location)
    if ltype == 'country' and info and info.get('type') != 'federal_state':
        return 'foreign', float(info.get('effective_rate', 0.35))
    if ltype == 'us_state':
        return 'us', float(info.get('rate', 0.0))
    if ltype == 'country':
        return 'us', 0.0
    return 'us', override if override is not None else 0.05


# Washington taxes long-term capital gains although it has no income tax (RCW 82.87): 7% above a standard
# deduction ($262,000 in 2024, indexed; $278,000 in 2025) and 9.9% on taxable gains above $1M (not indexed).
# Real estate and retirement accounts are exempt; v2 only realizes gains from taxable savings. [wa_dor_cg]
WA_CG_DEDUCTION = 262000.0   # TAX_BASE_YEAR value, indexed like the federal brackets
WA_CG_TIER = 1_000_000.0


def _us_state(location: str | None) -> str | None:
    from .reference import ref, CITY_TO_STATE
    if location in ref()["US_STATE_TAX_INFO"]:
        return location
    return CITY_TO_STATE.get(location)


def wa_capital_gains_tax(gains, index: float):
    taxable = np.maximum(np.asarray(gains, dtype=float) - WA_CG_DEDUCTION * index, 0.0)
    return np.minimum(taxable, WA_CG_TIER) * 0.07 + np.maximum(taxable - WA_CG_TIER, 0.0) * 0.099


def capital_gains_tax(gains, ordinary_taxable, magi, status: str, index: float, location: str | None,
                      override: float | None = None):
    """Tax on realized long-term gains stacked on top of ordinary taxable income (0/15/20%), plus NIIT and state."""
    g = np.maximum(np.asarray(gains, dtype=float), 0.0)
    kind, srate = state_rate(location, override)
    if kind == 'foreign':
        return g * srate
    if _us_state(location) == 'Washington':
        srate = 0.0
        state_part = wa_capital_gains_tax(g, index)
    else:
        state_part = g * srate
    lo, hi = LTCG[status]
    lo, hi = lo * index, hi * index
    base = np.maximum(np.asarray(ordinary_taxable, dtype=float), 0.0)
    top = base + g
    in0 = np.clip(np.minimum(top, lo) - base, 0, None)
    in15 = np.clip(np.minimum(top, hi) - np.maximum(base, lo), 0, None)
    in20 = g - in0 - in15
    fed = in15 * 0.15 + np.maximum(in20, 0) * 0.20
    niit = np.minimum(g, np.maximum(np.asarray(magi, dtype=float) - NIIT_THRESHOLD[status], 0)) * 0.038
    return fed + niit + state_part


# Medicare IRMAA 2026 (CMS): MAGI from two years earlier. (threshold, Part B extra, Part D extra) per person per month.
_B_STD = 202.90
IRMAA = {
    'married': [(218000, 0.0, 0.0), (274000, 284.10 - _B_STD, 14.50), (342000, 405.80 - _B_STD, 37.50),
                (410000, 527.50 - _B_STD, 60.40), (750000, 649.20 - _B_STD, 83.30), (np.inf, 689.90 - _B_STD, 91.00)],
    'single': [(109000, 0.0, 0.0), (137000, 284.10 - _B_STD, 14.50), (171000, 405.80 - _B_STD, 37.50),
               (205000, 527.50 - _B_STD, 60.40), (500000, 649.20 - _B_STD, 83.30), (np.inf, 689.90 - _B_STD, 91.00)],
}
IRMAA_BASE_YEAR = 2026


def irmaa_monthly(magi, status: str, index: float):
    """Extra monthly Medicare premium (Part B + Part D) per person for a MAGI, thresholds indexed from 2026."""
    m = np.asarray(magi, dtype=float)
    out = np.zeros_like(m)
    prev = 0.0
    for lim, b, d in IRMAA[status]:
        out = np.where((m > prev) & (m <= lim * index), (b + d) * index, out)
        prev = lim * index
    return out


def irmaa_tier(magi: float, status: str, index: float) -> int:
    prev = 0.0
    for i, (lim, _, _) in enumerate(IRMAA[status]):
        if magi <= lim * index:
            return i
    return len(IRMAA[status]) - 1


# ACA premium tax credit for 2026 coverage (IRS Rev. Proc. 2025-25; enhanced credits ended after 2025):
# applicable percentage by income as % of the federal poverty level, no credit above 400% FPL.
ACA_BANDS = [(1.33, 0.0210, 0.0210), (1.50, 0.0314, 0.0419), (2.00, 0.0419, 0.0660), (2.50, 0.0660, 0.0844),
             (3.00, 0.0844, 0.0996), (4.00, 0.0996, 0.0996)]
FPL_2025 = (15650.0, 5500.0)   # HHS 2025 poverty guideline (48 states): first person, each additional person
ACA_BASE_YEAR = 2026


def aca_applicable_pct(fpl_ratio):
    r = np.asarray(fpl_ratio, dtype=float)
    out = np.full_like(r, np.nan)
    prev = 0.0
    for hi, a, b in ACA_BANDS:
        lo = prev
        frac = np.clip((r - lo) / max(hi - lo, 1e-9), 0, 1) if lo > 0 else np.zeros_like(r)
        val = a + (b - a) * frac
        out = np.where(np.isnan(out) & (r <= hi), val, out)
        prev = hi
    return out   # NaN above 400% FPL


def aca_credit(magi, household_size: int, benchmark_annual, index: float):
    """Premium tax credit (annual) given household MAGI and the benchmark (second-lowest silver) premium.
    Below 138% FPL we assume Medicaid (premium covered). Above 400% FPL: no credit (the 'cliff')."""
    m = np.maximum(np.asarray(magi, dtype=float), 0.0)
    fpl = (FPL_2025[0] + FPL_2025[1] * max(household_size - 1, 0)) * index
    ratio = m / fpl
    pct = aca_applicable_pct(ratio)
    bench = np.asarray(benchmark_annual, dtype=float) * np.ones_like(m)
    credit = np.where(np.isnan(pct), 0.0, np.maximum(bench - np.nan_to_num(pct) * m, 0.0))
    credit = np.where(ratio < 1.38, bench, credit)
    return np.minimum(credit, bench), ratio
