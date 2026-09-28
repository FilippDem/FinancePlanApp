import copy
import json
import time
from pathlib import Path

import numpy as np
import pytest

from finplan.engine import (project, monte_carlo, simulate, ss_claim_factor, _amort_payment, _amort_balance,
                            build_schedule, historical_stats)
from finplan.plan import normalize_plan
from finplan.reference import default_plan, demo_plans, children_template, adult_template
from finplan.taxes import federal_income_tax, fica, taxable_ss, total_taxes


def base_plan(**kw):
    p = copy.deepcopy(default_plan())
    p.update({'current_year': 2026, 'houses': [], 'children_list': [], 'recurring_expenses': [],
              'major_purchases': [], 'ss_insolvency_enabled': False, 'pretax_401k': 0.0})
    p.update(kw)
    return p


# ── reference data / templates ───────────────────────────────────────────
def test_reference_templates_match_v08_shapes():
    t = children_template('Seattle', 'Average')
    assert all(len(v) == 31 for v in t.values())
    a = adult_template('Seattle', 'Average (statistical)')
    assert a['Groceries'] > 0
    assert adult_template('Nowhere-land', 'Average') == adult_template('Seattle', 'Average (statistical)')


# ── plan normalization / data preservation ──────────────────────────────
def test_normalize_preserves_unknown_keys_and_does_not_mutate():
    raw = {'parentX_age': 40, 'some_future_key': {'x': 1}, 'houses': []}
    before = copy.deepcopy(raw)
    p = normalize_plan(raw)
    assert raw == before
    assert p['some_future_key'] == {'x': 1}
    assert p['parentX_age'] == 40


def test_all_demo_plans_and_default_normalize_and_project():
    for name, plan in list(demo_plans().items()) + [('default', default_plan())]:
        r = project(plan)
        assert r['rows'], name
        assert all(np.isfinite(row['net_worth']) for row in r['rows']), name


def test_v13_format_migrates():
    v13 = {
        'current_year': 2025, 'marriage_year': 'N/A',
        'parent_settings': {'parent1_name': 'Filipp', 'parent2_name': 'Erin'},
        'parentX': {'age': 35, 'net_worth': 85000, 'income': 95000, 'raise': 3.5, 'retirement_age': 65,
                    'ss_benefit': 2500, 'job_changes': [{'Year': 2027, 'New Income': 105000}]},
        'parentY': {'age': 33, 'net_worth': 75000, 'income': 85000, 'raise': 3.2, 'retirement_age': 65,
                    'ss_benefit': 2200, 'job_changes': []},
        'expenses': {'Food & Groceries': 16800, 'Clothing': 4200},
        'economic_scenarios': {'Moderate': {'name': 'Moderate', 'investment_return': 0.06, 'inflation_rate': 0.025,
                                            'expense_growth_rate': 0.02, 'healthcare_inflation_rate': 0.045}},
        'active_scenario': 'Moderate',
        'houses': [{'name': 'Primary', 'purchase_year': 2020, 'purchase_price': 600000, 'current_value': 650000,
                    'mortgage_balance': 500000, 'mortgage_rate': 0.067, 'mortgage_years_left': 28,
                    'property_tax_rate': 0.0092, 'home_insurance': 1800, 'maintenance_rate': 0.015,
                    'upkeep_costs': 3000, 'owner': 'Shared',
                    'timeline': [{'year': 2020, 'status': 'Own_Live', 'rental_income': 0}]}],
        'tax_settings': {'state_tax_rate': 0.0, 'pretax_401k': 0},
        'social_security': {'insolvency_enabled': True, 'shortfall_percentage': 30},
    }
    p = normalize_plan(v13)
    assert p['parent1_name'] == 'Filipp'
    assert p['parentX_income'] == 95000
    assert p['parentX_job_changes'] == [{'Year': 2027, 'New Income': 105000.0}]
    assert p['economic_params']['inflation_rate'] == 0.025
    assert p['family_shared_expenses'] == {'Food & Groceries': 16800.0, 'Clothing': 4200.0}
    assert p['parentX_expenses'] == {}
    r = project(v13)
    assert r['rows'][0]['exp_family'] == pytest.approx(21000)


def test_sell_alias_and_dataframe_shapes():
    p = normalize_plan({'houses': [{'name': 'H', 'purchase_year': 2020, 'timeline': [
        {'year': 2020, 'status': 'Own_Live'}, {'year': 2030, 'status': 'Sell'}]}],
        'parentX_job_changes': {'Year': {'0': 2030}, 'New Income': {'0': 1000}}})
    assert p['houses'][0]['timeline'][1]['status'] == 'Sold'
    assert p['parentX_job_changes'] == [{'Year': 2030, 'New Income': 1000.0}]


# ── taxes ────────────────────────────────────────────────────────────────
def test_federal_brackets_2024():
    assert float(federal_income_tax(100000, 'married', 1.0)) == pytest.approx(12106)
    assert float(federal_income_tax(0, 'married', 1.0)) == 0
    # indexing doubles all thresholds -> tax on doubled income doubles
    assert float(federal_income_tax(200000, 'married', 2.0)) == pytest.approx(2 * 12106)


