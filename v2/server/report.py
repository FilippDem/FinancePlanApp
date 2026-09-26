"""PDF plan report (reportlab + matplotlib)."""
from __future__ import annotations

import io
from datetime import date

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether  # noqa: E402

from finplan.engine import project, monte_carlo  # noqa: E402
from finplan.plan import normalize_plan, is_single  # noqa: E402

S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
INK, MUTED, GRID = '#111318', '#80838c', '#e8e8e5'


def _m(v):
    if v is None:
        return '—'
    a = abs(v); s = '-' if v < 0 else ''
    if a >= 1e6:
        return f"{s}${a / 1e6:.2f}M"
    if a >= 1e4:
        return f"{s}${a / 1e3:.0f}k"
    return f"{s}${a:,.0f}"


def _axis(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _m(v)))
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)


def _img(fig, w=7.0, h=3.0):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=w * inch, height=h * inch)


def build(plan: dict, household: str, checkins: list | None = None) -> bytes:
    p = normalize_plan(plan)
    pr = project(p)
    mc = monte_carlo(p, 1000, seed=3, normalized=False)
    rows, s = pr['rows'], pr['summary']
    idx = [r['infl_index'] for r in rows]
    years = [r['year'] for r in rows]
    single = is_single(p)
    names = p['parent1_name'] + ('' if single else f" & {p['parent2_name']}")
    ret = next((r for r in rows if r['year'] == s['retirement_year']), rows[-1])

    ss = getSampleStyleSheet()
    H1 = ParagraphStyle('h1', parent=ss['Title'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor(INK), alignment=0, spaceAfter=4)
    H2 = ParagraphStyle('h2', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor(INK), spaceBefore=12, spaceAfter=6)
    B = ParagraphStyle('b', parent=ss['BodyText'], fontSize=9.5, leading=13, textColor=colors.HexColor('#333333'))
    Mu = ParagraphStyle('mu', parent=B, textColor=colors.HexColor(MUTED), fontSize=8.5)
    story = [Paragraph(f"Financial plan — {household}", H1),
             Paragraph(f"{names} · prepared {date.today():%B %d, %Y} · amounts in today's dollars unless noted", Mu), Spacer(1, 10)]

    kpis = [('Net worth today', _m(s['net_worth_now'])), (f"At retirement ({s['retirement_year']})", _m(ret['net_worth'] / ret['infl_index'])),
            ('Plan success', f"{mc['success_rate'] * 100:.0f}%"), ('Expected path: savings last', f"until {s['depletion_year']}" if s['depletion_year'] else 'for life')]
    t = Table([[Paragraph(f"<font size=8 color='{MUTED}'>{k}</font><br/><font size=15><b>{v}</b></font>", B) for k, v in kpis]],
              colWidths=[1.75 * inch] * 4)
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor(GRID)), ('INNERGRID', (0, 0), (-1, -1), 0.6, colors.HexColor(GRID)),
                           ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    story += [t, Spacer(1, 6)]

    # net worth chart with MC band
    fig, ax = plt.subplots(figsize=(8, 3.2))
    p10 = [v / i for v, i in zip(mc['net_worth']['10'], idx)]
    p90 = [v / i for v, i in zip(mc['net_worth']['90'], idx)]
    p25 = [v / i for v, i in zip(mc['net_worth']['25'], idx)]
    p75 = [v / i for v, i in zip(mc['net_worth']['75'], idx)]
    med = [v / i for v, i in zip(mc['net_worth']['50'], idx)]
    ax.fill_between(years, p10, p90, color=S[0], alpha=0.10, linewidth=0, label='10th–90th percentile')
    ax.fill_between(years, p25, p75, color=S[0], alpha=0.20, linewidth=0, label='25th–75th percentile')
    ax.plot(years, med, color=S[0], linewidth=2, label='Median')
    ax.plot(years, [r['net_worth'] / r['infl_index'] for r in rows], color=S[1], linewidth=1.6, label='Expected path')
    ax.axhline(0, color=MUTED, linewidth=0.8)
    exp_path = [r['net_worth'] / r['infl_index'] for r in rows]
    top = max(max(p75), max(exp_path), 1.0) * 1.25
    bot = min(min(p25), min(exp_path), 0.0)
    ax.set_ylim(bot - 0.05 * top if bot < 0 else 0, top)
    marks = [(s['retirement_year1'], p['parent1_name'])] + ([] if single else [(s['retirement_year2'], p['parent2_name'])])
    if len(marks) == 2 and abs(marks[0][0] - marks[1][0]) <= 4:
        marks = [(min(m[0] for m in marks), 'Both retire')]
    for y, who in marks:
        ax.axvline(y, color=MUTED, linewidth=0.8, alpha=0.6)
        ax.text(y + 0.5, top * 0.97, (who if who == 'Both retire' else f"{who} retires"), fontsize=7, color=MUTED, va='top')
    _axis(ax)
    ax.legend(frameon=False, fontsize=7.5, ncol=4, loc='upper left', bbox_to_anchor=(0, 1.13))
    story += [Paragraph('Net worth', H2), _img(fig, 7.0, 2.8)]

    # cash flow
    fig, ax = plt.subplots(figsize=(8, 3.0))
    cats = [('Living', lambda r: r['exp_person1'] + r['exp_person2'] + r['exp_family']), ('Housing', lambda r: r['exp_housing']),
            ('Children', lambda r: r['exp_children']), ('Healthcare', lambda r: r['exp_healthcare']),
            ('Recurring & one-time', lambda r: r['exp_recurring'] + r['exp_purchases'] + r['down_payment']), ('Taxes', lambda r: r['taxes'])]
    bottom = [0.0] * len(rows)
    for k, (lab, f) in enumerate(cats):
        vals = [f(r) / r['infl_index'] for r in rows]
        ax.bar(years, vals, bottom=bottom, color=S[k], width=0.8, label=lab, edgecolor='white', linewidth=0.4)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.step(years, [r['total_income'] / r['infl_index'] for r in rows], where='mid', color=INK, linewidth=1.6, label='Income')
    _axis(ax)
    ax.legend(frameon=False, fontsize=7.5, ncol=7, loc='upper left', bbox_to_anchor=(0, 1.13))
    story += [Paragraph('Income and spending', H2), _img(fig, 7.0, 2.6)]

    # assumptions
    ep = p['economic_params']
    ass = [['Investment return', f"{ep['investment_return'] * 100:.1f}%", 'Inflation', f"{ep['inflation_rate'] * 100:.1f}%"],
           ['Healthcare inflation', f"{ep['healthcare_inflation_rate'] * 100:.1f}%", 'Monte Carlo', f"{mc['n']:,} runs · {mc['mode']}"],
           ['Retirement ages', f"{p['parentX_retirement_age']}" + ('' if single else f" / {p['parentY_retirement_age']}"),
            'Plan until age', f"{p['parentX_death_age']}" + ('' if single else f" / {p['parentY_death_age']}")],
           ['Social Security cut', f"{p['ss_shortfall_percentage']:.0f}% from {p.get('ss_insolvency_year', 2034)}" if p['ss_insolvency_enabled'] else 'none',
            'Location', p['state_timeline'][0]['state']]]
    at = Table(ass, colWidths=[1.6 * inch, 1.9 * inch, 1.5 * inch, 2.0 * inch])
    at.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 8.5), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(MUTED)),
                            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor(MUTED)), ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor(GRID))]))
    story += [KeepTogether([Paragraph('Key assumptions', H2), at])]

    # homes & kids
    if p['houses']:
        hrows = [['Home', 'Ends as', 'Value', 'Mortgage', 'Rate']] + [[h['name'], h['timeline'][-1]['status'].replace('_', ' '),
                 _m(h['current_value']), _m(h['mortgage_balance']), f"{h['mortgage_rate'] * 100:.2f}%"] for h in p['houses']]
        ht = Table(hrows, colWidths=[2.4 * inch, 1.3 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch])
        ht.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 8.5), ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(MUTED)),
                                ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor(GRID)), ('ALIGN', (2, 0), (-1, -1), 'RIGHT')]))
        story += [KeepTogether([Paragraph('Homes', H2), ht])]

    story.append(Spacer(1, 6))
    story.append(Paragraph('Year by year', H2))
    story.append(Paragraph("Today's dollars. Savings = cash, investments and retirement accounts.", Mu))
    data = [['Year', 'Ages', 'Income', 'Taxes', 'Spending', 'Cash flow', 'Savings', 'Home equity', 'Net worth']]
    for r in rows:
        f = r['infl_index']
        data.append([r['year'], f"{r['age1']}" + ('' if single else f"/{r['age2']}"), _m(r['total_income'] / f), _m(r['taxes'] / f),
                     _m(r['total_expenses'] / f), _m(r['cashflow'] / f), _m(r['investable'] / f), _m(r['home_equity'] / f), _m(r['net_worth'] / f)])
    yt = Table(data, repeatRows=1, colWidths=[0.55 * inch, 0.6 * inch] + [0.83 * inch] * 7)
    style = [('FONTSIZE', (0, 0), (-1, -1), 7.5), ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(MUTED)),
             ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor(GRID)), ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
             ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5)]
    for i, r in enumerate(rows, 1):
        if r['investable'] < 0:
            style.append(('TEXTCOLOR', (6, i), (6, i), colors.HexColor('#d03b3b')))
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f7f7f5')))
    yt.setStyle(TableStyle(style))
    story.append(yt)

    if checkins:
        story += [PageBreak(), Paragraph('Check-in history', H2)]
        cd = [['Date', 'Type', 'Savings', 'Expected', 'Net worth', 'Status']]
        for c in checkins:
            cd.append([c.get('date'), c.get('kind'), _m((c.get('totals') or {}).get('investable')), _m((c.get('expected') or {}).get('investable')),
                       _m((c.get('totals') or {}).get('net_worth')), (c.get('status') or '').replace('_', ' ')])
        ct = Table(cd, colWidths=[1.0 * inch, 0.9 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.2 * inch])
        ct.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 8.5), ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(MUTED)),
                                ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor(GRID))]))
        story.append(ct)

    buf = io.BytesIO()

    def footer(canvas, doc):
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(0.6 * inch, 0.45 * inch, f"Financial Planning Suite · {household} · projections are estimates, not advice")
        canvas.drawRightString(7.9 * inch, 0.45 * inch, f"Page {doc.page}")

    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.6 * inch, bottomMargin=0.7 * inch,
                            title=f"Financial plan — {household}")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
