"""Excel tracking workbook (v0.8 layout, extended): export plan vs blank actuals, import filled actuals."""
from __future__ import annotations

import io
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from finplan.actuals import planned_for_year

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
HEADER = PatternFill(start_color="2A78D6", end_color="2A78D6", fill_type="solid")
MONTH_H = PatternFill(start_color="EB6834", end_color="EB6834", fill_type="solid")
PLAN = PatternFill(start_color="E8F1FC", end_color="E8F1FC", fill_type="solid")
ACTUAL = PatternFill(start_color="FFF6D5", end_color="FFF6D5", fill_type="solid")
CUR = '"$"#,##0'
PCT = '0.0%'

# section title -> (actuals group key, subkey-or-None)
def _sections(plan: dict, planned: dict):
    n1 = plan.get('parent1_name', 'Person 1')
    n2 = plan.get('parent2_name', 'Person 2')
    e = planned['expenses']
    yield f"{n1} — Individual", 'parentX', None, e['parentX']
    if n2 not in ('N/A', '') and sum(e['parentY'].values()) > 0:
        yield f"{n2} — Individual", 'parentY', None, e['parentY']
    yield "Family Shared", 'family', None, e['family']
    for kid, cats in e['children'].items():
        itemized = {k: v for k, v in cats.items() if k != 'Total'}
        yield f"Child — {kid}", 'children', kid, (itemized or {'Total': cats.get('Total', 0)})
    for h, cats in e['housing'].items():
        yield f"Housing — {h}", 'housing', h, cats
    yield "Healthcare", 'healthcare', None, e['healthcare'] or {'insurance_premiums': 0, 'out_of_pocket': 0}
    if e['recurring']:
        yield "Recurring", 'recurring', None, e['recurring']