def test_fica_per_earner():
    two = float(fica(95000, 'married', 1) + fica(85000, 'married', 1))
    assert two == pytest.approx(180000 * 0.0765)


def test_ss_taxation_caps_at_85pct():
    assert float(taxable_ss(40000, 200000, 'married')) == pytest.approx(34000)
    assert float(taxable_ss(40000, 0, 'married')) == 0


def test_rental_income_has_no_fica():
    a = total_taxes(0, 0, 0, 50000, 0, 2024, 0.0, 'Texas')
    assert float(a['fica']) == 0 and float(a['federal']) > 0


# ── mortgage / housing ──────────────────────────────────────────────────
def test_amortization():
    pay = _amort_payment(500000, 0.067, 28)
    assert pay / 12 == pytest.approx(3300, abs=5)
    assert _amort_balance(500000, 0.067, 28, 28 * 12) == pytest.approx(0, abs=1e-6)


def test_mortgage_paid_through_final_year_and_equity_grows():
    h = {'name': 'Home', 'purchase_year': 2020, 'purchase_price': 600000, 'current_value': 650000,
         'mortgage_balance': 500000, 'mortgage_rate': 0.067, 'mortgage_years_left': 28, 'property_tax_rate': 0.0,
         'home_insurance': 0, 'maintenance_rate': 0, 'upkeep_costs': 0, 'owner': 'Shared', 'appreciation_rate': 0,
         'timeline': [{'year': 2020, 'status': 'Own_Live', 'rental_income': 0}]}
    r = project(base_plan(houses=[h]))
    rows = {x['year']: x for x in r['rows']}
    assert rows[2026]['exp_mortgage_pi'] == pytest.approx(3300 * 12, rel=0.01)
    assert rows[2053]['exp_mortgage_pi'] > 0          # last payment year (2026 + 28 - 1)
    assert rows[2054]['exp_mortgage_pi'] == 0
    assert rows[2053]['home_equity'] == pytest.approx(650000, abs=1)
    assert rows[2026]['home_equity'] > 150000


def test_future_purchase_pays_down_payment_and_sale_has_no_double_count():
    h = {'name': 'Future', 'purchase_year': 2030, 'purchase_price': 500000, 'current_value': 500000,
         'mortgage_balance': 400000, 'mortgage_rate': 0.05, 'mortgage_years_left': 30, 'property_tax_rate': 0,
         'home_insurance': 0, 'maintenance_rate': 0, 'upkeep_costs': 0, 'appreciation_rate': 0,
         'timeline': [{'year': 2030, 'status': 'Own_Live', 'rental_income': 0},
                      {'year': 2035, 'status': 'Sold', 'rental_income': 0}]}
    p = base_plan(houses=[h], home_selling_cost_pct=0.0)
    p['economic_params'] = {**p['economic_params'], 'investment_return': 0.0, 'inflation_rate': 0.0}
    rows = {x['year']: x for x in project(p)['rows']}
    assert rows[2029]['home_equity'] == 0
    assert rows[2030]['down_payment'] == pytest.approx(100000)
    # selling at cost with 0% return: net worth should not jump in the sale year
    delta_sale = rows[2035]['net_worth'] - rows[2034]['net_worth']
    delta_before = rows[2034]['net_worth'] - rows[2033]['net_worth']
    assert abs(delta_sale - delta_before) < 45000  # only the saved P&I differs
    assert rows[2035]['sale_proceeds'] > 0 and rows[2036]['sale_proceeds'] == 0


def test_rent_counts_as_income():
    h = {'name': 'Rental', 'purchase_year': 2020, 'current_value': 400000, 'mortgage_balance': 0,
         'mortgage_years_left': 0, 'timeline': [{'year': 2020, 'status': 'Own_Rent', 'rental_income': 2000}]}
    r = project(base_plan(houses=[h]))
    assert r['rows'][0]['rent_income'] == pytest.approx(24000)


# ── social security ──────────────────────────────────────────────────────
def test_ss_claim_factors():
    assert ss_claim_factor(62) == pytest.approx(0.70)
    assert ss_claim_factor(67) == pytest.approx(1.0)
    assert ss_claim_factor(70) == pytest.approx(1.24)


def test_ss_starts_no_earlier_than_62_and_has_cola():
    p = base_plan(parentX_age=50, parentX_retirement_age=55, parentX_ss_benefit=2000, parentY_ss_benefit=0)
    rows = {x['year']: x for x in project(p)['rows']}
    assert rows[2026 + 11]['ss1'] == 0          # age 61
    y62 = rows[2026 + 12]['ss1']
    assert y62 == pytest.approx(2000 * 12 * 0.70 * 1.03 ** 12, rel=1e-6)
    assert rows[2026 + 13]['ss1'] == pytest.approx(y62 * 1.03, rel=1e-6)


# ── children / purchases ────────────────────────────────────────────────
def test_children_costs_inflate():
    kid = {'name': 'A', 'birth_year': 2026, 'template_state': 'Seattle', 'template_strategy': 'Average'}
    rows = project(base_plan(children_list=[kid]))['rows']
    assert rows[0]['exp_children'] > 10000
    assert rows[18]['exp_children'] > rows[17]['exp_children']  # college year


