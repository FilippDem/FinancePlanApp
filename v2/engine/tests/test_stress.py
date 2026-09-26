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
    assert len(r['results']) == 6
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


def test_v08_default_set_and_stoplight():
    from finplan.reference import demo_plans
    p = demo_plans()[next(k for k in demo_plans() if '3-Kid' in k)]
    tests = stress.default_tests(p)
    ids = {t['id'] for t in tests}
    assert {'crash', 'hyperinflation', 'unemployed_1', 'unemployed_2', 'disabled_0', 'disabled_1', 'disabled_2'} <= ids
    crash = next(t for t in tests if t['id'] == 'crash')
    assert crash['drop'] == -0.5 and crash['when'] == 'worst'
    r = stress.run(p, [crash, next(t for t in tests if t['id'] == 'disabled_0')], n=150)
    c = r['results'][0]
    assert c['worst_year'] is not None and len(c['search']) > 5
    assert c['success_rate'] == min(s['success_rate'] for s in c['search']) or c['success_rate'] <= r['base']['success_rate']
    assert set(c['stoplight']) == {'10', '25', '50', '75', '90'}
    # stoplight is monotone: surviving the 10th percentile implies surviving the 90th
    vals = [c['stoplight'][k] for k in ('10', '25', '50', '75', '90')]
    assert vals == sorted(vals)
    assert r['summary']['total'] == 10


def test_compound_combines_events():
    p = plan()
    comp = {'type': 'compound', 'label': 'Crash + job loss', 'events': [
        {'type': 'market_crash', 'year': 2030, 'drop': -0.3},
        {'type': 'income_loss', 'person': 1, 'start_year': 2030, 'years': 2, 'pct': 100}]}
    ev = stress.expand(comp, stress.normalize_plan(p))
    assert {e['type'] for e in ev} == {'market_crash', 'income_loss'}
    r = stress.run(p, [comp], n=100)
    single = stress.run(p, [comp['events'][0]], n=100)
    assert r['results'][0]['net_worth_end'] < single['results'][0]['net_worth_end']


def test_disabled_child_stops_parent_income():
    p = plan()
    p['children_list'] = [{'name': 'Ava', 'birth_year': 2028}]
    ev = stress.expand({'type': 'disabled_child', 'child': 'Ava', 'person': 2, 'extra_cost': 10000}, stress.normalize_plan(p))
    p['_stress'] = ev
    rows = {r['year']: r for r in project(p)['rows']}
    assert rows[2027]['wages2'] > 0 and rows[2028]['wages2'] == 0 and rows[2040]['wages2'] == 0
