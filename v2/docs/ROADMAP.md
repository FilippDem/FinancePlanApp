# v2: where it stands and what to build next

_Last updated 2026-10-12 (branch `v2-react`)_

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
| **Reports**: PDF, Excel, CSV and JSON with chosen sections and amounts by category per year | ✅ |
| **Where you live**: moves change prices and rent (BEA/World Bank), world map, custom places and templates | ✅ |
| **Spending slider** calibrated to BLS spending and BEA prices, with milestones | ✅ |
| **Data citations**: numbered [n] sources with links in the app and reports | ✅ |
| **Who owns what**: separate vs marital property by year, homes by contribution, gifts & inheritances, prenup rules | ✅ |
| **Linked accounts**: Fidelity/any CSV import and optional daily SnapTrade sync feeding check-ins | ✅ |
| **Roth / per-person pre-tax accounts, RMDs, spousal Social Security** | ✅ |
| **"What would it take?"** solver on the Dashboard | ✅ |
| Pages load on first visit (smaller first download) | ✅ |
| Cost-of-living raw data re-checked against BEA, BLS and World Bank (2026-09-27) | ✅ |
| **Scenario matrix**: every life scenario × every economy, with a builder for kids / moves / retirement / lifestyle variants | ✅ |
| **Where you'll live** lanes (place, home, kids at home) on the Dashboard and Where you live page | ✅ |
| **Plan editor on the life timeline**: zoom/pan, drag milestones, drop new ones, edit plan or scenario | ✅ |
| **Tax planning**: capital gains with cost basis, Roth conversions + comparison, IRMAA, ACA credits | ✅ |
| **Goals**, **safe spending**, **guardrails**, **every-historical-start backtest** | ✅ |
| **Pensions & annuities, loans, 529 plans** | ✅ |
| Demo households re-tuned for the corrected math | ✅ (success rates are a few points lower now that gains are taxed) |
| **2026-10-12:** hidden career-phase fix, automatic pre-65 health coverage, WA capital-gains tax, "Top 10%" spending milestone | ✅ |
| **2026-10-12:** "What your plan can afford" headline, plan score + one-page PDF, Need/Want spending with guardrails, glide path, Roth surplus sweep, Monarch CSV import, MCP server for Claude | ✅ |

Tests: 67 engine tests, 24 API tests, and a clean `tsc` build. The UI was checked end to end with Playwright.

## 2. What's still missing

### 2a. v0.8 features not yet ported
The 2026-09-26 audit found only small items left (see `PARITY.md`); their data is preserved.
- "What's new" changelog and an About panel
- Excel "include charts" option; median-return statistic in the Monte Carlo summary
- Long-term-care *benefits* (premiums are modeled, payouts are not)
- Guided walkthroughs and tab visibility are replaced by guided setup and per-page Help on purpose

### 2a'. Data freshness
The app cites every major dataset (`engine/finplan/data/sources.json`). Datasets to refresh each year: BEA price parities (February), BLS Consumer Expenditures (September/December), IRS brackets and limits (October/November), SSA wage cap and bend points (October), Medicare premiums (November), Social Security Trustees Report (spring/summer). International prices use 2024 World Bank price levels (updated 2026-09-27; refresh with each WDI update). The federal tax brackets are the 2024 ones indexed with the plan's inflation rate.

### 2b. Modeling gaps (these affect the numbers)
| Gap | Why it matters |
|---|---|
| **Social Security from earnings history** (spousal and survivor rules are done) | Benefits are typed in or estimated from today's salary |
| **Salaries don't respond to inflation** | Inflation stress tests are harsh, because wages stay flat while prices jump |
| ~~Pre-65 health insurance defaults to $0~~ | ✅ 2026-10-12: automatic employer/marketplace estimate. **Demos still have it off**; re-tune them with real health plans |
| ~~Fixed asset allocation~~ | ✅ 2026-10-12: optional glide path |
| **Historical bonds and CPI** in historical mode (bonds are a fixed 4%) | The 4% rule comes out 1–4 points too optimistic (see VALIDATION.md) |
| **Local income taxes** (NYC, Portland Metro/Multnomah), SS taxed by a few states | State tax uses state brackets only (2026-10-12) |
| **Dividend tax drag**, itemized deductions | Taxes on taxable accounts are approximate, and the Roth surplus sweep's benefit is understated |
| **Extra mortgage payments as a surplus priority** | The surplus sweep only targets Roth; prepaying a mortgage needs the loan schedule inside the simulation |

### 2c. Product gaps
- ~~Spending actuals still come from typing~~ ✅ 2026-10-12: Monarch transactions CSV import. Other bank CSVs with column mapping are still to do.
- **Nothing is live on the NAS yet.** v2 runs only locally, the NAS still serves v0.8, and there's no CI.
- **Bundle size.** Pages now load on first visit (main chunk 786 kB, was 1,068 kB). Recharts could still be split out.

## 2d. Compared with other planners (checked 2026-09-27; updated 2026-10-12)

**2026-10-12 update:** competitors shipped:
- Boldin: AI that edits the plan with a confirm step, plus an MCP server (Aug 2026); Planner Score and Investments (Sep 2026).
- ProjectionLab 4.5/4.6: flexible essential/discretionary spending, tax-strategy targets, transfers.
- Monarch: Forecasting in the Plus tier.

v2's answers are listed in §1 (2026-10-12 rows). Still open:
- IRMAA/ACA-cliff targets for Roth conversions.
- Extra mortgage payments as a surplus priority.
- Estate and insurance needs.
- MaxiFi-style consumption smoothing.
- Longevity (one partner to 95–100) view.