def test_financed_purchase_is_amortized():
    m = {'name': 'Car', 'year': 2027, 'amount': 30000, 'financing_years': 5, 'interest_rate': 0.05}
    p = base_plan(major_purchases=[m])
    p['economic_params'] = {**p['economic_params'], 'inflation_rate': 0.0}
    rows = {x['year']: x for x in project(p)['rows']}
    pay = _amort_payment(30000, 0.05, 5)
    assert rows[2027]['exp_purchases'] == pytest.approx(pay)
    assert rows[2031]['exp_purchases'] == pytest.approx(pay)
    assert rows[2032]['exp_purchases'] == 0


# ── Monte Carlo ──────────────────────────────────────────────────────────
def test_zero_variability_mc_equals_deterministic():
    p = base_plan(mc_use_asymmetric=False, mc_return_variability=0, mc_income_variability=0,
                  mc_expense_variability=0)
    det = project(p)['rows']
    mc = monte_carlo(p, 50)
    assert mc['net_worth']['50'][-1] == pytest.approx(det[-1]['net_worth'], rel=1e-6, abs=2)


def test_return_volatility_is_in_percentage_points():
    m = monte_carlo(base_plan(), 4000)
    assert 0.12 < m['return_std'] < 0.18  # v0.8 gave ~0.009


def test_historical_mode_and_sequential():
    for mode in ('random', 'sequential'):
        m = monte_carlo(base_plan(mc_use_historical=True, mc_historical_mode=mode, mc_stock_allocation=60), 500)
        assert 0 <= m['success_rate'] <= 1
    assert historical_stats()['total_years'] == 100


def test_monte_carlo_speed():
    t = time.time()
    monte_carlo(demo_plans()[list(demo_plans())[1]], 5000)
    assert time.time() - t < 3.0


def test_separate_mode_runs_and_splits():
    p = base_plan(finance_mode='Separate', shared_expense_split_pct=60)
    r = project(p)['rows']
    assert r[0]['liquid1'] != 0 and r[0]['liquid2'] != 0
    assert r[0]['liquid'] == pytest.approx(r[0]['liquid1'] + r[0]['liquid2'])


def test_demo_overrides_apply_and_keep_raw():
    raw = demo_plans(raw=True)
    tuned = demo_plans()
    assert raw.keys() == tuned.keys()
    k = next(n for n in raw if 'Tech Couple' in n)
    assert raw[k]['state_timeline'][1]['state'] == 'Houston' and tuned[k]['state_timeline'][1]['state'] == 'Austin'
    assert tuned[k].get('demo_note')
    # removed items disappear, untouched ones remain
    ex = next(n for n in raw if 'Executives' in n)
    names = [x['name'] for x in tuned[ex]['major_purchases']]
    assert 'Luxury Yacht Purchase' not in names and "Isabella's Wedding Reception" in names


def test_moves_adjust_spending_by_cost_of_living():
    from finplan.engine import project
    p = default_plan()
    cy = p['current_year']
    p['state_timeline'] = [{'year': cy, 'state': 'Seattle', 'spending_strategy': 'Average'},
                           {'year': cy + 3, 'state': 'Texas', 'spending_strategy': 'Average'}]
    rows = project(p)['rows']
    before, after = rows[2], rows[3]
    assert after['col_factor'] < 1.0 and before['col_factor'] == 1.0
    assert after['exp_family'] / after['infl_index'] < before['exp_family'] / before['infl_index'] * 0.99
    # per-category detail sums to the totals
    d = after['details']['living']
    assert abs(sum(d['shared'].values()) - after['exp_family']) < 1e-6
    assert abs(sum(d['p1'].values()) - after['exp_person1']) < 1e-6
    # toggle off -> v0.8 behaviour (location only changes taxes)
    p['move_adjusts_spending'] = False
    rows2 = project(p)['rows']
    assert rows2[3]['col_factor'] == 1.0


def test_detail_breakdowns_present():
    from finplan.engine import project
    p = default_plan()
    r = project(p)['rows'][0]
    for c in r['details']['children']:
        assert abs(sum(c['cats'].values()) - c['total']) < 1e-6
    assert 'investment_growth' in r and 'effective_tax_rate' in r
    assert isinstance(r['details']['healthcare'], list)


def test_cost_of_living_corrections():
    from finplan import reference as R
    sea = R.cost_of_living('Seattle', 'Average')
    # BEA 2024 non-housing prices: SF and Seattle are within a few percent of each other
    assert 0.97 < R.cost_of_living('San Francisco', 'Average') / sea < 1.10
    assert R.cost_of_living('Columbus', 'Average') > R.cost_of_living('Mississippi', 'Average') * 0.95
    assert R.cost_of_living('New York', 'Average') > R.cost_of_living('Houston', 'Average')
    for loc in ('Seattle', 'Chicago', 'Texas', 'Ontario'):
        a = R.cost_of_living(loc, 'Average')
        assert 0.65 < R.cost_of_living(loc, 'Conservative') / a < 0.85
        assert 1.25 < R.cost_of_living(loc, 'High-end') / a < 1.50
    assert R.cost_of_living('District of Columbia', 'Average') is not None
    raw = R.ref_raw()['ADULT_EXPENSE_TEMPLATES']['Columbus']['Average (statistical)']
    assert sum(raw.values()) == 21220          # v0.8 extract untouched
    assert R.rent_factor('Seattle', 'Houston') < 0.75


