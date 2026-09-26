# v0.8 → v2 feature parity

Status: ✅ in v2 · 🟡 partial · ⏳ not yet (planned) · ➖ not needed in v2

Data compatibility is ✅ for everything: v2 reads and writes the same household files and never drops keys, so features that aren't built yet keep their data.

## Accounts & data
| Feature | Status | Notes |
|---|---|---|
| Cloudflare Access sign-in (header) | ✅ | Same header. The email login is a dev/LAN fallback; set `ALLOW_DEV_LOGIN=0` behind Cloudflare. |
| Households: create, join by code, switch | ✅ | Same `households_index.json` and `households/<id>.json` |
| Encrypted households (passphrase) | ✅ | Same cipher, verified against v0.8-format files |
| Admin "test as new user" household | ✅ | |
| Auto-save with backups before every write | ✅ | Load-then-merge, 10 rolling backups, atomic writes |
| Named scenarios (save/load/rename/delete) | ✅ | Stored in the household file like v0.8 |
| Scenario comparison | ✅ | New: side-by-side chart + table (v0.8 only had a tip) |
| JSON export/import (v0.8, V14, V13 formats) | ✅ | V13 migration covered by a test |
| Reset to defaults | ✅ | |
| Demo households | ✅ | Numbers change, see ENGINE_CHANGES.md |
| Users tab: member list, invite code | 🟡 | Members and code show in the household picker |
| Version history / "What's new" | ⏳ | Server keeps 10 backups per household already |

## People & income
| Feature | Status |
|---|---|
| Names, emojis, current year, marriage year | ✅ |
| Age, net worth, retirement age, life expectancy, SS benefit | ✅ (+ SS claim age, pre-tax balance) |
| Income, raise %, job changes (with optional new raise %) | ✅ |
| Career phases (salary, raise, bonus, RSUs, options) | ✅ |
| Pooled / Separate finances with split % | ✅ |
| Single-person plans | ✅ |
| Setup wizard | ✅ TurboTax-style guided setup (`/setup`): one question per screen, 8 sections, live plan preview, review & edit; covers v0.8 wizard phase 1 + 2 (moves, HSA, custom purchase names and career phases are edited afterward on their pages) |
| Guided mode / tab walkthroughs | ⏳ |

## Spending
| Feature | Status |
|---|---|
| Per-person categories (grouped) + location/lifestyle templates | ✅ |
| Shared household categories, add/remove custom | ✅ |
| Recurring expenses (frequency, start/end, inflation, financing, owner) | ✅ (financing now actually applied) |
| One-time purchases (financing, asset type, appreciation) | ✅ (edit & delete, which V13 lacked) |
| Custom named templates per location | ⏳ |
| Custom locations / world map | ⏳ |

## Kids
| Feature | Status |
|---|---|
| Children list, duplicate-name prevention | ✅ |
| Template location & lifestyle, public/private school, college type & location | ✅ |
| Cost by age range, lifetime and peak | ✅ |
| CSV export/import of the per-age cost table | ✅ (per child) |

## Homes
| Feature | Status |
|---|---|
| Multiple homes, owner, value, mortgage, tax, insurance, maintenance, upkeep, appreciation | ✅ |
| Timeline: live in / rent out (monthly rent) / sell | ✅ |
| Equity by owner | ✅ (engine; chart shows per property) |
| Mortgage calculator: estimate (price / down % / term / rate) or actual loan (balance, rate, years, real payment) | ✅ new |
| PMI, HOA, closing costs, property tax as % or $/yr, amortization chart | ✅ new |

## Healthcare
| Feature | Status |
|---|---|
| Health insurance plans by age range | ✅ |
| Medicare B/D/Medigap | ✅ |
| Long-term care premiums | ✅ (benefits stored, not modeled) |
| Health expenses | ✅ (now used in projections) |
| HSA balance/contribution | ✅ (pre-tax bucket) |

## Assumptions
| Feature | Status |
|---|---|
| Investment return, inflation, healthcare inflation | ✅ |
| Historical-average buttons + historical returns chart & stats | ✅ |
| SS insolvency (cut %, start year) | ✅ (+ COLA toggle) |
| Tax: 401(k), state override, filing status | ✅ |
| State/country timeline (moves) | ✅ |
| Monte Carlo: runs, traditional asymmetric / symmetric, historical, today's $ | ✅ (+ allocation, sequential sampling) |

## Analysis
| Feature | Status |
|---|---|
| Dashboard with key metrics & alerts | ✅ |
| Deterministic cashflow chart + year-by-year table with drill-down | ✅ |
| CSV export of the projection | ✅ |
| Monte Carlo fan chart (10/25/50/75/90), success rate, final stats | ✅ |
| Timeline of life events | ✅ (swim lanes + by decade) |
| Taxes by year | ✅ |
| Retirement tab: early/delayed comparison, replacement ratio, 80% target | 🟡 claim-age benefit per person; comparison table not yet |
| Cashflow "critical years" and "life stages" views, Sankey | ⏳ |
| Stress tests (market crash, disabled child, unemployment, hyperinflation) | ⏳ |
| Actuals entry, plan vs actual | 🟡 via **Check-ins**: quarterly/semiannual/annual cadence, due banner, guided and quick check-ins, on-track percentile, actual-vs-plan history, roll plan forward, .ics reminders. Q4 check-ins also write v0.8 `actuals[year].net_worth`. Detailed income/expense actuals: not yet |
| Excel tracking workbook | ⏳ |
| PDF report export | ⏳ |
