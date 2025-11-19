# Lifetime Cashflow Visualization - Design Proposal

## Overview

Create a comprehensive "Lifetime Cashflow" tab that shows how money flows through your life from now until age 100, with multiple visualization layers.

---

## Proposed Visualizations

### 1. **Primary Timeline View** (Main Dashboard)

**Type**: Dual-axis line chart with area fills and event markers

**Shows**:
- Income (green line)
- Expenses (red line)
- Net Cashflow (blue area - shaded positive/negative)
- Major life events (markers)

**Example**:
```
        Income/Expenses ($)

$500k   ╱‾‾‾‾‾╲                    Retirement
        |      ╲                   ↓
$400k   |       ‾‾‾‾╲             ╱‾‾‾‾‾
        |            ╲           ╱
$300k   |             ‾‾‾‾‾╲   ╱
        |                   ╲╱
$200k   |___________________
        |  ┌College─┐  ┌College─┐
$100k   |  │ Peak  │  │ Peak  │
        |__│_______│__│_______│________
$0      └──┴───────┴──┴───────┴────────
        2025  2030    2040    2050  2060

        ■ Income   ■ Expenses   ▓ Net Cashflow (positive)   ░ Deficit (negative)
```

**Key Features**:
- Hover to see exact values for any year
- Click to zoom into time periods
- Toggle income sources (salary, SS, investments)
- Toggle expense categories
- Mark key events:
  - Job changes (💼)
  - Children entering college (🎓)
  - Retirement start (🏖️)
  - Major purchases (🏠)

---

### 2. **Waterfall View** (Net Worth Changes)

**Type**: Waterfall chart showing year-by-year changes

**Shows**: How net worth changes each year due to:
- Income (green bars going up)
- Expenses (red bars going down)
- Investment returns (blue bars)
- Cumulative net worth (connecting line)

**Example**:
```
Starting NW: $500k
  +$200k income ↑
  -$80k expenses ↓
  +$35k investment returns ↑
= $655k end of year 1
  +$206k income ↑
  -$85k expenses ↓
  +$46k investment returns ↑
= $822k end of year 2
  ...
```

**Benefits**:
- See exactly what drives net worth changes
- Identify years of growth vs decline
- Understand compound effect over time

---

### 3. **Expense Breakdown** (Stacked Area Chart)

**Type**: Stacked area chart showing composition of expenses over time

**Categories**:
- Housing (mortgage, property tax, maintenance)
- Children Education (age-dependent, shows spikes)
- Food & Groceries
- Healthcare
- Transportation
- Entertainment
- Other

**Example**:
```
$200k ┌────────────────────────────────
      │         ┌──────────┐
      │         │EDUCATION │  ← College years spike
      │   ┌─────┤(Children)│
$150k │   │     └──────────┘
      │   │ HEALTHCARE
      │   ├─────────────────
$100k │   │ HOUSING
      │   ├─────────────────
      │   │ FOOD
$50k  │   ├─────────────────
      │   │ OTHER
$0    └───┴─────────────────
      2025    2040    2055
```

**Benefits**:
- See which expenses dominate in each life phase
- Understand how children's aging affects total expenses
- Plan for expense spikes (college years)

---

### 4. **Income Composition View**

**Type**: Stacked area chart for income sources

**Sources**:
- Parent 1 Salary (with job changes visible as steps)
- Parent 2 Salary (with job changes visible as steps)
- Social Security (starting at retirement)
- Investment Returns
- Rental Income
- Other Income

**Example**:
```
$600k ┌────────────────────────────
      │ INVESTMENTS
      │ ───────────────────
$500k │     │ SS Benefits
      │     ├──────────────
      │ P1  │
$400k │Salary│
      │(job  │
      │changes)
$300k │─────┘
      │ P2 Salary
$200k │──────────────────
      │
$100k │
      │
$0    └────────────────────
      2025  2040  2060  2080
           Retirement →
```

**Benefits**:
- See transition from working to retirement income
- Visualize impact of job changes as steps up
- Understand diversification of income sources

---

### 5. **Critical Years Table** (Data View)

**Type**: Sortable table showing detailed breakdown

