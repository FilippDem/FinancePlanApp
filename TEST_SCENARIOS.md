# Financial Planner Test Scenarios

This document outlines comprehensive test scenarios to verify the functionality and accuracy of the Financial Planner application.

## Test Family 1: Young Family with Public School Children

### Family Profile
- **Parent 1 (Filipp)**: Age 35, Income $150,000/yr, Net Worth $300,000
- **Parent 2 (Erin)**: Age 33, Income $120,000/yr, Net Worth $200,000
- **Children**:
  - Child 1: Age 5 (born 2020), Public K-12, Public College in Seattle
  - Child 2: Age 3 (born 2022), Public K-12, Public College in Seattle
- **Location**: Seattle, Average spending
- **Current Year**: 2025

### Expected Child Expenses (Per Year)

#### Child 1 (Age 5 in 2025):
- Base expenses from template: ~$7,000-9,000/yr
- K-12 Public school: $0 additional
- **Total**: ~$7,000-9,000/yr

#### Child 1 (Age 18 in 2038 - College):
- Public college tuition: $12,000/yr
- Room & board: $18,000/yr
- Reduced home expenses (food 30%, transport 40%, entertainment 50%)
- **Total**: ~$30,000-32,000/yr

#### Child 2 (Age 18 in 2040 - College):
- Same as Child 1
- **Total**: ~$30,000-32,000/yr

### Timeline Test
- Should extend from 2025 to 2090 (when younger parent reaches 100)
- Parent 1 reaches 100 in: 2025 + (100 - 35) = 2090
- Parent 2 reaches 100 in: 2025 + (100 - 33) = 2092
- Timeline should show: 2025 → 2092 (67 years)

### Monte Carlo Test
- Starting net worth: $500,000
- Combined income: $270,000/yr
- With raises, by retirement should be significantly higher
- 50th percentile at year 30 should show positive growth if expenses < income
- Cashflow should be positive during working years, potentially negative in retirement

---

## Test Family 2: Wealthy Family with Private Education

### Family Profile
- **Parent 1**: Age 40, Income $300,000/yr, Net Worth $2,000,000
- **Parent 2**: Age 38, Income $250,000/yr, Net Worth $1,500,000
- **Children**:
  - Child 1: Age 10 (born 2015), Private K-12, Private College in New York
  - Child 2: Age 8 (born 2017), Private K-12, Private College in San Francisco
- **Location**: New York, High-end spending
- **Current Year**: 2025

### Expected Child Expenses (Per Year)

#### Child 1 (Age 10 in 2025):
- Base expenses from template: ~$12,000-15,000/yr (High-end)
- Private school in New York: $35,000/yr
- **Total**: ~$47,000-50,000/yr

#### Child 1 (Age 18 in 2033 - Private College in NY):
- Private college tuition: $60,000/yr
- Room & board: $25,000/yr
- Reduced home expenses
- **Total**: ~$85,000-90,000/yr

#### Child 2 (Age 18 in 2035 - Private College in SF):
- Private college tuition: $58,000/yr
- Room & board: $24,000/yr
- **Total**: ~$82,000-88,000/yr

### Expected Total Education Costs
- Child 1: Private K-12 (8 yrs × $35k) + Private College (4 yrs × $85k) = $280k + $340k = $620,000
- Child 2: Private K-12 (10 yrs × $35k) + Private College (4 yrs × $82k) = $350k + $328k = $678,000
- **Total**: ~$1,300,000 in education expenses

### Property Ownership Test
- If they add a house, owner should show "Parent 1" and "Parent 2" names, not "ParentX/ParentY"
- Recurring expenses should also show actual names

---

## Test Family 3: Single Parent, Mixed Education

### Family Profile
- **Parent 1**: Age 45, Income $80,000/yr, Net Worth $150,000
- **Parent 2**: Age 45, Income $0/yr, Net Worth $0 (single parent)
- **Children**:
  - Child 1: Age 15 (born 2010), Public K-12, Public College in Sacramento
  - Child 2: Age 12 (born 2013), Private K-12, Private College in Sacramento
