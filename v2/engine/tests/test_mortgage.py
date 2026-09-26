import copy

import pytest

from finplan.engine import project
from finplan.mortgage import monthly_payment, loan_terms, year_flows, payoff_year
from finplan.plan import normalize_plan
from finplan.reference import default_plan


def base(**kw):
    p = copy.deepcopy(default_plan())
    p.update({'current_year': 2026, 'houses': [], 'children_list': [], 'recurring_expenses': [], 'major_purchases': [],
              'ss_insolvency_enabled': False, 'pretax_401k': 0.0})
    p['economic_params'] = {**p['economic_params'], 'inflation_rate': 0.0}
    p.update(kw)
    return p


def redfin_house(**kw):
    # The listing in the user's screenshot: $1,399,000, 20% down, 30-yr fixed 7.5%
    h = {'name': 'Listing', 'mortgage_mode': 'estimate', 'purchase_year': 2027, 'purchase_price': 1399000,
         'current_value': 1399000, 'down_payment_pct': 20, 'loan_term_years': 30, 'mortgage_rate': 0.075,
         'property_tax_rate': 1102 * 12 / 1399000, 'home_insurance': 181 * 12, 'maintenance_rate': 0,
         'upkeep_costs': 0, 'appreciation_rate': 0,
         'timeline': [{'year': 2027, 'status': 'Own_Live', 'rental_income': 0}]}
    h.update(kw)
    return h


def test_matches_redfin_calculator():
    assert monthly_payment(1399000 * 0.8, 0.075, 30) == pytest.approx(7825, abs=1)
    rows = {r['year']: r for r in project(base(houses=[redfin_house()]))['rows']}
    h = rows[2028]['details']['houses'][0]
    monthly = (h['mortgage_pi'] + h['property_tax'] + h['insurance']) / 12
    assert monthly == pytest.approx(9108, abs=2)          # "$9,108 per month"
    assert rows[2027]['down_payment'] == pytest.approx(279800)  # "20% ($280k)"


def test_estimate_mode_syncs_legacy_fields_for_v08():
    p = normalize_plan(base(houses=[redfin_house()]))
    h = p['houses'][0]
    assert h['mortgage_balance'] == pytest.approx(1119200)
    assert h['mortgage_years_left'] == 30


def test_estimate_mode_past_purchase_derives_todays_balance():
    h = redfin_house(purchase_year=2016, timeline=[{'year': 2016, 'status': 'Own_Live', 'rental_income': 0}])
    p = normalize_plan(base(houses=[h]))
    t = loan_terms(p['houses'][0], 2026)
    assert p['houses'][0]['mortgage_balance'] == pytest.approx(year_flows(t, 2026)['bal_start'])
    assert p['houses'][0]['mortgage_balance'] < 1119200 * 0.9
    assert p['houses'][0]['mortgage_years_left'] == 20
    r = project(base(houses=[h]))['rows'][0]
    assert r['down_payment'] == 0          # already bought


def test_actual_mode_extra_payment_pays_off_sooner():
    h = {'name': 'Mine', 'mortgage_mode': 'actual', 'purchase_year': 2020, 'purchase_price': 600000, 'current_value': 650000,
         'mortgage_balance': 400000, 'mortgage_rate': 0.06, 'mortgage_years_left': 25, 'appreciation_rate': 0,
         'timeline': [{'year': 2020, 'status': 'Own_Live', 'rental_income': 0}]}
    t_req = loan_terms(normalize_plan({'houses': [h]})['houses'][0], 2026)
    t_extra = loan_terms(normalize_plan({'houses': [{**h, 'mortgage_payment_override': t_req['pmt'] + 1000}]})['houses'][0], 2026)
    assert payoff_year(t_req) == 2026 + 24
    assert payoff_year(t_extra) < 2026 + 17
    rows = {r['year']: r for r in project(base(houses=[{**h, 'mortgage_payment_override': t_req['pmt'] + 1000}]))['rows']}
    assert rows[2026]['exp_mortgage_pi'] == pytest.approx((t_req['pmt'] + 1000) * 12)
    assert rows[payoff_year(t_extra) + 1]['exp_mortgage_pi'] == 0


def test_pmi_below_20pct_down_and_drops_at_78pct():
    h = redfin_house(down_payment_pct=10, pmi_rate=0.5)
    rows = {r['year']: r for r in project(base(houses=[h]))['rows']}
    loan = 1399000 * 0.9
    assert rows[2027]['details']['houses'][0]['pmi'] == pytest.approx(loan * 0.005)
    later = [y for y in range(2027, 2057) if rows[y]['details']['houses'][0]['pmi'] == 0]
    assert later, 'PMI must stop'
    first_off = later[0]
    assert rows[first_off]['details']['houses'][0]['balance'] <= 0.78 * 1399000 + 1


def test_hoa_and_closing_costs():
    h = redfin_house(hoa_monthly=400, closing_cost_pct=3)
    rows = {r['year']: r for r in project(base(houses=[h]))['rows']}
    assert rows[2027]['down_payment'] == pytest.approx(279800 + 0.03 * 1399000)
    assert rows[2027]['details']['houses'][0]['hoa'] == pytest.approx(4800)


def test_old_files_default_to_actual_mode():
    p = normalize_plan({'houses': [{'name': 'Old', 'purchase_year': 2018, 'purchase_price': 500000, 'current_value': 600000,
                                    'mortgage_balance': 300000, 'mortgage_rate': 0.04, 'mortgage_years_left': 22}]})
    h = p['houses'][0]
    assert h['mortgage_mode'] == 'actual' and h['mortgage_balance'] == 300000 and h['down_payment_pct'] == pytest.approx(40)
