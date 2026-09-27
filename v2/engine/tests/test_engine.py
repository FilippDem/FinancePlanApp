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