def test_spending_slider_curve():
    from finplan import reference as R
    c = R.spending_curve('Seattle')
    xs = [a['x'] for a in c['anchors']]
    tots = [a['total'] for a in c['anchors']]
    assert xs == sorted(xs) and tots == sorted(tots) and c['basis'] == 'bea'
    keys = [a['key'] for a in c['anchors']]
    assert {'q2', 'all', 'q5', 'v08_avg', 'v08_high'} <= set(keys)
    # BLS average adult in Seattle is far below the old v0.8 "Average"
    avg = next(a for a in c['anchors'] if a['key'] == 'all')['total']
    old = next(a for a in c['anchors'] if a['key'] == 'v08_avg')['total']
    assert 14000 < avg < 22000 and old > 1.6 * avg
    # interpolation is monotone and hits anchors
    prev = 0
    for x in range(0, 101, 5):
        t = sum(R.spending_at_level('Seattle', x).values())
        assert t >= prev - 20
        prev = t
    assert abs(sum(R.spending_at_level('Seattle', 90).values()) - old) < 50


def test_career_phase_events_and_actuals_split():
    from finplan.actuals import planned_for_year
    p = {'parentX_age': 40, 'parentX_retirement_age': 60,
         'parentX_career_phases': [{'start_age': 30, 'end_age': 45, 'base_salary': 100000, 'label': 'Engineer'},
                                   {'start_age': 45, 'end_age': 60, 'base_salary': 150000, 'label': 'Manager'}],
         'health_insurances': [{'name': 'Emp', 'monthly_premium': 500, 'start_age': 0, 'end_age': 64}],
         'health_expenses': [{'name': 'OOP', 'annual_amount': 2000, 'affected_person': 'Both', 'start_age': 0, 'end_age': 120}],
         'state_timeline': [{'year': 2026, 'state': 'Seattle', 'spending_strategy': 'Average'},
                            {'year': 2030, 'state': 'Houston', 'spending_strategy': 'Average'}]}
    pr = project(p)
    jobs = [e for e in pr['events'] if e['type'] == 'job']
    assert len(jobs) == 1 and 'Manager' in jobs[0]['label']
    a = planned_for_year(p, 2031)['expenses']
    assert a['healthcare']['out_of_pocket'] > 0 and a['healthcare']['insurance_premiums'] > 0
    b = planned_for_year(p, 2027)['expenses']
    # Houston is cheaper than Seattle: planned categories follow the engine's cost-of-living and rent factors
    assert a['family']['Mortgage/Rent'] < b['family']['Mortgage/Rent']


def test_stress_worst_child_and_compound_year():
    from finplan.stress import run
    p = {'children_list': [{'name': 'A', 'birth_year': 2020}, {'name': 'B', 'birth_year': 2040}],
         'parentX_age': 35, 'parentY_age': 35, 'current_year': 2026}
    r = run(p, [{'id': 'c', 'type': 'compound', 'label': 'x', 'start_year': 2031,
                 'events': [{'type': 'disabled_child', 'child': '__worst__', 'person': 2},
                            {'type': 'market_crash', 'drop': -0.4, 'year': 2029}]}], n=60)
    res = r['results'][0]
    assert res['test']['events'][0]['child'] == 'A'
    assert any(e['type'] == 'market_crash' and e['year'] == 2031 for e in res['events'])


def _own_plan(**kw):
    p = {'parent1_name': 'A', 'parent2_name': 'B', 'parentX_age': 40, 'parentY_age': 38, 'parentX_income': 150000,
         'parentY_income': 90000, 'parentX_net_worth': 400000, 'parentX_pretax_balance': 150000,
         'parentY_net_worth': 200000, 'parentY_pretax_balance': 120000, 'marriage_year': 2015, 'current_year': 2026,
         'state_timeline': [{'year': 2026, 'state': 'Seattle', 'spending_strategy': 'Average'}],
         'houses': [{'name': 'Home', 'purchase_year': 2018, 'purchase_price': 800000, 'current_value': 1000000,
                     'mortgage_balance': 500000, 'mortgage_rate': 0.04, 'mortgage_years_left': 22,
                     'timeline': [{'year': 2018, 'status': 'Own_Live'}], 'separate_funds': {'p1': 100000}}],
         'windfalls': [{'name': 'Inheritance', 'year': 2030, 'amount': 300000, 'recipient': 'Parent 2', 'separate': True}],
         'ownership_tracking': {'enabled': True, 'today': {'p1': {'liquid': 200000, 'pretax': 0}, 'p2': {'liquid': 0, 'pretax': 50000}}}}
    p.update(kw)
    return p


