"""Planned values for a calendar year, in the same shape as v0.8 actuals[year].

actuals[year] = {net_worth, taxes_paid, notes, entered_at, entered_by,
                 income: {parent1_employment, parent2_employment, ss_income, investment_income, other_income},
                 expenses: {parentX:{cat:amt}, parentY:{...}, family:{...}, children:{name:{'Total':amt}},
                            housing:{house:{mortgage, property_tax, home_insurance, maintenance, upkeep}},
                            healthcare:{insurance_premiums, medicare, ltc_premiums, out_of_pocket},
                            recurring:{name:amt}, major_purchases:{name:amt}}}
"""
from __future__ import annotations

from .engine import project
from .plan import normalize_plan


def planned_for_year(plan: dict, year: int) -> dict:
    p = normalize_plan(plan)
    cy = p['current_year']
    infl = p['economic_params']['inflation_rate']
    ii = (1 + infl) ** (year - cy)
    pr = project(p)
    row = next((r for r in pr['rows'] if r['year'] == year), None)
    exp = {
        'parentX': {k: v * ii for k, v in p['parentX_expenses'].items()},
        'parentY': {k: v * ii for k, v in p['parentY_expenses'].items()},
        'family': {k: v * ii for k, v in p['family_shared_expenses'].items()},
        'children': {}, 'housing': {}, 'healthcare': {}, 'recurring': {}, 'major_purchases': {},
    }
    out = {'year': year, 'in_projection': row is not None, 'expenses': exp, 'income': {}, 'net_worth': None, 'taxes_paid': None,
           'totals': {}}
    if row:
        d = row['details']
        for c in d.get('children', []):
            exp['children'][c['name']] = {'Total': c['total']}
        for h in d.get('houses', []):
            if 'total' in h:
                exp['housing'][h['name']] = {'mortgage': h.get('mortgage_pi', 0) + h.get('pmi', 0), 'property_tax': h.get('property_tax', 0),
                                             'home_insurance': h.get('insurance', 0) + h.get('hoa', 0),
                                             'maintenance': h.get('maintenance', 0), 'upkeep': h.get('upkeep', 0)}
        exp['healthcare'] = {'insurance_premiums': row['exp_healthcare'], 'medicare': 0.0, 'ltc_premiums': 0.0, 'out_of_pocket': 0.0}
        for x in d.get('recurring', []):
            exp['recurring'][x['name']] = exp['recurring'].get(x['name'], 0) + x['amount']
        for x in d.get('purchases', []):
            exp['major_purchases'][x['name']] = exp['major_purchases'].get(x['name'], 0) + x['amount']
        statuses = [h.get('status') for h in d.get('houses', [])]
        if 'Own_Live' in statuses:
            exp['family']['Mortgage/Rent'] = 0.0
        if any(s_ in ('Own_Live', 'Own_Rent') for s_ in statuses):
            for k in ('Property Tax', 'Home Insurance'):
                if k in exp['family']:
                    exp['family'][k] = 0.0
        out['income'] = {'parent1_employment': row['wages1'], 'parent2_employment': row['wages2'], 'ss_income': row['ss_income'],
                         'investment_income': 0.0, 'other_income': row['rent_income']}
        out['net_worth'] = row['net_worth']
        out['taxes_paid'] = row['taxes']
        out['totals'] = {'income': row['total_income'], 'spending': row['total_expenses'], 'taxes': row['taxes'],
                         'investable': row['investable'], 'net_worth': row['net_worth']}
    return out


def group_totals(expenses: dict) -> dict:
    """Sum an actuals/planned expenses dict per group."""
    out = {}
    for g, v in (expenses or {}).items():
        if not isinstance(v, dict):
            continue
        tot = 0.0
        for x in v.values():
            tot += sum(float(y or 0) for y in x.values()) if isinstance(x, dict) else float(x or 0)
        out[g] = tot
    return out
