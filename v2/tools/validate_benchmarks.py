"""Benchmark the v2 engine against published figures. Usage: python tools/validate_benchmarks.py v2   (prints JSON)"""
import copy, json, sys
V2 = sys.argv[1]
sys.path[:0] = [V2, V2 + '/engine']
import numpy as np
from finplan import reference as R
from finplan.plan import normalize_plan
from finplan.engine import project, monte_carlo, rmd_divisor, rmd_age, _hist
from finplan import engine as E
from finplan import taxes as TX
from finplan.mortgage import monthly_payment
from finplan import backtest as BT

out = []
def chk(area, what, app, ref, tol, src, note=''):
    dev = (app - ref) / ref if ref else 0.0
    ok = abs(dev) <= tol
    out.append({'area': area, 'check': what, 'app': round(float(app), 2), 'benchmark': round(float(ref), 2), 'dev_pct': round(float(dev) * 100, 1),
                'ok': bool(ok), 'source': src, 'note': note})

# ── 1. Federal tax & FICA, 2026 (IRS Rev. Proc. 2025-32; SSA 2026 wage base $184,500) ──────────────
def irs2026_mfj(taxable):
    br = [(24800, .10), (100800, .12), (211400, .22), (403550, .24), (512450, .32), (768700, .35), (1e18, .37)]
    t, prev = 0.0, 0.0
    for lim, r in br:
        t += max(0, min(taxable, lim) - prev) * r; prev = lim
        if taxable <= lim: break
    return t
for wages in (100_000, 200_000, 400_000):
    tx = TX.total_taxes(np.array([wages]), np.array([0.0]), np.array([0.0]), np.array([0.0]), 0.0, 2026, 0.03, 'Texas')
    chk('Federal tax', f'MFJ, ${wages:,} wages, 2026 federal income tax', float(tx['federal'][0]), irs2026_mfj(wages - 32200), 0.03, 'IRS Rev. Proc. 2025-32')
for w1, w2 in ((200_000, 0), (200_000, 200_000)):
    tx = TX.total_taxes(np.array([float(w1)]), np.array([float(w2)]), np.array([0.0]), np.array([0.0]), 0.0, 2026, 0.03, 'Texas')
    ref = sum(min(w, 184500) * 0.062 + w * 0.0145 for w in (w1, w2)) + max(w1 + w2 - 250000, 0) * 0.009
    chk('FICA', f'FICA, wages {w1:,} + {w2:,}', float(tx['fica'][0]), ref, 0.01, 'SSA 2026 wage base; IRS Additional Medicare Tax (joint threshold)')

# ── 2. State income tax (Tax Foundation 2025 / state DORs) ─────────────────────────────────────
# California 2025 MFJ: FTB rate schedule (1%..9.3% to $721,318), std deduction $11,080, 2 x $149 exemption credits
def ca_2025_mfj(taxable):
    br = [(21512, .01), (50998, .02), (80490, .04), (111732, .06), (141732, .08), (721318, .093)]
    t, prev = 0.0, 0.0
    for lim, r in br:
        t += max(0, min(taxable, lim) - prev) * r; prev = lim
    return t - 298
for loc, w, ref, src in (('California', 200000, ca_2025_mfj(200000 - 11080), 'CA FTB 2025 schedule, by hand'),
                         ('Oregon', 150000, 418 + 0.0675 * 13300 + 0.0875 * (150000 - 5600 - 22100) - 500, 'OR DOR 2025 brackets, by hand'),
                         ('Colorado', 150000, (150000 - 32200) * 0.044, 'CO: 4.4% of federal taxable income')):
    tx = TX.total_taxes(np.array([float(w)]), np.array([0.0]), np.array([0.0]), np.array([0.0]), 0.0, 2026, 0.03, loc)
    chk('State tax', f'{loc} MFJ, ${w:,} wages, state income tax', float(tx['state'][0]), ref, 0.05, src)

# ── 3. Mortgage payment (standard amortization) ───────────────────────────────────────────────
chk('Mortgage', '$800k, 6.5%, 30 yr monthly P&I', monthly_payment(800000, 0.065, 30), 5056.54, 0.001, 'Amortization formula')

