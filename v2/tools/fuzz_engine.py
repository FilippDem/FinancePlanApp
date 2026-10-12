"""Random and extreme plans through the engine: no crashes, no NaN/inf, sane invariants. Usage: python tools/fuzz_engine.py v2 [N]"""
import random, sys, traceback, math
V2 = sys.argv[1]; sys.path[:0] = [V2, V2 + '/engine']
import numpy as np
from finplan.plan import normalize_plan
from finplan.engine import project, monte_carlo
from finplan.matrix import evaluate
from finplan.health import plan_health
from finplan.solver import solve

LOCS = ['Seattle', 'San Francisco', 'New York', 'Texas', 'Austin', 'Portland', 'Oregon', 'California', 'Massachusetts',
        'Florida', 'Mississippi', 'Utah', 'Iowa', 'Portugal', 'India', 'Unknownville', 'District of Columbia', 'Hawaii']
rng = random.Random(7)


def rand_plan(i):
    single = rng.random() < 0.3
    a1 = rng.choice([18, 25, 35, 45, 55, 64, 67, 75, 90, 99])
    p = {'parent1_name': 'A', 'parent2_name': 'N/A' if single else 'B',
         'parentX_age': a1, 'parentY_age': max(18, a1 + rng.randint(-15, 15)),
         'parentX_retirement_age': rng.choice([30, 50, 60, 65, 70, 100]), 'parentY_retirement_age': rng.choice([40, 62, 67]),
         'parentX_death_age': rng.choice([70, 90, 100, 110]),
         'parentX_net_worth': rng.choice([-200000, 0, 1000, 250000, 3e6, 5e7]),
         'parentY_net_worth': rng.choice([0, 50000, 1e6]),
         'parentX_pretax_balance': rng.choice([0, 100000, 1e7]), 'parentY_roth_balance': rng.choice([0, 50000]),
         'parentX_income': rng.choice([0, 30000, 120000, 450000, 3e6]), 'parentY_income': rng.choice([0, 60000, 200000]),
         'parentX_career_phases': [] if rng.random() < 0.7 else None,
         'parentX_job_changes': [{'Year': 2026 + rng.randint(0, 10), 'New Income': rng.choice([0, 90000, 400000])}] if rng.random() < 0.5 else [],
         'parentX_ss_benefit': rng.choice([0, 1500, 4000]), 'parentX_ss_claim_age': rng.choice([None, 62, 70]),
         'state_timeline': [{'year': 2026, 'state': rng.choice(LOCS), 'spending_strategy': rng.choice(['Conservative', 'Average', 'High-end'])}]
                           + ([{'year': 2026 + rng.randint(1, 30), 'state': rng.choice(LOCS), 'spending_strategy': 'Average'}] if rng.random() < 0.4 else []),
         'children_list': [{'name': f'C{k}', 'birth_year': 2026 + rng.randint(-25, 8), 'school_type': rng.choice(['Public', 'Private']),
                            'college_type': rng.choice(['Public', 'Private'])} for k in range(rng.choice([0, 0, 1, 2, 5]))],
         'houses': [{'name': 'H', 'purchase_year': 2026 + rng.randint(-20, 10), 'purchase_price': rng.choice([300000, 1.5e6]),
                     'current_value': rng.choice([300000, 1.5e6]), 'mortgage_balance': rng.choice([0, 250000, 1.2e6]),
                     'mortgage_years_left': rng.choice([0, 10, 30]), 'mortgage_mode': rng.choice(['actual', 'estimate']),
                     'timeline': [{'year': 2026, 'status': 'Own_Live'}] + ([{'year': 2040, 'status': 'Sold'}] if rng.random() < 0.3 else [])}]
                   if rng.random() < 0.6 else [],
         'finance_mode': rng.choice(['Pooled', 'Separate']),
         'mc_use_historical': rng.random() < 0.4, 'mc_historical_mode': rng.choice(['random', 'sequential']),
         'glide_path': {'enabled': rng.random() < 0.3, 'at_retirement': 40, 'years_before': 5},
         'surplus_sweep': {'enabled': rng.random() < 0.3},
         'guardrails': {'enabled': rng.random() < 0.3, 'lower': 20, 'cut': 10, 'upper': 20, 'raise': 10, 'retired_only': True},
         'roth_conversion': {'mode': rng.choice(['off', 'fixed', 'fill_bracket']), 'amount': 20000, 'bracket': 0.22},
         'essential_categories': rng.choice([None, [], ['Groceries']]),
         'economic_params': {'investment_return': rng.choice([-0.02, 0.0, 0.06, 0.15]), 'inflation_rate': rng.choice([0.0, 0.03, 0.12])},
         'windfalls': [{'year': 2030, 'amount': 500000}] if rng.random() < 0.2 else [],
         'debts': [{'name': 'Car', 'balance': 30000, 'rate': 0.07, 'monthly_payment': 600}] if rng.random() < 0.3 else [],
         'ownership_tracking': {'enabled': rng.random() < 0.15}}
    if p['parentX_career_phases'] is None:
        p.pop('parentX_career_phases')
    return p


fails, warn = [], []
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
for i in range(N):
    p = rand_plan(i)
    try:
        q = normalize_plan(p)
        pr = project(q)
        rows = pr['rows']
        for r in rows:
            for k, v in r.items():
                if isinstance(v, float) and not math.isfinite(v):
                    raise AssertionError(f'non-finite {k} in {r["year"]}')
            if r['taxes'] < -0.01:
                raise AssertionError(f'negative taxes {r["taxes"]} in {r["year"]}')
            if r['exp_healthcare'] < -0.01 or r['total_expenses'] < -0.01:
                raise AssertionError('negative expenses')
        if i % 3 == 0:
            mc = monte_carlo(q, 120, seed=i)
            assert 0 <= mc['success_rate'] <= 1
            plan_health(q, pr, mc)
        if i % 25 == 0:
            evaluate(q, ['plan', 'crash', 'history'], n=60)
        if i % 50 == 0:
            solve(q, n=200)
        if not q['children_list'] and not q['houses'] and q['parentX_income'] == 0 and q['parentY_income'] == 0 \
                and q['parentX_net_worth'] > 1e6 and abs(q['economic_params']['investment_return']) < 1e-9 and False:
            pass
    except Exception as e:
        fails.append((i, repr(e)[:300], traceback.format_exc().splitlines()[-3:]))
print(f'{N} plans, {len(fails)} failures')
for f in fails[:15]:
    print(f)
