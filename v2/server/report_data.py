"""Tables shared by the PDF, Excel, CSV and JSON reports."""
from __future__ import annotations

from collections import OrderedDict

from finplan.engine import project, monte_carlo
from finplan.plan import normalize_plan, is_single
from finplan import reference as _REF

SECTIONS = OrderedDict([
    ('summary', 'Summary & key numbers'),
    ('charts', 'Charts (net worth range, income & spending)'),
    ('people', 'People & income'),
    ('children', 'Children'),
    ('spending', 'Spending plan (categories)'),
    ('homes', 'Homes & mortgages'),
    ('healthcare', 'Healthcare & insurance'),
    ('purchases', 'One-time purchases & recurring costs'),
    ('locations', 'Where you live (location timeline)'),
    ('ownership', 'Who owns what (separate vs marital property, gifts & inheritances)'),
    ('assumptions', 'Economic assumptions'),
    ('monte_carlo', 'Monte Carlo results'),
    ('year_by_year', 'Year by year by category'),
    ('category_detail', 'Detailed category breakdown (every line item, every year)'),
    ('checkins', 'Check-in history'),
])
DEFAULT_SECTIONS = list(SECTIONS)

# (key, header, getter) for the per-year category table
CATEGORY_COLS = [
    ('year', 'Year', lambda r: r['year']),
    ('ages', 'Ages', None),
    ('wages', 'Wages', lambda r: r['wages1'] + r['wages2']),
    ('ss', 'Social Security', lambda r: r['ss_income']),
    ('rent', 'Rent income', lambda r: r['rent_income']),
    ('sales', 'Home sales', lambda r: r['sale_proceeds']),
    ('gifts', 'Gifts & inheritances', lambda r: r.get('windfalls', 0.0)),
    ('growth', 'Investment growth', lambda r: r.get('investment_growth', 0.0)),
    ('taxes', 'Taxes', lambda r: r['taxes']),
    ('p1', 'Living: %1', lambda r: r['exp_person1']),
    ('p2', 'Living: %2', lambda r: r['exp_person2']),
    ('family', 'Household', lambda r: r['exp_family']),
    ('children', 'Children', lambda r: r['exp_children']),
    ('housing', 'Housing', lambda r: r['exp_housing']),
    ('healthcare', 'Healthcare', lambda r: r['exp_healthcare']),
    ('recurring', 'Recurring', lambda r: r['exp_recurring']),
    ('onetime', 'One-time', lambda r: r['exp_purchases']),
    ('down', 'Down payments', lambda r: r['down_payment']),
    ('spend', 'Total spending', lambda r: r['total_expenses']),
    ('cashflow', 'Cash flow', lambda r: r['cashflow']),
    ('savings', 'Savings', lambda r: r['investable']),
    ('equity', 'Home equity', lambda r: r['home_equity']),
    ('nw', 'Net worth', lambda r: r['net_worth']),
]
MONEY_KEYS = [k for k, _, g in CATEGORY_COLS if g is not None and k != 'year']


def compute(plan: dict, n_mc: int = 1000) -> dict:
    p = normalize_plan(plan)
    pr = project(p)
    mc = monte_carlo(p, n_mc, seed=3, normalized=False)
    return {'plan': p, 'proj': pr, 'mc': mc, 'single': is_single(p),
            'names': (p['parent1_name'], p.get('parent2_name', ''))}


def category_table(ctx: dict, today: bool = True) -> tuple[list[str], list[list]]:
    single, (n1, n2) = ctx['single'], ctx['names']
    cols = [c for c in CATEGORY_COLS if not (single and c[0] in ('p2',))]
    headers = [h.replace('%1', n1).replace('%2', n2) for _, h, _ in cols]
    rows = []
    for r in ctx['proj']['rows']:
        f = r['infl_index'] if today else 1.0
        line = []
        for key, _, g in cols:
            if key == 'year':
                line.append(r['year'])
            elif key == 'ages':
                line.append(f"{r['age1']}" + ('' if single else f"/{r['age2']}"))
            else:
                line.append(g(r) / f)
        rows.append(line)
    return headers, rows