def build(plan: dict, start: int, end: int, actuals: dict | None = None) -> bytes:
    actuals = actuals or {}
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    lines = [("Financial Planning Suite — tracking workbook", True),
             (f"Generated {datetime.now():%Y-%m-%d} for {plan.get('parent1_name', '')}"
              + (f" & {plan.get('parent2_name')}" if plan.get('parent2_name') not in ('N/A', '') else ''), False), ("", False),
             ("Blue cells are the plan. Yellow cells are for you to fill in.", False),
             ("Expenses_<year> sheets: enter monthly amounts; the Annual Actual column sums them.", False),
             ("Summary sheet: enter year-end net worth, income and spending.", False),
             ("When done, import this file on the Actuals page. Existing actuals are merged, never erased.", False)]
    for i, (t, b) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=t).font = Font(bold=b, size=14 if b else 11)
    ws.column_dimensions['A'].width = 90

    s = wb.create_sheet("Summary")
    hdr = ['Year', 'Net Worth (Plan)', 'Net Worth (Actual)', 'Income (Plan)', 'Income (Actual)',
           'Spending (Plan)', 'Spending (Actual)', 'Cash Flow (Plan)', 'Cash Flow (Actual)']
    for c, h in enumerate(hdr, 1):
        cell = s.cell(row=1, column=c, value=h); cell.fill = HEADER; cell.font = Font(bold=True, color="FFFFFF")
        s.column_dimensions[get_column_letter(c)].width = 18
    for r, year in enumerate(range(start, end + 1), 2):
        pl = planned_for_year(plan, year)
        a = actuals.get(str(year), {})
        t = pl['totals']
        s.cell(row=r, column=1, value=year)
        vals = [(t.get('net_worth'), a.get('net_worth')), (t.get('income'), (a.get('income') or {}).get('total')),
                (t.get('spending'), a.get('total_spending')), ((t.get('income') or 0) - (t.get('spending') or 0) - (t.get('taxes') or 0) if t else None, None)]
        for k, (pv, av) in enumerate(vals):
            pc = s.cell(row=r, column=2 + 2 * k, value=round(pv) if pv is not None else None); pc.fill = PLAN; pc.number_format = CUR
            ac = s.cell(row=r, column=3 + 2 * k, value=av); ac.fill = ACTUAL; ac.number_format = CUR
        s.cell(row=r, column=9).value = f"=IF(E{r}=\"\",\"\",E{r}-G{r})"
    s.freeze_panes = 'B2'

    for year in range(start, end + 1):
        pl = planned_for_year(plan, year)
        ws = wb.create_sheet(f"Expenses_{year}")
        headers = ['Category', 'Monthly Plan'] + MONTHS + ['Annual Plan', 'Annual Actual', 'Variance', 'Variance %']
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=c, value=h)
            cell.fill = MONTH_H if 3 <= c <= 14 else HEADER
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center')
        row = 2
        for title, group, sub, cats in _sections(plan, pl):
            ws.cell(row=row, column=1, value=title).font = Font(bold=True, size=12)
            row += 1
            for cat, annual in cats.items():
                ws.cell(row=row, column=1, value=cat)
                c = ws.cell(row=row, column=2, value=round((annual or 0) / 12)); c.fill = PLAN; c.number_format = CUR
                for m in range(3, 15):
                    mc = ws.cell(row=row, column=m); mc.fill = ACTUAL; mc.number_format = CUR
                c = ws.cell(row=row, column=15, value=round(annual or 0)); c.fill = PLAN; c.number_format = CUR
                c = ws.cell(row=row, column=16, value=f"=SUM(C{row}:N{row})"); c.fill = ACTUAL; c.number_format = CUR
                c = ws.cell(row=row, column=17, value=f"=P{row}-O{row}"); c.number_format = CUR
                c = ws.cell(row=row, column=18, value=f"=IF(O{row}<>0,Q{row}/O{row},\"\")"); c.number_format = PCT
                row += 1
            row += 1
        ws.column_dimensions['A'].width = 28
        ws.column_dimensions['B'].width = 14
        for c in range(3, 19):
            ws.column_dimensions[get_column_letter(c)].width = 12
        ws.freeze_panes = 'C2'
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def parse(data: bytes, plan: dict) -> dict:
    """Return {year: partial actuals} from a filled workbook. Sums month cells itself
    (formulas are not recalculated unless the file was saved by Excel)."""
    wb = load_workbook(io.BytesIO(data), data_only=True)
    n1 = str(plan.get('parent1_name', '')).lower()
    out: dict = {}
    for name in wb.sheetnames:
        if not name.startswith('Expenses_'):
            continue
        year = name.split('_', 1)[1]
        ws = wb[name]
        exp: dict = {}
        group = sub = None
        for r in ws.iter_rows(min_row=2, max_col=16):
            cat = r[0].value
            if cat is None:
                continue
            if r[0].font is not None and r[0].font.bold:
                t = str(cat)
                tl = t.lower()
                sub = None
                if 'individual' in tl:
                    group = 'parentX' if tl.startswith(n1) and n1 else ('parentY' if 'parentX' in exp else 'parentX')
                elif tl.startswith('family'):
                    group = 'family'
                elif tl.startswith('child —') or tl.startswith('child -'):
                    group, sub = 'children_cat', t.split('—', 1)[-1].strip() if '—' in t else t.split('-', 1)[-1].strip()
                elif tl.startswith('children'):
                    group = 'children'
                elif tl.startswith('housing'):
                    group, sub = 'housing', t.split('—', 1)[-1].strip()
                elif tl.startswith('healthcare'):
                    group = 'healthcare'
                elif tl.startswith('recurring'):
                    group = 'recurring'
                else:
                    group = None
                continue
            if not group:
                continue
            months = [c.value for c in r[2:14]]
            nums = [float(v) for v in months if isinstance(v, (int, float))]
            total = sum(nums) if nums else (r[15].value if isinstance(r[15].value, (int, float)) else None)
            if total is None:
                continue
            if group == 'children_cat':
                exp.setdefault('children', {}).setdefault(sub, {})[str(cat)] = float(total)
                continue
            g = exp.setdefault(group, {})
            if group == 'children':
                g[str(cat)] = {'Total': float(total)}
            elif group == 'housing':
                g.setdefault(sub, {})[str(cat)] = float(total)
            else:
                g[str(cat)] = float(total)
        if exp:
            out.setdefault(year, {})['expenses'] = exp
    if 'Summary' in wb.sheetnames:
        for r in wb['Summary'].iter_rows(min_row=2, max_col=9, values_only=True):
            if r[0] is None:
                continue
            y = str(int(r[0])) if isinstance(r[0], (int, float)) else str(r[0])
            if isinstance(r[2], (int, float)):
                out.setdefault(y, {})['net_worth'] = float(r[2])
            if isinstance(r[4], (int, float)):
                out.setdefault(y, {}).setdefault('income', {})['total'] = float(r[4])
            if isinstance(r[6], (int, float)):
                out.setdefault(y, {})['total_spending'] = float(r[6])
    return out


def merge(actuals: dict, parsed: dict, who: str) -> dict:
    """Deep-merge parsed workbook values into existing actuals (never erase)."""
    for y, v in parsed.items():
        cur = actuals.setdefault(y, {})
        for k, val in v.items():
            if isinstance(val, dict):
                tgt = cur.setdefault(k, {})
                for g, gv in val.items():
                    if isinstance(gv, dict) and isinstance(tgt.get(g), dict):
                        tgt[g].update(gv)
                    else:
                        tgt[g] = gv
            else:
                cur[k] = val
        cur['entered_at'] = datetime.now().isoformat()
        cur['entered_by'] = who
    return actuals