def test_ownership_labels_never_change_totals():
    import copy
    p = _own_plan()
    off = copy.deepcopy(p); off['ownership_tracking'] = {'enabled': False}
    a, b = project(p), project(off)
    for x, y in zip(a['rows'], b['rows']):
        assert abs(x['net_worth'] - y['net_worth']) < 1e-6
        o = x['ownership']
        assert abs(o['separate1'] + o['separate2'] + o['marital'] - x['net_worth']) < 1e-3
    r0 = a['rows'][0]['ownership']
    # Washington: community property, income from separate property stays separate
    assert a['summary']['ownership']['regime_resolved'] == 'community'
    assert a['summary']['ownership']['separate_income_resolved'] == 'separate'
    # home bought after the wedding with $100k of person 1's separate money: 1/3 separate, 2/3 marital
    assert abs(r0['homes']['s1'] / (r0['homes']['s1'] + r0['homes']['m']) - 1 / 3) < 0.01
    # the inheritance lands in person 2's separate property
    y30 = next(r for r in a['rows'] if r['year'] == 2030)['ownership']
    y29 = next(r for r in a['rows'] if r['year'] == 2029)['ownership']
    assert y30['separate2'] - y29['separate2'] > 290000
    tot = y30['separate1'] + y30['separate2'] + y30['marital']
    assert abs(y30['division']['p1'] + y30['division']['p2'] - tot) < 1e-3
    assert abs(y30['division']['p1'] - (y30['separate1'] + y30['marital'] / 2)) < 1e-3


def test_ownership_commingling_and_rules():
    p = _own_plan(parentX_retirement_age=45, parentY_retirement_age=43, parentX_net_worth=300000,
                  parentY_net_worth=120000, windfalls=[])
    s = project(p)['summary']['ownership']
    assert s['commingled_total'] > 0 and s['first_commingled_year'] is not None
    # Texas: income from separate property is community property
    tx = project(_own_plan(state_timeline=[{'year': 2026, 'state': 'Houston', 'spending_strategy': 'Average'}]))
    assert tx['summary']['ownership']['separate_income_resolved'] == 'marital'
    # prenup keeping earnings separate: marital property doesn't grow from pay
    pre = _own_plan(ownership_tracking={'enabled': True, 'earnings': 'separate', 'regime': 'prenup'})
    base = project(_own_plan())
    assert project(pre)['rows'][10]['ownership']['marital'] < base['rows'][10]['ownership']['marital']
    # not married yet: everything is separate until the wedding
    fut = project(_own_plan(marriage_year=2029))['rows']
    assert fut[0]['ownership']['phase'] == 'before' and abs(fut[0]['ownership']['marital'] - fut[0]['other_assets']) < 1
    assert fut[3]['ownership']['phase'] == 'married'


def test_windfalls_add_cash_untaxed():
    import copy
    p = _own_plan(ownership_tracking={'enabled': False})
    q = copy.deepcopy(p); q['windfalls'] = []
    a, b = project(p)['rows'], project(q)['rows']
    t = 2030 - 2026
    assert a[t]['windfalls'] > 300000 and abs(a[t]['taxes'] - b[t]['taxes']) < 1
    assert a[t]['investable'] - b[t]['investable'] > 300000


def test_checkin_keeps_separate_balances():
    from datetime import date
    from finplan.checkin import rebase
    q = rebase(_own_plan(), {'p1': {'liquid': 300000, 'pretax': 160000},
                             'p2': {'liquid': 90000, 'pretax': 130000, 'separate_pretax': 60000}}, date(2027, 3, 1))
    t = q['ownership_tracking']['today']
    assert t['p1']['liquid'] > 200000          # carried forward from the projection
    assert t['p2']['pretax'] == 60000          # what the check-in said


def test_rmds_roth_and_spousal_ss():
    from finplan.engine import rmd_age, spousal_factor, ss_claim_factor
    assert rmd_age(1959) == 73 and rmd_age(1960) == 75 and rmd_age(1950) == 72
    assert abs(spousal_factor(62) - 0.65) < 1e-9 and spousal_factor(67) == 1 and spousal_factor(70) == 1
    # a 75-year-old (born 1951) with $1.5M pre-tax must take 1.5M/24.6 this year, taxed as income
    base = {'current_year': 2026, 'parentX_age': 75, 'parentY_age': 75, 'parentX_retirement_age': 65, 'parentY_retirement_age': 65,
            'parentX_net_worth': 1800000, 'parentX_pretax_balance': 1500000, 'parentY_net_worth': 0, 'parentX_ss_benefit': 2500,
            'parentY_ss_benefit': 800, 'parentX_ss_claim_age': 67, 'parentY_ss_claim_age': 67}
    r = project(base)['rows']
    assert abs(r[0]['rmd'] - 1500000 / 24.6) < 1
    off = project({**base, 'rmd_enabled': False})['rows']
    assert off[0]['rmd'] == 0 and r[0]['taxes'] > off[0]['taxes']
    # spousal: person 2's own $800 < 50% of $2,500, so they get $1,250/mo (both claimed at 67)
    assert abs(r[0]['ss2'] / r[0]['infl_index'] - 1250 * 12) < 1
    nosp = project({**base, 'spousal_ss': False})['rows']
    assert abs(nosp[0]['ss2'] - 800 * 12) < 1
    # Roth: part of net worth, grows, no RMD, used after pre-tax money, never taxed
    roth = project({**base, 'parentX_roth_balance': 200000})['rows']
    assert roth[0]['roth'] > 200000 and abs(roth[0]['rmd'] - r[0]['rmd']) < 1
    assert abs(roth[0]['liquid'] + roth[0]['pretax'] + roth[0]['roth'] - roth[0]['investable']) < 1e-6
    # Roth contributions while working come out of after-tax cash
    w = {'current_year': 2026, 'parentX_age': 40, 'parentY_age': 40, 'parentX_income': 150000, 'parentY_income': 0,
         'parentX_net_worth': 100000, 'roth_contribution': 7000}
    rw = project(w)['rows']
    assert abs(rw[0]['contrib_roth'] - 7000) < 1 and rw[0]['roth'] >= 7000