**Columns**:
- Year
- Ages (Parent1/Parent2)
- Income
- Expenses
- Cashflow
- Children (who's in college)
- Net Worth
- Notes (job changes, major events)

**Highlighting**:
- 🔴 Red rows: Negative cashflow years
- 🟡 Yellow rows: College overlap years
- 🟢 Green rows: High savings years
- 💼 Blue rows: Job change years

**Sortable by any column** to find:
- Worst cashflow years
- Best savings years
- Peak expense years

**Example**:
```
| Year | Ages  | Income  | Expenses | Cashflow | Children      | Net Worth | Notes           |
|------|-------|---------|----------|----------|---------------|-----------|-----------------|
| 2025 | 35/33 | $270k   | $95k     | +$175k   | Ages 5, 3     | $500k     |                 |
| 2030 | 40/38 | $329k   | $110k    | +$219k   | Ages 10, 8    | $1.2M     | P1 job change   |
| 2038 | 48/46 | $420k   | $178k    | +$242k   | Emma college  | $2.5M     | 🎓 College      |
| 2040 | 50/48 | $455k   | $211k    | +$244k   | Both college  | $3.1M     | 🎓 Peak overlap |
| 2060 | 70/68 | $78k SS | $85k     | -$7k     | None          | $4.2M     | 🏖️ Retired     |
```

---

### 6. **Scenario Comparison View**

**Type**: Side-by-side comparison of different scenarios

**Scenarios to compare**:
- Base case (current plan)
- All children public vs all private
- Different job change timelines
- Earlier/later retirement
- Different investment returns

**Example**:
```
                Base Case    All Private    Early Retire
Peak Expenses:  $146k/yr    $220k/yr       $146k/yr
Retirement NW:  $3.5M       $2.1M          $2.8M
Success Rate:   95%         78%            88%
Years Deficit:  2 years     8 years        5 years
```

**Visualization**: Overlay multiple scenarios on same chart with different colors

---

### 7. **Sankey Diagram** (Annual Flow)

**Type**: Sankey diagram for a selected year

**Shows**: Flow of money from sources to uses

**Example for Year 2040**:
```
Income Sources          →          Expense Categories

Parent 1 Salary $240k ──┐
                        ├─→ Housing $45k
Parent 2 Salary $165k ──┤
                        ├─→ Children Education $66k (2 in college!)
SS Benefits $0 ─────────┤
                        ├─→ Food $15k
Investments $50k ───────┤
                        ├─→ Healthcare $12k
                        │
                        ├─→ Transportation $8k
                        │
                        ├─→ Other $20k
                        │
                        └─→ Net Savings $289k → Net Worth
```

**Interactive**: Click on any flow to see details

---

### 8. **Life Stage Summary**

**Type**: Summary cards for major life phases

**Phases**:
1. **Young Family (2025-2035)**: Kids ages 0-15
   - Avg Income: $310k/yr
   - Avg Expenses: $105k/yr
   - Avg Savings: $205k/yr
   - Net Worth Growth: $500k → $2.1M

2. **College Years (2036-2043)**: Kids in college
   - Avg Income: $435k/yr
   - Avg Expenses: $185k/yr (peak $211k)
   - Avg Savings: $250k/yr
   - Net Worth Growth: $2.1M → $4.3M
   - ⚠️ Peak stress: 2040-2041 with 2 in college

3. **Empty Nest (2044-2059)**: Kids done, still working
   - Avg Income: $550k/yr
   - Avg Expenses: $95k/yr
   - Avg Savings: $455k/yr
   - Net Worth Growth: $4.3M → $9.2M

4. **Retirement (2060-2092)**: Both retired
   - Avg Income: $78k/yr (SS) + investments
   - Avg Expenses: $85k/yr
   - Drawdown Phase: Living on savings + SS
   - Net Worth at 100: $5.8M (if 4% rule)

---

## Implementation Priority

### Phase 1 (High Priority - Implement First)
1. ✅ Primary Timeline View (most important!)
2. ✅ Critical Years Table
3. ✅ Life Stage Summary

### Phase 2 (Medium Priority)
4. Expense Breakdown Stacked Chart
5. Income Composition View
6. Waterfall View

### Phase 3 (Nice to Have)
7. Scenario Comparison
8. Sankey Diagram (interactive)

---

## Technical Implementation

### New Tab: "💰 Lifetime Cashflow"

Add after the Monte Carlo tab, containing:

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│ 💰 Lifetime Cashflow Visualization                  │
│                                                      │
│ [Timeline View] [Breakdown] [Table] [Phases]        │ ← Tabs
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │  Chart Area (Primary Visualization)           │   │
│ │                                               │   │
│ │  [Interactive Plotly Chart]                   │   │
│ │                                               │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │  Controls                                     │   │
│ │  [Year Range Slider]                          │   │
│ │  [☐ Show Job Changes] [☐ Show College Years] │   │
│ │  [☐ Normalize to Today's Dollars]             │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │  Key Insights (Auto-generated)                │   │
│ │  • Peak expense year: 2040 ($211k)            │   │
│ │  • Years with deficit: 2061-2063 (3 years)    │   │
│ │  • College overlap: 2040-2041 (2 children)    │   │
│ │  • Retirement net worth: $4.2M (age 65)       │   │
│ └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Data Structure

```python
def calculate_lifetime_cashflow():
    """Calculate year-by-year cashflow for entire lifetime"""

    results = []

    for year in range(current_year, timeline_end + 1):
        # Calculate income
        income = get_total_income_for_year(year)
        income_breakdown = {
            'parent1_salary': ...,
            'parent2_salary': ...,
            'ss_benefits': ...,
            'investments': ...,
        }

        # Calculate expenses
        expenses = get_total_expenses_for_year(year)
        expense_breakdown = {
            'housing': ...,
            'children_education': ...,
            'food': ...,
            'healthcare': ...,
            'other': ...,
        }

        # Calculate cashflow
        cashflow = income - expenses

        # Track events
        events = []
        if has_job_change(year):
            events.append(('job_change', parent, new_income))
        if children_in_college(year):
            events.append(('college', children_names))
        if is_retirement_year(year):
            events.append(('retirement', parent))

        results.append({
            'year': year,
            'ages': (parent1_age, parent2_age),
            'income': income,
            'income_breakdown': income_breakdown,
            'expenses': expenses,
            'expense_breakdown': expense_breakdown,
            'cashflow': cashflow,
            'net_worth': cumulative_net_worth,
            'events': events
        })

    return results
```

---

## Example Visualizations with Real Data

### Young Family Example (From Test Family 1)

**Timeline View 2025-2092**:
- See income grow from $270k → $456k (peak working years) → $78k (SS)
- Watch expenses spike during college years (2038-2043)
- Observe positive cashflow throughout working years
- See modest deficit in late retirement if not careful

**Critical Years**:
- 2040-2041: Peak college overlap ($66k/yr education)
- 2060: Retirement starts, income drops from $500k+ to $78k SS
- 2070-2080: Potential deficit years if not enough saved

**Life Stages**:
- Young Family (2025-2037): Building wealth, $205k/yr savings
- College Years (2038-2043): Still saving but slower, $180k/yr
- Empty Nest (2044-2059): Maximum savings, $400k/yr
- Retirement (2060-2092): Drawing down, need $3.5M+ to sustain

---

### Wealthy Family Example (From Test Family 2)

**Timeline View 2025-2092**:
- High income $550k+ throughout career
- Massive expense spike 2035-2036 ($164k/yr - 2 in private college)
- Still extremely positive cashflow even during college
- Comfortable retirement

**Critical Years**:
- 2025: Current - $83k/yr for private K-12
- 2033-2038: College years ($88k-$164k/yr)
- Peak: $164k/yr when both in private college
- Retirement: Still $300k+ cushion even with $85k expenses

**Life Stages**:
- Current (2025-2032): $467k/yr average savings
- College Years (2033-2038): $386k/yr savings (still huge!)
- Empty Nest (2039-2065): $500k+/yr savings
- Retirement: Could sustain $200k/yr lifestyle indefinitely

---

## User Benefits

### What You'll See Instantly:

1. **"When am I most vulnerable?"**
   - Red zones on timeline = deficit years
   - Usually: late retirement if undersaved

2. **"When do I have the most flexibility?"**
   - Green zones = high surplus years
   - Usually: empty nest years (40s-50s)

3. **"What's my biggest expense driver?"**
   - Stacked chart shows education often exceeds housing
   - For family with 2 in private college: education = 50% of all expenses!

4. **"When should I accelerate savings?"**
   - Before college years hit
   - During peak earning years (empty nest)

5. **"Can I afford early retirement?"**
   - Compare scenarios: see exact impact on deficit years

6. **"What if both kids go private vs public?"**
   - Scenario comparison shows: $1.5M difference in net worth at retirement!

---

## Next Steps

Would you like me to:

1. **Implement Phase 1** (Timeline View, Table, Life Stages)?
   - Most impactful visualizations
   - Can be done in ~1-2 hours

2. **Create a mockup** with your actual family data?
   - Show you exactly what your lifetime cashflow would look like

3. **Start with simpler version**?
   - Just income vs expenses line chart first
   - Then iterate based on feedback

4. **All of the above**?
   - Full implementation of comprehensive cashflow visualization

Let me know which approach you prefer, and I'll get started!