# ── 4. RMDs (IRS Uniform Lifetime Table, SECURE 2.0) ──────────────────────────────────────────
for age, d in ((73, 26.5), (75, 24.6), (80, 20.2), (90, 12.2)):
    chk('RMD', f'Uniform Lifetime divisor at {age}', rmd_divisor(age), d, 0.0001, 'IRS Pub. 590-B Table III')
chk('RMD', 'RMD start age, born 1955', rmd_age(1955), 73, 0, 'SECURE 2.0')
chk('RMD', 'RMD start age, born 1962', rmd_age(1962), 75, 0, 'SECURE 2.0')

# ── 5. Social Security claiming (SSA: FRA 67; 62 = 70%, 70 = 124%) ────────────────────────────
def ss_factor(claim):
    p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 60, 'parentX_retirement_age': 60,
                        'parentX_ss_benefit': 2000, 'parentX_ss_claim_age': claim, 'ss_insolvency_enabled': False,
                        'parentX_career_phases': [], 'parentX_income': 0, 'parentX_net_worth': 5e6, 'ss_cola': False,
                        'economic_params': {'inflation_rate': 0.0}})
    rows = project(p)['rows']
    r = next(r for r in rows if r['age1'] == 71)
    return r['ss1'] / (2000 * 12)
for claim, ref in ((62, 0.70), (67, 1.00), (70, 1.24)):
    chk('Social Security', f'Benefit factor claiming at {claim} (FRA 67)', ss_factor(claim), ref, 0.005, 'SSA benefit reduction / delayed credits')
d = normalize_plan({})
chk('Social Security', 'Default shortfall after depletion (%)', d['ss_shortfall_percentage'], 17, 0.10,
    '2026 Trustees Report: combined funds 2034, 83% payable (OASI alone 2032, 78%)', 'default may be harsher than the Trustees')
chk('Social Security', 'Default depletion year', d['ss_insolvency_year'], 2034, 0, '2026 Trustees Report (combined OASDI)')

# ── 6. Historical returns data (Damodaran S&P 500 incl. dividends, 1928-2024) ─────────────────
H = np.array(_hist())
geo = np.prod(1 + H) ** (1 / len(H)) - 1
chk('Market data', 'S&P 500 arithmetic mean annual return', H.mean(), 0.1179, 0.05, 'Damodaran 1928-2024 (11.79%)')
chk('Market data', 'S&P 500 geometric mean annual return', geo, 0.0994, 0.05, 'Damodaran 1928-2024 (9.94%)')
chk('Market data', 'S&P 500 standard deviation', H.std(ddof=1), 0.195, 0.08, 'Damodaran 1928-2024 (~19.5%)')

# ── 7. 4% rule: every historical 30-year start ────────────────────────────────────────────────
def four_pct(stock, rate=0.04):
    p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 65, 'parentX_retirement_age': 65,
                        'parentX_death_age': 94, 'parentX_net_worth': 1_000_000, 'parentX_income': 0, 'parentX_career_phases': [],
                        'parentX_ss_benefit': 0, 'mc_stock_allocation': stock, 'bond_return': 0.04,
                        'parentX_expenses': {'Other Personal': 1_000_000 * rate}, 'family_shared_expenses': {},
                        'houses': [], 'children_list': [], 'capital_gains_enabled': False, 'auto_health_coverage': False,
                        'medicare_part_b_premium': 0, 'medicare_part_d_premium': 0, 'medigap_premium': 0,
                        'irmaa_enabled': False, 'state_timeline': [{'year': 2026, 'state': 'Texas', 'spending_strategy': 'Average'}],
                        'economic_params': {'investment_return': 0.06, 'inflation_rate': 0.03}})
    return BT.run(p)['success_rate'], p
for stock, ref in ((100, 0.95), (75, 0.95), (50, 0.95)):
    sr, _ = four_pct(stock)
    chk('4% rule', f'4% withdrawal, 30 yrs, {stock}% stocks, every historical start', sr, ref, 0.06,
        'Trinity study (1926-95, 4% @ 50/50 = 95%); cFIREsim/FIRECalc ~95%+ for 75/25',
        'app: bonds are a fixed 4%, inflation is the plan rate (not historical CPI)')

# ── 8. Kids & college ─────────────────────────────────────────────────────────────────────────
child = {'name': 'K', 'template_state': 'Seattle', 'template_strategy': 'Average', 'school_type': 'Public',
         'college_type': 'Public', 'college_location': 'Ohio', 'use_template': True}   # college at a near-national-average location