def test_what_would_it_take_solver():
    from finplan.solver import solve, apply
    # a plan short of 85%: each lever that works must actually reach the target, and the patch must match
    p = {'current_year': 2026, 'parentX_age': 45, 'parentY_age': 45, 'parentX_income': 120000, 'parentY_income': 60000,
         'parentX_retirement_age': 60, 'parentY_retirement_age': 60, 'parentX_net_worth': 900000, 'parentY_net_worth': 50000,
         'parentX_ss_benefit': 2200, 'parentY_ss_benefit': 1400}
    r = solve(p, 0.6, n=300)
    if not r['reached']:
        ok = [l for l in r['levers'] if l.get('feasible')]
        assert ok, r
        for l in ok:
            assert l['success_after'] >= 0.6
            q = apply(normalize_plan(p), l['id'], l['amount'])
            for k, v in l['patch'].items():
                assert q[k] == v
        rl = next(l for l in r['levers'] if l['id'] == 'retire_later')
        if rl.get('feasible'):
            assert rl['patch']['parentX_retirement_age'] == 60 + rl['amount']
    # a comfortable plan reports headroom instead
    rich = {**p, 'parentX_net_worth': 5000000}
    h = solve(rich, 0.85, n=300)
    assert h['reached'] and any(l['id'] == 'spend_more' and l['amount'] > 0 for l in h['levers'])


def test_cost_data_matches_published_sources():
    """Spot values re-checked against BEA/FRED 2024 RPPs, BLS CE Table 1101 (2022) and WDI 2024 (2026-09-27)."""
    from finplan import calibrate as K
    d = K.data()
    assert abs(d['rpp_states']['California'][0] - 110.7) < 0.1 and abs(d['rpp_states']['California'][2] - 154.3) < 0.1
    assert d['rpp_metros']['Honolulu'] == [110.961, 111.562, 135.538, 102.898]
    assert d['rpp_metros']['Seattle'] == [111.133, 103.972, 151.314, 106.835]
    assert d['rpp_metros']['San Francisco'][2] == 194.718
    q = d['cex_2022_quintiles']
    assert q['total'] == [72967, 32612, 47657, 61950, 81957, 140654]
    assert q['persons'] == [2.4, 1.6, 2.1, 2.4, 2.9, 3.2] and q['children'] == [0.6, 0.3, 0.4, 0.6, 0.7, 0.8]
    # the two BLS-suppressed cells come out exactly from the published entertainment subtotal
    assert K._q('other_entertainment', 'q2') == 258 and K._q('other_entertainment', 'q3') == 712
    # transportation and entertainment parts add up to their published subtotals
    for i in range(6):
        parts = sum(q[r][i] for r in ('vehicle_purchases', 'gasoline', 'vehicle_insurance', 'vehicle_finance', 'maintenance',
                                      'vehicle_fees', 'public_transport'))
        assert abs(parts - q['transportation'][i]) <= 2
    assert d['cex_2024_all']['total'] == 78535
    assert d['country_price_level']['Japan'] == 0.624 and d['country_price_level']['United States'] == 1.0


def test_spending_curves_are_sane_everywhere():
    """Every location: slider totals rise, lifestyles are ordered, and no jump to Seattle's old templates."""
    from finplan import reference as R, calibrate as K
    locs = set(R.all_locations()) | set(K.data()['country_price_level'])
    for loc in locs:
        a = R.spending_curve(loc)['anchors']
        tots = [x['total'] for x in a]
        assert tots == sorted(tots), loc
        by = {x['key']: x['total'] for x in a}
        if 'v08_avg' in by:
            assert by['v08_avg'] < 2.2 * by['q5'], (loc, by)   # the old-app anchor stays near the top-20% level
        lv = [sum(R.adult_template_calibrated(loc, s).values()) for s in ('Conservative', 'Average', 'High-end')]
        assert lv[0] < lv[1] < lv[2], loc
    # cheaper places are cheaper
    tot = lambda l: sum(R.adult_template_calibrated(l, 'Average').values())
    assert tot('Mississippi') < tot('Texas') < tot('Seattle') < tot('San Francisco')
    assert tot('India') < tot('Mexico') < tot('Portugal') < tot('Seattle')
    assert K.rent_factor('Seattle', 'San Francisco') > 1.2 and K.rent_factor('Seattle', 'Mississippi') < 0.5


