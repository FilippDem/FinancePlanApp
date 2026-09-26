"""Retirement analysis: Social Security claiming options, retire-age what-ifs, income replacement."""
from __future__ import annotations

import copy

from .engine import project, monte_carlo, ss_claim_factor
from .plan import normalize_plan, is_single


def ss_options(plan: dict) -> list[dict]:
    """Per person: benefit if claimed at 62 / 67 / 70 / planned (today's $)."""
    p = normalize_plan(plan)
    out = []
    people = [('X', p['parent1_name'])] + ([] if is_single(p) else [('Y', p['parent2_name'])])
    for who, name in people:
        pia = p[f'parent{who}_ss_benefit'] * 12
        death = p[f'parent{who}_death_age']
        planned = p.get(f'parent{who}_ss_claim_age') or min(max(p[f'parent{who}_retirement_age'], 62), 70)
        cut_year = p.get('ss_insolvency_year', 2034) if p['ss_insolvency_enabled'] else 9999
        cut = 1 - p['ss_shortfall_percentage'] / 100
        birth_year = p['current_year'] - p[f'parent{who}_age']

        def lifetime(claim):
            tot = 0.0
            for age in range(int(claim), death + 1):
                y = birth_year + age
                tot += pia * ss_claim_factor(claim) * (cut if y >= cut_year else 1.0)
            return tot
        opts = []
        for age in sorted({62, 67, 70, int(planned)}):
            opts.append({'age': age, 'annual': pia * ss_claim_factor(age), 'factor': ss_claim_factor(age),
                         'lifetime': lifetime(age), 'planned': age == int(planned)})
        # break-even: first age where cumulative(70) >= cumulative(62)
        be = None
        c62 = c70 = 0.0
        for age in range(62, 101):
            c62 += pia * ss_claim_factor(62)
            if age >= 70:
                c70 += pia * ss_claim_factor(70)
            if age >= 70 and c70 >= c62:
                be = age
                break
        out.append({'who': who, 'name': name, 'pia_monthly': p[f'parent{who}_ss_benefit'], 'plan_until': death,
                    'options': opts, 'break_even_70_vs_62': be})
    return out


def retire_whatif(plan: dict, deltas=(-3, -2, -1, 0, 1, 2, 3), n: int = 400) -> list[dict]:
    base = normalize_plan(plan)
    rows = []
    for d in deltas:
        p = copy.deepcopy(base)
        p['parentX_retirement_age'] = max(p['parentX_age'], p['parentX_retirement_age'] + d)
        if not is_single(p):
            p['parentY_retirement_age'] = max(p['parentY_age'], p['parentY_retirement_age'] + d)
        pr = project(p)
        mc = monte_carlo(p, n, seed=5, normalized=False)
        s = pr['summary']
        ret = next((r for r in pr['rows'] if r['year'] == s['retirement_year']), pr['rows'][-1])
        rows.append({'delta': d, 'age1': p['parentX_retirement_age'], 'age2': p['parentY_retirement_age'],
                     'year': s['retirement_year'], 'success_rate': mc['success_rate'], 'depletion_year': s['depletion_year'],
                     'investable_at_retirement': ret['investable'] / ret['infl_index']})
    return rows


def replacement(plan: dict, withdrawal_rate: float = 0.04) -> dict:
    """Compare the last working year's income with sustainable retirement income (today's $)."""
    p = normalize_plan(plan)
    pr = project(p)
    rows = pr['rows']
    working = [r for r in rows if r['wages1'] + r['wages2'] > 0]
    if not working:
        return {'pre_income': 0, 'retirement_income': 0, 'ratio': None}
    last = working[-1]
    # household pay before the first person retires: best of the last 5 working years
    # (the final year alone may have only one earner left)
    pre = max((r['wages1'] + r['wages2']) / r['infl_index'] for r in working[-5:])
    after = [r for r in rows if r['year'] > last['year']]
    first = next((r for r in after if r['wages1'] + r['wages2'] == 0), after[0] if after else last)
    ss = first['ss_income'] / first['infl_index']
    draw = max(first['investable'], 0) / first['infl_index'] * withdrawal_rate
    rent = first['rent_income'] / first['infl_index']
    total = ss + draw + rent
    return {'pre_income': pre, 'last_working_year': last['year'], 'first_retired_year': first['year'],
            'ss': ss, 'portfolio_draw': draw, 'rent': rent, 'retirement_income': total,
            'ratio': total / pre if pre else None, 'target_80': 0.8 * pre, 'gap_80': max(0.0, 0.8 * pre - total),
            'spending_first_year': first['total_expenses'] / first['infl_index']}
