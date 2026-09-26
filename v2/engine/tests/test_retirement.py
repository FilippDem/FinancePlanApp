import copy
import pytest
from finplan import retirement as R
from finplan.reference import default_plan


def plan():
    p = copy.deepcopy(default_plan())
    p.update({'current_year': 2026, 'houses': [], 'children_list': [], 'recurring_expenses': [], 'major_purchases': []})
    return p


def test_ss_options_factors_and_break_even():
    o = R.ss_options(plan())
    assert len(o) == 2
    opts = {x['age']: x for x in o[0]['options']}
    assert opts[62]['factor'] == pytest.approx(0.70) and opts[70]['factor'] == pytest.approx(1.24)
    assert 78 <= o[0]['break_even_70_vs_62'] <= 84


def test_retiring_later_improves_odds():
    rows = R.retire_whatif(plan(), deltas=(-2, 0, 2), n=200)
    assert rows[0]['success_rate'] <= rows[1]['success_rate'] <= rows[2]['success_rate']


def test_replacement_ratio():
    r = R.replacement(plan())
    assert r['pre_income'] > 0 and r['retirement_income'] > 0 and 0 < r['ratio'] < 3