- **Location**: Sacramento, Conservative spending
- **Current Year**: 2025

### Expected Child Expenses (Per Year)

#### Child 1 (Age 15 in 2025 - Public High School):
- Base expenses: ~$6,000-8,000/yr (Conservative)
- Public school: $0 additional
- **Total**: ~$6,000-8,000/yr

#### Child 1 (Age 18 in 2028 - Public College):
- Public college tuition: $10,000/yr
- Room & board: $15,000/yr
- **Total**: ~$25,000-27,000/yr

#### Child 2 (Age 12 in 2025 - Private Middle School):
- Base expenses: ~$8,000-10,000/yr
- Private school: $18,000/yr
- **Total**: ~$26,000-28,000/yr

#### Child 2 (Age 18 in 2031 - Private College):
- Private college tuition: $50,000/yr
- Room & board: $15,000/yr
- **Total**: ~$65,000-70,000/yr

### Financial Stress Test
- Single income of $80,000
- Two children with mixed education (one private)
- When Child 2 is in private college (2031-2035), expenses will be very high
- Monte Carlo should show risk of running out of money if no additional savings

---

## Test Family 4: Retired Couple, No Children

### Family Profile
- **Parent 1**: Age 70, Income $0/yr (retired), SS Benefit $3,500/mo
- **Parent 2**: Age 68, Income $0/yr (retired), SS Benefit $3,000/mo
- **Combined Net Worth**: $2,000,000
- **Location**: Portland, Average spending
- **Current Year**: 2025

### Expected Calculations

#### Income (2025):
- Parent 1 SS: $3,500 × 12 = $42,000/yr
- Parent 2 SS: $3,000 × 12 = $36,000/yr
- Investment returns: ~7% × $2,000,000 = $140,000/yr
- **Total**: ~$218,000/yr

#### Timeline Test:
- Parent 1 reaches 100 in: 2025 + (100 - 70) = 2055
- Parent 2 reaches 100 in: 2025 + (100 - 68) = 2057
- Timeline should extend to 2057

#### Monte Carlo Considerations:
- No children expenses
- Fixed SS income (with potential insolvency risk after 2034)
- Should test 4% withdrawal rule sustainability
- With $2M portfolio and ~$100k/yr expenses, should be sustainable

---

## Test Family 5: Multiple Children, College Overlap

### Family Profile
- **Parent 1**: Age 42, Income $180,000/yr, Net Worth $600,000
- **Parent 2**: Age 40, Income $150,000/yr, Net Worth $400,000
- **Children**:
  - Child 1: Age 16 (born 2009), Public K-12, Public College in Seattle
  - Child 2: Age 14 (born 2011), Public K-12, Public College in Seattle
  - Child 3: Age 12 (born 2013), Public K-12, Private College in Seattle
  - Child 4: Age 10 (born 2015), Private K-12, Private College in Seattle
- **Location**: Seattle, Average spending
- **Current Year**: 2025

### College Overlap Years (Critical Test)

#### 2027-2028:
- Child 1 in college: $30,000/yr
- **Total**: $30,000/yr

#### 2029-2030:
- Child 1 in college: $30,000/yr
- Child 2 in college: $30,000/yr
- **Total**: $60,000/yr

#### 2031-2032:
- Child 2 in college: $30,000/yr
- Child 3 in college (PRIVATE): $73,000/yr ($55k tuition + $18k room/board)
- **Total**: $103,000/yr

#### 2033-2034:
- Child 3 in college (PRIVATE): $73,000/yr
- Child 4 in college (PRIVATE): $73,000/yr
- **Total**: $146,000/yr (PEAK EXPENSE YEARS)

### Expected Issues:
- During 2033-2034, college expenses alone = $146,000/yr
- Combined income = $330,000/yr
- After taxes (~30%), take-home ≈ $231,000/yr
- With college + living expenses, this will be tight
- Monte Carlo should show potential stress during these years

---

## Key Calculation Validations