def test_scenario_matrix_economies_and_variants():
    from finplan import reference as R, matrix as M
    plan = R.default_plan()
    r = M.evaluate(plan, list(M.ECONOMIES), n=200)
    c = r['cells']
    assert c['weak']['success'] <= c['plan']['success'] <= c['strong']['success']
    assert c['weak']['final_median'] < c['plan']['final_median'] < c['strong']['final_median']
    assert c['crash']['final_median'] < c['plan']['final_median']
    assert c['seventies']['final_median'] < c['plan']['final_median']
    assert r['passed'] == sum(x['ok'] for x in c.values()) and r['total'] == len(M.ECONOMIES)
    # the plan itself is untouched by the economy overlays
    assert '_stress' not in plan
    # variants: add two kids with given years, a move, a retirement age; removing kids drops the youngest
    cy = plan['current_year']
    n0 = len(plan['children_list'])
    v = M.build_variant(plan, {'kids': n0 + 2, 'kid_years': [cy + 1, cy + 4], 'move': {'location': 'Portugal', 'year': cy + 5},
                               'retire_x': plan['parentX_retirement_age'] + 2})
    assert [k['birth_year'] for k in v['children_list'][-2:]] == [cy + 1, cy + 4]
    assert len({k['name'] for k in v['children_list']}) == n0 + 2
    assert v['state_timeline'][-1] == {'year': cy + 5, 'state': 'Portugal', 'spending_strategy': v['state_timeline'][-2]['spending_strategy']}
    assert v['parentX_retirement_age'] == plan['parentX_retirement_age'] + 2
    fewer = M.build_variant(v, {'kids': n0})
    assert [k['name'] for k in fewer['children_list']] == [k['name'] for k in plan['children_list']]
    more_kids = M.evaluate(v, ['plan'], n=200)['cells']['plan']['final_median']
    assert more_kids != c['plan']['final_median']


def _rich(**kw):
    from finplan import reference as R
    p = R.default_plan()
    p.update({'parentX_career_phases': [], 'parentY_career_phases': [], 'parent1_name': 'A', 'parent2_name': 'B', 'parentX_age': 55, 'parentY_age': 53, 'parentX_retirement_age': 60,
              'parentY_retirement_age': 60, 'parentX_income': 150000, 'parentY_income': 90000, 'parentX_net_worth': 900000,
              'parentY_net_worth': 600000, 'parentX_pretax_balance': 500000, 'parentY_pretax_balance': 300000,
              'state_timeline': [{'year': p['current_year'], 'state': 'Texas', 'spending_strategy': 'Average'}]})
    p.update(kw)
    return p


def test_capital_gains_tax_on_selling_taxable_savings():
    from finplan.engine import project
    import copy
    p = _rich()
    on = project(p)
    q = copy.deepcopy(p); q['capital_gains_enabled'] = False
    off = project(q)
    assert on['summary']['lifetime_cap_gains_tax'] > 0 and off['summary']['lifetime_cap_gains_tax'] == 0
    assert on['rows'][-1]['net_worth'] < off['rows'][-1]['net_worth']
    # full basis = no gain to tax
    z = copy.deepcopy(p); z['taxable_basis_pct'] = 100; z['parentX_income'] = 0; z['parentY_income'] = 0
    r = project(z)
    assert r['rows'][0]['cap_gains_realized'] == 0
    # 0% bracket: small gains on top of low income are untaxed federally (Texas has no income tax)
    import numpy as np
    from finplan.taxes import capital_gains_tax
    assert capital_gains_tax(np.array([20000.]), np.array([30000.]), np.array([50000.]), 'married', 1.0, 'Texas')[0] == 0


def test_roth_conversions_fill_bracket_and_compare():
    from finplan.engine import project
    from finplan.taxes import MFJ, STD_DED
    from finplan import taxplan
    p = _rich(roth_conversion={'mode': 'fill_bracket', 'bracket': 0.12})
    r = project(p)
    conv = [x for x in r['rows'] if x['roth_conversion'] > 0]
    assert conv, 'expected conversions in retirement before RMD age'
    first = conv[0]
    assert first['age1'] >= 60
    # taxable income is filled to about the top of the 12% bracket (indexed)
    idx = (1 + r['plan']['economic_params']['inflation_rate']) ** (first['year'] - 2024)
    assert abs(first['taxable_ordinary'] - MFJ[1][0] * idx) < 0.02 * MFJ[1][0] * idx
    assert max(x['roth'] for x in r['rows']) > 0
    f = project(_rich(roth_conversion={'mode': 'fixed', 'amount': 30000}))
    fx = [x for x in f['rows'] if x['roth_conversion'] > 0]
    assert fx and abs(fx[0]['roth_conversion'] / fx[0]['infl_index'] - 30000) < 1
    cmp = taxplan.compare(_rich(), n=100)
    ids = [s['id'] for s in cmp['strategies']]
    assert {'off', 'fill_12', 'fill_22'} <= set(ids) and cmp['best'] in ids
    assert next(s for s in cmp['strategies'] if s['id'] == 'off')['lifetime_conversions'] == 0


