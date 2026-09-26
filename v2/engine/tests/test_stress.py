import copy
from finplan import stress
from finplan.engine import project
from finplan.reference import default_plan


def plan():
    p = copy.deepcopy(default_plan())
    p.update({'current_year': 2026, 'houses': [], 'children_list': [], 'recurring_expenses': [], 'major_purchases': []})
    return p


def test_each_stress_hurts_or_equals_base():
    r = stress.run(plan(), n=200)
    assert len(r['results']) == 5
    for x in r['results']:
        assert x['net_worth_end'] <= r['base']['net_worth_end'] + 1, x['id']


def test_income_loss_zeroes_wages_that_year():
    p = plan(); p['_stress'] = [{'type': 'income_loss', 'person': 1, 'start_year': 2027, 'years': 1, 'pct': 100}]
    rows = {r['year']: r for r in project(p)['rows']}
    assert rows[2027]['wages1'] == 0 and rows[2028]['wages1'] > 0


def test_inflation_spike_raises_index():
    base = {r['year']: r for r in project(plan())['rows']}
    p = plan(); p['_stress'] = [{'type': 'inflation_spike', 'start_year': 2027, 'years': 3, 'rate': 0.10}]
    rows = {r['year']: r for r in project(p)['rows']}
    assert rows[2030]['infl_index'] > base[2030]['infl_index'] * 1.15


def test_early_death_stops_income_and_spending():
    p = plan(); p['_stress'] = [{'type': 'early_death', 'person': 2, 'year': 2030}]
    rows = {r['year']: r for r in project(p)['rows']}
    assert rows[2030]['wages2'] == 0 and rows[2030]['exp_person2'] == 0 and rows[2029]['wages2'] > 0


def test_market_crash_applies_return():
    p = plan(); p['_stress'] = [{'type': 'market_crash', 'year': 2028, 'drop': -0.5}]
    base = {r['year']: r for r in project(plan())['rows']}
    rows = {r['year']: r for r in project(p)['rows']}
    assert rows[2028]['investable'] < base[2028]['investable'] * 0.7