### 1. Child Age Calculation
```
Current Age = Current Year - Birth Year
```
**Example**: Child born 2020, current year 2025 → Age = 5 ✓

### 2. Private K-12 School Costs (Ages 5-17)
- Seattle: $20,000/yr
- New York: $35,000/yr
- Houston: $15,000/yr
**Applied**: Only to children aged 5-17 with school_type='Private' ✓

### 3. Public College Costs (Ages 18-21)
- Tuition: $10,000-$13,000/yr (location dependent)
- Room & Board: $12,000-$25,000/yr (location dependent)
- Total: $22,000-$38,000/yr ✓

### 4. Private College Costs (Ages 18-21)
- Tuition: $48,000-$60,000/yr (location dependent)
- Room & Board: $12,000-$25,000/yr (location dependent)
- Total: $60,000-$85,000/yr ✓

### 5. Timeline Age 100 Calculation
```
Year when parent reaches 100 = (Current Year - Current Age) + 100
```
**Example**: Parent age 35 in 2025 → 100 in year (2025 - 35) + 100 = 2090 ✓

### 6. Monte Carlo Random Historical Returns
- Should use `np.random.choice(HISTORICAL_STOCK_RETURNS)`
- NOT sequential: `HISTORICAL_STOCK_RETURNS[year_idx % len()]`
- This ensures random market simulation ✓

### 7. Property Owner Names
- Should display actual parent names (e.g., "Filipp", "Erin")
- Should handle backwards compatibility (ParentX → Parent1 Name)
- Default options: ["Shared", Parent1_Name, Parent2_Name] ✓

---

## Edge Cases to Test

### Edge Case 1: Child Born in Future
- Birth year: 2027
- Current year: 2025
- Age: 2025 - 2027 = -2
- **Expected**: No expenses (age < 0 handled) ✓

### Edge Case 2: Child Over Age 30
- Birth year: 1990
- Current year: 2025
- Age: 35
- **Expected**: No expenses (age > 30 handled) ✓

### Edge Case 3: College Location Not in Templates
- College location: "Unknown City"
- **Expected**: Should use default values ✓

### Edge Case 4: Empty State Timeline
- No timeline entries
- **Expected**: Default to "Seattle", "Average" ✓

### Edge Case 5: SS Insolvency Enabled
- Year < 2034: Full benefits
- Year >= 2034: Reduced by shortfall percentage
- **Expected**: Benefits reduced after 2034 ✓

### Edge Case 6: Parent Already Over 100
- Parent age: 102
- **Expected**: Timeline should still extend to their current age + time horizon

---

## Report Generation Tests

### Test 1: Children Data
- Should include: name, age, birth_year
- Age calculated as: `current_year - birth_year`
- **Expected**: No KeyError on 'age' field ✓

### Test 2: Export Formats
- Excel (.xlsx): Should include all sections
- CSV: Should create multiple files
- JSON: Should export all data

### Test 3: Included Sections
- Summary, Income & Expenses, Assets & Debts, Children, Healthcare, Education, Tax Strategies, Monte Carlo Analysis, Timeline
- Each section should populate correctly

---

## Monte Carlo Simulation Tests

### Test 1: 50th Percentile Breakdown
- Should show median Income, Expenses, Cashflow
- Should display table with key years
- Should show chart with three lines (Income, Expenses, Cashflow)
- **Expected**: Income (green), Expenses (red), Cashflow (blue) ✓

### Test 2: Cashflow Calculation
```
Cashflow = Income - Expenses
```
- During working years: Should be positive (income > expenses)
- During retirement: May be negative if expenses > SS benefits
- **Expected**: Logical progression over time ✓

### Test 3: Inflation Adjustment
- If "Normalize to Today's Dollars" enabled:
  - All values divided by (1 + inflation_rate)^year_offset
- **Expected**: Values should decrease over time (constant dollars) ✓

### Test 4: Historical Returns
- Should randomly sample from 100 years of S&P 500 data
- Each simulation should have different return sequence
- **Expected**: More varied results than sequential ✓

---

## Timeline Visualization Tests

