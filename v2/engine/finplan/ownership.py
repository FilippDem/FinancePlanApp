"""Separate vs marital property tracking ("who owns what").

An accounting layer on top of the simulation: it never changes totals (taxes,
spending, net worth, success rates). It labels every dollar as

    s1 = person 1's separate property
    s2 = person 2's separate property
    m  = marital (community) property

for liquid savings, pre-tax accounts and each home, year by year, and reports
when separate money had to pay shared costs ("commingling").

Rules (plan['ownership_tracking'], all optional):
    enabled            bool
    regime             'auto' | 'community' | 'equitable' | 'prenup'
    earnings           'marital' (default) | 'separate'  (prenup: each keeps their own pay)
    separate_income    'auto' | 'separate' | 'marital'   (growth/rent from separate property)
    marital_split_pct  person 1's share of marital property if divided (default 50)
    shortfall          'balances' | 'split'  (how separate money covers a marital shortfall)
    today              {'p1': {'liquid', 'pretax'}, 'p2': {...}}  separate part of today's balances
Homes: house['separate_funds'] = {'p1': $, 'p2': $} put in from separate money.
Gifts/inheritances: plan['windfalls'] = [{name, year, amount, recipient, separate, inflation_adjust}].

Homes use a pro-rata contribution method: each class's share of equity equals its
share of the money put in (down payment + principal paid), so appreciation follows
the contributions. Courts use more detailed formulas; this is a planning estimate.
"""
from __future__ import annotations

import numpy as np

# IRS Publication 555: community property states. In Idaho, Louisiana, Texas and
# Wisconsin, income from separate property is community property.
COMMUNITY_STATES = {'Arizona', 'California', 'Idaho', 'Louisiana', 'Nevada', 'New Mexico', 'Texas', 'Washington', 'Wisconsin'}
INCOME_IS_MARITAL = {'Idaho', 'Louisiana', 'Texas', 'Wisconsin'}

DEFAULTS = {'enabled': False, 'regime': 'auto', 'earnings': 'marital', 'separate_income': 'auto',
            'marital_split_pct': 50.0, 'shortfall': 'balances',
            'today': {'p1': {'liquid': 0.0, 'pretax': 0.0}, 'p2': {'liquid': 0.0, 'pretax': 0.0}}}
KEYS = ('s1', 's2', 'm')


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def marriage_year(p: dict) -> int | None:
    try:
        return int(p.get('marriage_year'))
    except (TypeError, ValueError):
        return None


def normalize(raw) -> dict:
    o = dict(DEFAULTS)
    if isinstance(raw, dict):
        o.update({k: v for k, v in raw.items() if k != 'today'})
    today = {'p1': dict(DEFAULTS['today']['p1']), 'p2': dict(DEFAULTS['today']['p2'])}
    for who in ('p1', 'p2'):
        src = ((raw or {}).get('today') or {}).get(who) or {} if isinstance(raw, dict) else {}
        today[who] = {'liquid': max(0.0, _num(src.get('liquid'))), 'pretax': max(0.0, _num(src.get('pretax')))}
    o['today'] = today
    o['enabled'] = bool(o.get('enabled'))
    o['marital_split_pct'] = min(100.0, max(0.0, _num(o.get('marital_split_pct'), 50.0)))
    for k, allowed in (('regime', ('auto', 'community', 'equitable', 'prenup')), ('earnings', ('marital', 'separate')),
                       ('separate_income', ('auto', 'separate', 'marital')), ('shortfall', ('balances', 'split'))):
        if o.get(k) not in allowed:
            o[k] = DEFAULTS[k]
    return o


def _state_of(p: dict, year: int) -> str:
    from .reference import CITY_TO_STATE, location_tax_info
    stl = p.get('state_timeline') or []
    cur = stl[0]['state'] if stl else 'Seattle'
    for e in stl:
        if e['year'] <= year:
            cur = e['state']
    cur = ((p.get('custom_locations') or {}).get(cur) or {}).get('tax_location') or cur
    cur = CITY_TO_STATE.get(cur, cur)
    kind, _ = location_tax_info(cur)
    return cur if kind == 'us_state' else ''


