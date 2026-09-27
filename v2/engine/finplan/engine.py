"""v2 projection engine.

One code path serves both the deterministic projection (1 path, expected
returns) and Monte Carlo (N paths, vectorized with numpy).

Money conventions
  * Recurring amounts the user types (expenses, rent, premiums, SS benefit,
    401k contribution, one-time purchase costs) are in TODAY's dollars and are
    inflated each year.  Healthcare uses healthcare inflation.
  * Salaries are nominal and grow by the raise %.
  * House prices / values / mortgage balances are nominal as entered.
  * parentX/Y_net_worth = savings & investments (excluding home equity, which
    comes from the Homes list). parentX/Y_pretax_balance is the part of that
    held in pre-tax retirement accounts.

Major fixes vs v0.8 (see CHANGES in docs/V2_ENGINE.md):
  mortgage P&I is paid and amortized; home equity & appreciation count toward
  net worth; future home purchases pay the down payment; sales realize
  proceeds (net of selling costs, no double counting); rent is income;
  "Sold"/"Sell" both end ownership; SS starts at claim age >= 62 with COLA,
  early/late claiming factors and survivor benefit; children, one-time
  purchases and healthcare are inflated; financed purchases are amortized;
  taxes are included in Monte Carlo; brackets are inflation-indexed;
  Monte Carlo return volatility is in percentage points (not % of the rate);
  negative savings accrue debt interest instead of "investment returns".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .plan import normalize_plan, is_single
from . import ownership
from .reference import child_expenses_for_age, ref, HEALTH_CATEGORIES, col_factor, rent_factor
from .taxes import total_taxes, marginal_rate, TAX_BASE_YEAR
from .mortgage import loan_terms, year_flows

TEMPLATE_BASE_YEAR = 2024


# ─────────────────────────────── helpers ────────────────────────────────

def _amort_payment(principal: float, annual_rate: float, years: int) -> float:
    """Annual payment (12 x monthly) for a fully amortizing loan."""
    if principal <= 0 or years <= 0:
        return 0.0
    n = years * 12
    r = annual_rate / 12
    if r <= 0:
        return principal / years
    return principal * r / (1 - (1 + r) ** -n) * 12


def _amort_balance(principal: float, annual_rate: float, years: int, months_paid: int) -> float:
    if principal <= 0 or years <= 0:
        return 0.0
    n = years * 12
    k = min(max(months_paid, 0), n)
    r = annual_rate / 12
    if r <= 0:
        return principal * (1 - k / n)
    pm = principal * r / (1 - (1 + r) ** -n)
    return max(0.0, principal * (1 + r) ** k - pm * ((1 + r) ** k - 1) / r)


def ss_claim_factor(claim_age: float, fra: float = 67.0) -> float:
    """SSA benefit factor relative to the full-retirement-age benefit."""
    months = round((claim_age - fra) * 12)
    if months >= 0:
        return 1 + min(months, 36) * (2 / 3) / 100  # +8%/yr until 70
    early = -months
    return 1 - (min(early, 36) * 5 / 9 + max(early - 36, 0) * 5 / 12) / 100


def spousal_factor(claim_age: float, fra: float = 67.0) -> float:
    """Spousal benefit factor (of 50% of the worker's FRA benefit): 25/36% per month for the first 36 months
    early, 5/12% after that (62 with FRA 67 -> 65%, i.e. 32.5% of the worker's benefit). No increase after FRA."""
    early = max(0, round((fra - claim_age) * 12))
    return 1 - (min(early, 36) * 25 / 36 + max(early - 36, 0) * 5 / 12) / 100


# IRS Uniform Lifetime Table, 26 CFR 1.401(a)(9)-9(c)
ULT = {72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
       83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1,
       94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6,
       106: 4.3, 107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1, 114: 3.0, 115: 2.9, 116: 2.8,
       117: 2.7, 118: 2.5, 119: 2.3}


def rmd_age(birth_year: int) -> int:
    """SECURE 2.0 section 107: 73 if born 1951-1959, 75 if born 1960 or later (72 before that)."""
    return 75 if birth_year >= 1960 else 73 if birth_year >= 1951 else 72


def rmd_divisor(age: int) -> float:
    return ULT.get(int(age), 2.0 if age >= 120 else ULT[72])


def career_comp(phases: list, age_now: int, current_year: int, year: int) -> dict:
    age = age_now + (year - current_year)
    z = {'base_salary': 0.0, 'bonus': 0.0, 'rsu_income': 0.0, 'options_income': 0.0, 'total': 0.0}
    ph = next((p for p in phases if p['start_age'] <= age < p['end_age']), None)
    if ph is None:
        return z
    yrs = age - ph['start_age']
    base = ph['base_salary'] * (1 + ph['annual_raise_pct'] / 100) ** yrs
    bonus = base * ph['annual_bonus_pct'] / 100
    # each yearly grant vests evenly over the vesting period, so RSU income ramps up to the full grant
    vest = max(1, int(ph.get('rsu_vesting_years') or 1))
    rsu = ph['rsu_annual_grant'] * min(yrs, vest) / vest if yrs >= 1 else 0.0
    opt = 0.0
    if ph['stock_options_grant'] > 0 and ph['stock_options_liquidity_year'] == year:
        held = year - (current_year + (ph['start_age'] - age_now))
        if held > 0:
            opt = ph['stock_options_grant'] * (1 + ph['stock_options_growth_pct'] / 100) ** held
    return {'base_salary': base, 'bonus': bonus, 'rsu_income': rsu, 'options_income': opt,
            'total': base + bonus + rsu + opt}


def simple_income(base: float, raise_pct: float, job_changes: list, current_year: int, year: int) -> float:
    applicable = [j for j in job_changes if j['Year'] <= year]
    if applicable:
        j = applicable[-1]
        r = j.get('New Raise %', raise_pct)
        return j['New Income'] * (1 + r / 100) ** (year - j['Year'])
    return base * (1 + raise_pct / 100) ** (year - current_year)


def status_for_year(house: dict, year: int):
    """Returns (status or None if not owned yet, monthly rent)."""
    st, rent = None, 0.0
    for e in house['timeline']:
        if e['year'] <= year:
            st, rent = e['status'], e['rental_income']
        else:
            break
    return st, rent


# ─────────────────────────────── schedule ───────────────────────────────

@dataclass
class Schedule:
    years: list
    T: int
    cols: dict = field(default_factory=dict)       # name -> np.array(T)
    details: list = field(default_factory=list)    # per-year detail dicts (deterministic)
    events: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def build_schedule(p: dict) -> Schedule:
    cy = p['current_year']
    econ = p['economic_params']
    infl = econ['inflation_rate']
    hc_infl = econ['healthcare_inflation_rate']
    single = is_single(p)
    n1, n2 = p.get('parent1_name', 'Parent 1'), p.get('parent2_name', 'Parent 2')

    a1, a2 = p['parentX_age'], p['parentY_age']
    d1, d2 = p['parentX_death_age'], p['parentY_death_age']
    end1 = cy + (d1 - a1)
    end2 = cy + (d2 - a2) if not single else end1
    last = max(end1, end2, cy)
    years = list(range(cy, last + 1))
    T = len(years)
    tscale = (1 + infl) ** max(0, cy - TEMPLATE_BASE_YEAR)  # template $ -> today's $

    # inflation path (stress tests can override years)
    stress = p.get('_stress') or []
    infl_path = [infl] * T
    for sx in stress:
        if sx.get('type') == 'inflation_spike':
            for t_ in range(T):
                if sx['start_year'] <= years[t_] < sx['start_year'] + sx.get('years', 5):
                    infl_path[t_] = sx.get('rate', 0.08)
    wage_pt = max([sx.get('wage_passthrough', 50) / 100 for sx in stress if sx.get('type') == 'inflation_spike'] + [0.0])
    ii_arr, hi_arr = [1.0] * T, [1.0] * T
    for t_ in range(1, T):
        ii_arr[t_] = ii_arr[t_ - 1] * (1 + infl_path[t_])
        hi_arr[t_] = hi_arr[t_ - 1] * (1 + hc_infl + (infl_path[t_] - infl))

    C = {k: np.zeros(T) for k in (
        'age1', 'age2', 'alive1', 'alive2', 'work1', 'work2', 'wages1', 'wages2', 'ss1', 'ss2',
        'contrib', 'contrib1', 'contrib2', 'p1_exp', 'p2_exp', 'family_exp', 'children_exp', 'recurring_exp',
        'purchase_exp', 'healthcare_exp', 'house_exp', 'house_exp_p1', 'house_exp_p2', 'house_exp_shared',
        'mortgage_pi', 'rent_income', 'rent_taxable', 'sale_proceeds', 'sale_p1', 'sale_p2', 'sale_shared',
        'down_payment', 'dp_p1', 'dp_p2', 'dp_shared', 'home_value', 'mortgage_balance', 'home_equity',
        'equity_p1', 'equity_p2', 'equity_shared', 'other_assets', 'consumer_debt', 'infl_index', 'hc_index',
        'hc_p1', 'hc_p2', 'hc_shared', 'married', 'windfall', 'hsa_c1', 'hsa_c2', 'roth_c1', 'roth_c2', 'roth_contrib')}
    details = [dict() for _ in range(T)]
    events = []

    # 401k contribution split by current income share
    i1, i2 = max(p['parentX_income'], 0), max(p['parentY_income'], 0)
    share1 = i1 / (i1 + i2) if (i1 + i2) > 0 else (1.0 if single else 0.5)

    claim1 = p.get('parentX_ss_claim_age') or min(max(p['parentX_retirement_age'], 62), 70)
    claim2 = p.get('parentY_ss_claim_age') or min(max(p['parentY_retirement_age'], 62), 70)
    claim1, claim2 = min(max(float(claim1), 62), 70), min(max(float(claim2), 62), 70)
    ben1 = p['parentX_ss_benefit'] * 12 * ss_claim_factor(claim1)
    ben2 = (0 if single else p['parentY_ss_benefit'] * 12 * ss_claim_factor(claim2))

    # ---- precompute houses ------------------------------------------------
    sell_cost = p.get('home_selling_cost_pct', 6.0) / 100
    house_rows = []
    for h in p['houses']:
        s = max(cy, h['purchase_year'])
        future = h['purchase_year'] > cy
        terms = loan_terms(h, cy)
        owner = h.get('owner', 'Shared')
        own_key = 'p1' if owner in ('Parent1', n1) else 'p2' if owner in ('Parent2', n2) else 'shared'
        house_rows.append((h, s, future, terms, own_key))

    # cost of living: moves / spending-level changes scale everyday spending
    stl = p['state_timeline']
    base_loc, base_strat = stl[0]['state'], stl[0].get('spending_strategy', 'Average')
    for e in stl:
        if e['year'] <= cy:
            base_loc, base_strat = e['state'], e.get('spending_strategy', 'Average')
    custom_t = p.get('custom_expense_templates') or None
    custom_l = p.get('custom_locations') or {}
    # a custom city borrows prices from the location it is "like" unless it has its own template
    price_loc = lambda l: l if (custom_t and l in custom_t) else (custom_l.get(l, {}).get('cost_like') or l)
    col = [1.0] * T
    rentf = [1.0] * T                   # rent follows a rent index, not the everyday-prices ratio
    if p.get('move_adjusts_spending', True):
        cache = {}
        for t_, y_ in enumerate(years):
            loc_, st_ = base_loc, base_strat
            for e in stl:
                if e['year'] <= y_:
                    loc_, st_ = e['state'], e.get('spending_strategy', 'Average')
            key = (loc_, st_)
            if key not in cache:
                cf_ = col_factor(price_loc(base_loc), base_strat, price_loc(loc_), st_, custom_t)
                rf_ = rent_factor(price_loc(base_loc), price_loc(loc_))
                cache[key] = (cf_, rf_ if rf_ is not None else cf_)
            col[t_], rentf[t_] = cache[key]
    C['col_factor'] = np.array(col)

    for t, y in enumerate(years):
        age1, age2 = a1 + t, a2 + t
        alive1 = age1 <= d1
        alive2 = (not single) and age2 <= d2
        work1 = alive1 and age1 < p['parentX_retirement_age']
        work2 = alive2 and age2 < p['parentY_retirement_age']
        ii = ii_arr[t]
        hi = hi_arr[t]
        C['age1'][t], C['age2'][t] = age1, age2
        C['alive1'][t], C['alive2'][t] = alive1, alive2
        C['work1'][t], C['work2'][t] = work1, work2
        C['infl_index'][t], C['hc_index'][t] = ii, hi
        C['married'][t] = 1.0 if (alive1 and alive2) else 0.0
        det = details[t]

        # income
        comp1 = comp2 = None
        if work1:
            if p['parentX_career_phases']:
                comp1 = career_comp(p['parentX_career_phases'], a1, cy, y); w1 = comp1['total']
            else:
                w1 = simple_income(p['parentX_income'], p['parentX_raise'], p['parentX_job_changes'], cy, y)
        else:
            w1 = 0.0
        if work2:
            if p['parentY_career_phases']:
                comp2 = career_comp(p['parentY_career_phases'], a2, cy, y); w2 = comp2['total']
            else:
                w2 = simple_income(p['parentY_income'], p['parentY_raise'], p['parentY_job_changes'], cy, y)
        else:
            w2 = 0.0
        if wage_pt:
            # stress: part of an inflation spike passes through to pay
            bump = 1 + (ii / ((1 + infl) ** t) - 1) * wage_pt
            w1, w2 = w1 * bump, w2 * bump
        C['wages1'][t], C['wages2'][t] = w1, w2
        det['comp1'], det['comp2'] = comp1, comp2

        # social security (today's $, COLA), insolvency cut, survivor benefit
        cola = ii if p.get('ss_cola', True) else 1.0
        cut = (1 - p['ss_shortfall_percentage'] / 100) if (p['ss_insolvency_enabled'] and y >= p.get('ss_insolvency_year', 2034)) else 1.0
        s1 = ben1 if (alive1 and age1 >= claim1) else 0.0
        s2 = ben2 if (alive2 and age2 >= claim2) else 0.0
        # spousal benefit: up to 50% of the partner's age-67 benefit, once both have claimed
        if p.get('spousal_ss', True) and not single and alive1 and alive2:
            pia1, pia2 = p['parentX_ss_benefit'] * 12, p['parentY_ss_benefit'] * 12
            if s1 and age2 >= claim2:
                s1 = max(s1, 0.5 * pia2 * spousal_factor(claim1))
            if s2 and age1 >= claim1:
                s2 = max(s2, 0.5 * pia1 * spousal_factor(claim2))
        if alive1 and not alive2 and not single and age1 >= 60:
            s1 = max(s1, ben2)  # survivor keeps the larger benefit
        if alive2 and not alive1 and age2 >= 60:
            s2 = max(s2, ben1)
        C['ss1'][t], C['ss2'][t] = s1 * cola * cut, s2 * cola * cut

        # pre-tax contributions (401k + HSA), today's $
        c1 = (p['pretax_401k'] * share1 + p.get('hsa_contribution', 0) * share1) * ii if work1 else 0.0
        c2 = (p['pretax_401k'] * (1 - share1) + p.get('hsa_contribution', 0) * (1 - share1)) * ii if work2 else 0.0
        c1, c2 = min(c1, w1), min(c2, w2)
        C['contrib1'][t], C['contrib2'][t], C['contrib'][t] = c1, c2, c1 + c2
        hs = p.get('hsa_contribution', 0) * ii
        C['hsa_c1'][t] = min(hs * share1, c1) if work1 else 0.0
        C['hsa_c2'][t] = min(hs * (1 - share1), c2) if work2 else 0.0
        rc = p.get('roth_contribution', 0) * ii
        C['roth_c1'][t] = max(0.0, min(rc * share1, w1 - c1)) if work1 else 0.0
        C['roth_c2'][t] = max(0.0, min(rc * (1 - share1), w2 - c2)) if work2 else 0.0
        C['roth_contrib'][t] = C['roth_c1'][t] + C['roth_c2'][t]

        # houses
        lives_owned = False
        any_owned = False
        hdet = []
        for (h, s, future, terms, own_key) in house_rows:
            st, rent = status_for_year(h, y)
            prev_st, _ = status_for_year(h, y - 1)
            owned = st in ('Own_Live', 'Own_Rent') and not (future and y < h['purchase_year'])
            row = {'name': h['name'], 'status': st if owned else ('Sold' if st == 'Sold' else 'Not owned')}
            if owned:
                any_owned = True
                if st == 'Own_Live':
                    lives_owned = True
                k = y - s
                value = h['current_value'] * (1 + h['appreciation_rate'] / 100) ** k
                fl = year_flows(terms, y)
                pi, interest, bal_end = fl['paid'], fl['interest'], fl['bal_end']
                # PMI: until the balance reaches 78% of the purchase price
                ltv_base = terms['price'] or h['current_value']
                pmi = 0.0
                if fl['bal_start'] > 0.78 * ltv_base and pi > 0:
                    if h.get('mortgage_mode') == 'estimate':
                        if h.get('down_payment_pct', 20) < 20:
                            pmi = terms['original'] * h.get('pmi_rate', 0.5) / 100
                    else:
                        pmi = h.get('pmi_monthly', 0.0) * 12
                hoa = h.get('hoa_monthly', 0.0) * 12 * ii
                ptax = value * h['property_tax_rate']
                ins = h['home_insurance'] * ii
                maint = value * h['maintenance_rate']
                upk = h['upkeep_costs'] * ii
                total = pi + pmi + hoa + ptax + ins + maint + upk
                C['house_exp'][t] += total
                C[f'house_exp_{own_key}'][t] += total
                C['mortgage_pi'][t] += pi
                r_inc = rent * 12 * ii if st == 'Own_Rent' else 0.0
                C['rent_income'][t] += r_inc
                if r_inc:
                    C['rent_taxable'][t] += max(0.0, r_inc - (interest + pmi + hoa + ptax + ins + maint + upk))
                C['home_value'][t] += value
                C['mortgage_balance'][t] += bal_end
                eq = value - bal_end
                C['home_equity'][t] += eq
                C[f'equity_{own_key}'][t] += eq
                if future and y == h['purchase_year']:
                    dp = terms['down'] + h.get('closing_cost_pct', 0.0) / 100 * terms['price']
                    C['down_payment'][t] += dp
                    C[f'dp_{own_key}'][t] += dp
                    row['down_payment'] = dp
                    events.append({'year': y, 'type': 'house_buy', 'label': f"Buy {h['name']}", 'amount': h['purchase_price']})
                row.update(value=value, balance=bal_end, equity=eq, mortgage_pi=pi, interest=interest,
                           principal=fl['principal'], pmi=pmi, hoa=hoa, property_tax=ptax, insurance=ins,
                           maintenance=maint, upkeep=upk, rent=r_inc, total=total)
                if prev_st in ('Own_Live', 'Own_Rent') and st != prev_st and y > cy:
                    events.append({'year': y, 'type': 'house_status', 'label': f"{h['name']}: {'rent out' if st == 'Own_Rent' else 'move in'}"})
            elif st == 'Sold' and prev_st in ('Own_Live', 'Own_Rent') and y > cy and y >= h['purchase_year']:
                k = y - s
                value = h['current_value'] * (1 + h['appreciation_rate'] / 100) ** k
                bal = year_flows(terms, y)['bal_start']
                proceeds = value * (1 - sell_cost) - bal
                C['sale_proceeds'][t] += proceeds
                C[f'sale_{own_key}'][t] += proceeds
                row.update(sale_price=value, payoff=bal, proceeds=proceeds)
                events.append({'year': y, 'type': 'house_sell', 'label': f"Sell {h['name']}", 'amount': proceeds})
            hdet.append(row)
        det['houses'] = hdet

        # base living expenses (per category, scaled by cost of living)
        f = ii * col[t]
        liv1 = {k: v * f for k, v in p['parentX_expenses'].items()} if alive1 else {}
        liv2 = {k: v * f for k, v in p['parentY_expenses'].items()} if alive2 else {}
        fam = dict(p['family_shared_expenses'])
        if lives_owned:
            fam['Mortgage/Rent'] = 0.0
        if any_owned:
            for k in ('Property Tax', 'Home Insurance'):
                if k in fam:
                    fam[k] = 0.0
        livf = {k: v * (ii * rentf[t] if k == 'Mortgage/Rent' else f) for k, v in fam.items()} if (alive1 or alive2) else {}
        e1, e2, famtot = sum(liv1.values()), sum(liv2.values()), sum(livf.values())
        C['p1_exp'][t], C['p2_exp'][t], C['family_exp'][t] = e1, e2, famtot
        det['living'] = {'p1': {k: v for k, v in liv1.items() if v}, 'p2': {k: v for k, v in liv2.items() if v},
                         'shared': {k: v for k, v in livf.items() if v}}
        det['col_factor'] = col[t]

        # children
        ch_total, ch_det = 0.0, []
        for ch in p['children_list']:
            age = y - ch['birth_year']
            if age == 0:
                events.append({'year': y, 'type': 'birth', 'label': f"{ch['name']} born"})
            if age == 18:
                events.append({'year': y, 'type': 'college', 'label': f"{ch['name']} starts college"})
            exp = child_expenses_for_age(ch, age, p.get('children_expenses'))
            if not exp:
                continue
            tot = 0.0
            cats = {}
            cf = 1.0 if 18 <= age <= 21 else col[t]     # college costs follow the college's location
            for cat, v in exp.items():
                amt = v * tscale * (hi if cat in HEALTH_CATEGORIES else ii) * cf
                if amt:
                    cats[cat] = amt
                tot += amt
            ch_total += tot
            if tot > 0:
                ch_det.append({'name': ch['name'], 'age': age, 'total': tot, 'cats': cats,
                               'in_college': 18 <= age <= 21})
        C['children_exp'][t] = ch_total
        det['children'] = ch_det

        # healthcare
        hc = {'p1': 0.0, 'p2': 0.0, 'shared': 0.0}
        hc_items = []

        def _hc(key, name, amt, kind='insurance_premiums'):
            hc[key] += amt
            if amt:
                hc_items.append({'name': name, 'who': {'p1': n1, 'p2': n2, 'shared': 'Family'}[key], 'amount': amt, 'kind': kind})
        for ins in p['health_insurances']:
            prem = ins['monthly_premium'] * 12 * hi
            cb = ins['covered_by']
            in1 = alive1 and ins['start_age'] <= age1 <= ins['end_age']
            in2 = alive2 and ins['start_age'] <= age2 <= ins['end_age']
            if cb == 'Parent 1' and in1:
                _hc('p1', ins.get('name') or 'Health insurance', prem)
            elif cb == 'Parent 2' and in2:
                _hc('p2', ins.get('name') or 'Health insurance', prem)
            elif cb in ('Both', 'Family') and (in1 or in2):
                _hc('shared', ins.get('name') or 'Health insurance', prem)
        for key, alive_, age_ in (('p1', alive1, age1), ('p2', alive2, age2)):
            if alive_ and age_ >= 65:
                _hc(key, 'Medicare Part B', p['medicare_part_b_premium'] * 12 * hi, 'medicare')
                _hc(key, 'Medicare Part D', p['medicare_part_d_premium'] * 12 * hi, 'medicare')
                _hc(key, 'Medigap', p['medigap_premium'] * 12 * hi, 'medicare')
        for ltc in p['ltc_insurances']:
            if ltc['covered_person'] == 'Parent 1' and alive1 and age1 >= ltc['start_age']:
                _hc('p1', ltc.get('name') or 'Long-term care', ltc['monthly_premium'] * 12, 'ltc_premiums')
            elif ltc['covered_person'] == 'Parent 2' and alive2 and age2 >= ltc['start_age']:
                _hc('p2', ltc.get('name') or 'Long-term care', ltc['monthly_premium'] * 12, 'ltc_premiums')
        for he in p['health_expenses']:
            who = he['affected_person']
            in1 = alive1 and he['start_age'] <= age1 <= he['end_age']
            in2 = alive2 and he['start_age'] <= age2 <= he['end_age']
            amt = he['annual_amount'] * hi
            nm = he.get('name') or he.get('category') or 'Health expense'
            if who == 'Parent 1' and in1:
                _hc('p1', nm, amt, 'out_of_pocket')
            elif who == 'Parent 2' and in2:
                _hc('p2', nm, amt, 'out_of_pocket')
            elif who not in ('Parent 1', 'Parent 2') and (in1 or in2):
                _hc('shared', nm, amt, 'out_of_pocket')
        det['healthcare'] = hc_items
        C['hc_p1'][t], C['hc_p2'][t], C['hc_shared'][t] = hc['p1'], hc['p2'], hc['shared']
        C['healthcare_exp'][t] = sum(hc.values())

        # retirement / job-change events
        if age1 == p['parentX_retirement_age'] and alive1:
            events.append({'year': y, 'type': 'retire', 'label': f"{n1} retires"})
        if age2 == p['parentY_retirement_age'] and alive2:
            events.append({'year': y, 'type': 'retire', 'label': f"{n2} retires"})
        if alive1 and age1 == math.ceil(claim1):
            events.append({'year': y, 'type': 'ss', 'label': f"{n1} claims Social Security"})
        if alive2 and age2 == math.ceil(claim2):
            events.append({'year': y, 'type': 'ss', 'label': f"{n2} claims Social Security"})
        for who, jc, nm, ag, alive in (('X', p['parentX_job_changes'], n1, age1, alive1), ('Y', p['parentY_job_changes'], n2, age2, alive2)):
            phases = p[f'parent{who}_career_phases']
            if phases:
                # career-phase transitions (the first phase in effect today is not an event)
                for ph in phases:
                    if alive and ph['start_age'] == ag and y > cy and ph['start_age'] < p[f'parent{who}_retirement_age']:
                        events.append({'year': y, 'type': 'job', 'label': f"{nm}: {ph.get('label') or 'new career phase'}",
                                       'amount': ph['base_salary']})
                continue
            for j in jc:
                if j['Year'] == y:
                    events.append({'year': y, 'type': 'job', 'label': f"{nm}: new job", 'amount': j['New Income']})

    # ---- one-time purchases & recurring (with financing) -------------------
    rec_det = [[] for _ in range(T)]
    pur_det = [[] for _ in range(T)]

    def add_financed(t0, cost, rate, n_years, target, det_list, name):
        if n_years and n_years > 0:
            pay = _amort_payment(cost, rate, n_years)
            for j in range(n_years):
                if t0 + j < T:
                    C[target][t0 + j] += pay
                    det_list[t0 + j].append({'name': name + (' (payment)' if j else ''), 'amount': pay})
                    C['consumer_debt'][t0 + j] += _amort_balance(cost, rate, n_years, 12 * (j + 1))
        else:
            C[target][t0] += cost
            det_list[t0].append({'name': name, 'amount': cost})

    for m in p['major_purchases']:
        if m['year'] < cy or m['year'] > years[-1]:
            continue
        t0 = m['year'] - cy
        cost = m['amount'] * C['infl_index'][t0]
        add_financed(t0, cost, m['interest_rate'], m['financing_years'], 'purchase_exp', pur_det, m['name'])
        events.append({'year': m['year'], 'type': 'purchase', 'label': m['name'], 'amount': cost})
        if m.get('asset_type', 'Expense') not in ('Expense', '', None):
            g = m.get('appreciation_rate', 0.0)
            g = g / 100 if abs(g) > 1 else g
            for j in range(t0, T):
                C['other_assets'][j] += cost * (1 + g) ** (j - t0)

    for r in p['recurring_expenses']:
        for t, y in enumerate(years):
            if y < r['start_year'] or (r['end_year'] is not None and y > r['end_year']):
                continue
            if (y - r['start_year']) % r['frequency_years'] != 0:
                continue
            cost = r['amount'] * (C['infl_index'][t] if r['inflation_adjust'] else 1.0)
            add_financed(t, cost, r['interest_rate'], r['financing_years'], 'recurring_exp', rec_det, r['name'])
            if r['frequency_years'] > 1:
                events.append({'year': y, 'type': 'recurring', 'label': r['name'], 'amount': cost})

    for t in range(T):
        details[t]['recurring'] = rec_det[t]
        details[t]['purchases'] = pur_det[t]

    # gifts & inheritances (cash in, not taxable to the recipient)
    for w in p.get('windfalls') or []:
        try:
            y_w, amt0 = int(w.get('year')), float(w.get('amount') or 0)
        except (TypeError, ValueError):
            continue
        if cy <= y_w <= years[-1] and amt0:
            t_ = y_w - cy
            amt = amt0 * (C['infl_index'][t_] if w.get('inflation_adjust', True) else 1.0)
            C['windfall'][t_] += amt
            details[t_].setdefault('windfalls', []).append({'name': w.get('name') or 'Gift / inheritance', 'amount': amt,
                                                           'recipient': w.get('recipient', 'Parent 1'), 'separate': bool(w.get('separate', True))})
            events.append({'year': y_w, 'type': 'windfall', 'label': w.get('name') or 'Gift / inheritance', 'amount': amt})

    # separate vs marital property ("who owns what"): an accounting layer, totals unchanged
    own = None
    if not single and (p.get('ownership_tracking') or {}).get('enabled'):
        own = ownership.build(p, years, C, details, house_rows, p['shared_expense_split_pct'] / 100)

    # tax location per year
    loc = []
    stl = p['state_timeline']
    for y in years:
        cur = stl[0]['state'] if stl else 'Seattle'
        for e in stl:
            if e['year'] <= y:
                cur = e['state']
        # custom cities are taxed like the jurisdiction the user picked
        loc.append((custom_l.get(cur) or {}).get('tax_location') or cur)
    for prev, e in zip(stl, stl[1:]):
        if cy < e['year'] <= years[-1] and e['state'] != prev['state']:
            events.append({'year': e['year'], 'type': 'move', 'label': f"Move to {e['state']}"})

    # stress tests that act on the schedule
    for sx in stress:
        kind = sx.get('type')
        if kind == 'income_loss':
            who = sx.get('person', 1)
            for t_, y in enumerate(years):
                if sx['start_year'] <= y < sx['start_year'] + sx.get('years', 1):
                    keep = 1 - sx.get('pct', 100) / 100
                    for w in ((1, 2) if who == 'both' else (int(who),)):
                        C[f'wages{w}'][t_] *= keep
                        C[f'contrib{w}'][t_] *= keep
                    C['contrib'][t_] = C['contrib1'][t_] + C['contrib2'][t_]
        elif kind == 'extra_cost':
            for t_, y in enumerate(years):
                if sx['start_year'] <= y < sx['start_year'] + sx.get('years', 1):
                    amt = sx.get('amount', 0) * C['infl_index'][t_]
                    C['family_exp'][t_] += amt
                    details[t_].setdefault('recurring', [])
            events.append({'year': sx['start_year'], 'type': 'stress', 'label': sx.get('name', 'Extra cost')})

    events.sort(key=lambda e: e['year'])
    return Schedule(years=years, T=T, cols=C, details=details, events=events,
                    meta={'location': loc, 'single': single, 'claim1': claim1, 'claim2': claim2,
                          'names': (n1, n2), 'end1': end1, 'end2': end2, 'ownership': own})


# ─────────────────────────────── simulation ──────────────────────────────

HIST = None


def _hist():
    global HIST
    if HIST is None:
        HIST = np.array(ref()['HISTORICAL_STOCK_RETURNS'], dtype=float)
    return HIST


def _returns(p: dict, T: int, n: int, stochastic: bool, rng: np.random.Generator):
    r = p['economic_params']['investment_return']
    if not stochastic:
        return np.full((T, n), r)
    if p['mc_use_historical']:
        H = _hist()
        alloc = p.get('mc_stock_allocation', 100.0) / 100
        if p.get('mc_historical_mode') == 'sequential':
            start = rng.integers(0, len(H), size=n)
            idx = (start[None, :] + np.arange(T)[:, None]) % len(H)
            stock = H[idx]
        else:
            stock = rng.choice(H, size=(T, n))
        return alloc * stock + (1 - alloc) * p.get('bond_return', 0.04)
    z = rng.standard_normal((T, n))
    if p.get('mc_use_asymmetric', True):
        sp = p['mc_return_variability_positive'] / 100
        sn = p['mc_return_variability_negative'] / 100
        return r + np.where(z >= 0, z * sp, z * sn)
    return r + z * p['mc_return_variability'] / 100


def _mult(p: dict, kind: str, T: int, n: int, stochastic: bool, rng):
    """Income/expense multipliers (v0.8 semantics: iid uniform per year)."""
    if not stochastic:
        return np.ones((T, n))
    if p.get('mc_use_asymmetric', True) and not p['mc_use_historical']:
        up = p[f'mc_{kind}_variability_positive'] / 100
        dn = p[f'mc_{kind}_variability_negative'] / 100
        coin = rng.random((T, n)) > 0.5
        u = rng.random((T, n))
        return np.where(coin, 1 + u * up, 1 - u * dn)
    v = p[f'mc_{kind}_variability'] / 100
    return 1 + rng.uniform(-v, v, size=(T, n))


def simulate(plan: dict, n_paths: int = 1, stochastic: bool = False, seed: int | None = None,
             normalized: bool = False, _p: dict | None = None, _sched: Schedule | None = None) -> dict:
    p = _p or normalize_plan(plan)
    S = _sched or build_schedule(p)
    C, T, n = S.cols, S.T, n_paths
    rng = np.random.default_rng(seed)
    R = _returns(p, T, n, stochastic, rng)
    for sx in p.get('_stress') or []:
        if sx.get('type') == 'market_crash':
            for t_, y in enumerate(S.years):
                if y == sx['year']:
                    R[t_] = sx.get('drop', -0.3)
    IM = _mult(p, 'income', T, n, stochastic, rng)
    EM = _mult(p, 'expense', T, n, stochastic, rng)
    infl = p['economic_params']['inflation_rate']
    debt_rate = p.get('debt_interest_rate', 0.07)
    separate = p['finance_mode'] == 'Separate'
    split = p['shared_expense_split_pct'] / 100
    status_default = 'single' if (S.meta['single'] or p.get('tax_filing_status') == 'single') else 'married'
    override = p.get('state_tax_rate')
    override = override if (override not in (None, 0, 0.0)) else None

    pre1 = min(p.get('parentX_pretax_balance', 0.0), max(p['parentX_net_worth'], 0))
    pre2 = min(p.get('parentY_pretax_balance', 0.0), max(p['parentY_net_worth'], 0))
    ro1 = min(p.get('parentX_roth_balance', 0.0), max(p['parentX_net_worth'] - pre1, 0))
    ro2 = min(p.get('parentY_roth_balance', 0.0), max(p['parentY_net_worth'] - pre2, 0))
    L1 = np.full(n, p['parentX_net_worth'] - pre1 - ro1)
    L2 = np.full(n, p['parentY_net_worth'] - pre2 - ro2)
    # pre-tax accounts per person (RMDs follow each owner's age) + HSA; Roth (tax-free, no lifetime RMDs)
    P1, P2, H = np.full(n, pre1), np.full(n, pre2), np.full(n, p.get('hsa_balance', 0.0))
    Ro = np.full(n, ro1 + ro2)
    P = P1 + P2 + H
    cy_ = p['current_year']
    rmd_on = p.get('rmd_enabled', True)
    rmd_age1 = rmd_age(cy_ - int(p['parentX_age']))
    rmd_age2 = rmd_age(cy_ - int(p['parentY_age']))
    OV = (ownership.Overlay(p, S, L1, L2, pre1 + ro1, pre2 + ro2, p.get('hsa_balance', 0.0), n, split)
          if S.meta.get('ownership') else None)

    out = {k: np.zeros((T, n)) for k in ('liquid', 'pretax', 'net_worth', 'investable', 'taxes', 'cashflow',
                                          'wages', 'expenses', 'withdrawal', 'returns', 'liquid1', 'liquid2', 'growth',
                                          'roth', 'rmd', 'roth_withdrawal')}
    tax_parts = {k: np.zeros((T, n)) for k in ('federal', 'state', 'fica', 'foreign')}

    for t in range(T):
        y = S.years[t]
        status = 'married' if (C['married'][t] and status_default == 'married') else 'single'
        w1 = C['wages1'][t] * IM[t]
        w2 = C['wages2'][t] * IM[t]
        ss = C['ss1'][t] + C['ss2'][t]
        contrib = np.minimum(C['contrib'][t] * np.ones(n), w1 + w2)
        roth_c = np.minimum(C['roth_contrib'][t] * np.ones(n), np.maximum(w1 + w2 - contrib, 0))
        # a deceased spouse's pre-tax accounts roll over to the survivor
        if not C['alive1'][t] and C['alive2'][t]:
            P2, P1 = P2 + P1, np.zeros(n)
        elif not C['alive2'][t] and C['alive1'][t]:
            P1, P2 = P1 + P2, np.zeros(n)
        # required minimum distributions (prior year-end balance / IRS Uniform Lifetime divisor)
        rmd1 = rmd2 = np.zeros(n)
        if rmd_on:
            a1_, a2_ = int(C['age1'][t]), int(C['age2'][t])
            if C['alive1'][t] and a1_ >= rmd_age1:
                rmd1 = np.maximum(P1, 0) / rmd_divisor(a1_)
            if C['alive2'][t] and a2_ >= rmd_age2:
                rmd2 = np.maximum(P2, 0) / rmd_divisor(a2_)
        rmd = rmd1 + rmd2
        if OV is not None and np.any(rmd > 0):
            OV.rmd(rmd, P1 + P2 + H + Ro)
        P1, P2 = P1 - rmd1, P2 - rmd2
        disc = (C['p1_exp'][t] + C['p2_exp'][t] + C['family_exp'][t] + C['children_exp'][t]
                + C['recurring_exp'][t] + C['healthcare_exp'][t]) * EM[t]
        fixed = C['house_exp'][t] + C['purchase_exp'][t] + C['down_payment'][t]
        expenses = disc + fixed
        loc = S.meta['location'][t]
        tx = total_taxes(w1, w2, ss, C['rent_taxable'][t] + rmd, contrib, y, infl, loc, status, override)
        taxes = tx['total']
        inflow = w1 + w2 + ss + C['rent_income'][t] + C['sale_proceeds'][t] + C['windfall'][t] + rmd
        net = inflow - taxes - contrib - roth_c - expenses
        inc_share = np.where((w1 + w2 + ss) > 0, (w1 + C['ss1'][t]) / np.maximum(w1 + w2 + ss, 1), 0.5)
        if OV is not None:
            OV.step(t, R[t], debt_rate, C, EM, w1, w2, taxes, expenses, inc_share)

        r = R[t]
        if separate:
            shared = (C['family_exp'][t] + C['children_exp'][t] + C['recurring_exp'][t]) * EM[t] + \
                C['purchase_exp'][t] + C['hc_shared'][t] * EM[t]
            e1 = C['p1_exp'][t] * EM[t] + C['hc_p1'][t] * EM[t] + shared * split + C['house_exp_p1'][t] + \
                C['house_exp_shared'][t] * split + C['dp_p1'][t] + C['dp_shared'][t] * split
            e2 = expenses - e1
            in1 = w1 + C['ss1'][t] + (C['sale_p1'][t] + C['sale_shared'][t] * split) + C['rent_income'][t] * split + C['windfall'][t] * split + rmd1
            in2 = inflow - in1
            net1 = in1 - taxes * inc_share - C['contrib1'][t] - C['roth_c1'][t] - e1
            net2 = in2 - taxes * (1 - inc_share) - C['contrib2'][t] - C['roth_c2'][t] - e2
            gain = np.where(L1 >= 0, L1 * r, L1 * debt_rate) + np.where(L2 >= 0, L2 * r, L2 * debt_rate)
            L1 = L1 + np.where(L1 >= 0, L1 * r, L1 * debt_rate) + net1
            L2 = L2 + np.where(L2 >= 0, L2 * r, L2 * debt_rate) + net2
        else:
            L = L1 + L2
            gain = np.where(L >= 0, L * r, L * debt_rate)
            L = L + gain + net
            L1, L2 = L, np.zeros(n)

        gain = gain + (P1 + P2 + H + Ro) * r
        hsa_c = np.minimum((C['hsa_c1'][t] + C['hsa_c2'][t]) * np.ones(n), contrib)
        k401 = np.where(C['contrib'][t] > 0, (contrib - hsa_c) / max(C['contrib'][t] - C['hsa_c1'][t] - C['hsa_c2'][t], 1e-9), 0)
        P1 = P1 * (1 + r) + (C['contrib1'][t] - C['hsa_c1'][t]) * k401
        P2 = P2 * (1 + r) + (C['contrib2'][t] - C['hsa_c2'][t]) * k401
        H = H * (1 + r) + hsa_c
        Ro = Ro * (1 + r) + roth_c
        P = P1 + P2 + H
        # cover a liquid shortfall from pre-tax accounts (grossed up for tax), then Roth (tax-free)
        Lsum = L1 + L2
        need = np.maximum(-Lsum, 0)
        W = np.zeros(n)
        if np.any((need > 0) & (P > 0)):
            m = marginal_rate(np.maximum(w1 + w2 - contrib, 0) + C['rent_taxable'][t] + rmd + ss * 0.85, status,
                              (1 + infl) ** max(0, y - TAX_BASE_YEAR))
            state_guess = 0.05
            gross = need / np.maximum(1 - m - state_guess, 0.4)
            W = np.minimum(gross, np.maximum(P, 0))
            tx2 = total_taxes(w1, w2, ss, C['rent_taxable'][t] + rmd + W, contrib, y, infl, loc, status, override)
            extra_tax = tx2['total'] - taxes
            # take it proportionally from each pre-tax account
            fw = np.where(P > 0, W / np.maximum(P, 1e-9), 0)
            P1, P2, H = P1 * (1 - fw), P2 * (1 - fw), H * (1 - fw)
            P = P1 + P2 + H
            add = W - extra_tax
            if separate:
                need1 = np.maximum(-L1, 0); need2 = np.maximum(-L2, 0)
                frac1 = np.where(need > 0, need1 / np.maximum(need, 1e-9), 0.5)
                L1 = L1 + add * frac1
                L2 = L2 + add * (1 - frac1)
            else:
                L1 = L1 + add
            taxes = tx2['total']
            tx = tx2
            if OV is not None:
                OV.withdraw(t, W, add)
        # still short: Roth money, no tax
        Rw = np.zeros(n)
        short = np.maximum(-(L1 + L2), 0)
        if np.any((short > 0) & (Ro > 0)):
            Rw = np.minimum(short, np.maximum(Ro, 0))
            Ro = Ro - Rw
            if separate:
                n1_ = np.maximum(-L1, 0)
                f1_ = np.where(short > 0, n1_ / np.maximum(short, 1e-9), 0.5)
                L1, L2 = L1 + Rw * f1_, L2 + Rw * (1 - f1_)
            else:
                L1 = L1 + Rw
            if OV is not None:
                OV.withdraw(t, Rw, Rw)
        fac = C['infl_index'][t] if normalized else 1.0
        if OV is not None:
            OV.record(t, L1 + L2, P + Ro, fac)
        home = C['home_equity'][t] + C['other_assets'][t] - C['consumer_debt'][t]
        out['liquid'][t] = (L1 + L2) / fac
        out['liquid1'][t] = L1 / fac
        out['liquid2'][t] = L2 / fac
        out['pretax'][t] = P / fac
        out['investable'][t] = (L1 + L2 + P + Ro) / fac
        out['net_worth'][t] = (L1 + L2 + P + Ro + home) / fac
        out['roth'][t] = Ro / fac
        out['rmd'][t] = rmd / fac
        out['roth_withdrawal'][t] = Rw / fac
        out['taxes'][t] = taxes / fac
        out['cashflow'][t] = net / fac
        out['wages'][t] = (w1 + w2) / fac
        out['expenses'][t] = expenses / fac
        out['withdrawal'][t] = W / fac
        out['returns'][t] = r
        out['growth'][t] = gain / fac
        for k in tax_parts:
            tax_parts[k][t] = tx[k] / fac
    out.update({f'tax_{k}': v for k, v in tax_parts.items()})
    if OV is not None:
        out.update(OV.out)
    return {'p': p, 'schedule': S, 'paths': out}


# ─────────────────────────────── public API ──────────────────────────────

def _apply_plan_stress(p: dict) -> dict:
    for sx in p.get('_stress') or []:
        if sx.get('type') == 'early_death':
            who = 'X' if int(sx.get('person', 1)) == 1 else 'Y'
            age_then = p[f'parent{who}_age'] + (sx['year'] - p['current_year'])
            p[f'parent{who}_death_age'] = min(p[f'parent{who}_death_age'], age_then - 1)
            if sx.get('life_insurance'):
                p.setdefault('major_purchases', [])
                # payout modeled as a negative one-time cost (cash in)
                p['major_purchases'].append({'name': 'Life insurance payout', 'year': sx['year'], 'amount': -abs(sx['life_insurance']),
                                             'financing_years': 0, 'interest_rate': 0.0, 'asset_type': 'Expense', 'appreciation_rate': 0.0})
    return p


def project(plan: dict) -> dict:
    """Deterministic projection with a full row per year (for tables/charts)."""
    p = _apply_plan_stress(normalize_plan(plan))
    S = build_schedule(p)
    res = simulate(p, 1, False, _p=p, _sched=S)
    P, C = res['paths'], S.cols
    rows = []
    for t, y in enumerate(S.years):
        g = lambda k: float(P[k][t, 0])
        total_exp = g('expenses')
        rows.append({
            'year': y, 'age1': int(C['age1'][t]), 'age2': int(C['age2'][t]),
            'alive1': bool(C['alive1'][t]), 'alive2': bool(C['alive2'][t]),
            'work1': bool(C['work1'][t]), 'work2': bool(C['work2'][t]),
            'wages1': float(C['wages1'][t]), 'wages2': float(C['wages2'][t]),
            'ss_income': float(C['ss1'][t] + C['ss2'][t]), 'ss1': float(C['ss1'][t]), 'ss2': float(C['ss2'][t]),
            'rent_income': float(C['rent_income'][t]), 'sale_proceeds': float(C['sale_proceeds'][t]),
            'windfalls': float(C['windfall'][t]),
            'total_income': float(C['wages1'][t] + C['wages2'][t] + C['ss1'][t] + C['ss2'][t] + C['rent_income'][t]),
            'taxes': g('taxes'), 'tax_federal': g('tax_federal'), 'tax_state': g('tax_state'),
            'tax_fica': g('tax_fica'), 'tax_foreign': g('tax_foreign'),
            'contrib_pretax': float(C['contrib'][t]),
            'exp_person1': float(C['p1_exp'][t]), 'exp_person2': float(C['p2_exp'][t]),
            'exp_family': float(C['family_exp'][t]), 'exp_children': float(C['children_exp'][t]),
            'exp_housing': float(C['house_exp'][t]), 'exp_mortgage_pi': float(C['mortgage_pi'][t]),
            'exp_healthcare': float(C['healthcare_exp'][t]), 'exp_recurring': float(C['recurring_exp'][t]),
            'exp_purchases': float(C['purchase_exp'][t]), 'down_payment': float(C['down_payment'][t]),
            'total_expenses': total_exp,
            'cashflow': g('cashflow'), 'withdrawal_pretax': g('withdrawal'),
            'liquid': g('liquid'), 'pretax': g('pretax'), 'investable': g('investable'),
            'roth': g('roth'), 'rmd': g('rmd'), 'withdrawal_roth': g('roth_withdrawal'),
            'contrib_roth': float(C['roth_contrib'][t]),
            'home_value': float(C['home_value'][t]), 'mortgage_balance': float(C['mortgage_balance'][t]),
            'home_equity': float(C['home_equity'][t]), 'other_assets': float(C['other_assets'][t]),
            'consumer_debt': float(C['consumer_debt'][t]), 'net_worth': g('net_worth'),
            'liquid1': g('liquid1'), 'liquid2': g('liquid2'),
            'investment_growth': g('growth'),
            'effective_tax_rate': (g('taxes') / float(C['wages1'][t] + C['wages2'][t] + C['ss1'][t] + C['ss2'][t] + C['rent_income'][t])
                                   if (C['wages1'][t] + C['wages2'][t] + C['ss1'][t] + C['ss2'][t] + C['rent_income'][t]) > 0 else 0.0),
            'col_factor': float(C['col_factor'][t]),
            'location': S.meta['location'][t], 'infl_index': float(C['infl_index'][t]),
            'details': S.details[t],
        })
        if S.meta.get('ownership'):
            rows[-1]['ownership'] = ownership.rows(S.meta['ownership'], P, C, S, t, 1.0)
    depleted = next((r['year'] for r in rows if r['investable'] < 0), None)
    summary = _summary(p, S, rows, depleted)
    if S.meta.get('ownership'):
        o = S.meta['ownership']
        comm = [(r['year'], r['ownership']['commingled']) for r in rows if r['ownership']['commingled'] > 1]
        summary['ownership'] = {k: o[k] for k in ('regime_resolved', 'separate_income_resolved', 'earnings', 'marital_split_pct',
                                                  'marriage_year', 'state', 'shortfall')}
        summary['ownership'].update(commingled_total=sum(v for _, v in comm), commingled_years=[y for y, _ in comm],
                                    first_commingled_year=comm[0][0] if comm else None)
    return {'rows': rows, 'events': S.events, 'summary': summary, 'plan': p}


def _summary(p, S, rows, depleted):
    cy = p['current_year']
    r0 = rows[0]
    n1, n2 = S.meta['names']
    ret_year1 = cy + max(0, p['parentX_retirement_age'] - p['parentX_age'])
    ret_year2 = cy + max(0, p['parentY_retirement_age'] - p['parentY_age'])
    first_ret = min(ret_year1, ret_year2) if not S.meta['single'] else ret_year1
    at_ret = next((r for r in rows if r['year'] == first_ret), rows[-1])
    income0 = r0['total_income']
    spend0 = r0['total_expenses']
    savings_rate = (income0 - r0['taxes'] - spend0) / income0 if income0 > 0 else 0.0
    return {
        'current_year': cy, 'end_year': S.years[-1],
        'net_worth_now': p['parentX_net_worth'] + p['parentY_net_worth'] + r0['home_equity'] + r0['other_assets'],
        'investable_now': p['parentX_net_worth'] + p['parentY_net_worth'],
        'net_worth_at_retirement': at_ret['net_worth'], 'retirement_year': first_ret,
        'retirement_year1': ret_year1, 'retirement_year2': ret_year2,
        'net_worth_end': rows[-1]['net_worth'], 'investable_end': rows[-1]['investable'],
        'depletion_year': depleted,
        'depletion_age1': (p['parentX_age'] + depleted - cy) if depleted else None,
        'savings_rate_now': savings_rate,
        'names': [n1, n2], 'single': S.meta['single'],
        'claim_age1': S.meta['claim1'], 'claim_age2': S.meta['claim2'],
    }


PCTS = (5, 10, 25, 50, 75, 90, 95)


def monte_carlo(plan: dict, n: int | None = None, seed: int | None = 42, normalized: bool | None = None) -> dict:
    p = _apply_plan_stress(normalize_plan(plan))
    S = build_schedule(p)
    n = int(n or p.get('mc_simulations', 1000))
    n = max(10, min(n, 20000))
    norm = p['mc_normalize_to_today_dollars'] if normalized is None else normalized
    res = simulate(p, n, True, seed=seed, normalized=norm, _p=p, _sched=S)
    X = res['paths']
    inv = X['investable']
    nw = X['net_worth']
    alive_any = (S.cols['alive1'] + S.cols['alive2']) > 0
    depleted = (inv < 0) & alive_any[:, None]
    ever = depleted.any(axis=0)
    first_dep = np.where(ever, depleted.argmax(axis=0), -1)
    pct = lambda A: {str(q): np.percentile(A, q, axis=1).round(0).tolist() for q in PCTS}
    final = nw[-1]
    solvent_by_year = (1 - np.cumsum(depleted, axis=0).clip(0, 1).mean(axis=1)).round(4).tolist()
    # median path (by final investable) for breakdown
    order = np.argsort(inv[-1])
    mid = order[len(order) // 2]
    return {
        'years': S.years, 'n': n, 'normalized': norm,
        'mode': 'historical' if p['mc_use_historical'] else 'parametric',
        'net_worth': pct(nw), 'investable': pct(inv),
        'success_rate': float(1 - ever.mean()),
        'solvent_by_year': solvent_by_year,
        'depletion_year_median': (int(S.years[int(np.median(first_dep[ever]))]) if ever.any() else None),
        'final': {'median': float(np.median(final)), 'p10': float(np.percentile(final, 10)),
                  'p25': float(np.percentile(final, 25)), 'p75': float(np.percentile(final, 75)),
                  'p90': float(np.percentile(final, 90)), 'min': float(final.min()), 'max': float(final.max()),
                  'std': float(final.std()), 'prob_positive': float((final > 0).mean()),
                  'prob_millionaire': float((final >= 1e6).mean()), 'count_negative': int((final < 0).sum())},
        'median_path': {k: X[k][:, mid].round(0).tolist() for k in ('net_worth', 'investable', 'taxes', 'expenses', 'wages', 'cashflow')},
        'avg_return': float(X['returns'].mean()), 'return_std': float(X['returns'].std()),
        'events': S.events,
    }


def historical_stats() -> dict:
    H = _hist()
    return {'mean': float(H.mean()), 'median': float(np.median(H)), 'std': float(H.std()), 'min': float(H.min()),
            'max': float(H.max()), 'positive_years': int((H > 0).sum()), 'negative_years': int((H < 0).sum()),
            'total_years': int(len(H)), 'start_year': 1924, 'returns': H.tolist()}