### Test 1: Gantt Chart Display
- Should show horizontal bars, not vertical
- Should group consecutive years with same state/strategy
- **Expected**: Clear segments with labels ✓

### Test 2: Year Range
- Should start at current_year
- Should end at max(parent1_100_year, parent2_100_year)
- **Expected**: No fractional years, integer ticks ✓

### Test 3: Tick Marks
- Should show every 5 years (dtick=5)
- Starting from current_year
- **Expected**: 2025, 2030, 2035, 2040... ✓

---

## Common Issues to Watch For

### Issue 1: College Type Not Defaulting
- **Symptom**: Existing children don't have 'college_type' field
- **Fix**: Use `.get('college_type', 'Public')` with default
- **Status**: ✓ Fixed

### Issue 2: Age Calculation in Report
- **Symptom**: KeyError: 'age'
- **Fix**: Calculate age as `current_year - birth_year`
- **Status**: ✓ Fixed

### Issue 3: ParentX/ParentY in Dropdowns
- **Symptom**: Old sessions still show ParentX/ParentY
- **Fix**: Map old values to new parent names
- **Status**: ✓ Fixed

### Issue 4: Sequential Historical Returns
- **Symptom**: Same return pattern in every simulation
- **Fix**: Use random sampling instead of modulo indexing
- **Status**: ✓ Fixed

---

## Recommended Manual Testing Steps

1. **Create Test Family 1** (Young family, public schools)
   - Add children with public education
   - Run Monte Carlo (30 years)
   - Verify 50th percentile shows positive cashflow
   - Check timeline extends to 2092

2. **Create Test Family 2** (Wealthy family, private education)
   - Add children with private K-12 and private college
   - Verify education costs in Children tab
   - Run Monte Carlo and check expenses are high during college years

3. **Create Test Family 5** (College overlap)
   - Add 4 children with 2-year age gaps
   - Run Monte Carlo to 2040
   - Verify peak expenses during overlap years (2033-2034)
   - Check if cashflow goes negative during peak years

4. **Test Property Ownership**
   - Add a house
   - Check owner dropdown shows actual names
   - Add recurring expense
   - Check owner dropdown shows actual names

5. **Test Report Generation**
   - Configure a family with children
   - Generate Excel report
   - Verify no errors
   - Check children data includes ages

6. **Test Timeline**
   - Add timeline entries for multiple years
   - View visualization
   - Verify Gantt chart shows properly
   - Verify extends to age 100

7. **Test Historical Returns**
   - Enable "Use Historical Returns"
   - Run multiple simulations
   - Compare results - should vary significantly
   - Disable historical returns, compare again

---

## Expected Results Summary

| Test Scenario | Key Metric | Expected Result |
|---------------|------------|-----------------|
| Family 1 (Public) | Total education/child | ~$120,000 (4 years college) |
| Family 2 (Private) | Total education/child | ~$620,000-680,000 |
| Family 3 (Mixed) | Child 2 private college | ~$65,000-70,000/yr |
| Family 4 (Retired) | Timeline end year | 2057 (when younger reaches 100) |
| Family 5 (Overlap) | Peak expense year | $146,000/yr in 2033-2034 |
| Timeline Display | Year increments | Integer years, dtick=5 |
| Monte Carlo | Cashflow breakdown | Shows income, expenses, cashflow |
| Property Owner | Dropdown values | Actual parent names |
| Report Export | Children data | No KeyError, includes age |
| Historical Returns | Simulation variety | High variance across runs |

---

## Notes for Developers

- All monetary calculations use annual values
- Child expenses are age-based (0-30 years)
- College costs apply ages 18-21 only
- Private K-12 applies ages 5-17 only
- Timeline should handle edge cases (no entries, future dates)
- Monte Carlo should cap at 1000 simulations for web performance
- All currency displays should use `format_currency()` helper
- Age calculations should always use `current_year - birth_year`

---

## Test Results Log

| Date | Tester | Test Scenario | Result | Issues Found |
|------|--------|---------------|--------|--------------|
| 2025-01-XX | User | Manual testing | To be completed | - |