def resolve(p: dict) -> dict:
    """Settings with 'auto' rules resolved from the state where the couple lives at marriage (or now)."""
    o = normalize(p.get('ownership_tracking'))
    my = marriage_year(p)
    st = _state_of(p, max(my or p['current_year'], p['current_year']) if my and my > p['current_year'] else (my or p['current_year']))
    auto_regime = 'community' if st in COMMUNITY_STATES else 'equitable'
    o['state'] = st
    o['regime_resolved'] = auto_regime if o['regime'] == 'auto' else o['regime']
    o['separate_income_resolved'] = (('marital' if st in INCOME_IS_MARITAL else 'separate')
                                     if o['separate_income'] == 'auto' else o['separate_income'])
    o['marriage_year'] = my
    return o


# ─────────────────────────── schedule (deterministic parts) ─────────────────

def phases(p: dict, years: list, married_col) -> list[str]:
    """'before' marriage, 'married', or 'after' (widowed) for each year."""
    my = marriage_year(p)
    out = []
    was = False
    for t, y in enumerate(years):
        if married_col[t] and (my is None or y >= my):
            out.append('married'); was = True
        elif was or (my is not None and y >= my):
            out.append('after')
        else:
            out.append('before')
    return out


def build(p: dict, years: list, C: dict, details: list, house_rows: list, split: float) -> dict:
    """Class arrays for homes and gifts/inheritances. Adds to C: own_heq_*, own_rent_*, own_sale_*,
    own_dp_s1/s2, wf_*; returns the resolved settings and phases."""
    T = len(years)
    o = resolve(p)
    ph = phases(p, years, C['married'])
    for k in KEYS:
        for base in ('own_heq_', 'own_rent_', 'own_sale_', 'wf_'):
            C[base + k] = np.zeros(T)
    C['own_dp_s1'], C['own_dp_s2'] = np.zeros(T), np.zeros(T)
    sep_inc_marital = o['separate_income_resolved'] == 'marital'
    earn_marital = o['earnings'] == 'marital'
    my = o['marriage_year']
    cy = p['current_year']

    def payer(t, own_key) -> dict:
        """Which class pays (and so owns) new principal in year t."""
        if ph[t] == 'married' and earn_marital:
            return {'m': 1.0}
        if own_key == 'p1':
            return {'s1': 1.0}
        if own_key == 'p2':
            return {'s2': 1.0}
        return {'s1': split, 's2': 1 - split}

    home_rows = [[] for _ in range(T)]
    for hi, (h, s, future, terms, own_key) in enumerate(house_rows):
        basis = {k: 0.0 for k in KEYS}
        started = False
        last_f = None
        sf = h.get('separate_funds') or {}
        c1, c2 = max(0.0, _num(sf.get('p1'))), max(0.0, _num(sf.get('p2')))
        for t in range(T):
            row = details[t]['houses'][hi]
            if 'equity' in row:
                if not started:
                    started = True
                    if future and 'down_payment' in row:
                        dp = row['down_payment']
                        k = min(1.0, dp / (c1 + c2)) if (c1 + c2) > 0 else 0.0
                        a1, a2 = c1 * k, c2 * k
                        C['own_dp_s1'][t] += a1
                        C['own_dp_s2'][t] += a2
                        basis['s1'] += a1; basis['s2'] += a2
                        for kk, f in payer(t, own_key).items():
                            basis[kk] += (dp - a1 - a2) * f
                    else:
                        # existing home: money put in so far = price - today's loan (else today's equity)
                        put_in = max(0.0, (h.get('purchase_price') or 0) - h.get('mortgage_balance', 0)) or max(row['equity'], 0.0)
                        k = min(1.0, put_in / (c1 + c2)) if (c1 + c2) > 0 else 0.0
                        a1, a2 = c1 * k, c2 * k
                        basis['s1'] += a1; basis['s2'] += a2
                        rest = put_in - a1 - a2
                        py = int(h.get('purchase_year') or cy)
                        # split the rest by the years owned before / after the wedding
                        if ph[0] == 'before':
                            before = 1.0
                        elif my is None or py >= my:
                            before = 0.0
                        else:
                            before = min(1.0, max(0.0, (my - py) / max(cy - py, 1)))
                        owner_pay = {'s1': 1.0} if own_key == 'p1' else {'s2': 1.0} if own_key == 'p2' else {'s1': split, 's2': 1 - split}
                        for kk, f in owner_pay.items():
                            basis[kk] += rest * before * f
                        for kk, f in payer(0, own_key).items():
                            basis[kk] += rest * (1 - before) * f
                else:
                    for kk, f in payer(t, own_key).items():
                        basis[kk] += max(row.get('principal', 0.0), 0.0) * f
                tot = sum(basis.values())
                f = {k: basis[k] / tot for k in KEYS} if tot > 0 else payer(t, own_key)
                f = {k: f.get(k, 0.0) for k in KEYS}
                last_f = f
                eq, rent = row['equity'], row.get('rent', 0.0)
                for k in KEYS:
                    C['own_heq_' + k][t] += eq * f[k]
                rs = {k: rent * f[k] for k in KEYS}
                if sep_inc_marital and ph[t] == 'married':
                    rs = {'s1': 0.0, 's2': 0.0, 'm': rent}
                for k in KEYS:
                    C['own_rent_' + k][t] += rs[k]
                home_rows[t].append({'name': h['name'], **{k: eq * f[k] for k in KEYS}})
            elif 'proceeds' in row and last_f:
                for k in KEYS:
                    C['own_sale_' + k][t] += row['proceeds'] * last_f[k]
    for t in range(T):
        details[t]['ownership_homes'] = home_rows[t]

    # gifts & inheritances
    for w in p.get('windfalls') or []:
        t = int(w['year']) - cy
        if 0 <= t < T:
            amt = w['amount'] * (C['infl_index'][t] if w.get('inflation_adjust', True) else 1.0)
            who = w.get('recipient', 'Parent 1')
            sep = bool(w.get('separate', True))
            k = 's1' if (sep and who == 'Parent 1') else 's2' if (sep and who == 'Parent 2') else 'm'
            C['wf_' + k][t] += amt
    o['phases'] = ph
    return o


