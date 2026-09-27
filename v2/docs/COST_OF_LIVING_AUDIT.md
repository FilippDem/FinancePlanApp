# Cost-of-living data audit (2026-09-26)

This audit covers the spending templates the app inherited from v0.8: per-adult templates for 24 cities, 50 states and 10 provinces, each at three lifestyles; the children's per-age templates; and the tuition, room & board and private-school tables. They were compared with public benchmarks.

- The benchmark numbers and their sources are in `docs/data/col_benchmarks.json`.
- The full proposal is in `docs/data/col_proposed_fixes.json`.
- The fixes that were applied are in `engine/finplan/data/reference_corrections.json`. They're applied on top of the untouched v0.8 extract by `reference.ref()`. `reference.ref_raw()` still returns the v0.8 numbers, and setting `FP_RAW_REFERENCE=1` turns the corrections off.

## Summary

| Check | Result |
|---|---|
| Structure | ✅ All 84 locations have all 3 lifestyles and the same 23 categories, with no missing or negative values. Children arrays have 31 entries each |
| Lifestyle ordering | ✅ Conservative < Average < High-end everywhere, in total and in every category |
| **Relative cost between locations** | ❌ **About 20 of 24 cities were off by more than 10%.** This matters now because moving scales spending by these ratios |
| **Duplicate templates** | ❌ Seattle = Munich, Portland = Toronto = Brisbane, Vancouver = Melbourne, Toulouse = Auckland. Every international city was just Seattle × a constant |
| **Absolute level** | ⚠️ "Average" is about 2× what BLS says the average adult spends (see the decision below) |
| Lifestyle ratios | ⚠️ In the 18 original cities, High-end/Average was 1.73; everywhere else it was 1.50 |
| State "Medical" | ⚠️ 2,300–3,200 per adult, which looks like it includes insurance premiums. That double counts with the Healthcare page |
| Children | ⚠️ College-age reductions never applied to generated templates. Daycare was a flat $22k everywhere. Generated templates gave teens a car payment |
| Rent when moving | ⚠️ Rent was scaled by the everyday-prices ratio, but rents vary far more than other prices |

## What was off (before the fix)

Average per-adult totals relative to Seattle, compared with the benchmark: the geometric mean of the BEA 2024 all-items Regional Price Parity and the Numbeo 2025 cost-of-living index (excluding rent).

| City | Template ÷ Seattle | Benchmark ÷ Seattle | Error | Scale applied |
|---|---|---|---|---|
| Columbus | 0.58 | 0.85 | −32% | ×1.468 |
| San Diego | 0.78 | 1.00 | −22% | ×1.283 |
| Miami | 0.78 | 0.97 | −20% | ×1.243 |
| Chicago | 0.77 | 0.93 | −17% | ×1.209 |
| Honolulu | 0.87 | 1.05 | −17% | ×1.204 |
| Washington DC | 0.86 | 0.99 | −13% | ×1.148 |
| San Francisco | 1.36 | 1.09 | +24% | ×0.805 |
| New York | 1.32 | 1.13 | +17% | ×0.857 |
| Los Angeles | 1.16 | 0.99 | +16% | ×0.860 |
| Paris | 1.20 | 0.86 | +39% | ×0.720 |
| Melbourne / Vancouver / Brisbane / Sydney | 1.05–1.20 | 0.78–0.87 | +28 to +36% | ×0.735–0.779 |
| Toronto, Wellington, Toulouse, Auckland, Munich, Berlin | | | +13 to +22% | ×0.819–0.889 |
| Sacramento, Houston, Portland | | | within ±5% | unchanged |

## Fixes applied (`reference_corrections.json`)

1. **Location scale** for the cities above, plus Ontario and British Columbia (×0.819 and ×0.757, lower confidence).
2. **Lifestyle scale.** Every location now has Conservative = 0.70× and High-end = 1.50× Average, the convention 66 of the 84 locations already used. The BLS income quintiles support a top-to-middle ratio of 1.5–2.0.
3. **State Medical** is replaced with out-of-pocket levels, about 1,100–1,240 at Average scaled by state prices; premiums belong on the Healthcare page. All other state categories are ×1.084, so states sit on the same price line as the Seattle anchor.
4. **District of Columbia** now uses the Washington DC template. It used to fall back to Seattle silently.
5. **Children**:
   - Daycare by city, from Child Care Aware 2024: for example Miami $11.9k and Chicago $20.1k at Average, instead of a flat $22k. Houston's daycare is ×0.65 and Sacramento's ×0.81.
   - College-age reductions now apply to the new category names (groceries and transport shrink while living at college).
   - Generated templates no longer give teens a car payment. Model a teen's car as a one-time purchase.