def detail_lines(ctx: dict, today: bool = True) -> tuple[list[int], list[tuple[str, str, list[float]]]]:
    """Every line item for every year: [(group, label, [amount per year])]."""
    single, (n1, n2) = ctx['single'], ctx['names']
    rows = ctx['proj']['rows']
    years = [r['year'] for r in rows]
    T = len(rows)
    lines: 'OrderedDict[tuple[str, str], list[float]]' = OrderedDict()

    def add(group, label, t, amt):
        if not amt:
            return
        key = (group, label)
        if key not in lines:
            lines[key] = [0.0] * T
        lines[key][t] += amt

    for t, r in enumerate(rows):
        f = r['infl_index'] if today else 1.0
        d = r['details']
        add('Income', f'Wages: {n1}', t, r['wages1'] / f)
        if not single:
            add('Income', f'Wages: {n2}', t, r['wages2'] / f)
        add('Income', f'Social Security: {n1}', t, r['ss1'] / f)
        if not single:
            add('Income', f'Social Security: {n2}', t, r['ss2'] / f)
        add('Income', 'Rental income', t, r['rent_income'] / f)
        add('Income', 'Home sale proceeds', t, r['sale_proceeds'] / f)
        add('Income', 'Investment growth', t, r.get('investment_growth', 0.0) / f)
        add('Taxes', 'Federal income tax', t, r['tax_federal'] / f)
        add('Taxes', 'State income tax', t, r['tax_state'] / f)
        add('Taxes', 'Social Security & Medicare (FICA)', t, r['tax_fica'] / f)
        add('Taxes', 'Foreign income tax', t, r['tax_foreign'] / f)
        liv = d.get('living') or {}
        for cat, v in (liv.get('p1') or {}).items():
            add(f'Living: {n1}', cat, t, v / f)
        for cat, v in (liv.get('p2') or {}).items():
            add(f'Living: {n2}', cat, t, v / f)
        for cat, v in (liv.get('shared') or {}).items():
            add('Household', cat, t, v / f)
        for c in d.get('children') or []:
            add('Children', f"{c['name']} (total)", t, c['total'] / f)
            for cat, v in (c.get('cats') or {}).items():
                add('Children by category', cat, t, v / f)
        for h in d.get('houses') or []:
            for key, lab in (('mortgage_pi', 'Mortgage P&I'), ('pmi', 'PMI'), ('hoa', 'HOA'), ('property_tax', 'Property tax'),
                             ('insurance', 'Insurance'), ('maintenance', 'Maintenance'), ('upkeep', 'Upkeep')):
                add(f"Home: {h['name']}", lab, t, h.get(key, 0.0) / f)
        add('Homes', 'Down payments & closing', t, r['down_payment'] / f)
        for it in d.get('healthcare') or []:
            add('Healthcare', f"{it['name']} ({it['who']})", t, it['amount'] / f)
        for it in d.get('recurring') or []:
            add('Recurring', it['name'], t, it['amount'] / f)
        for it in d.get('purchases') or []:
            add('One-time', it['name'], t, it['amount'] / f)
    def rank(g):
        order = ['Income', 'Taxes', f'Living: {n1}', f'Living: {n2}', 'Household', 'Children', 'Children by category']
        if g in order:
            return (order.index(g), '')
        if g.startswith('Home: '):
            return (10, g)
        return (20 + ['Homes', 'Healthcare', 'Recurring', 'One-time'].index(g) if g in ('Homes', 'Healthcare', 'Recurring', 'One-time') else 30, g)
    items = list(lines.items())
    items.sort(key=lambda kv: rank(kv[0][0]))       # stable: keeps first-seen order inside a group
    return years, [(g, l, v) for (g, l), v in items]


def people_table(ctx: dict) -> tuple[list[str], list[list]]:
    p = ctx['plan']
    hdr = ['', 'Age', 'Income', 'Raise %', 'Savings', 'Of which pre-tax', 'Retire at', 'SS at 67 ($/mo)', 'Claim at', 'Plan until']
    out = []
    for who, name in (('X', p['parent1_name']), ('Y', p.get('parent2_name'))):
        if who == 'Y' and ctx['single']:
            continue
        out.append([name, p[f'parent{who}_age'], p[f'parent{who}_income'], p[f'parent{who}_raise'], p[f'parent{who}_net_worth'],
                    p.get(f'parent{who}_pretax_balance', 0), p[f'parent{who}_retirement_age'], p[f'parent{who}_ss_benefit'],
                    p.get(f'parent{who}_ss_claim_age') or '', p[f'parent{who}_death_age']])
    return hdr, out