Compared with ProjectionLab, Boldin, and adviser tools like RightCapital, Pralana and MaxiFi.

**Where v2 is ahead:**
- Separate vs marital property.
- Kids' costs by age.
- Cost-of-living moves priced with BEA data.
- Check-ins and plan-vs-actual.
- A shared household.
- Worst-year stress tests.
- The scenario × economy matrix. Boldin compares up to 10 plans side by side, but not each plan under several economies.
- Self-hosted: the data stays at home.

**What they have that v2 doesn't, most valuable first:**

| Gap | Who has it | Status |
|---|---|---|
| Roth conversion optimizer + tax-bracket view | Boldin, ProjectionLab, Pralana | ✅ 2026-09-28: bracket chart, fixed or bracket-fill conversions, strategy comparison |
| Capital-gains tax on taxable accounts, cost basis | ProjectionLab, Boldin, Pralana | ✅ 2026-09-28 (withdrawal order is fixed: cash → pre-tax → Roth) |
| Medicare IRMAA surcharges and ACA subsidy cliffs | Boldin, Pralana | ✅ 2026-09-28 |
| Safe-spending target / guardrails | Boldin, MaxiFi | ✅ 2026-09-28 |
| Goals and milestones with progress | ProjectionLab | ✅ 2026-09-28 |
| Historical backtest of every rolling period | ProjectionLab, cFIREsim | ✅ 2026-09-28 (Stress tests + scenario-matrix economy) |
| Visual timeline you edit by dragging milestones | ProjectionLab | ✅ 2026-09-28: zoomable plan editor, works on scenarios too |
| Pensions/annuities, debts, 529 plans | Boldin, RightCapital, ProjectionLab | ✅ 2026-09-28 |
| Asset classes and a glide path (stocks/bonds/cash by age) | Boldin, ProjectionLab | Next: sequence risk around retirement |
| Estate and legacy (what heirs get, estate tax, step-up) | RightCapital, ProjectionLab | Later |
| Insurance needs (life/disability coverage gap) | RightCapital | Later |
| Bank/brokerage aggregation, budgeting import (Monarch/YNAB) | Boldin, ProjectionLab | Later; balances already come from SnapTrade + CSV |
| Plan-aware AI assistant | Boldin AI | Later |

**Next:**
1. Glide path.
2. Estate.
3. Insurance needs.
4. Transaction import.

## 3. Plan (in priority order)

### Phase 1: Ship it (make v2 the app you actually use)
1. **Deploy v2 on the NAS next to v0.8.** Use a copy of the real data first, then switch the volume to `../app-data`. Set `ALLOW_DEV_LOGIN=0` behind Cloudflare. Configure SMTP (a Gmail App Password) and `APP_URL`.
2. **CI on GitHub Actions**: engine and API pytest, `tsc`, and a Playwright smoke test (login → setup → check-in → actuals → PDF).
3. **Off-NAS backup** of `data/` (nightly copy to a cloud drive). Version history protects against bad edits, not against disk loss.
4. ✅ Pages code-split (2026-09-27). Still to do: lazy-load Recharts. Add a PWA manifest so it installs on phones.
5. Merge `v2-react` into `main` once a full quarter of check-ins has run on v2.

### Phase 2: Answer the real questions
1. ✅ **"What would it take?" solver** (done 2026-09-27: retire later, spend less, claim later, or a mix). A binary search over one lever at a time (extra savings per month, retirement age, spending cut %, home budget) to reach a target success rate. Show it on the Dashboard as 2–3 one-click suggestions.
2. **Plan health checklist**: emergency fund, insurance coverage (from the stress tests), savings rate, housing cost ratio, college funding. Each item gets a status and a link.
3. **Goals** with progress, shown on the Dashboard and in every check-in result.

### Phase 3: Make the math trustworthy
1. **Account types** (partly done: per-person pre-tax, Roth and RMDs; still to do: capital-gains tax, Roth conversions): taxable, traditional and Roth per person. Withdrawal order (taxable → traditional → Roth), RMDs from 73/75, and capital-gains tax on taxable withdrawals. This is the biggest accuracy gain for retirement years.
2. **Social Security** (spousal and survivor done; earnings-based estimates still to do): spousal (50%) and survivor (100% of the higher benefit) rules, plus earnings-based estimates.
3. **Pensions and annuities** as an income type (start age, COLA, survivor %).
4. **Guardrail spending in Monte Carlo** (optional): cut discretionary spending by X% when the portfolio falls below its path.
5. **Glide path** (stock % declines toward retirement) and a wage-inflation link option for stress tests.
6. **Pre-65 health insurance template** (ACA-style by age and state) applied automatically after early retirement.
7. Debts (balance, rate, payment), 529 plans, and an emergency-fund target.

### Phase 4: Real data in, less typing
1. **CSV import for actuals**: Monarch Money transaction export, plus generic bank CSVs with column mapping. Map merchant categories to plan categories once, then remember the mapping.
2. ~~Balance import for check-ins~~ ✅ done: Linked accounts (CSV or SnapTrade), including Roth vs pre-tax per account. Next: Monarch accounts CSV format.
3. Check-in insights: explain drift ("spending was $6k over plan, mostly Travel").
4. Household activity feed ("Erin updated Homes") and comments on scenarios.

### Phase 5: Parity leftovers and polish
What's new, About, LTC benefit payouts, Excel charts. A yearly data refresh script that re-pulls the cited datasets and flags changes.

## 4. Principles that stay fixed
- The household file format stays v0.8-compatible, with additive keys only. Every write is backed up and merged. Any v2 build can open any older file.
- One engine code path serves both the deterministic and Monte Carlo runs.
- Never remove a ✅ item from `PARITY.md`.
