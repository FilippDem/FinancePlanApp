"""Plan schema handling.

A *plan* is a plain dict using exactly the JSON keys written by v0.8
``save_data()`` (so existing household files load unchanged). v2 only ADDS
optional keys (documented in V2_KEYS) and never renames/removes keys.

normalize_plan() fills defaults, migrates older formats (V13/V14/partial demo
files) and returns a new dict. Unknown keys are preserved untouched.
"""
from __future__ import annotations

import copy
from datetime import datetime

from .reference import default_plan, adult_template, normalize_strategy_name
from .mortgage import sync_legacy_fields

# New optional keys introduced in v2 (all have safe defaults).
V2_KEYS = {
    # Social Security claim ages (default: max(retirement age, 62), capped at 70)
    'parentX_ss_claim_age': None,
    'parentY_ss_claim_age': None,
    'ss_cola': True,                 # benefits grow with inflation (entered in today's $)
    'ss_insolvency_year': 2034,      # year the trust-fund shortfall starts
    # Portion of each person's savings that sits in pre-tax retirement accounts
    'parentX_pretax_balance': 0.0,
    'parentY_pretax_balance': 0.0,
    # Portfolio / Monte Carlo
    'mc_stock_allocation': 100.0,    # % stocks in historical mode (rest earns bond_return)
    'bond_return': 0.04,
    'mc_historical_mode': 'random',  # 'random' (iid bootstrap) | 'sequential' (historical sequences)
    'debt_interest_rate': 0.07,      # interest charged when liquid savings go negative
    'home_selling_cost_pct': 6.0,    # realtor + closing costs when a home is sold
}

HOUSE_DEFAULTS = {
    'name': 'Home', 'purchase_year': None, 'purchase_price': 0.0, 'current_value': 0.0,
    'mortgage_balance': 0.0, 'mortgage_rate': 0.065, 'mortgage_years_left': 30,
    'property_tax_rate': 0.01, 'home_insurance': 1500.0, 'maintenance_rate': 0.01,
    'upkeep_costs': 0.0, 'owner': 'Shared', 'location': '', 'appreciation_rate': 3.0, 'timeline': None,
    # v2 mortgage calculator fields
    'mortgage_mode': 'actual',          # 'estimate' (price/down%/term/rate) | 'actual' (statement numbers)
    'down_payment_pct': None,           # estimate mode; derived from price & balance when missing
    'loan_term_years': 30,
    'mortgage_payment_override': None,  # actual mode: real monthly P&I (extra = faster payoff)
    'pmi_rate': 0.5,                    # estimate mode: annual % of loan while down payment < 20%
    'pmi_monthly': 0.0,                 # actual mode: PMI on your statement
    'hoa_monthly': 0.0,
    'closing_cost_pct': 0.0,            # paid with the down payment for future purchases
}
RECURRING_DEFAULTS = {'name': 'Expense', 'category': 'Other', 'amount': 0.0, 'frequency_years': 1,
                      'start_year': None, 'end_year': None, 'inflation_adjust': True, 'parent': 'Both',
                      'financing_years': 0, 'interest_rate': 0.0}
PURCHASE_DEFAULTS = {'name': 'Purchase', 'year': None, 'amount': 0.0, 'financing_years': 0,
                     'interest_rate': 0.0, 'asset_type': 'Expense', 'appreciation_rate': 0.0}
CHILD_DEFAULTS = {'name': 'Child', 'birth_year': None, 'use_template': True, 'template_state': 'Seattle',
                  'template_strategy': 'Average', 'school_type': 'Public', 'college_type': 'Public',
                  'college_location': 'Seattle'}
CAREER_DEFAULTS = {'start_age': 30, 'end_age': 65, 'philosophy': 'Stable', 'base_salary': 0.0,
                   'annual_raise_pct': 3.0, 'annual_bonus_pct': 0.0, 'rsu_annual_grant': 0.0,
                   'rsu_vesting_years': 4, 'stock_options_grant': 0.0, 'stock_options_growth_pct': 0.0,
                   'stock_options_liquidity_year': 0, 'label': ''}
HEALTH_INS_DEFAULTS = {'name': 'Health plan', 'type': 'Employer', 'monthly_premium': 0.0, 'annual_deductible': 0.0,
                       'annual_out_of_pocket_max': 0.0, 'copay_primary': 0.0, 'copay_specialist': 0.0,
                       'covered_by': 'Both', 'start_age': 0, 'end_age': 64}
LTC_DEFAULTS = {'name': 'LTC policy', 'monthly_premium': 0.0, 'daily_benefit': 0.0, 'benefit_period_days': 0,
                'elimination_period_days': 90, 'covered_person': 'Parent 1', 'start_age': 55,
                'inflation_protection': 0.03}
