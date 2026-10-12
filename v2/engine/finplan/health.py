"""Plan score: a short checklist of the habits financial planners check first, each rated good / ok / bad, rolled
up into a 0-100 score (the Boldin "Planner Score" / RightCapital snapshot idea, from this plan's own numbers).

Thresholds are common rules of thumb, not advice:
  - success: chance the money lasts (Monte Carlo) >= 85% good, >= 70% ok
  - emergency fund: cash/taxable savings >= 6 months of spending good, >= 3 ok
  - savings rate while working: >= 15% of gross income good, >= 5% ok
  - housing cost: <= 28% of gross income good, <= 36% ok (the lender "28/36" ratios)
  - withdrawal rate in the first retirement year: <= 4% good, <= 5% ok
  - college: 529 balance on track for kids under 18 (info only when no kids)
  - consumer debt: none good
  - health coverage before 65: entered plans good, automatic estimate ok, none bad
"""
from __future__ import annotations

WEIGHTS = {'success': 30, 'emergency': 10, 'savings_rate': 15, 'housing': 10, 'withdrawal': 15, 'college': 5,
           'debt': 5, 'health': 10}
POINTS = {'good': 1.0, 'ok': 0.6, 'bad': 0.0}


def _grade(v, good, ok, higher_is_better=True):
    if higher_is_better:
        return 'good' if v >= good else 'ok' if v >= ok else 'bad'
    return 'good' if v <= good else 'ok' if v <= ok else 'bad'


def plan_health(p: dict, proj: dict, mc: dict | None) -> dict:
    rows, s = proj['rows'], proj['summary']
    r0 = rows[0]
    items = []

    def add(id_, label, status, value, detail, to):
        items.append({'id': id_, 'label': label, 'status': status, 'value': value, 'detail': detail, 'to': to,
                      'weight': WEIGHTS[id_]})

    if mc is not None:
        sr = mc['success_rate']
        add('success', 'Chance your money lasts', _grade(sr, 0.85, 0.70), f'{sr * 100:.0f}%',
            'Share of market simulations where savings never run out. 85% or more is a common bar.', '/projections')

    spend = max(r0['total_expenses'], 1.0)
    months = max(r0['liquid'], 0.0) / (spend / 12)
    add('emergency', 'Emergency fund', _grade(months, 6, 3), f'{months:.0f} months',
        'Cash and taxable savings you could reach quickly, in months of this year\'s spending (aim for 6+).', '/people')

    working = [r for r in rows if r['wages1'] + r['wages2'] > 0][:5]
    if working:
        gross = sum(r['wages1'] + r['wages2'] for r in working)
        saved = sum(r['cashflow'] + r['contrib_pretax'] + r.get('contrib_roth', 0.0) for r in working)
        rate = saved / gross if gross else 0.0
        add('savings_rate', 'Savings rate (next 5 working years)', _grade(rate, 0.15, 0.05), f'{rate * 100:.0f}%',
            'Money left over plus 401(k)/Roth contributions, as a share of gross pay. 15%+ is a common target.', '/spending')
        # owned homes are in exp_housing (incl. mortgage payments); rent is the household budget's Mortgage/Rent line in
        # years without an owned home (skipped automatically once a home is owned)
        rent = (p.get('family_shared_expenses') or {}).get('Mortgage/Rent', 0.0)
        housing = sum(r['exp_housing'] +
                      (rent * r['infl_index'] * r.get('col_factor', 1.0) if r['exp_housing'] == 0 else 0.0)
                      for r in working) / max(gross, 1)
        add('housing', 'Housing cost', _grade(housing, 0.28, 0.36, False), f'{housing * 100:.0f}% of pay',
            'Mortgage, property tax, insurance, upkeep (and rent) as a share of gross pay. Lenders like 28% or less.', '/homes')

    ret_year = s.get('retirement_year')
    ret = next((r for r in rows if r['year'] == ret_year), None)
    if ret is not None and ret['investable'] > 0:
        need = max(ret['total_expenses'] + ret['taxes'] - ret['ss_income'] - ret.get('pension_income', 0.0)
                   - ret['rent_income'], 0.0)
        wr = need / ret['investable']
        add('withdrawal', f'Withdrawal rate at retirement ({ret_year})', _grade(wr, 0.04, 0.05, False), f'{wr * 100:.1f}%',
            'Spending not covered by Social Security, pensions or rent, as a share of savings. About 4% is the classic safe rate.', '/retirement')

    kids = [c for c in p.get('children_list') or [] if p['current_year'] - c['birth_year'] < 18]
    if kids:
        bal = sum(e.get('balance', 0.0) for e in p.get('college_529') or [])
        monthly = sum(e.get('monthly', 0.0) for e in p.get('college_529') or [])
        status = 'good' if monthly > 0 or bal > 0 else 'ok'
        add('college', 'College savings', status, f'{len(kids)} kid{"s" if len(kids) > 1 else ""} · ${bal:,.0f} in 529s',
            'Saving in a 529 plan for each child. Nothing saved yet is fine if college is paid from general savings.', '/kids')

    debt = r0.get('debt_balance', 0.0) + r0.get('consumer_debt', 0.0)
    add('debt', 'Consumer debt', 'good' if debt <= 0 else 'ok' if debt < 0.1 * max(r0['total_income'], 1) else 'bad',
        f'${debt:,.0f}', 'Car loans, student loans and cards (mortgages excluded).', '/spending')

    if p.get('health_insurances'):
        add('health', 'Health coverage before 65', 'good', 'Entered', 'Your own health plans are in the plan.', '/healthcare')
    elif p.get('auto_health_coverage', True):
        add('health', 'Health coverage before 65', 'ok', 'Estimated',
            'Using average employer and marketplace premiums. Enter your real plans for exact numbers.', '/healthcare')
    else:
        add('health', 'Health coverage before 65', 'bad', 'Missing',
            'No health insurance before Medicare: costs are understated, especially in early retirement.', '/healthcare')

    tot = sum(i['weight'] for i in items)
    score = round(100 * sum(i['weight'] * POINTS[i['status']] for i in items) / tot) if tot else 0
    grade = 'Strong' if score >= 85 else 'Solid' if score >= 70 else 'Needs work' if score >= 50 else 'At risk'
    return {'score': score, 'grade': grade, 'items': items}
