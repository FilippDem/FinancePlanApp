# Engine validation against published figures

_Run 2026-10-12. Rerun: `python tools/validate_benchmarks.py v2` (from the repo root) and `python tools/fuzz_engine.py v2 300`. The core checks are also pytest tests in `engine/tests/test_benchmarks.py`._

## Result
**33 of 33 checks are within tolerance. Fuzzing ran 300 random and extreme plans with 0 failures.**

Seven problems were found and fixed along the way:

| Problem | Effect before the fix | Fix |
|---|---|---|
| **State income tax used each state's top rate on all taxable income** (30 states) | California, $200k couple: $22,600 instead of $10,350 (+123%). Tech Couple, Single Mom and Executives demos were heavily overtaxed. | 2025 brackets, standard deductions and exemptions for all 41 income-tax states + DC (`data/state_income_tax_2025.json`). Gains are stacked on other income in the state brackets. |
| **The old state table was stale** | WV 6.5% vs 4.82%, NE 6.84% vs 5.2%, and 9 others; GA, IA and LA are flat now | Replaced by the 2025 table |
| **A single person's plan counted the absent partner's savings** | The default plan's $40k partner balance was added: $100k grew like $140k | The engine ignores partner balances while the plan is single. The stored fields are kept. |
| **Federal tables were 2024 values indexed by the plan's inflation** | 2026 federal tax 1–2% high; SS wage base $178,868 vs $184,500 | 2026 brackets, standard deduction, capital-gains thresholds and wage base (Rev. Proc. 2025-32, SSA) |
| **Additional Medicare Tax was applied per person** | Two $200k earners: $1,350/yr under-taxed | 0.9% on the couple's combined wages above $250k |
| **Social Security default cut of 30%** | Nearly twice the Trustees' figure | 17% from 2034 (2026 Trustees, combined funds). Saved plans keep their own setting. |
| College fallback (checked, no change needed) | — | Tuition + room & board already match the College Board national averages. The remaining gap is the student's other costs. |

## All checks
| Area | Check | App | Benchmark | Diff | Source |
|---|---|---|---|---|---|
| Federal tax | MFJ, $100,000 wages, 2026 federal income tax | 7,640 | 7,640 | +0.0% | IRS Rev. Proc. 2025-32 |
| Federal tax | MFJ, $200,000 wages | 26,340 | 26,340 | +0.0% | IRS Rev. Proc. 2025-32 |
| Federal tax | MFJ, $400,000 wages | 73,468 | 73,468 | +0.0% | IRS Rev. Proc. 2025-32 |
| FICA | wages 200,000 + 0 | 14,339 | 14,339 | +0.0% | SSA 2026 wage base |
| FICA | wages 200,000 + 200,000 | 30,028 | 30,028 | +0.0% | IRS Additional Medicare Tax (joint threshold) |
| State tax | California MFJ, $200,000 | 10,350 | 10,350 | +0.0% | CA FTB 2025 schedule, by hand |
| State tax | Oregon MFJ, $150,000 | 11,517 | 11,517 | +0.0% | OR 2025 brackets, by hand |
| State tax | Colorado MFJ, $150,000 | 5,280 | 5,183 | +1.9% | CO: 4.4% of federal taxable income |
| Mortgage | $800k, 6.5%, 30 yr monthly P&I | 5,056.54 | 5,056.54 | +0.0% | Amortization formula |
| RMD | Uniform Lifetime divisors at 73/75/80/90 | 26.5/24.6/20.2/12.2 | same | 0% | IRS Pub. 590-B Table III |
| RMD | Start age, born 1955 / 1962 | 73 / 75 | 73 / 75 | 0% | SECURE 2.0 |
| Social Security | Benefit factor claiming at 62 / 67 / 70 (FRA 67) | 0.70 / 1.00 / 1.24 | same | 0% | SSA |
| Social Security | Default cut and year | 17% from 2034 | 17% from 2034 | 0% | 2026 Trustees Report |
| Market data | S&P 500 arithmetic / geometric mean, std dev | 12.1% / 10.3% / 19.4% | 11.8% / 9.9% / 19.5% | ≤3.3% | Damodaran 1928-2024 |
| 4% rule | 30 years, every historical start, 100 / 75 / 50% stocks | 96 / 98 / 99% | ~95% | +1 to +4 pts | Trinity study, cFIREsim |
| Kids | Seattle "Average" child, birth to 17 (2026 $) | 312,520 | 319,000 (national) | −2.0% | USDA (2015 child) inflated |
| College | Public in-state, one year incl. student costs (2026 $) | 36,494 | 31,732 | +15.0% | College Board full budget 2024-25 |
| College | Private, one year incl. student costs (2026 $) | 72,225 | 66,826 | +8.1% | College Board full budget 2024-25 |
| Healthcare | Lifetime retiree healthcare, single, 65–87, nominal | 190,589 | 172,500 | +10.5% | Fidelity 2025 estimate |
| Spending | Default two-adult Seattle "Average" budget | 107,140 | 94,242 | +13.7% | BLS CE 2024 × Seattle price level |
| Math | $100k at 6% for 30 years | 574,349 | 574,349 | 0% | Compound interest |
| Math | MC median, 30 yrs, 6% mean, 15% sd | 418,224 | 425,329 | −1.7% | Lognormal volatility drag |

## Known limits (not fixed; the direction of the bias is noted)
- **Historical mode uses fixed 4% bonds and the plan's inflation**, not historical bond returns and CPI. The 4% rule comes out 1–4 points more optimistic than studies that use real bond and inflation history, which hurt 1966–1982 retirees.
- **No yearly tax on dividends/interest in taxable accounts.** Taxable savings grow slightly too fast (about 0.3–0.5%/yr for a stock index fund at 15% tax), and the Roth sweep's benefit is understated.
- **Wages don't rise with inflation shocks** (only the stress tests pass part of the shock through).
- **State tax simplifications:** Social Security is excluded everywhere (a few states tax part of it). There are no phase-outs, AGI-based deductions or local income taxes (NYC adds about 3–4%, Portland's Metro/Multnomah taxes are 1.5–4%).
- **Social Security for top earners:** guided setup's estimate assumes 35 years at today's capped wage, about 5% above SSA's published maximum. Entering the figure from ssa.gov/myaccount is best.
- **College** (+8–15%): a student's food and transport are reduced but not removed while room & board is also charged.

## Sources
[1] IRS, [Rev. Proc. 2025-32 / 2026 inflation adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill)
[2] SSA, [Contribution and benefit base](https://www.ssa.gov/oact/cola/cbb.html)
[3] Tax Foundation, [State individual income tax rates and brackets, 2025](https://taxfoundation.org/data/all/state/state-income-tax-rates/)
[4] SSA, [2026 Trustees Report](https://www.ssa.gov/news/en/press/releases/2026-06-09.html)
[5] Damodaran, [Historical returns on stocks, bonds and bills](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)
[6] College Board, [Trends in College Pricing 2025](https://research.collegeboard.org/trends/college-pricing/highlights)
[7] Fidelity, [2025 Retiree Health Care Cost Estimate](https://www.businesswire.com/news/home/20250730447812/en)
[8] BLS, [Consumer Expenditures 2024](https://www.bls.gov/news.release/cesan.nr0.htm)
[9] USDA / Brookings, [cost of raising a child](https://www.brookings.edu/articles/the-cost-of-raising-a-child/)
[10] Trinity study summary, [ChooseFI](https://choosefi.com/four-percent-rule), and the [Poor Swiss update](https://thepoorswiss.com/updated-trinity-study)