def test_irmaa_and_aca_credit():
    from finplan.engine import project
    import copy
    # high income in Medicare years -> IRMAA surcharge
    p = _rich(parentX_age=66, parentY_age=66, parentX_retirement_age=75, parentY_retirement_age=75,
              parentX_income=300000, parentY_income=200000, parentX_career_phases=[], parentY_career_phases=[])
    r = project(p)
    assert r['rows'][3]['irmaa'] > 0 and r['summary']['irmaa_years']
    q = copy.deepcopy(p); q['irmaa_enabled'] = False
    assert project(q)['rows'][3]['irmaa'] == 0
    # early retirees on a marketplace plan with modest income get a premium tax credit
    a = _rich(parentX_age=58, parentY_age=58, parentX_retirement_age=58, parentY_retirement_age=58,
              parentX_income=0, parentY_income=0,
              health_insurances=[{'name': 'Marketplace silver', 'monthly_premium': 2000, 'covered_by': 'Both',
                                  'start_age': 58, 'end_age': 64, 'marketplace': True}])
    ra = project(a)
    assert ra['rows'][1]['aca_credit'] > 0 and ra['rows'][1]['aca_credit'] <= ra['rows'][1]['aca_benchmark'] + 1
    b = copy.deepcopy(a); b['aca_enabled'] = False
    assert project(b)['rows'][1]['aca_credit'] == 0


def test_pensions_debts_and_529():
    from finplan.engine import project
    from finplan import reference as R
    p = _rich(pensions=[{'name': 'State pension', 'person': 'Parent 1', 'start_age': 62, 'monthly': 3000,
                         'cola_pct': 2, 'survivor_pct': 50}],
              debts=[{'name': 'Car loan', 'kind': 'auto', 'balance': 20000, 'rate': 6, 'monthly_payment': 600}],
              parentX_death_age=80)
    r = project(p)
    rows = r['rows']
    by = {x['age1']: x for x in rows}
    assert by[61]['pension_income'] == 0 and by[62]['pension_income'] > 3000 * 12
    assert by[64]['pension_income'] > by[63]['pension_income']          # COLA
    after = [x for x in rows if x['age1'] > 80 and x['alive2']]
    if after:
        assert abs(after[0]['pension2'] - by[80]['pension1'] * 0.5 * 1.02) < 50   # survivor share
    assert rows[0]['debt_payment'] > 0 and r['summary']['debt_free_year'] is not None
    paid = next(x for x in rows if x['debt_balance'] == 0)
    assert paid['year'] <= rows[0]['year'] + 4
    assert any(e['type'] == 'debt_paid' for e in r['events'])
    # 529 pays college
    q = R.default_plan()
    cy = q['current_year']
    q['children_list'] = [{'name': 'Kid', 'birth_year': cy - 10}]
    q['college_529'] = [{'child': 'Kid', 'balance': 30000, 'monthly': 400}]
    rq = project(q)
    col = [x for x in rq['rows'] if 18 <= x['year'] - (cy - 10) <= 21]
    assert sum(x['paid_529'] for x in col) > 0
    assert rq['rows'][0]['edu_529'] > 30000
    assert all(x['edu_529'] == 0 for x in rq['rows'] if x['year'] - (cy - 10) >= 22)


def test_goals_evaluate_and_probabilities():
    from finplan.engine import project, monte_carlo
    p = _rich()
    cy = p['current_year']
    p['debts'] = [{'name': 'Loan', 'balance': 10000, 'rate': 5, 'monthly_payment': 500}]
    p['goals'] = [{'type': 'net_worth', 'amount': 100000, 'year': cy + 5}, {'type': 'net_worth', 'amount': 1e9, 'year': cy + 5},
                  {'type': 'emergency_fund', 'months': 6}, {'type': 'debt_free', 'year': cy + 5}, {'type': 'fi', 'year': cy + 4}]
    r = project(p)
    g = {x['id']: x for x in r['goals']}
    assert g['goal1']['status'] == 'on_track' and g['goal2']['status'] == 'off_track'
    assert g['goal3']['status'] == 'on_track' and g['goal4']['status'] == 'on_track'
    assert g['goal5']['target'] > 0
    m = monte_carlo(p, 200)
    assert m['goal_probs']['goal1'] > 0.9 and m['goal_probs']['goal2'] == 0


def test_safe_spending_guardrails_and_backtest():
    from finplan import solver, backtest
    from finplan.engine import monte_carlo
    import copy
    p = _rich()
    s = solver.safe_spending(p, 0.85, n=200)
    assert s['current'] > 0
    if s['multiplier'] not in (None, 3.0):
        assert abs(s['success_at_safe'] - 0.85) < 0.06
    g = copy.deepcopy(p); g['guardrails'] = {'enabled': True, 'lower': 15, 'cut': 15, 'upper': 25, 'raise': 5}
    mg = monte_carlo(g, 300, seed=5)
    m0 = monte_carlo(p, 300, seed=5)
    assert 'guardrails' in mg and mg['guardrails']['prob_any_cut'] > 0
    assert mg['success_rate'] >= m0['success_rate'] - 0.02
    b = backtest.run(p)
    assert b['n'] == 100 and b['first_year'] == 1924 and len(b['starts']) == 100
    assert 0 <= b['success_rate'] <= 1 and len(b['median_path']) == b['plan_years']