def career_rows(ctx: dict) -> list[list]:
    p = ctx['plan']
    out = []
    for who, name in (('X', p['parent1_name']), ('Y', p.get('parent2_name'))):
        for ph in p.get(f'parent{who}_career_phases') or []:
            out.append([name, ph.get('label') or ph.get('philosophy', ''), f"{ph['start_age']}–{ph['end_age']}", ph['base_salary'],
                        ph['annual_raise_pct'], ph['annual_bonus_pct'], ph['rsu_annual_grant']])
        for j in p.get(f'parent{who}_job_changes') or []:
            out.append([name, 'Job change', j.get('Year'), j.get('New Income'), j.get('New Raise %', ''), '', ''])
    return out


def children_table(ctx: dict) -> tuple[list[str], list[list]]:
    p, cy = ctx['plan'], ctx['plan']['current_year']
    hdr = ['Name', 'Born', 'Age now', 'Cost location', 'Lifestyle', 'K-12', 'College', 'College location']
    return hdr, [[c['name'], c['birth_year'], cy - c['birth_year'], c.get('template_state', ''), c.get('template_strategy', ''),
                  c.get('school_type', ''), c.get('college_type', ''), c.get('college_location', '')] for c in p['children_list']]


def spending_inputs(ctx: dict) -> list[tuple[str, str, float]]:
    p, (n1, n2) = ctx['plan'], ctx['names']
    out = [(n1, k, v) for k, v in p['parentX_expenses'].items() if v]
    if not ctx['single']:
        out += [(n2, k, v) for k, v in p['parentY_expenses'].items() if v]
    out += [('Household', k, v) for k, v in p['family_shared_expenses'].items() if v]
    return out


def homes_table(ctx: dict) -> tuple[list[str], list[list]]:
    hdr = ['Home', 'Bought', 'Price', 'Value', 'Mortgage', 'Rate', 'Years left', 'Property tax', 'Insurance/yr', 'Timeline']
    out = []
    for h in ctx['plan']['houses']:
        tl = ', '.join(f"{e['year']} {e['status'].replace('_', ' ')}" + (f" (${e['rental_income']:,.0f}/mo)" if e.get('rental_income') else '')
                       for e in h['timeline'])
        out.append([h['name'], h['purchase_year'], h['purchase_price'], h['current_value'], h['mortgage_balance'],
                    f"{h['mortgage_rate'] * 100:.2f}%", h['mortgage_years_left'], f"{h['property_tax_rate'] * 100:.2f}%", h['home_insurance'], tl])
    return hdr, out


def healthcare_tables(ctx: dict) -> dict:
    p = ctx['plan']
    return {
        'insurance': (['Plan', 'Type', 'Premium/mo', 'Deductible', 'OOP max', 'Covers', 'Ages'],
                      [[i.get('name', ''), i.get('type', ''), i['monthly_premium'], i.get('annual_deductible', 0),
                        i.get('annual_out_of_pocket_max', 0), i['covered_by'], f"{i['start_age']}–{i['end_age']}"] for i in p['health_insurances']]),
        'ltc': (['Policy', 'Person', 'Premium/mo', 'Daily benefit', 'Benefit days', 'From age'],
                [[l.get('name', ''), l['covered_person'], l['monthly_premium'], l.get('daily_benefit', 0), l.get('benefit_period_days', 0), l['start_age']]
                 for l in p['ltc_insurances']]),
        'other': [('Medicare Part B /mo', p['medicare_part_b_premium']), ('Medicare Part D /mo', p['medicare_part_d_premium']),
                  ('Medigap /mo', p['medigap_premium']), ('HSA balance', p.get('hsa_balance', 0)),
                  ('HSA contribution /yr', p.get('hsa_contribution', 0))],
    }


def purchases_tables(ctx: dict) -> dict:
    p = ctx['plan']
    return {
        'purchases': (['Purchase', 'Year', 'Amount (today $)', 'Financed (yrs)', 'Rate', 'Kind'],
                      [[m['name'], m['year'], m['amount'], m['financing_years'], f"{m['interest_rate'] * 100:.1f}%" if m['interest_rate'] < 1 else m['interest_rate'],
                        m.get('asset_type', 'Expense')] for m in p['major_purchases']]),
        'recurring': (['Cost', 'Category', 'Amount (today $)', 'Every (yrs)', 'From', 'To', 'Owner'],
                      [[r['name'], r.get('category', ''), r['amount'], r['frequency_years'], r['start_year'], r['end_year'] or 'end',
                        r.get('parent', '')] for r in p['recurring_expenses']]),
    }


