import copy
from datetime import date

import pytest

from finplan.checkin import evaluate, rebase, percentile_rank, status_for
from finplan.engine import project
from finplan.reference import default_plan


def plan(**kw):
    p = copy.deepcopy(default_plan())
    p.update({'current_year': 2026, 'houses': [], 'children_list': [], 'recurring_expenses': [], 'major_purchases': []})
    p.update(kw)
    return p


def test_percentile_rank_and_status():
    pts = {5: 10, 10: 20, 25: 40, 50: 50, 75: 60, 90: 80, 95: 90}
    assert percentile_rank(50, pts) == 50
    assert percentile_rank(55, pts) == pytest.approx(62.5)
    assert percentile_rank(0, pts) < 5 and percentile_rank(1000, pts) > 95
    assert status_for(80) == 'ahead' and status_for(50) == 'on_track' and status_for(15) == 'behind' and status_for(3) == 'off_track'


def test_evaluate_on_plan_is_on_track():
    p = plan()
    rows = {r['year']: r for r in project(p)['rows']}
    # at mid-2027 the plan expects roughly halfway between end-2026 and end-2027
    exp = (rows[2026]['investable'] + rows[2027]['investable']) / 2
    ev = evaluate(p, date(2027, 7, 2), exp)
    assert ev['expected']['investable'] == pytest.approx(exp, rel=0.01)
    assert ev['status'] == 'on_track'
    assert 25 <= ev['percentile'] <= 75
    low = evaluate(p, date(2027, 7, 2), exp * 0.5)
    assert low['status'] in ('behind', 'off_track') and low['gap'] < 0


def test_rebase_rolls_year_ages_and_balances():
    h = {'name': 'Home', 'mortgage_mode': 'estimate', 'purchase_year': 2020, 'purchase_price': 500000, 'current_value': 550000,
         'down_payment_pct': 20, 'loan_term_years': 30, 'mortgage_rate': 0.05,
         'timeline': [{'year': 2020, 'status': 'Own_Live', 'rental_income': 0}]}
    p = plan(houses=[h], parentX_age=40, parentY_age=38)
    out = rebase(p, {'p1': {'liquid': 100000, 'pretax': 50000}, 'p2': {'liquid': 50000, 'pretax': 20000},
                     'homes': [{'name': 'Home', 'value': 600000, 'mortgage': 330000}], 'other_debts': 15000},
                 date(2028, 1, 15))
    assert out['current_year'] == 2028 and out['parentX_age'] == 42 and out['parentY_age'] == 40
    assert out['parentX_net_worth'] == pytest.approx(150000 - 10000)
    assert out['parentY_net_worth'] == pytest.approx(70000 - 5000)
    assert out['parentX_pretax_balance'] == 50000
    hh = out['houses'][0]
    assert hh['mortgage_mode'] == 'actual' and hh['mortgage_balance'] == 330000 and hh['current_value'] == 600000
    assert hh['mortgage_years_left'] == 22        # 30-year loan from 2020, as of 2028
    assert project(out)['rows'][0]['year'] == 2028
