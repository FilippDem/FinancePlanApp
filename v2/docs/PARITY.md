# v0.8 → v2 feature parity

Status: ✅ in v2 · 🟡 partial · ⏳ not yet (planned) · ➖ not carried over on purpose (reason given)

Last full audit: 2026-09-26. Two independent passes compared every tab, wizard step, scenario and slider in `FinancialPlanner_v0_8.py` with v2 and checked each item in the running app.

Data compatibility is ✅ for everything: v2 reads and writes the same household files and never drops keys, so features not rebuilt yet keep their data.

## Accounts & data
| Feature | Status | Notes |
|---|---|---|
| Cloudflare Access sign-in (header) | ✅ | Same header. The email login is a dev/LAN fallback; set `ALLOW_DEV_LOGIN=0` behind Cloudflare |
| Households: create, join by code, switch | ✅ | Same `households_index.json` and `households/<id>.json` |
| Standard or encrypted household at creation | ✅ | Same cipher, verified against v0.8-format files; passphrase needs 8+ characters and confirmation |
| Household & members page (rename, member list, remove member, invite code) | ✅ | v0.8 Users tab. Rename backs up the index and household file first |
| Admin: test household with a demo | ✅ | Isolated `_test_` household (no backups, per policy). The Test mode banner's **Exit** deletes it and returns to your own household; admins can clean up all their test households |
| Auto-save with backups before every write | ✅ | Load-then-merge, 10 rolling backups, atomic writes |
| Named scenarios (save/load/rename/delete) | ✅ | Stored in the household file like v0.8 |
| Scenario comparison + what-if buttons | ✅ | Side-by-side chart and inputs table; quick what-ifs save "Current Plan (before what-if)" first |
| JSON export/import (v0.8, V14, V13 formats) | ✅ | V13 migration covered by a test |
| Reset to defaults | ✅ | |
| Demo households | ✅ | Re-tuned for the corrected math (originals kept); each explains what changed |
| Version history | ✅ | Last 10 saves plus one snapshot a day for 120 days; preview and restore |
| Sidebar quick summary | ✅ | Net worth, income, spending, kids · homes, location, alert counts |
| Help for each page | ✅ | Help button in the header (v0.8 tab "What this tab does" text) |
| "What's new" changelog | ⏳ | |
| About panel | ⏳ | Minor |

## Guided setup (v0.8 wizard, phase 1 + 2)
| Feature | Status | Notes |
|---|---|---|
| Single or couple, names, emojis, ages, marriage year | ✅ | |
| Tax filing status | ✅ | Couples choose joint or separate |
| Location: country → state → city, planned moves | ✅ | |
| Income, raise, retirement age, job changes | ✅ | Warns when a change falls after retirement |
| Career stages (label, ages, salary, raise %) | ✅ | Optional; replaces the single income. Warns when a stage runs past retirement |
| Savings, retirement accounts, 401(k) contribution | ✅ | |
| Social Security: estimate or from statement; insolvency toggle | ✅ | Estimate uses the 2026 SSA formula |
| Housing: rent / own (value, mortgage, rate, years, property tax) / other; buying later | ✅ | |
| Children (name, birth year, school, college) | ✅ | |
| Spending style | ✅ | Now a calibrated slider with milestones (see Spending) |
| Household bills (utilities, water & garbage, internet, subscriptions, pets, other) | ✅ | Garbage is asked together with water, not double counted |
| Vacation budget | ✅ | Asked under big plans; goes into household "Family Vacations" (not also a recurring cost) |
| Healthcare: employer premium share, marketplace/bridge premium, out-of-pocket, HSA balance and contribution | ✅ | |
| Custom one-time and recurring purchases | ✅ | |
| Planning horizon per person | ✅ | |
| Check-in cadence | ✅ | New in v2 |

## People & income
| Feature | Status |
|---|---|
| Names, emojis, current year, marriage year | ✅ |
| Age, net worth, retirement age, life expectancy, SS benefit | ✅ (+ SS claim age, pre-tax balance) |
| Income, raise %, job changes (with optional new raise %) | ✅ |
| Career phases (salary, raise, bonus, RSUs with vesting, options) | ✅ Style defaults per phase; RSU income ramps over the vesting period |
| Pooled / Separate finances with split % | ✅ |
| Single-person plans | ✅ |
| Guided mode / tab walkthroughs | ➖ The guided setup plus per-page Help replace it |
| Tab visibility settings | ➖ v2 navigation has no tabs to hide |

