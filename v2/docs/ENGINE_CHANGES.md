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
| Tech Couple | 68% | 86% | SF → Austin → Seattle, retire at 50/51 |
| 3-Kid Family | 9% | 69% | Seattle → Portland → Denver, work to 63 |
| Executives | 3% | 76% | NYC → Miami → Portugal, retire at 55 |
| Single Mom | 0% | 64% | Sacramento → San Diego, teacher → principal |
| Empty Nesters | 41% | 82% | Portland → Arizona → Montana (RV), retire at 60 |
| Budget Family | 0% | 71% | Houston → Austin, careful savers |

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

### Sources
[1] U.S. Bureau of Economic Analysis, [Regional Price Parities by State and Metro Area, 2024](https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area)
[2] World Bank, [Price level ratio of PPP conversion factor to market exchange rate (PA.NUS.PPPC.RF)](https://data.worldbank.org/indicator/PA.NUS.PPPC.RF)
[3] HUD, [Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr.html)
[4] BLS, [Consumer Expenditure Surveys Table 1101, income quintiles, 2022](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2022.pdf)
[5] BLS, [Consumer Expenditures — 2024](https://www.bls.gov/news.release/cesan.nr0.htm)
[6] NYU Stern (Damodaran), [Historical returns: S&P 500 including dividends](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)
[7] CMS, [2026 Medicare Parts A & B Premiums and Deductibles](https://www.cms.gov/newsroom/fact-sheets/2026-medicare-parts-b-premiums-deductibles)

The full, numbered list the app cites lives in `engine/finplan/data/sources.json`.
