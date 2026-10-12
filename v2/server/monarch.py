"""Monarch Money transactions CSV -> yearly actuals (plan vs actual).

Monarch's export (Transactions -> Download CSV) has the columns
    Date, Merchant, Category, Account, Original Statement, Notes, Amount, Tags
with spending as negative amounts. Transactions are summed per calendar year and Monarch category, then mapped onto
the plan's categories. Personal categories are split evenly between the two adults (Monarch doesn't say whose they
are); a household's own mapping (household key 'monarch_map') overrides the built-in one. Importing the same file
again replaces those categories instead of adding to them.
"""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime

# Monarch default category -> (actuals group, plan category). group: personal | family | children | skip | income | taxes
DEFAULT_MAP = {
    'Groceries': ('personal', 'Groceries'), 'Restaurants & Bars': ('personal', 'Dining Out'),
    'Coffee Shops': ('personal', 'Coffee Shops'), 'Auto Payment': ('personal', 'Auto Payment'),
    'Gas': ('personal', 'Gas & Fuel'), 'Auto Maintenance': ('personal', 'Auto Maintenance'),
    'Parking & Tolls': ('personal', 'Parking & Tolls'), 'Public Transit': ('personal', 'Public Transit'),
    'Taxi & Ride Shares': ('personal', 'Ride Shares'), 'Clothing': ('personal', 'Clothing'),
    'Personal': ('personal', 'Personal Care'), 'Medical': ('personal', 'Medical'), 'Dentist': ('personal', 'Dental'),
    'Fitness': ('personal', 'Fitness'), 'Entertainment & Recreation': ('personal', 'Entertainment'),
    'Phone': ('personal', 'Phone'), 'Shopping': ('personal', 'Other Personal'), 'Electronics': ('personal', 'Other Personal'),
    'Fun Money': ('personal', 'Hobbies'), 'Miscellaneous': ('personal', 'Other Personal'),
    'Mortgage': ('family', 'Mortgage/Rent'), 'Rent': ('family', 'Mortgage/Rent'),
    'Home Improvement': ('family', 'Home Improvement'), 'Furniture & Housewares': ('family', 'Home Improvement'),
    'Gas & Electric': ('family', 'Gas & Electric'), 'Water': ('family', 'Water'), 'Garbage': ('family', 'Garbage'),
    'Internet & Cable': ('family', 'Internet & Cable'), 'Travel & Vacation': ('family', 'Family Vacations'),
    'Pets': ('family', 'Pet Care'), 'Gift': ('family', 'Other Family Expenses'), 'Charity': ('family', 'Other Family Expenses'),
    'Insurance': ('family', 'Other Family Expenses'), 'Financial & Legal Services': ('family', 'Other Family Expenses'),
    'Financial Fees': ('family', 'Other Family Expenses'), 'Cash & ATM': ('personal', 'Other Personal'),
    'Check': ('family', 'Other Family Expenses'),
    'Child Care': ('children', 'Child care'), 'Child Activities': ('children', 'Activities'), 'Education': ('children', 'Education'),
    'Taxes': ('taxes', ''),
    'Paychecks': ('income', ''), 'Interest': ('income', ''), 'Business Income': ('income', ''), 'Other Income': ('income', ''),
    'Dividends & Capital Gains': ('income', ''),
    'Transfer': ('skip', ''), 'Credit Card Payment': ('skip', ''), 'Balance Adjustments': ('skip', ''),
    'Loan Repayment': ('skip', ''), 'Student Loans': ('skip', ''), 'Buy': ('skip', ''), 'Sell': ('skip', ''),
}
UNMAPPED = ('family', 'Other Family Expenses')


def _amount(s: str) -> float:
    s = (s or '').replace('$', '').replace(',', '').strip()
    neg = s.startswith('(') and s.endswith(')')
    v = float(s.strip('()') or 0)
    return -v if neg else v


def _year(s: str) -> int:
    s = (s or '').strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d'):
        try:
            return datetime.strptime(s, fmt).year
        except ValueError:
            pass
    raise ValueError(f'unrecognized date {s!r}')


def parse(raw: bytes | str, plan: dict, custom_map: dict | None = None) -> dict:
    text = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw
    rd = csv.DictReader(io.StringIO(text))
    cols = {c.strip().lower(): c for c in (rd.fieldnames or [])}
    need = ('date', 'category', 'amount')
    if not all(k in cols for k in need):
        raise ValueError('This does not look like a Monarch transactions export (needs Date, Category and Amount columns)')
    mapping = {**DEFAULT_MAP, **{k: tuple(v) for k, v in (custom_map or {}).items()}}
    single = plan.get('parent2_name') in (None, '', 'N/A')
    sums: dict = defaultdict(lambda: defaultdict(float))       # (year) -> (group, cat) -> spending
    income, taxes = defaultdict(float), defaultdict(float)
    unmapped, skipped, n = defaultdict(float), 0, 0
    for row in rd:
        try:
            y, amt = _year(row[cols['date']]), _amount(row[cols['amount']])
        except (ValueError, KeyError):
            continue
        cat = (row[cols['category']] or '').strip()
        group, pc = mapping.get(cat, (None, None))
        n += 1
        if group == 'skip':
            skipped += 1
            continue
        if group == 'income':
            income[y] += amt
            continue
        if group == 'taxes':
            taxes[y] += -amt
            continue
        if group is None:
            unmapped[cat or '(no category)'] += -amt
            group, pc = UNMAPPED
        sums[y][(group, pc)] += -amt                            # spending is negative in Monarch; refunds reduce it
    out = {}
    for y, cats in sums.items():
        exp: dict = {'parentX': {}, 'parentY': {}, 'family': {}, 'children': {}}
        for (group, pc), v in cats.items():
            v = round(v, 2)
            if group == 'personal':
                if single:
                    exp['parentX'][pc] = exp['parentX'].get(pc, 0.0) + v
                else:
                    exp['parentX'][pc] = exp['parentX'].get(pc, 0.0) + v / 2
                    exp['parentY'][pc] = exp['parentY'].get(pc, 0.0) + v / 2
            elif group == 'children':
                kids = exp['children'].setdefault('All children (Monarch)', {})
                kids[pc] = kids.get(pc, 0.0) + v
            else:
                exp['family'][pc] = exp['family'].get(pc, 0.0) + v
        if exp['children']:
            k = exp['children']['All children (Monarch)']
            k['Total'] = sum(x for kk, x in k.items() if kk != 'Total')
        out[str(y)] = {'expenses': {g: v for g, v in exp.items() if v}, 'source': 'Monarch CSV'}
        if taxes.get(y):
            out[str(y)]['taxes_paid'] = round(taxes[y], 2)
    return {'years': out, 'transactions': n, 'skipped_transfers': skipped,
            'income_seen': {str(y): round(v, 2) for y, v in income.items()},
            'unmapped': {k: round(v, 2) for k, v in sorted(unmapped.items(), key=lambda kv: -abs(kv[1]))}}