# ─────────────────────────── simulation overlay ──────────────────────────────

class Overlay:
    """Runs alongside simulate(); pots are arrays over paths. Totals are reconciled to the engine's."""

    def __init__(self, p: dict, S, L1, L2, pre1: float, pre2: float, hsa: float, n: int, split: float):
        o = S.meta['ownership']
        self.o, self.S, self.split = o, S, split
        self.ph = o['phases']
        self.earn_marital = o['earnings'] == 'marital'
        self.sep_inc_marital = o['separate_income_resolved'] == 'marital'
        T = S.T
        L1, L2 = np.asarray(L1, float), np.asarray(L2, float)
        if self.ph[0] == 'before':
            # not married yet: everything each person has is theirs
            self.S1, self.S2, self.M = L1.copy(), L2.copy(), np.zeros(n)
            self.Q1, self.Q2, self.QM = np.full(n, pre1 + hsa), np.full(n, pre2), np.zeros(n)
        else:
            td = o['today']
            self.S1 = np.minimum(np.full(n, td['p1']['liquid']), np.maximum(L1, 0))
            self.S2 = np.minimum(np.full(n, td['p2']['liquid']), np.maximum(L2, 0))
            self.M = L1 + L2 - self.S1 - self.S2
            self.Q1 = np.full(n, min(td['p1']['pretax'], pre1))
            self.Q2 = np.full(n, min(td['p2']['pretax'], pre2))
            self.QM = np.full(n, pre1 + pre2 + hsa) - self.Q1 - self.Q2
        self.out = {k: np.zeros((T, n)) for k in ('own_s1', 'own_s2', 'own_m', 'own_q1', 'own_q2', 'own_qm', 'own_comm')}
        self.comm = np.zeros(n)

    @staticmethod
    def _g(X, r, debt_rate):
        return np.where(X >= 0, X * r, X * debt_rate)

    def step(self, t, r, debt_rate, C, EM, w1, w2, taxes, expenses, inc_share):
        ph = self.ph[t]
        married = ph == 'married'
        g = self._g
        self.comm = np.zeros_like(self.M)
        # growth: separate income stays separate unless the state/prenup says otherwise
        gs1, gs2, gm = g(self.S1, r, debt_rate), g(self.S2, r, debt_rate), g(self.M, r, debt_rate)
        if married and self.sep_inc_marital:
            self.M = self.M + gm + gs1 + gs2
        else:
            self.S1, self.S2, self.M = self.S1 + gs1, self.S2 + gs2, self.M + gm
        # income
        inc1, inc2 = w1 + C['ss1'][t], w2 + C['ss2'][t]
        if married and self.earn_marital:
            self.M = self.M + inc1 + inc2
        else:
            self.S1, self.S2 = self.S1 + inc1, self.S2 + inc2
        for k, attr in (('s1', 'S1'), ('s2', 'S2'), ('m', 'M')):
            setattr(self, attr, getattr(self, attr) + C['own_rent_' + k][t] + C['own_sale_' + k][t] + C['wf_' + k][t])
        # separate money put into a home purchase
        self.S1 = self.S1 - C['own_dp_s1'][t]
        self.S2 = self.S2 - C['own_dp_s2'][t]
        # everything else that leaves liquid savings
        roth_c = (C['roth_contrib'][t] if 'roth_contrib' in C else 0.0)
        out = taxes + C['contrib'][t] + roth_c + expenses - C['own_dp_s1'][t] - C['own_dp_s2'][t]
        split = self.split
        shared = (C['family_exp'][t] + C['children_exp'][t] + C['recurring_exp'][t]) * EM[t] + C['purchase_exp'][t] + C['hc_shared'][t] * EM[t]
        e1 = (C['p1_exp'][t] * EM[t] + C['hc_p1'][t] * EM[t] + shared * split + C['house_exp_p1'][t]
              + C['house_exp_shared'][t] * split + C['dp_p1'][t] + C['dp_shared'][t] * split)
        o1 = e1 + taxes * inc_share + C['contrib1'][t]
        tot = taxes + C['contrib'][t] + expenses
        f1 = np.clip(np.where(tot > 0, o1 / np.maximum(tot, 1e-9), split), 0, 1)
        if ph == 'before':
            self.S1, self.S2 = self.S1 - out * f1, self.S2 - out * (1 - f1)
        else:
            if married and self.earn_marital:
                # marital money pays first, including marital retirement money (the cash may come out of the
                # 401(k) later; until then marital cash runs negative against it). Separate money is only
                # touched once all marital savings are used up.
                room = np.maximum(self.M + np.maximum(self.QM, 0), 0)
                take = np.minimum(room, np.maximum(out, 0))
            else:
                take = np.minimum(np.maximum(self.M, 0), np.maximum(out, 0))
            self.M = self.M - take
            rem = out - take
            if married and self.earn_marital:
                a1, a2 = np.maximum(self.S1, 0), np.maximum(self.S2, 0)
                avail = a1 + a2
                d = np.minimum(np.maximum(rem, 0), avail)
                if self.o['shortfall'] == 'split':
                    g1 = np.where(avail > 0, np.minimum(d * split, a1), 0)
                    g2 = np.minimum(d - g1, a2)
                    g1 = np.minimum(d - g2, a1)
                else:
                    fr = np.where(avail > 0, a1 / np.maximum(avail, 1e-9), 0.5)
                    g1, g2 = d * fr, d * (1 - fr)
                self.S1, self.S2 = self.S1 - g1, self.S2 - g2
                self.comm = self.comm + g1 + g2
                self.M = self.M - (rem - g1 - g2)
            else:
                # prenup with separate earnings, or after a death: each person's own share, as far as their
                # separate money goes; anything left becomes household (marital) debt
                a1, a2 = np.maximum(self.S1, 0), np.maximum(self.S2, 0)
                g1 = np.minimum(np.maximum(rem, 0) * f1, a1)
                g2 = np.minimum(np.maximum(rem, 0) * (1 - f1), a2)
                # one side short: the other covers the rest of the household share
                g1b = np.minimum(np.maximum(rem, 0) - g1 - g2, a1 - g1)
                g1 = g1 + g1b
                g2 = g2 + np.minimum(np.maximum(rem, 0) - g1 - g2, a2 - g2)
                self.S1, self.S2 = self.S1 - g1, self.S2 - g2
                self.M = self.M - (rem - g1 - g2)
        # pre-tax accounts
        gq1, gq2, gqm = self.Q1 * r, self.Q2 * r, self.QM * r
        if married and self.sep_inc_marital:
            self.QM = self.QM + gqm + gq1 + gq2
        else:
            self.Q1, self.Q2, self.QM = self.Q1 + gq1, self.Q2 + gq2, self.QM + gqm
        rc1, rc2 = C['roth_c1'][t] if 'roth_c1' in C else 0.0, C['roth_c2'][t] if 'roth_c2' in C else 0.0
        if married and self.earn_marital:
            self.QM = self.QM + C['contrib'][t] + rc1 + rc2
        else:
            self.Q1, self.Q2 = self.Q1 + C['contrib1'][t] + rc1, self.Q2 + C['contrib2'][t] + rc2

    def rmd(self, amount, retirement_total):
        """Required distributions move money from each class's retirement pot to its cash pot."""
        f = np.where(retirement_total > 0, amount / np.maximum(retirement_total, 1e-9), 0)
        for q, l in (('Q1', 'S1'), ('Q2', 'S2'), ('QM', 'M')):
            mv = np.maximum(getattr(self, q), 0) * f
            setattr(self, q, getattr(self, q) - mv)
            setattr(self, l, getattr(self, l) + mv)

    def withdraw(self, t, W, add):
        """Pre-tax money pulled in to cover a shortfall (W gross, `add` after tax)."""
        if not np.any(W > 0):
            return
        married = self.ph[t] == 'married'
        rem = W.copy()
        wm = np.zeros_like(W)
        if married:
            wm = np.minimum(np.maximum(self.QM, 0), rem)
            rem = rem - wm
        a1, a2 = np.maximum(self.Q1, 0), np.maximum(self.Q2, 0)
        av = a1 + a2
        d = np.minimum(rem, av)
        fr = np.where(av > 0, a1 / np.maximum(av, 1e-9), 0.5)
        w1, w2 = d * fr, d * (1 - fr)
        wm = wm + (rem - d)
        self.QM, self.Q1, self.Q2 = self.QM - wm, self.Q1 - w1, self.Q2 - w2
        k = np.where(W > 0, add / np.maximum(W, 1e-9), 0)
        if married and self.earn_marital:
            self.M = self.M + (wm + w1 + w2) * k
            self.comm = self.comm + (w1 + w2) * k
        else:
            self.M, self.S1, self.S2 = self.M + wm * k, self.S1 + w1 * k, self.S2 + w2 * k

    def record(self, t, liquid_total, pretax_total, fac):
        # reconcile to the engine's own totals (differences come from pooled vs per-pot interest)
        self.M = self.M + (liquid_total - (self.S1 + self.S2 + self.M))
        self.QM = self.QM + (pretax_total - (self.Q1 + self.Q2 + self.QM))
        for k, v in (('own_s1', self.S1), ('own_s2', self.S2), ('own_m', self.M), ('own_q1', self.Q1),
                     ('own_q2', self.Q2), ('own_qm', self.QM), ('own_comm', self.comm)):
            self.out[k][t] = v / fac


def rows(o: dict, P: dict, C: dict, S, t: int, fac: float) -> dict:
    """Per-year ownership block for a projection row (deterministic path)."""
    g = lambda k: float(P[k][t, 0])
    heq = {k: float(C['own_heq_' + k][t]) / fac for k in KEYS}
    other = (float(C['other_assets'][t]) - float(C['consumer_debt'][t])) / fac
    s1 = g('own_s1') + g('own_q1') + heq['s1']
    s2 = g('own_s2') + g('own_q2') + heq['s2']
    m = g('own_m') + g('own_qm') + heq['m'] + other
    pct = o['marital_split_pct'] / 100
    return {'phase': o['phases'][t],
            'liquid': {'s1': g('own_s1'), 's2': g('own_s2'), 'm': g('own_m')},
            'pretax': {'s1': g('own_q1'), 's2': g('own_q2'), 'm': g('own_qm')},
            'homes': heq, 'other': other,
            'separate1': s1, 'separate2': s2, 'marital': m,
            'commingled': g('own_comm'),
            'division': {'p1': s1 + m * pct, 'p2': s2 + m * (1 - pct)}}