## Spending
| Feature | Status | Notes |
|---|---|---|
| Per-person categories (grouped) + location/lifestyle templates | ✅ | Data option: BLS/BEA calibrated (default) or v0.8 original (audited) |
| Spending-level slider with milestones | ✅ | New: one slider per adult (or both), categories follow; manual edits kept in proportion |
| Shared household categories, add/remove custom | ✅ | |
| Recurring expenses (frequency, start/end, inflation, financing, owner) | ✅ (financing now actually applied) | |
| One-time purchases (financing, asset type, appreciation) | ✅ (edit & delete, which V13 lacked) | |
| Custom named templates per location | ✅ | Save, edit, delete; offered as a lifestyle for that place in Moves, Assumptions and Spending |
| Save a template as a new city | ✅ | Creates the place under My places, taxed and priced like the source |
| Custom locations / world map | ✅ | My places (map position, taxed like, prices like); Where you live page with Equal Earth map and flight paths |

## Where you live (v0.8 Settings → location timeline)
| Feature | Status |
|---|---|
| Location & lifestyle timeline (moves) | ✅ |
| Timeline Gantt, "now / next 5 years", relocation journey text | ✅ |
| Everyday prices and rent follow moves | ✅ New; can be turned off to match v0.8 |
| Tax rules per location, including countries | ✅ |

## Kids
| Feature | Status |
|---|---|
| Children list, duplicate-name prevention | ✅ |
| Template location & lifestyle, public/private school, college type & location | ✅ |
| Cost by age range, lifetime and peak | ✅ |
| CSV export/import of the per-age cost table | ✅ (per child) |
| Template explorer (costs by age before adding a child) | ✅ |

## Homes
| Feature | Status |
|---|---|
| Multiple homes, owner, value, mortgage, tax, insurance, maintenance, upkeep, appreciation | ✅ |
| Timeline: live in / rent out (monthly rent) / sell | ✅ |
| Equity by owner | ✅ |
| Mortgage calculator: estimate or actual loan | ✅ new |
| PMI, HOA, closing costs, property tax as % or $/yr, amortization chart | ✅ new |

## Healthcare
| Feature | Status |
|---|---|
| Health insurance plans by age range | ✅ |
| Medicare B/D/Medigap | ✅ (2026 Part B default) |
| Long-term care premiums | ✅ (benefits stored, not modeled) |
| Health expenses | ✅ (now used in projections) |
| HSA balance/contribution | ✅ (pre-tax bucket) |
| Summary tiles (this year, Medicare at 65, lifetime) | ✅ |

## Assumptions
| Feature | Status |
|---|---|
| Investment return, inflation, healthcare inflation, expense growth (stored) | ✅ |
| Historical-average buttons + historical returns chart & stats | ✅ |
| SS insolvency (cut %, start year) | ✅ (+ COLA toggle) |
| Tax: 401(k), state override, filing status | ✅ |
| State/country timeline (moves) | ✅ |
| Monte Carlo: runs, traditional asymmetric / symmetric, historical, today's $ | ✅ (+ allocation, sequential sampling) |
| Monte Carlo start year / horizon overrides | ➖ v0.8 stored them but the simulation ignored them |

## Analysis
| Feature | Status |
|---|---|
| Dashboard with key metrics & alerts | ✅ v0.8 alerts ported (separate-finance per person, peak/drawdown, healthcare share, years covered, plan end) plus health lights and peer comparison |
| Deterministic cashflow chart + year-by-year table with drill-down | ✅ |
| Cashflow explorer: timeline with surplus/deficit and event stars, year drill-down (donuts, Sankey, full expense summary, taxes) | ✅ |
| Cashflow "critical years" and "life stages" views | ✅ Life stages use planned retirement ages and the youngest living adult |
| CSV export of the projection | ✅ (+ line-item detail option) |
| Monte Carlo fan chart (10/25/50/75/90), success rate, final stats | ✅ |
| Median-return statistic in MC summary | ⏳ Minor |
| Timeline of life events | ✅ (swim lanes + by decade; career-phase changes now included) |
| Taxes by year | ✅ |
| Retirement tab: early/delayed comparison, replacement ratio, 80% target | ✅ |
| Stress tests: market crash, disabled child, unemployment, hyperinflation | ✅ All v0.8 defaults, "worst possible year" search, stoplight by percentile, verdict. Plus extra cost, early death, compound tests |
| Stress: worst-case child picked automatically | ✅ |
| Stress: compound test in a chosen year | ✅ |
| Actuals entry, plan vs actual | ✅ Planned categories come from the engine (cost of living, deaths, owned homes applied); healthcare split into premiums / Medicare / LTC / out of pocket; per-child categories; unplanned purchases |
| Excel tracking workbook | ✅ Per-child sections, monthly columns, variance formulas, import merges back |
| Excel "include charts" option | ⏳ Charts are in the PDF |
| Multi-file CSV export | ➖ One CSV or a multi-sheet Excel file instead |
| PDF report export | ✅ Choose sections; landscape; charts; every input table; year-by-year amounts by category; 10-year line-item blocks; check-ins; numbered data sources |
| Report formats | ✅ PDF, Excel (one sheet per section + Sources), CSV, JSON; today's or future dollars |

## Data sources
Every major dataset the app relies on is listed in `engine/finplan/data/sources.json` and cited in the app as a small [n] marker, with linked sources at the bottom of the page and at the end of reports.