6. **Education.**
   - Fallbacks now use College Board 2024-25: public $11,610; private $43,350; room & board $13,310, plus $1,940 at private schools.
   - Private K-12 fees added for Chicago, Miami, Columbus, Honolulu, San Diego and DC; the fallback is now $13,300.
7. **Moving (engine).** "Mortgage/Rent" scales by the BEA 2024 rent index (for example Houston 0.69, SF 1.29 relative to Seattle). Everything else scales by the everyday-prices ratio.

## Resolution: the absolute level (decided 2026-09-26)

Seattle "Average" in v0.8 is **$36,520 per adult per year** for groceries, dining, transport, clothing, personal care, out-of-pocket health and entertainment. BLS Consumer Expenditure data [1][2], priced for Seattle with BEA price parities [3], puts the average adult at about **$18,000**. The v0.8 template sits closer to the top income fifth. For example, its $6,000 of groceries per adult exceeds USDA's *Liberal* food plan.

Instead of renaming or rescaling the three lifestyles, spending is now a **slider** calibrated to public data (`engine/finplan/calibrate.py`, `data/cost_index.json`):

- **Spending levels** come from BLS CE Table 1101, the 2022 income fifths [1], grown to 2024 totals ($78,535 per household) [2]. They are converted to per adult as household ÷ (adults + 0.5 × children).
- **Local prices** come from BEA 2024 Regional Price Parities [3]: goods and services for everyday categories, rents for "Mortgage/Rent". For 2024, states range from 86.9 (Arkansas) to 110.7 (California), and rents from 54.2 to 154.3. Outside the US, World Bank price levels are used [4]. These are rough: economy-wide, 2020 values, and sensitive to exchange rates.
- **Milestones on the slider:**
  - Bare-bones (lowest fifth), Frugal, Middle, the local average, the US average, Upper-middle, Top 20%.
  - The old v0.8 "Average" and "High-end" levels stay reachable as "Old app" marks, about twice the BLS figures.
- **Lifestyle names map to positions:** Conservative is about the second fifth, Average the US average, High-end the top fifth. Old plans and moves keep working.
- **Where the old numbers are still used:** the templates can still be applied with the "v0.8 original (audited)" data option. They also remain the basis for children's costs [5], with daycare [6] and college [7] corrections.

| Seattle, per adult, 2024 $ | v0.8 template | Calibrated |
|---|---|---|
| Conservative | $25,560 (after audit ×0.70) | $13,440 (second fifth) |
| Average | $36,520 | $18,030 (US average at Seattle prices) |
| High-end | $54,820 (after audit ×1.50) | $24,230 (top fifth) |

The slider moves every category: untouched ones follow the curve, edited ones keep their proportion to it, and custom categories scale with the total. Spending already entered is never changed until you move the slider or apply a template.

## Not fixed yet
- International cities still carry Seattle's category mix (for example Paris car payments). They need rebuilding from local data.
- Family templates use an old schema that overlaps the per-adult templates and has no housing. They're not used by the v2 pages.
- Provinces are StatCan 2022 data converted at 0.74 USD/CAD with no inflation adjustment (about −6%).

## Sources
[1] BLS, [Consumer Expenditure Surveys, Table 1101: quintiles of income before taxes, 2022](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2022.pdf)
[2] BLS, [Consumer Expenditures — 2024](https://www.bls.gov/news.release/cesan.nr0.htm) (released Dec 19, 2025)
[3] BEA, [Regional Price Parities by State and Metro Area, 2024](https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area), via [FRED state tables](https://fred.stlouisfed.org/release/tables?eid=233639&rid=403) and [metro tables](https://fred.stlouisfed.org/release/tables?eid=233895&rid=403)
[4] World Bank WDI, [Price level ratio of PPP conversion factor (GDP) to market exchange rate](https://data.worldbank.org/indicator/PA.NUS.PPPC.RF), 2020 values via [indexmundi](https://www.indexmundi.com/facts/indicators/PA.NUS.PPPC.RF/rankings)
[5] MIT, [Living Wage Calculator](https://livingwage.mit.edu/) (basis of the v0.8 templates)
[6] Child Care Aware of America, [Child Care in America: 2024 Price & Supply](https://www.childcareaware.org/price-landscape24/)
[7] College Board, [Trends in College Pricing](https://research.collegeboard.org/trends/college-pricing)
[8] Numbeo, [Cost of Living](https://www.numbeo.com/cost-of-living/) (crowdsourced; used only to cross-check international cities)
[9] HUD, [Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr.html) (rent index where BEA has no figure)

The app cites the same list in the UI and reports; see `engine/finplan/data/sources.json`.
