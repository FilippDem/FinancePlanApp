# v2 engine: what changed vs v0.8

The v0.8 engine was spread across `calculate_lifetime_cashflow()` (deterministic),
the Monte Carlo loop in `monte_carlo_simulation_tab()` and the stress-test tab,
each reading `st.session_state` directly and each with slightly different math.
v2 has **one** engine (`engine/finplan/engine.py`) used for both the
deterministic projection and Monte Carlo. It is pure Python/numpy with no
Streamlit dependency, and it runs 5,000 Monte Carlo paths in well under a second.

Numbers from v2 **will differ** from v0.8. Most differences come from v0.8 bugs
that made plans look far better than they are. Every change below is covered by
a test in `engine/tests/test_engine.py`.

## Bugs fixed (these change results)

| # | v0.8 behaviour | v2 behaviour |
|---|---|---|
| 1 | **Mortgage payments were never charged.** House costs covered property tax, insurance, maintenance and upkeep only, and "Mortgage/Rent" was zeroed whenever you lived in an owned home. | Principal and interest are paid every year until payoff, using real amortization. |
| 2 | Home equity was estimated with a linear payoff, never added to net worth, and "liquid = net worth − equity" subtracted equity that had never been added. | Net worth = savings + pre-tax accounts + home equity + other assets − consumer loans. Equity grows with appreciation and principal paydown. |
| 3 | Future home purchases were free: no down payment. | A purchase after the current year pays (price − mortgage) from savings in the purchase year. |
| 4 | Selling a home produced no proceeds. Timelines saved as `Sell` were never treated as sold, so the house kept costing money. | The sale year pays off the loan, deducts selling costs (default 6%) and adds the proceeds to savings. `Sell` and `Sold` both work. |
| 5 | Rental income (`Own_Rent`) was ignored. | Rent is income, and net rental profit is taxed as ordinary income without FICA. |
| 6 | Social Security started at the **retirement** age (even at 50), was flat forever (no COLA) and had no claiming adjustment. | Benefits start at the claim age (62–70, default max(retirement, 62)). The entered benefit is treated as the age-67 amount and adjusted by the SSA early/late factors (62 → 70%, 70 → 124%). Benefits grow with inflation, and a surviving spouse keeps the larger benefit. The insolvency cut and its start year remain configurable. |
| 7 | Monte Carlo return "variability" multiplied the *rate*: 6% × (1 ± 15%) gives 5.1–6.9%, which is almost no market risk. | Volatility is in percentage points (6% ± 15 pp gives a realistic spread). The asymmetric upside/downside split is kept. |
| 8 | Monte Carlo ignored taxes entirely. | Monte Carlo runs the same cash flow, tax and housing code as the projection. |
| 9 | The "Historical average" economy toggle set the return to the S&P arithmetic mean (12.4%, 100% stocks, no fees). | The value is still available as a button, with a warning. Historical Monte Carlo adds a stock/bond allocation and an optional *sequential* (real historical sequences) sampling mode. |
| 10 | Children, one-time purchases and healthcare premiums were never inflated. | Children and purchases inflate with CPI; healthcare with healthcare inflation. Child templates (2024 dollars) are also scaled to the current year. |
| 11 | College cost = the template's own college "Education" amount **plus** tuition **plus** room & board (double counted). | College years use tuition + room & board for the college location, replacing the template amount. |
| 12 | Financing on recurring expenses and one-time purchases was ignored: the full amount was charged at once. | Financed items are amortized over the loan term and the remaining loan balance counts as a liability. Purchases marked Vehicle/Real Estate/Investment/Depreciating are kept as assets that appreciate or depreciate. |
| 13 | Tax brackets, the standard deduction and the FICA wage base were frozen at 2024 nominal values. | These are indexed to inflation. FICA applies per earner, not on combined wages. |
| 14 | Health expenses (`health_expenses`) were collected but never used. | They are included, age-ranged and per person. |
| 15 | A negative net worth kept "earning" investment returns (which shrinks the debt in down years). | A negative savings balance accrues interest at the borrowing rate (default 7%). |
| 16 | Plans without `parentX_career_phases` (e.g. all six demos) silently used a default 75k phase starting at age 30, so the Tech Couple demo earned **$0** in year one. | Missing career phases means the simple income model is used: income, raise and job changes. |
| 17 | 401(k) contributions were only a tax deduction and then disappeared. | Contributions (and HSA contributions) are deducted from taxable wages and accumulate in a pre-tax bucket. Shortfalls are withdrawn from it, grossed up for income tax. |

