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

## Decision still open: the absolute level

Seattle "Average" is **$36,520 per adult per year** for groceries, dining, transport, clothing, personal care, out-of-pocket health and entertainment. BLS Consumer Expenditure 2024, adjusted to Seattle prices, puts the *average* adult at about **$17,300**. The template is closer to the top income quintile (about $23–24k per adult × 1.5). For example, groceries of $6,000 exceed USDA's *Liberal* food plan ($5,245/yr).

Two options:
- **Keep the levels and rename the lifestyles**, for example Frugal / Comfortable / Affluent.
- **Scale everything by 0.55**, so "Average" means the BLS average.

This choice only affects templates when you apply them. Spending you've already entered is unchanged, and the relative levels used for moves don't depend on it. It has **not** been applied.

## Not fixed yet
- International cities still carry Seattle's category mix (for example Paris car payments). They need rebuilding from local data.
- Family templates use an old schema that overlaps the per-adult templates and has no housing. They're not used by the v2 pages.
- Provinces are StatCan 2022 data converted at 0.74 USD/CAD with no inflation adjustment (about −6%).