HEALTH_EXP_DEFAULTS = {'category': 'Routine Care', 'annual_amount': 0.0, 'covered_by_insurance': False,
                       'start_age': 0, 'end_age': 100, 'affected_person': 'Both'}
ECON_DEFAULTS = {'investment_return': 0.06, 'inflation_rate': 0.03, 'expense_growth_rate': 0.02,
                 'healthcare_inflation_rate': 0.045, 'use_historical_returns': False,
                 'use_historical_inflation': False, 'use_historical_expense_growth': False,
                 'use_historical_healthcare_inflation': False}


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        f = float(v)
        if f != f:  # NaN
            return default
        return f
    except (TypeError, ValueError):
        return default


def _int(v, default=0):
    return int(round(_num(v, default)))


def _fill(item: dict, defaults: dict) -> dict:
    out = dict(defaults)
    out.update({k: v for k, v in (item or {}).items()})
    return out


def _records(v) -> list:
    """Accept list-of-records or pandas 'dict of columns' shapes."""
    if v is None:
        return []
    if isinstance(v, list):
        return [r for r in v if isinstance(r, dict)]
    if isinstance(v, dict):  # {'Year': {0: 2027}, 'New Income': {0: 1}} or {'Year':[..]}
        cols = list(v.keys())
        if not cols:
            return []
        first = v[cols[0]]
        if isinstance(first, dict):
            idx = list(first.keys())
            return [{c: v[c].get(i) for c in cols} for i in idx]
        if isinstance(first, list):
            return [{c: v[c][i] for c in cols} for i in range(len(first))]
    return []


