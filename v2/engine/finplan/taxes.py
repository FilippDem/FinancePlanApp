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

TAX_BASE_YEAR = 2026
# 2026 brackets and standard deduction (IRS Rev. Proc. 2025-32, after the 2025 tax law); later years are
# indexed with the plan's inflation rate. [irs_2026_tax]
MFJ = [(24800, .10), (100800, .12), (211400, .22), (403550, .24), (512450, .32), (768700, .35), (np.inf, .37)]
SINGLE = [(12400, .10), (50400, .12), (105700, .22), (201775, .24), (256225, .32), (640600, .35), (np.inf, .37)]
STD_DED = {'married': 32200.0, 'single': 16100.0}
SS_WAGE_BASE = 184500.0     # 2026 (SSA) [ssa_wage_base]


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


def fica(wages, status: str, index: float, other_wages=0.0):
    """Social Security (per person, up to the wage base) + Medicare. The 0.9% Additional Medicare Tax applies to
    a couple's combined wages above $250,000 (not indexed, by law); pass the spouse's wages as other_wages and
    this person's share of it is returned."""
    wages = np.maximum(np.asarray(wages, dtype=float), 0.0)
    other = np.maximum(np.asarray(other_wages, dtype=float), 0.0)
    ss = np.minimum(wages, SS_WAGE_BASE * index) * 0.062
    thr = 250000.0 if status == 'married' else 200000.0
    both = wages + other
    extra = np.maximum(both - thr, 0) * 0.009 * np.where(both > 0, wages / np.maximum(both, 1e-9), 0)
    return ss + wages * 0.0145 + extra


# State income tax: 2025 brackets, standard deductions and personal exemptions for the 41 states (+ DC) with a wage
# income tax (Tax Foundation). Thresholds are indexed with the plan's inflation like the federal ones (the one-year
# difference in base year is ignored). Social Security is left out of state income, as most states do. [taxfoundation_state_2025]
_STATE = None


def _state_table() -> dict:
    global _STATE
    if _STATE is None:
        import json
        from pathlib import Path
        with open(Path(__file__).parent / 'data' / 'state_income_tax_2025.json', encoding='utf-8') as f:
            _STATE = json.load(f)['states']
    return _STATE


def state_income_tax(income, status: str, index: float, state: str | None):
    """State tax on state income (AGI without Social Security), or None when the state isn't in the table."""
    st = _state_table().get(state or '')
    if st is None:
        return None
    inc = np.maximum(np.asarray(income, dtype=float), 0.0)
    ded = st['std'][status] + (0.0 if st['exemption_is_credit'] else st['exemption'][status])
    taxable = np.maximum(inc - ded * index, 0.0)
    tax = np.zeros_like(taxable)
    br = st[status]
    for i, (lo, rate) in enumerate(br):
        hi = br[i + 1][0] * index if i + 1 < len(br) else np.inf
        tax = tax + np.clip(taxable - lo * index, 0, hi - lo * index) * rate
    if st['exemption_is_credit']:
        tax = np.maximum(tax - st['exemption'][status] * index, 0.0)
    return tax


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
    state_inc = [None]

    def us_federal():
        agi_wo_ss = np.maximum(wages - pretax_deduction, 0) + other
        state_inc[0] = agi_wo_ss
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
            fic = fica(w1, status, index, w2) + fica(w2, status, index, w1)
    else:
        fed, taxable = us_federal()
        fic = fica(w1, status, index, w2) + fica(w2, status, index, w1)
        if ltype == 'us_state':
            st_tax = state_income_tax(state_inc[0], status, index, _us_state(location))
            state = st_tax if st_tax is not None else taxable * float(info.get('rate', 0.0))
        elif ltype == 'country':  # "United States" without a state
            state = zeros
        else:
            state = taxable * (state_rate_override if state_rate_override is not None else 0.05)
    total = fed + state + fic + foreign
    return {'federal': fed, 'state': state, 'fica': fic, 'foreign': foreign, 'total': total,
            'taxable': taxable, 'agi': agi[0] if agi[0] is not None else zeros}


# ── capital gains, IRMAA, ACA (added 2026-09-28; see data/sources.json) ─────────────────────
# Long-term capital-gains brackets, 2026 (IRS Rev. Proc. 2025-32), indexed like the ordinary brackets.
LTCG = {'married': (98900.0, 613700.0), 'single': (49450.0, 545500.0)}
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
WA_CG_DEDUCTION = 278000.0   # 2025 value (2026 not published yet), indexed from TAX_BASE_YEAR
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
    st_name = _us_state(location)
    if st_name == 'Washington':
        srate = 0.0
        state_part = wa_capital_gains_tax(g, index)
    elif st_name in _state_table():
        # gains stacked on top of other income in the state's own brackets (most states tax gains as income)
        base_inc = np.maximum(np.asarray(magi, dtype=float) - g, 0.0)
        state_part = (state_income_tax(base_inc + g, status, index, st_name)
                      - state_income_tax(base_inc, status, index, st_name))
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
