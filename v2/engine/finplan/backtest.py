"""Rolling historical backtest (2026-09-28): run the plan once from every historical start year.

Year 1 of the plan earns the S&P 500 return of the start year, year 2 the next year, and so on
(wrapping to the start of the record when a long plan runs past 2023), at the plan's stock share with the
rest earning the bond return. Income and spending follow the plan exactly (no random variation), so the
only difference between runs is the sequence of market returns.
"""
from __future__ import annotations

import copy

import numpy as np

from .engine import simulate, build_schedule, _apply_plan_stress, _hist
from .plan import normalize_plan
from .reference import ref

FIRST_YEAR = 1924


def first_year() -> int:
    hr = (ref().get('_corrections') or {}).get('historical_returns') or {}
    return int(hr.get('first_year', FIRST_YEAR))


def run(plan: dict) -> dict:
    p = _apply_plan_stress(normalize_plan(copy.deepcopy(plan)))
    H = _hist()
    N = len(H)
    p.update({'mc_use_historical': True, 'mc_historical_mode': 'sequential', 'mc_use_asymmetric': False,
              'mc_income_variability': 0.0, 'mc_expense_variability': 0.0, '_backtest_starts': list(range(N))})
    S = build_schedule(p)
    res = simulate(p, N, True, seed=0, normalized=True, _p=p, _sched=S)
    X = res['paths']
    inv, nw = X['investable'], X['net_worth']
    alive = (S.cols['alive1'] + S.cols['alive2']) > 0
    dep = (inv < 0) & alive[:, None]
    ever = dep.any(axis=0)
    first = np.where(ever, dep.argmax(axis=0), -1)
    fy = FIRST_YEAR
    T = S.T
    starts = []
    for s in range(N):
        starts.append({'year': fy + s, 'ok': bool(not ever[s]),
                       'depletion_year': int(S.years[first[s]]) if ever[s] else None,
                       'final_nw': float(nw[-1, s]), 'min_investable': float(inv[:, s].min()),
                       'wrapped': s + T > N})
    finals = np.array([x['final_nw'] for x in starts])
    worst = sorted(starts, key=lambda x: (x['ok'], x['final_nw']))[:5]
    return {'first_year': fy, 'last_year': fy + N - 1, 'years': S.years, 'n': N, 'plan_years': T,
            'success_rate': float(1 - ever.mean()), 'failed': int(ever.sum()),
            'median_final': float(np.median(finals)), 'p10_final': float(np.percentile(finals, 10)),
            'median_path': np.median(nw, axis=1).round(0).tolist(),
            'p10_path': np.percentile(nw, 10, axis=1).round(0).tolist(),
            'starts': starts, 'worst': worst,
            'full_periods': max(0, N - T + 1)}