def locations_table(ctx: dict) -> tuple[list[str], list[list]]:
    p = ctx['plan']
    stl = p['state_timeline']
    end = ctx['proj']['summary']['end_year']
    out = []
    for i, e in enumerate(stl):
        until = (stl[i + 1]['year'] - 1) if i + 1 < len(stl) else end
        row = next((r for r in ctx['proj']['rows'] if r['year'] == max(e['year'], p['current_year'])), None)
        out.append([e['year'], until, e['state'], e.get('spending_strategy', ''), f"{row['col_factor']:.2f}×" if row else ''])
    return ['From', 'Until', 'Location', 'Lifestyle', 'Spending vs today'], out


def assumptions_rows(ctx: dict) -> list[tuple[str, str]]:
    p = ctx['plan']
    ep = p['economic_params']
    mc = ctx['mc']
    return [('Investment return', f"{ep['investment_return'] * 100:.1f}%"), ('Inflation', f"{ep['inflation_rate'] * 100:.1f}%"),
            ('Healthcare inflation', f"{ep['healthcare_inflation_rate'] * 100:.1f}%"),
            ('Monte Carlo', f"{mc['n']:,} runs · {mc['mode']}"),
            ('Social Security cut', f"{p['ss_shortfall_percentage']:.0f}% from {p.get('ss_insolvency_year', 2034)}" if p['ss_insolvency_enabled'] else 'none'),
            ('Finances', p['finance_mode']), ('401(k) contributions /yr', f"${p['pretax_401k']:,.0f}"),
            ('Filing status', p.get('tax_filing_status', 'married')),
            ('Spending follows moves', 'yes' if p.get('move_adjusts_spending', True) else 'no')]


def lifetime_summary(ctx: dict, today: bool = True) -> list[tuple[str, str]]:
    rows = ctx['proj']['rows']
    s = ctx['proj']['summary']
    td = (lambda r, k: r[k] / r['infl_index']) if today else (lambda r, k: r[k])
    mx = max(rows, key=lambda r: td(r, 'net_worth'))
    mn = min(rows, key=lambda r: td(r, 'net_worth'))
    is_working = lambda r: r.get('work1') or (not ctx['single'] and r.get('work2')) if 'work1' in r else r['wages1'] + r['wages2'] > 0
    working = [r for r in rows if is_working(r)]
    retired = [r for r in rows if not is_working(r)]
    avg = lambda xs, k: sum(td(r, k) for r in xs) / len(xs) if xs else 0.0
    m = lambda v: f"${v:,.0f}"
    return [('Plan horizon', f"{s['current_year']}–{s['end_year']} ({len(rows)} years)"),
            ('Peak net worth', f"{m(td(mx, 'net_worth'))} in {mx['year']}"),
            ('Lowest net worth', f"{m(td(mn, 'net_worth'))} in {mn['year']}"),
            ('Final net worth', m(td(rows[-1], 'net_worth'))),
            ('Average income while working', m(avg(working, 'total_income'))),
            ('Average spending while working', m(avg(working, 'total_expenses'))),
            ('Average spending in retirement', m(avg(retired, 'total_expenses'))),
            ('Years in retirement', str(len(retired))),
            ('Savings run out', str(s['depletion_year']) if s['depletion_year'] else 'never (expected path)')]


def mc_percentiles(ctx: dict, today: bool = True) -> tuple[list[str], list[list]]:
    mc, rows = ctx['mc'], ctx['proj']['rows']
    qs = ['10', '25', '50', '75', '90']
    out = []
    for t, r in enumerate(rows):
        d = r['infl_index'] if today else 1.0
        out.append([r['year']] + [mc['net_worth'][q][t] / d for q in qs] + [mc['solvent_by_year'][t]])
    return ['Year'] + [f'{q}th pct NW' for q in qs] + ['Still solvent'], out


