import copy
from finplan.actuals import planned_for_year, group_totals
from finplan.reference import default_plan


def test_planned_for_year_shape_and_totals():
    p = copy.deepcopy(default_plan()); p.update({'current_year': 2026, 'houses': []})
    pl = planned_for_year(p, 2027)
    assert pl['in_projection'] and pl['income']['parent1_employment'] > 0
    g = group_totals(pl['expenses'])
    assert g['parentX'] > 0 and g['family'] > 0
    past = planned_for_year(p, 2025)
    assert not past['in_projection'] and past['expenses']['parentX']


def test_group_totals_nested():
    assert group_totals({'children': {'A': {'Total': 5}}, 'family': {'Rent': 10}}) == {'children': 5.0, 'family': 10.0}