## Mortgage calculator (new in v2)
Homes can describe their loan in one of two ways (`mortgage_mode`):
- **Estimate from rate.** Enter home price, down payment %, loan term and interest rate, like a listing calculator. The loan starts in the purchase year. For a home bought in the past, today's balance comes from amortizing the original loan. This matches Redfin's calculator: $1,399,000 with 20% down at 7.5% over 30 years gives $7,825 P&I, which is covered by a test.
- **Actual loan.** Enter the current balance, rate and years left from your statement, plus optionally the monthly P&I you actually pay. Paying more than required is extra principal, so the loan pays off sooner.

Both modes support:
- PMI: a % of the loan when the down payment is under 20% (estimate mode), or a $/month amount (actual mode). PMI stops once the balance reaches 78% of the price.
- HOA dues ($/month, inflated).
- Closing costs (% of price, paid with the down payment on future purchases).
- Property tax entered as a % or as $/yr. It is stored as a rate.

`mortgage_balance` and `mortgage_years_left` are kept in sync in estimate mode, so v0.8 can still read the file. Old files load in actual mode, so their numbers are unchanged.

## Behaviour kept from v0.8 (intentionally)
- Expense categories, templates and all reference data are extracted automatically from v0.8 by `tools/extract_v08_data.py`. Audited corrections are layered on top by `reference.ref()` (`reference_corrections.json`); `reference.ref_raw()` or `FP_RAW_REFERENCE=1` gives the untouched v0.8 numbers.
- Family "Mortgage/Rent" is skipped in years you live in an owned home. "Property Tax" and "Home Insurance" family lines are also skipped while any home is owned, because they come from the Homes page.
- Pooled vs Separate finances. The shared-cost split % and per-owner house costs are kept.
- Income variability applies to wages only, not Social Security (V14 fix). Maintenance uses `maintenance_rate` (V14 fix). Children's health categories use healthcare inflation (V14 fix).
- `expense_growth_rate` is stored but not used (v0.8 didn't use it either).

## Money conventions
- Recurring amounts you type (spending, rent, premiums, SS benefit, 401(k), one-time costs) are **today's dollars** and inflate every year.
- Salaries are nominal and grow by the raise %.
- House prices, values and mortgage balances are nominal as entered.
- `parentX_net_worth` means **savings & investments excluding home equity**. That matches how v0.8's math used it. Homes are added from the Homes list.

## Demo plans (re-tuned)
The six demo households were tuned against the v0.8 engine, which never charged mortgage payments or down payments. Under the corrected math most of them ran out of money. `engine/finplan/data/demo_overrides.json` re-tunes them while keeping each story (moves, retirement ages, homes). `demo_plans.json` stays a verbatim extract of v0.8, and `reference.demo_plans(raw=True)` returns the originals. Each demo carries a `demo_note` explaining what changed, shown on the Scenarios page. Monte Carlo success (1,000 runs, seed 3, v2 engine):

| Demo | v0.8 data | Re-tuned | Story kept |
|---|---|---|---|
| Tech Couple | 68% | 87% | SF → Austin → Seattle, retire at 50/51 |
| 3-Kid Family | 9% | 70% | Seattle → Portland → Denver, work to 63 |
| Executives | 3% | 74% | NYC → Miami → Portugal, retire at 55 |
| Single Mom | 0% | 61% | Sacramento → San Diego, teacher → principal |
| Empty Nesters | 41% | 80% | Portland → Arizona → Montana (RV), retire at 60 |
| Budget Family | 0% | 72% | Houston → Austin, careful savers |

Re-tuned again on 2026-10-12 after two engine changes: real 2025 state income-tax brackets (lower taxes for the CA/NY/OR demos) and health premiums before Medicare. Each demo now enters its own health plans instead of relying on the automatic estimate: the average worker share of an employer plan while working ($6,850 family / $1,440 single a year, KFF 2025 [22]) and, after an early retirement, a marketplace silver plan priced from the 2026 benchmark ($625/month at 40 [23]) on the federal age curve [24] ($980 / $1,205 / $1,410 a month per person at 50–54 / 55–59 / 60–64), with the premium tax credit. To keep the spread, Single Mom earns $115k (was $118k), the 3-Kid Family $125k + $102k (was $115k + $95k), the Budget Family $72k + $60k (was $66k + $55k), and the Executives start with $6.2M (was $5.6M). Tech Couple and Empty Nesters needed no change. With 600 runs and seed 1 the results are 85 / 70 / 71 / 58 / 78 / 67%.

`demo_plans()` and `default_plan()` now return fresh copies. They used to return the cached object itself, so any caller that edited a demo changed it for every later caller (a test caught this).

## Analysis modules added in v2
- **Stress tests** (`finplan/stress.py`). A runtime-only `plan['_stress']` list, never saved, applies one bad event per run: a market crash (overrides that year's return), income loss (a % of one or both earners' wages for N years), an extra cost (today's $ per year for N years), an inflation spike (prices *and* inflation-indexed items follow a higher rate for N years; salaries stay nominal, so this is a harsh test), or early death (sets the death age, with an optional life-insurance payout). Survivor Social Security benefits are **not** modeled yet.
- **Retirement** (`finplan/retirement.py`). Social Security claim options at 62/67/70/planned, with lifetime totals that include the insolvency cut and the break-even age. Retire-age what-if (−3…+3 years, 300 MC runs each). Replacement ratio: the best household wages in the last 5 working years, compared with SS + a withdrawal-rate draw on savings + rent in the first fully retired year.
- **Actuals** (`finplan/actuals.py`). Planned values for any year in the v0.8 `actuals[year]` shape, so plan-vs-actual lines up category by category.

## Round 3 changes (2026-09-26)

### Cost of living follows you (new)
- `move_adjusts_spending` (default on): when the location or lifestyle in `state_timeline` changes, everyday spending is multiplied by the price ratio between the two places. Off reproduces v0.8, where a move only changed taxes.
- Prices come from BEA 2024 Regional Price Parities for states and metros [1] and World Bank price levels abroad [2] (`calibrate.py`, `data/cost_index.json`). "Mortgage/Rent" uses the BEA rents index instead [1], falling back to HUD Fair Market Rents [3].
- Unknown destinations keep today's prices; a lifestyle change still applies.
- Custom places (`custom_locations`) borrow prices from their "prices like" place and taxes from their "taxed like" place, unless the user saved a template for that name.
- Per-year `col_factor` / `rent_factor` and the scaled per-category living costs are in each row's `details.living`, which reports and Actuals now use.

### Spending level (new)
- Per-adult spending comes from BLS Consumer Expenditure 2022 income quintiles [4] grown to 2024 totals [5], priced locally as above. A slider position (0–100) maps to milestones: income quintiles, the local average, the US average and the old v0.8 levels. Stored as `parentX/Y_spending_level`.

### Other engine changes
- RSU income ramps up over the vesting period (a yearly grant vesting over 4 years pays ¼, ½, ¾, then the full grant), instead of the full grant from year one.
- Career-phase transitions are life events (they were only emitted for simple job changes).
- Healthcare line items carry a kind (premiums, Medicare, long-term care, out of pocket), so Actuals can split them.
- `CITY_TO_STATE` gained Columbus → Ohio, Honolulu → Hawaii and San Jose → California, which were taxed as unknown before.
- Historical S&P 500 list: four v0.8 years (1928, 1929, 1933, 1936) differed from the published series by more than 2 points, 1929 by 20 points; corrected via `reference_corrections.json` [6].
- New plans default the Medicare Part B premium to $202.90/month, the 2026 standard premium [7]. v0.8 used $174.70 (the 2024 figure) and labelled it 2025. Saved plans keep their own value.
- Stress tests: disabled-child tests can pick the worst child automatically (v0.8 `find_worst_case_disabled_child`), and compound tests can start every event in a chosen year.

### Who owns what (separate vs marital property)
`finplan/ownership.py`. Off unless `ownership_tracking.enabled`, and couples only. An accounting layer inside `simulate()`: it runs alongside the pooled (or separate-finances) math and is reconciled to the engine's totals every year, so it can never change taxes, spending, net worth or success rates.
- Three classes: person 1's separate (`s1`), person 2's separate (`s2`) and marital (`m`), each for cash, pre-tax accounts and each home's equity. Other assets and consumer loans count as marital.
- Phases: *before* the wedding (`marriage_year` in the future) everything is each person's own; *married*; *after* a death, labels are kept.
- Rules (`ownership_tracking`): state regime (community property in AZ, CA, ID, LA, NV, NM, TX, WA, WI; otherwise equitable distribution) [8]; pay during marriage marital or separate (prenup); growth and rent from separate property stay separate except in ID, LA, TX and WI [8]; person 1's share of marital property on division; how separate money covers a shortfall.
- Spending order while married: marital money first (including marital retirement money), then separate money. Any separate money spent on shared costs is reported as commingled, per year.
- Homes: a pro-rata contribution method. Each class's share of equity equals its share of money put in: separate money entered per home (`separate_funds`), the rest of the down payment, and principal paid each year by whoever pays that year. For homes bought before today, money put in so far is price − loan, split by years owned before and after the wedding.
- Check-ins carry the separate balances forward from the projection unless the check-in states them (`separate_liquid`, `separate_pretax`).
- Rows gain `ownership` (per class, division, commingled); the summary gains `ownership` (resolved rules, commingled total and years).

### Gifts & inheritances
`windfalls` (new, additive): cash that arrives in a given year (today's dollars by default), not taxed as income, shown as events and in the cash-flow timeline. Tagged separate (to one person) or joint.

## Round 4 changes (2026-09-27)

### Account types: Roth, per-person pre-tax, RMDs
- Savings are now split into cash/taxable, each person's pre-tax accounts (401(k)/IRA), HSA and Roth. New inputs: `parentX/Y_roth_balance` and `roth_contribution` (per year, taken from after-tax pay). Plans without them behave as before, because all Roth values default to 0.
- Withdrawal order in a shortfall: cash first, then pre-tax (grossed up for income tax), then Roth (tax-free).
- **Required minimum distributions** (`rmd_enabled`, on by default): each year, prior-year pre-tax balance ÷ the Uniform Lifetime Table divisor [10]. RMDs start at 73 if born 1951–1959 and at 75 if born 1960 or later [9][11]. Roth accounts have no RMDs while the owner is alive [9]. The RMD is taxed as ordinary income and lands in cash. A deceased spouse's pre-tax accounts roll over to the survivor.
- Rows gain `roth`, `rmd`, `withdrawal_roth` and `contrib_roth`. Investable assets and net worth include Roth.

### Spousal Social Security
- `spousal_ss` (on by default, couples only). Once both partners have claimed, the lower earner gets the larger of their own benefit and up to 50% of the partner's full-retirement-age benefit [12]. Claiming before 67 reduces this by 25/36 of 1% a month for the first 36 months and 5/12 of 1% after that, so 62 gives 32.5% [12][13]. Survivor benefits apply after that, as before.

### "What would it take?" solver (`finplan/solver.py`, `POST /api/solve`)
- For a target chance of success, it finds the smallest single change that reaches it:
  - retire later (0–10 years)
  - spend less (0–40% of everyday, personal and recurring costs; housing, kids and healthcare are untouched)
  - claim Social Security later (up to 70)
  - a mix of all three (up to 5 years later, 25% less and 3 years later together)
- When the plan is already above the target, it reports headroom instead: retire earlier or spend more.
- Each option is a bisection over the Monte Carlo success rate with a fixed seed, so every candidate sees the same market paths. The answer is a patch the UI applies after saving the old plan as a scenario.
- There is no "save more" option: money not spent is already saved in this model, so it is the same lever as "spend less".

### Scenario matrix (`finplan/matrix.py`, `/api/scenarios/economies`, `/api/scenarios/evaluate`, `/api/scenarios/variant`)
- Each saved life scenario is run under several economic conditions. Every condition is expressed with the existing stress primitives, so the plan itself never changes:
  - Weak or strong markets: returns 2 points lower or higher every year. This uses the new `return_shift` primitive, which also works in historical mode and can be limited to a range of years.
  - High inflation: +1.5 points a year, with pay catching up by half.
  - Crash at retirement: markets fall 35% in the first retirement year.
  - 1970s-style decade: 8% inflation for 6 years and returns 3 points lower for 10 years.
  - Real market history: sequential historical S&P 500 returns at the plan's stock share.
- All cells use one seed, so scenarios in a column face identical markets.
- Verdict per scenario:
  - *holds up*: reaches the target in every economy.
  - *fragile*: reaches it as planned but not in every economy.
  - *falls short*: doesn't reach it as planned.
- `build_variant` makes a life scenario from a plan. You can set the number of children (with birth years; lowering it drops the youngest), add a move (replacing moves from that year on), change retirement ages, or change the lifestyle.

### Cost-of-living data re-check
Every table in `data/cost_index.json` was re-checked against its publisher; see `COST_OF_LIVING_AUDIT.md` → *Raw-data re-check*.
- World Bank country price levels moved from 2020 to 2024 values [2].
- The two BLS-suppressed cells are now calculated exactly from the published subtotal.
- For countries without an old-app template, the "Old app" slider marks are now at local prices (they had used Seattle's dollars).

## Round 5 changes (2026-09-28)

### Taxes
- **Capital gains** (`capital_gains_enabled`, default on; `taxable_basis_pct`, default 80):
  - Cash and taxable savings carry a cost basis. New savings add to it.
  - When spending sells investments, the gain share of the sale (as of the start of the year) is realized.
  - Realized gains are taxed at the 0/15/20% long-term rates stacked on ordinary taxable income [14], plus the 3.8% net investment income tax above $250k joint / $200k single [15], plus state tax (a country's effective rate abroad).
  - Plans with large taxable savings now show slightly lower success rates. The math is unchanged when this is off (checked against the previous engine on all demos).
- **Roth conversions** (`roth_conversion`):
  - Two modes: a fixed amount per year (today's $), or filling the chosen federal bracket (10/12/22/24/32%) using the standard deduction and taxable Social Security.
  - The window runs from retirement to the year before RMDs by default, on person 1's age.
  - Conversions come out of each pre-tax account proportionally. The tax is paid from cash [16].
  - `taxplan.compare()` runs every strategy through the whole plan and compares lifetime taxes, IRMAA, success, and after-tax money left (pre-tax balances counted at 75% for heirs).
- **IRMAA** (`irmaa_enabled`, default on): Medicare Part B + D surcharges per person on Medicare. They use the 2026 CMS table on MAGI from two years earlier, with thresholds indexed after 2026 [17].
- **ACA premium tax credit** (`aca_enabled` + `health_insurances[].marketplace`):
  - The entered premium is treated as the benchmark silver price.
  - Credit = premium − applicable % × MAGI, using the 2026 IRS table (2.10%–9.96%) [18].
  - Household income is measured against the 2025 poverty guideline (+$5,500 per extra person) [19].
  - No credit above 400% of the poverty guideline (the cliff). Below 138% it is treated as Medicaid.
  - The credit is reconciled on the year's actual MAGI.
- Rows gain `taxable_ordinary`, `magi`, `cap_gains_realized`, `tax_cap_gains`, `roth_conversion`, `irmaa`, `aca_credit`, `aca_benchmark` and `fpl_ratio`. The summary gains lifetime totals, `irmaa_years` and `aca_cliff_years`.

### Pensions, loans, 529 plans (`extras.py`)
- **Pensions and annuities:**
  - Paid from a start age, in today's dollars or as quoted, with a COLA.
  - A survivor share goes to the spouse after the owner dies. Only the taxable share is taxed [20].
  - An optional annuity purchase is a one-time cost.
- **Loans:**
  - Balance, APR, monthly payment plus extra, and start year.
  - Payments are fixed nominal amounts. The balance counts in `consumer_debt`, which lowers net worth.
  - A "paid off" event is added. A warning appears when the payment doesn't cover the interest.
- **529 plans per child:**
  - Monthly saving (today's $) until an age. The account earns the portfolio return and pays that child's college-age costs [21].
  - At 22, leftover money goes to a younger sibling's 529, or back to savings after about 32% tax and penalty on the earnings.
  - 529 balances count in net worth, not in investable savings.
- Check-ins roll loan and 529 balances forward with the projection, unless the check-in states them. Actuals gain a `debts` group, and pensions count as other income.

### Goals (`goals.py`)
- Goal types: work optional (25× the spending not covered by Social Security or pensions), net worth, savings, emergency fund, college funded, house paid off, debt free.
- Each goal gets progress, the projected value, and a status.
- `monte_carlo()` adds `goal_probs`: the share of paths meeting each money goal. On track needs at least 75%; 50–75% is at risk.

### Spending
- **Safe spending** (`solver.safe_spending`): bisection on a multiplier of flexible spending (personal, household excluding housing, recurring) to find the highest level that still reaches the target success rate.
- **Guardrails** (`guardrails`): in Monte Carlo, each path compares its savings with the expected path. If savings are X% below, flexible spending is cut by Y%; if X% above, it is raised. By default this applies only after retiring. Monte Carlo reports how often each happens.

### Rolling historical backtest (`backtest.py`)
- The plan runs once from each start year 1924–2023, with S&P 500 returns in order (wrapping for long plans) and no income or spending noise.
- The result is the share of start years that never ran out, plus the worst starts.
- It is also the "Every historical start" economy in the scenario matrix.

### Plan editor
- `web/src/lib/lifeEdit.ts` maps plan items to timeline items and back: set the year from a drag, create from a palette drop, edit, and delete.
- Everything stays additive to the v0.8 schema.

### 2026-10-12: fixes from a real household, plus competitor-review features
**Fixes:**
- **Hidden career phase.** The template's untouched 75k "Current Job" phase (30-65) silently overrode the simple income model. `normalize_plan` now drops it when the plan clearly uses income + job changes (an income other than 75k, or job changes). Edited or real phases are never touched.
- **Health coverage before 65.** `auto_health_coverage` is on by default and applies only when no health plan is entered:
  - **Years with wages:** the worker's share of an employer plan, $1,440 single or $6,850 family (KFF EHBS 2025).
  - **Years with no wages under 65:** a marketplace benchmark plan, $625/mo at 40 in 2026 (KFF), age-rated on the federal default curve (CMS). Children are rated 0.6. It feeds the ACA credit like an entered marketplace plan.
  - Grown with healthcare inflation.
  - **Demos:** the estimate is off in the six demos (`demo_overrides.json`) so their tuned results are unchanged. Turning it on would cost them 1–46 points of success. They should be re-tuned with real health plans.
- **Washington capital-gains tax:** 7% on long-term gains above the standard deduction ($262k in 2024, indexed; $278k in 2025) and 9.9% above $1M (not indexed), once per household. It applies only to sales from taxable savings, matching the law's real-estate and retirement-account exemptions.
- **Spending slider:** new "Top 10%" milestone at x=85 from BLS CE Table 1110 (highest decile, 2022), parsed and checked against Table 1101's all-units column. Existing positions are unchanged.

**New:**
- **Essential vs discretionary spending.** `essential_categories` (default: groceries, transport basics, medical, phone, housing and utilities) and `recurring_expenses[].essential`. Guardrails cut only the discretionary part.
- **Glide path.** `glide_path {enabled, at_retirement, years_before}` with `allocation_path()`. Stocks move linearly from `mc_stock_allocation` to the target over the years before the first retirement.
  - **Historical mode:** applied directly to the stock/bond mix.
  - **Statistical mode:** `investment_return` is read as today's mix, the stock part is backed out, and returns and spread scale with the stock share.
- **Surplus sweep.** `surplus_sweep {enabled, roth_per_person}`: while working, each earner's leftover cash goes to Roth up to the limit (IRS 2026 IRA $7,500, inflation-adjusted).
  - It is not applied with ownership tracking on.
  - There is no yearly dividend drag on taxable savings yet, so its benefit shows only as capital-gains tax avoided.
- **Plan score.** `finplan/health.py` is a weighted checklist (success, emergency fund, savings rate, housing, withdrawal rate, college, debt, health coverage) producing a 0–100 score.
  - Used by `/api/plan-health`, the Dashboard and the `plan_health` report section.
  - The "One-page summary" PDF preset uses it.
- **Monarch import.** `server/monarch.py` and `/api/actuals/monarch` read a Monarch transactions CSV and produce yearly actuals.
  - Personal categories are split between the two adults; transfers and card payments are skipped.
  - Unrecognized categories are counted as Other Family Expenses and reported back.
  - Re-importing replaces rather than adds.
- **MCP server.** `server/mcp_server.py` lets Claude read and edit plans over stdio (see `desktop/README.md`). Edits are propose → confirm → apply, with a backup.

### 2026-10-12 (later): validation against published figures
See `VALIDATION.md`: 33 of 33 benchmark checks pass, and 300 fuzzed plans run without failures.
- **State income tax:** real 2025 brackets, deductions and exemptions for all 41 income-tax states + DC, replacing "top rate × all taxable income" (California $200k couple: $22.6k → $10.3k). Gains are stacked in the state brackets. Demo results move: Single Mom 50→88%, Tech Couple 85→92%, Executives 65→69%.
- **Federal tables:** 2026 values (Rev. Proc. 2025-32) with `TAX_BASE_YEAR` 2026; SS wage base $184,500; 2026 capital-gains thresholds.
- **Additional Medicare Tax:** on a couple's combined wages.
- **Single-person plans:** the inactive partner's balances are ignored, so the $40k template value no longer counts.
- **Social Security default cut:** 17% from 2034 (2026 Trustees), was 30%.

### Sources
[1] U.S. Bureau of Economic Analysis, [Regional Price Parities by State and Metro Area, 2024](https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area)
[2] World Bank, [Price level ratio of PPP conversion factor to market exchange rate (PA.NUS.PPPC.RF)](https://data.worldbank.org/indicator/PA.NUS.PPPC.RF), 2024 values via [Our World in Data](https://ourworldindata.org/grapher/gdp-price-levels-relative-to-the-us)
[3] HUD, [Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr.html)
[4] BLS, [Consumer Expenditure Surveys Table 1101, income quintiles, 2022](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2022.pdf)
[5] BLS, [Consumer Expenditures — 2024](https://www.bls.gov/news.release/cesan.nr0.htm)
[6] NYU Stern (Damodaran), [Historical returns: S&P 500 including dividends](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)
[7] CMS, [2026 Medicare Parts A & B Premiums and Deductibles](https://www.cms.gov/newsroom/fact-sheets/2026-medicare-parts-b-premiums-deductibles)
[8] IRS, [Publication 555, Community Property](https://www.irs.gov/publications/p555) (Dec 2024)

The full, numbered list the app cites lives in `engine/finplan/data/sources.json`.
[9] IRS, [Retirement topics: Required minimum distributions](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-required-minimum-distributions-rmds)
[10] 26 CFR 1.401(a)(9)-9, [Uniform Lifetime Table](https://www.law.cornell.edu/cfr/text/26/1.401(a)(9)-9)
[11] Federal Register, [Required Minimum Distributions final regulations (SECURE 2.0 applicable age)](https://www.federalregister.gov/documents/2024/07/19/2024-14542/required-minimum-distributions)
[12] SSA, [Benefits for spouses](https://www.ssa.gov/oact/quickcalc/spouse.html)
[13] SSA, [Retirement age and benefit reduction](https://www.ssa.gov/benefits/retirement/planner/agereduction.html)
[14] IRS, [Rev. Proc. 2023-34 (2024 capital-gains thresholds)](https://www.irs.gov/pub/irs-drop/rp-23-34.pdf)
[15] IRS, [Net Investment Income Tax](https://www.irs.gov/individuals/net-investment-income-tax)
[16] IRS, [Publication 590-A (Roth conversions)](https://www.irs.gov/publications/p590a)
[17] CMS, [2026 Medicare Parts A & B premiums and deductibles (IRMAA)](https://www.cms.gov/newsroom/fact-sheets/2026-medicare-parts-b-premiums-deductibles)
[18] IRS, [Rev. Proc. 2025-25 (2026 applicable percentage table)](https://www.irs.gov/pub/irs-drop/rp-25-25.pdf)
[19] HHS ASPE, [Poverty guidelines](https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines)
[20] IRS, [Topic no. 410, Pensions and annuities](https://www.irs.gov/taxtopics/tc410)
[21] IRS, [Publication 970 (529 plans)](https://www.irs.gov/publications/p970)
[22] KFF, [2025 Employer Health Benefits Survey](https://www.kff.org/health-costs/2025-employer-health-benefits-survey/)
[23] KFF, [Marketplace average benchmark premiums](https://www.kff.org/affordable-care-act/state-indicator/marketplace-average-benchmark-premiums/)
[24] CMS, [Market rating reforms (age curve)](https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/state-rating)
[25] Washington DOR, [Capital gains tax](https://dor.wa.gov/taxes-rates/other-taxes/capital-gains-tax)
[26] BLS, [Consumer Expenditure Surveys Table 1110, income deciles, 2022](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-deciles-before-taxes-2022.pdf)