tot0_17 = sum(sum(R.child_expenses_for_age(child, a).values()) for a in range(18)) * 1.03 ** 2
chk('Kids', 'Seattle "Average" child, birth to 17 (2026 $)', tot0_17, 319000, 0.25,
    'USDA middle-income (2015 child, $233,610) inflated to 2025: ~$319k national; Seattle costs ~15-25% above',
    'national benchmark; Seattle should be higher')
col_pub = sum(R.child_expenses_for_age(child, 18).values()) * 1.03 ** 2
chk('College', 'Public in-state college + student costs, one year (2026 $)', col_pub, 29910 * 1.0609, 0.20,
    'College Board 2024-25 full student budget, public in-state on campus ($29,910), inflated to 2026')
child_p = {**child, 'college_type': 'Private'}
col_pri = sum(R.child_expenses_for_age(child_p, 18).values()) * 1.03 ** 2
chk('College', 'Private college + student costs, one year (2026 $)', col_pri, 62990 * 1.0609, 0.20,
    'College Board 2024-25 full student budget, private nonprofit ($62,990), inflated to 2026')

# ── 9. Retiree healthcare (Fidelity 2025: $172,500 per 65-year-old, lifetime) ──────────────────
p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 65, 'parentX_retirement_age': 65,
                    'parentX_death_age': 87, 'parentX_net_worth': 5e6, 'parentX_income': 0, 'parentX_career_phases': [],
                    'state_timeline': [{'year': 2026, 'state': 'Texas', 'spending_strategy': 'Average'}]})
rows = project(p)['rows']
hc_today = sum(r['exp_healthcare'] / r['infl_index'] for r in rows)
hc_nom = sum(r['exp_healthcare'] for r in rows)
chk('Healthcare', 'Lifetime retiree healthcare, single, 65 to 87, nominal $', hc_nom, 172500, 0.30,
    'Fidelity 2025 Retiree Health Care Cost Estimate ($172,500, includes Medicare premiums and out-of-pocket)',
    f"default plan; today's dollars = ${hc_today:,.0f}; app counts premiums + entered out-of-pocket only")

# ── 10. Household spending (BLS CE 2024: $78,535 average annual expenditures) ─────────────────
d = normalize_plan({'parent1_name': 'A', 'parent2_name': 'B'})
everyday = sum(d['parentX_expenses'].values()) + sum(d['parentY_expenses'].values()) + sum(d['family_shared_expenses'].values())
chk('Spending', 'Default two-adult household budget, Seattle "Average" (template year $)', everyday, 78535 * 1.20, 0.35,
    'BLS CE 2024 average household ($78,535; 2.5 people) x ~1.2 Seattle price level (BEA RPP)',
    'default template is the v0.8 Seattle Average')

# ── 11. Monte Carlo sanity: zero cash flows grow at the expected rate ─────────────────────────
p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 40, 'parentX_retirement_age': 99, 'parentX_death_age': 70,
                    'parentX_net_worth': 100000, 'parentX_income': 0, 'parentX_career_phases': [], 'parentX_expenses': {},
                    'family_shared_expenses': {}, 'auto_health_coverage': False, 'parentX_ss_benefit': 0,
                    'capital_gains_enabled': False, 'medicare_part_b_premium': 0, 'medicare_part_d_premium': 0, 'medigap_premium': 0,
                    'economic_params': {'investment_return': 0.06, 'inflation_rate': 0.03}})
rows = project(p)['rows']
chk('Math', '$100k at 6% for 30 years (deterministic)', rows[29]['investable'], 100000 * 1.06 ** 30, 0.001, 'Compound interest')
mc = monte_carlo({**p, 'mc_use_asymmetric': False}, 4000, seed=1)
med = np.median(np.array(mc['net_worth']['50'])[29]) if isinstance(mc['net_worth']['50'], list) else None
ref_med = 100000 * np.exp(30 * (np.log(1.06) - 0.15 ** 2 / (2 * 1.06 ** 2)))
chk('Math', 'MC median after 30 yrs, 6% mean, 15% sd (lognormal approx.)', float(mc['net_worth']['50'][29]), ref_med, 0.05,
    'Volatility drag: median = exp(n(ln(1+m) - s^2/2(1+m)^2))')

print(json.dumps(out, indent=1))