def normalize_plan(raw: dict | None) -> dict:
    """Return a complete, migrated plan dict. Never mutates the input."""
    raw = copy.deepcopy(raw or {})
    base = copy.deepcopy(default_plan())
    now_year = datetime.now().year
    p = base
    p.update(raw)  # raw wins; unknown keys preserved

    # ---- V13 format: economic_scenarios + active_scenario --------------
    if 'economic_params' not in raw and isinstance(raw.get('economic_scenarios'), dict):
        sc = raw['economic_scenarios'].get(raw.get('active_scenario', 'Moderate')) or next(iter(raw['economic_scenarios'].values()), {})
        p['economic_params'] = {**ECON_DEFAULTS, **{k: sc[k] for k in ECON_DEFAULTS if k in sc}}
    # V13 nests parent data under parentX/parentY
    for who in ('X', 'Y'):
        nested = raw.get(f'parent{who}')
        if isinstance(nested, dict):
            for k in ('age', 'net_worth', 'income', 'raise', 'retirement_age', 'ss_benefit', 'job_changes'):
                if k in nested and f'parent{who}_{k}' not in raw:
                    p[f'parent{who}_{k}'] = nested[k]
    if isinstance(raw.get('parent_settings'), dict):
        for k, v in raw['parent_settings'].items():
            p.setdefault(k, v)
            if k not in raw:
                p[k] = v
    if isinstance(raw.get('tax_settings'), dict):
        for k in ('state_tax_rate', 'pretax_401k'):
            if k in raw['tax_settings'] and k not in raw:
                p[k] = raw['tax_settings'][k]
    if isinstance(raw.get('social_security'), dict):
        ss = raw['social_security']
        if 'ss_insolvency_enabled' not in raw and 'insolvency_enabled' in ss:
            p['ss_insolvency_enabled'] = ss['insolvency_enabled']
        if 'ss_shortfall_percentage' not in raw and 'shortfall_percentage' in ss:
            p['ss_shortfall_percentage'] = ss['shortfall_percentage']
    if isinstance(raw.get('monte_carlo'), dict):
        for k, v in raw['monte_carlo'].items():
            key = f'mc_{k}'
            if key not in raw:
                p[key] = v

    # ---- Legacy family expenses ('expenses') ---------------------------
    # v0.8 ignores 'expenses'. If a file has only the legacy dict (V13/V14 or
    # partial demo files), treat it as the shared family budget and don't
    # silently add Seattle template spending on top of it.
    legacy = raw.get('expenses') if isinstance(raw.get('expenses'), dict) else None
    has_new = any(k in raw for k in ('parentX_expenses', 'parentY_expenses', 'family_shared_expenses'))
    if legacy and not has_new and sum(_num(v) for v in legacy.values()) > 0:
        p['family_shared_expenses'] = {k: _num(v) for k, v in legacy.items()}
        p['parentX_expenses'] = {}
        p['parentY_expenses'] = {}
        p['_migrated_legacy_expenses'] = True

    # ---- Scalars --------------------------------------------------------
    p['current_year'] = _int(p.get('current_year'), now_year) or now_year
    for who in ('X', 'Y'):
        p[f'parent{who}_age'] = _int(p.get(f'parent{who}_age'), 30)
        p[f'parent{who}_net_worth'] = _num(p.get(f'parent{who}_net_worth'))
        p[f'parent{who}_income'] = _num(p.get(f'parent{who}_income'))
        p[f'parent{who}_raise'] = _num(p.get(f'parent{who}_raise'), 3.0)
        p[f'parent{who}_retirement_age'] = _int(p.get(f'parent{who}_retirement_age'), 65)
        p[f'parent{who}_death_age'] = _int(p.get(f'parent{who}_death_age'), 100)
        p[f'parent{who}_ss_benefit'] = _num(p.get(f'parent{who}_ss_benefit'))
        p[f'parent{who}_expenses'] = {k: _num(v) for k, v in (p.get(f'parent{who}_expenses') or {}).items()}
        jc = []
        for r in _records(p.get(f'parent{who}_job_changes')):
            y, inc = r.get('Year'), r.get('New Income')
            if _num(y, 0) > 0 and inc is not None and _num(inc, -1) >= 0:
                row = {'Year': _int(y), 'New Income': _num(inc)}
                if 'New Raise %' in r and r['New Raise %'] is not None:
                    row['New Raise %'] = _num(r['New Raise %'])
                jc.append(row)
        p[f'parent{who}_job_changes'] = sorted(jc, key=lambda r: r['Year'])
        # Demo/partial files have no career phases: v0.8 then silently used its
        # default 75k phase. v2 uses the simple income model instead.
        if f'parent{who}_career_phases' not in raw:
            p[f'parent{who}_career_phases'] = []
        p[f'parent{who}_career_phases'] = [_fill(c, CAREER_DEFAULTS) for c in (p.get(f'parent{who}_career_phases') or [])]
        if f'parent{who}_expenses' not in raw and not p.get('_migrated_legacy_expenses'):
            loc = p.get(f'parent{who}_expense_location') or 'Seattle'
            p[f'parent{who}_expenses'] = adult_template(loc, p.get(f'parent{who}_expense_strategy') or 'Average')

    p['family_shared_expenses'] = {k: _num(v) for k, v in (p.get('family_shared_expenses') or {}).items()}
    p['finance_mode'] = p.get('finance_mode') if p.get('finance_mode') in ('Pooled', 'Separate') else 'Pooled'
    p['shared_expense_split_pct'] = _num(p.get('shared_expense_split_pct'), 50)
    p['ss_insolvency_enabled'] = bool(p.get('ss_insolvency_enabled', True))
    p['ss_shortfall_percentage'] = _num(p.get('ss_shortfall_percentage'), 30.0)
    p['pretax_401k'] = _num(p.get('pretax_401k'), 0.0)
    if p.get('state_tax_rate') is not None:
        p['state_tax_rate'] = _num(p.get('state_tax_rate'))
    for k, v in V2_KEYS.items():
        if k not in p or p[k] is None and v is not None:
            p[k] = v

    econ = p.get('economic_params') or {}
    p['economic_params'] = {**ECON_DEFAULTS, **econ}
    for k in ('investment_return', 'inflation_rate', 'expense_growth_rate', 'healthcare_inflation_rate'):
        p['economic_params'][k] = _num(p['economic_params'][k], ECON_DEFAULTS[k])

    # ---- Lists ----------------------------------------------------------
    houses = []
    for h in p.get('houses') or []:
        h = _fill(h, HOUSE_DEFAULTS)
        for k in ('purchase_price', 'current_value', 'mortgage_balance', 'mortgage_rate', 'property_tax_rate',
                  'home_insurance', 'maintenance_rate', 'upkeep_costs', 'appreciation_rate'):
            h[k] = _num(h[k], HOUSE_DEFAULTS[k] or 0.0)
        h['purchase_year'] = _int(h.get('purchase_year'), p['current_year'])
        h['mortgage_years_left'] = _int(h.get('mortgage_years_left'), 0)
        for k in ('pmi_rate', 'pmi_monthly', 'hoa_monthly', 'closing_cost_pct'):
            h[k] = _num(h.get(k), HOUSE_DEFAULTS[k])
        h['loan_term_years'] = _num(h.get('loan_term_years'), 30) or 30
        if h.get('mortgage_mode') not in ('estimate', 'actual'):
            h['mortgage_mode'] = 'actual'
        if h.get('down_payment_pct') is None:
            h['down_payment_pct'] = round((1 - h['mortgage_balance'] / h['purchase_price']) * 100, 2) if h['purchase_price'] > 0 else 20.0
        h['down_payment_pct'] = min(max(_num(h['down_payment_pct'], 20.0), 0.0), 100.0)
        ov = h.get('mortgage_payment_override')
        h['mortgage_payment_override'] = _num(ov) if ov not in (None, '', 0) and _num(ov) > 0 else None
        tl = []
        for e in h.get('timeline') or []:
            if not isinstance(e, dict) or e.get('year') is None:
                continue
            status = e.get('status') or 'Own_Live'
            status = {'Sell': 'Sold', 'Own': 'Own_Live', 'Rent': 'Own_Rent'}.get(status, status)
            tl.append({'year': _int(e['year']), 'status': status, 'rental_income': _num(e.get('rental_income'))})
        if not tl:
            tl = [{'year': h['purchase_year'], 'status': 'Own_Live', 'rental_income': 0.0}]
        h['timeline'] = sorted(tl, key=lambda e: e['year'])
        sync_legacy_fields(h, p['current_year'])
        houses.append(h)
    p['houses'] = houses

    p['recurring_expenses'] = []
    for r in raw.get('recurring_expenses', base.get('recurring_expenses')) or []:
        r = _fill(r, RECURRING_DEFAULTS)
        r['amount'] = _num(r['amount'])
        r['frequency_years'] = max(1, _int(r['frequency_years'], 1))
        r['start_year'] = _int(r['start_year'], p['current_year'])
        r['end_year'] = None if r.get('end_year') in (None, '', 0) else _int(r['end_year'])
        r['financing_years'] = _int(r.get('financing_years'), 0)
        r['interest_rate'] = _num(r.get('interest_rate'))
        p['recurring_expenses'].append(r)

    p['major_purchases'] = []
    for m in raw.get('major_purchases', base.get('major_purchases')) or []:
        m = _fill(m, PURCHASE_DEFAULTS)
        m['amount'] = _num(m['amount'])
        m['year'] = _int(m['year'], p['current_year'])
        m['financing_years'] = _int(m.get('financing_years'), 0)
        m['interest_rate'] = _num(m.get('interest_rate'))
        m['appreciation_rate'] = _num(m.get('appreciation_rate'))
        p['major_purchases'].append(m)

    kids, seen = [], set()
    for c in p.get('children_list') or []:
        c = _fill(c, CHILD_DEFAULTS)
        c['birth_year'] = _int(c.get('birth_year'), p['current_year'])
        c['name'] = str(c.get('name') or 'Child')
        base_name, n = c['name'], 2
        while c['name'].lower() in seen:  # v0.8 forbids duplicate names
            c['name'] = f"{base_name} {n}"; n += 1
        seen.add(c['name'].lower())
        kids.append(c)
    p['children_list'] = kids

    st = []
    for e in p.get('state_timeline') or []:
        if isinstance(e, dict) and e.get('year') is not None:
            st.append({'year': _int(e['year']), 'state': e.get('state') or 'Seattle',
                       'spending_strategy': e.get('spending_strategy') or 'Average'})
    if not st:
        st = [{'year': p['current_year'], 'state': 'Seattle', 'spending_strategy': 'Average'}]
    p['state_timeline'] = sorted(st, key=lambda e: e['year'])

    p['health_insurances'] = [_fill(x, HEALTH_INS_DEFAULTS) for x in p.get('health_insurances') or []]
    p['ltc_insurances'] = [_fill(x, LTC_DEFAULTS) for x in p.get('ltc_insurances') or []]
    p['health_expenses'] = [_fill(x, HEALTH_EXP_DEFAULTS) for x in p.get('health_expenses') or []]
    for k, d in (('medicare_part_b_premium', 174.70), ('medicare_part_d_premium', 55.0), ('medigap_premium', 150.0),
                 ('hsa_balance', 0.0), ('hsa_contribution', 0.0)):
        p[k] = _num(p.get(k), d)

    # MC settings
    for k, d in (('mc_simulations', 1000), ('mc_income_variability', 10.0), ('mc_expense_variability', 5.0),
                 ('mc_return_variability', 15.0), ('mc_income_variability_positive', 10.0),
                 ('mc_income_variability_negative', 10.0), ('mc_expense_variability_positive', 5.0),
                 ('mc_expense_variability_negative', 5.0), ('mc_return_variability_positive', 15.0),
                 ('mc_return_variability_negative', 15.0)):
        p[k] = _num(p.get(k), d)
    p['mc_use_historical'] = bool(p.get('mc_use_historical', False))
    p['mc_normalize_to_today_dollars'] = bool(p.get('mc_normalize_to_today_dollars', False))
    p['mc_use_asymmetric'] = bool(p.get('mc_use_asymmetric', True))
    return p


def is_single(p: dict) -> bool:
    return p.get('parent2_name', '') in ('N/A', '') or (
        p.get('parent2_name') == 'Parent 2' and _num(p.get('parentY_income')) == 0 and _num(p.get('parentY_net_worth')) == 0
        and _num(p.get('parentY_ss_benefit')) == 0)


def strategy_label(s: str) -> str:
    return normalize_strategy_name(s)
