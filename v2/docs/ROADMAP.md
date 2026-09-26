# v2: where it stands and what to build next

_Last updated 2026-09-26 (branch `v2-react`)_

## 1. Current state

v2 now covers every v0.8 tab and adds a set of "living plan" features. See `PARITY.md` for the item-by-item list.

| Area | Status |
|---|---|
| Plan editing (people, income, career phases, spending, kids, homes, healthcare, assumptions) | ✅ live recalculation and auto-save |
| Mortgage calculator (estimate or actual loan, PMI, HOA, closing costs) | ✅ |
| Guided setup (TurboTax-style) | ✅ |
| Projections, Monte Carlo, taxes, timeline, scenarios and comparison | ✅ |
| **Check-ins**: cadence, due banner, guided and quick check-ins, on-track percentile, roll forward, .ics, **email reminders** | ✅ |
| **Actuals**: yearly plan vs actual by category, **Excel workbook** export/import | ✅ |
| **Retirement**: SS claim options, retire-age what-if, replacement ratio | ✅ |
| **Stress tests**: crash, income loss, extra cost, inflation spike, early death | ✅ |
| **Version history**: 10 recent saves plus 120 daily snapshots, with preview and restore | ✅ |
| **PDF report** | ✅ |
| Demo households re-tuned for the corrected math | ✅ |

Tests: 43 engine tests, 15 API tests, and a clean `tsc` build. The UI was checked end to end with Playwright.

## 2. What's still missing

### 2a. v0.8 features not yet ported
The data for all of these is preserved, so nothing is lost in the meantime.
- Custom named expense templates per location, custom locations, and the world map
- Guided walkthroughs on each page (the "guided mode" tooltips)
- Cash-flow "critical years" and "life stages" views, and the Sankey diagram
- "What's new" changelog, and a full Users tab (remove members, rename household)
- Long-term-care *benefits* (premiums are modeled, payouts are not)

### 2b. Modeling gaps (these affect the numbers)
| Gap | Why it matters |
|---|---|
| **One savings pool** (liquid + pre-tax) with no Roth/taxable split, no RMDs and no capital-gains tax | Taxes in retirement are approximate. Roth conversions and withdrawal order can't be planned |
| **No survivor or spousal Social Security** | "Early death" and single-earner plans look worse than reality |
| **No pension/annuity income type** | Teachers, government and military plans have to fake it through the SS field (the Single Mom demo does this) |
| **Salaries don't respond to inflation** | Inflation stress tests are harsh, because wages stay flat while prices jump |
| **Fixed spending in Monte Carlo** | Real families cut back in bad years, so success rates are pessimistic for flexible spenders. Guardrails would fix this |
| **Pre-65 health insurance defaults to $0** unless entered | Early retirees are under-costed (all demos show this) |
| **Fixed asset allocation** (no glide path) | Sequence risk around retirement isn't reduced the way a real portfolio would reduce it |
| **No non-mortgage debts** (student loans, car loans as balances), **no 529s**, no emergency-fund rule | Common family situations need workarounds |

### 2c. Product gaps
- **"What would it take?"** The app shows success %, but can't answer "save how much more / retire when / spend how much less to reach 85%?"
- **No goals.** "Retire at 55", "college fully funded" and "pay off the house by 60" aren't first-class items with progress bars.
- **Actual data still comes from typing.** Monarch Money, Mint-style CSVs or bank exports can't fill actuals or check-in balances yet.
- **Nothing is live on the NAS yet.** v2 runs only locally, the NAS still serves v0.8, and there's no CI.
- **Bundle size.** The web bundle is 820 kB (one chunk). Code-splitting per page would halve the first load on phones.

## 3. Plan (in priority order)

### Phase 1: Ship it (make v2 the app you actually use)
1. **Deploy v2 on the NAS next to v0.8.** Use a copy of the real data first, then switch the volume to `../app-data`. Set `ALLOW_DEV_LOGIN=0` behind Cloudflare. Configure SMTP (a Gmail App Password) and `APP_URL`.
2. **CI on GitHub Actions**: engine and API pytest, `tsc`, and a Playwright smoke test (login → setup → check-in → actuals → PDF).
3. **Off-NAS backup** of `data/` (nightly copy to a cloud drive). Version history protects against bad edits, not against disk loss.
4. **Code-split** the pages and lazy-load Recharts. Add a PWA manifest so it installs on phones.
5. Merge `v2-react` into `main` once a full quarter of check-ins has run on v2.

### Phase 2: Answer the real questions
1. **"What would it take?" solver.** A binary search over one lever at a time (extra savings per month, retirement age, spending cut %, home budget) to reach a target success rate. Show it on the Dashboard as 2–3 one-click suggestions.
2. **Plan health checklist**: emergency fund, insurance coverage (from the stress tests), savings rate, housing cost ratio, college funding. Each item gets a status and a link.
3. **Goals** with progress, shown on the Dashboard and in every check-in result.

### Phase 3: Make the math trustworthy
1. **Account types**: taxable, traditional and Roth per person. Withdrawal order (taxable → traditional → Roth), RMDs from 73/75, and capital-gains tax on taxable withdrawals. This is the biggest accuracy gain for retirement years.
2. **Social Security**: spousal (50%) and survivor (100% of the higher benefit) rules, plus earnings-based estimates.
3. **Pensions and annuities** as an income type (start age, COLA, survivor %).
4. **Guardrail spending in Monte Carlo** (optional): cut discretionary spending by X% when the portfolio falls below its path.
5. **Glide path** (stock % declines toward retirement) and a wage-inflation link option for stress tests.
6. **Pre-65 health insurance template** (ACA-style by age and state) applied automatically after early retirement.
7. Debts (balance, rate, payment), 529 plans, and an emergency-fund target.

### Phase 4: Real data in, less typing
1. **CSV import for actuals**: Monarch Money transaction export, plus generic bank CSVs with column mapping. Map merchant categories to plan categories once, then remember the mapping.
2. **Balance import for check-ins** (a Monarch accounts CSV) so a quarterly check-in takes 30 seconds.
3. Check-in insights: explain drift ("spending was $6k over plan, mostly Travel").
4. Household activity feed ("Erin updated Homes") and comments on scenarios.

### Phase 5: Parity leftovers and polish
Custom templates and locations, page walkthroughs, the cash-flow Sankey and critical years, What's new, the full Users tab, and LTC benefit payouts.

## 4. Principles that stay fixed
- The household file format stays v0.8-compatible, with additive keys only. Every write is backed up and merged. Any v2 build can open any older file.
- One engine code path serves both the deterministic and Monte Carlo runs.
- Never remove a ✅ item from `PARITY.md`.