# ── data citations ─────────────────────────────────────────────────────────
def _abroad(p: dict) -> bool:
    return any(_REF.location_tax_info((p.get('custom_locations') or {}).get(e['state'], {}).get('tax_location') or e['state'])[0] == 'country'
               for e in p['state_timeline'])


def section_sources(ctx: dict, section: str) -> list[str]:
    """Source ids (data/sources.json) behind a report section, in citation order."""
    p = ctx['plan']
    abroad = _abroad(p)
    hist = bool(p.get('mc_use_historical'))
    m = {
        'people': ['ssa_claiming'],
        'children': ['mit_living_wage', 'childcareaware_2024', 'collegeboard'],
        'spending': ['bls_cex_2022', 'bls_cex_2024', 'bea_rpp_2024'] + (['worldbank_pli'] if abroad else []),
        'healthcare': ['cms_partb_2026', 'cms_partd_2026', 'cms_nhe'],
        'locations': ['bea_rpp_2024', 'taxfoundation_state_2025'] + (['worldbank_pli', 'oecd_taxing_wages_2025'] if abroad else []),
        'assumptions': ['bls_cpi', 'cms_nhe', 'irs_2024_tax', 'ssa_wage_base', 'ssa_trustees_2026'] + (['damodaran_sp500'] if hist else []),
        'monte_carlo': ['damodaran_sp500'] if hist else [],
        'ownership': ['irs_pub555', 'lii_equitable'] if (p.get('ownership_tracking') or {}).get('enabled') else [],
    }
    return m.get(section, [])


def sources_for(ctx: dict, sections: list) -> list[tuple[str, dict]]:
    """Every cited source for the chosen sections, first-use order, with its data."""
    src = _REF.sources()
    order: list[str] = []
    for sec in sections:
        for i in section_sources(ctx, sec):
            if i in src and i not in order:
                order.append(i)
    return [(i, src[i]) for i in order]


# ── who owns what ──────────────────────────────────────────────────────────
def ownership_enabled(ctx: dict) -> bool:
    return bool(ctx['proj']['summary'].get('ownership'))


def ownership_rules(ctx: dict) -> list[tuple[str, str]]:
    o = ctx['proj']['summary']['ownership']
    n1, n2 = ctx['names']
    reg = {'community': 'Community property', 'equitable': 'Equitable distribution', 'prenup': 'Prenup'}.get(o['regime_resolved'], o['regime_resolved'])
    return [('Rules', reg + (f" ({o['state']})" if o.get('state') else '')), ('Married', str(o.get('marriage_year') or 'before the plan starts')),
            ('Pay during marriage', 'marital' if o['earnings'] == 'marital' else "each person's own"),
            ('Growth/rent on separate property', o['separate_income_resolved']),
            (f"{n1}'s share of marital property if divided", f"{o['marital_split_pct']:.0f}%"),
            ('Separate money spent on shared costs', f"${o['commingled_total']:,.0f}" + (f" (from {o['first_commingled_year']})" if o.get('first_commingled_year') else ''))]


def ownership_table(ctx: dict, today: bool = True, every: int = 1) -> tuple[list[str], list[list]]:
    n1, n2 = ctx['names']
    rows = [r for r in ctx['proj']['rows'] if r.get('ownership')]
    hdr = ['Year', f'{n1} separate', f'{n2} separate', 'Marital', f'{n1} would get', f'{n2} would get', 'Separate spent on shared']
    out = []
    for i, r in enumerate(rows):
        if every > 1 and i % every and i != len(rows) - 1:
            continue
        f = r['infl_index'] if today else 1.0
        o = r['ownership']
        out.append([r['year'], o['separate1'] / f, o['separate2'] / f, o['marital'] / f, o['division']['p1'] / f, o['division']['p2'] / f, o['commingled'] / f])
    return hdr, out


def windfalls_table(ctx: dict) -> tuple[list[str], list[list]]:
    p, (n1, n2) = ctx['plan'], ctx['names']
    who = {'Parent 1': n1, 'Parent 2': n2, 'Both': 'Both'}
    return (['Gift / inheritance', 'Year', "Amount (today's $)", 'To', 'Kept separate'],
            [[w['name'], w['year'], w['amount'], who.get(w['recipient'], w['recipient']), 'yes' if w['separate'] and w['recipient'] != 'Both' else 'no']
             for w in p.get('windfalls') or []])
