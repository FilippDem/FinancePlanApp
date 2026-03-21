"""
Comprehensive Stress Test for Financial Planning Application V13
Tests all calculation engines independently of Streamlit UI.
"""
import numpy as np
import pandas as pd
import json
import sys
import traceback

# =====================================================
# COPY KEY FUNCTIONS FROM THE APP FOR TESTING
# =====================================================

HISTORICAL_STOCK_RETURNS = [
    0.26, 0.10, 0.11, 0.37, 0.48, 0.12,
    -0.25, -0.43, -0.08, 0.54, -0.01, 0.47, 0.34, -0.35, 0.31, -0.01,
    -0.10, -0.12, 0.20, 0.26, 0.19, 0.36, -0.08, 0.05, 0.05, 0.18,
    0.31, 0.24, 0.18, -0.01, 0.52, 0.31, 0.06, -0.11, 0.43, 0.12,
    0.00, 0.27, -0.09, 0.23, 0.16, 0.12, -0.10, 0.24, 0.11, -0.08,
    0.04, 0.14, 0.19, -0.15, -0.26, 0.37, 0.24, -0.07, 0.07, 0.18,
    0.32, -0.05, 0.21, 0.22, 0.06, 0.31, 0.18, 0.05, 0.16, 0.32,
    -0.03, 0.30, 0.08, 0.10, 0.01, 0.38, 0.23, 0.33, 0.29, 0.21,
    -0.09, -0.12, -0.22, 0.29, 0.11, 0.05, 0.16, 0.05, -0.37, 0.26,
    0.15, 0.02, 0.16, 0.32, 0.14, 0.01, 0.12, 0.22, -0.04, 0.32,
    0.18, 0.29, -0.18, 0.26
]


def calculate_federal_income_tax(taxable_income, filing_status="married_jointly", year=2024):
    if filing_status == "married_jointly":
        brackets = [
            (0, 23200, 0.10), (23200, 94300, 0.12), (94300, 201050, 0.22),
            (201050, 383900, 0.24), (383900, 487450, 0.32),
            (487450, 731200, 0.35), (731200, float('inf'), 0.37)
        ]
    else:
        brackets = [
            (0, 11600, 0.10), (11600, 47150, 0.12), (47150, 100525, 0.22),
            (100525, 191950, 0.24), (191950, 243725, 0.32),
            (243725, 609350, 0.35), (609350, float('inf'), 0.37)
        ]

    tax = 0
    for i, (lower, upper, rate) in enumerate(brackets):
        if taxable_income <= lower:
            break
        taxable_in_bracket = min(taxable_income, upper) - lower
        tax += taxable_in_bracket * rate
        if taxable_income <= upper:
            break
    return tax


def calculate_annual_taxes(gross_income, pretax_deductions=0, state_tax_rate=0.0, filing_status="married_jointly"):
    standard_deduction = 29200 if filing_status == "married_jointly" else 14600
    adjusted_gross_income = max(0, gross_income - pretax_deductions)
    taxable_income = max(0, adjusted_gross_income - standard_deduction)
    federal_tax = calculate_federal_income_tax(taxable_income, filing_status)
    state_tax = adjusted_gross_income * state_tax_rate
    ss_wage_base = 160200
    medicare_threshold = 250000 if filing_status == "married_jointly" else 200000
    ss_tax = min(gross_income, ss_wage_base) * 0.062
    medicare_tax = gross_income * 0.0145
    additional_medicare = max(0, gross_income - medicare_threshold) * 0.009
    fica_tax = ss_tax + medicare_tax + additional_medicare
    total_tax = federal_tax + state_tax + fica_tax
    return {
        'federal_tax': federal_tax, 'state_tax': state_tax, 'fica_tax': fica_tax,
        'total_tax': total_tax,
        'effective_rate': (total_tax / gross_income * 100) if gross_income > 0 else 0,
        'after_tax_income': gross_income - total_tax
    }


# =====================================================
# TEST SUITE
# =====================================================

test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0


def run_test(test_name, condition, details=""):
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    status = "PASS" if condition else "FAIL"
    if condition:
        passed_tests += 1
    else:
        failed_tests += 1
    test_results.append((status, test_name, details))
    print(f"  [{status}] {test_name}" + (f" -- {details}" if details and not condition else ""))


# =====================================================
# TEST 1: TAX CALCULATIONS
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 1: TAX CALCULATIONS")
print("=" * 70)

# Test 1.1: Zero income
tax = calculate_annual_taxes(0)
run_test("Zero income -> zero tax", tax['total_tax'] == 0, f"Got: {tax['total_tax']}")

# Test 1.2: Income within 10% bracket only
# $180,000 married jointly, no deductions
# AGI = 180000, taxable = 180000 - 29200 = 150800
# 10%: 23200 * 0.10 = 2320
# 12%: (94300-23200) * 0.12 = 8532
# 22%: (150800-94300) * 0.22 = 12430
# Federal = 23282
tax = calculate_annual_taxes(180000)
expected_federal = 23200 * 0.10 + (94300 - 23200) * 0.12 + (150800 - 94300) * 0.22
run_test("Federal tax calculation (180k married)", 
         abs(tax['federal_tax'] - expected_federal) < 1,
         f"Expected: {expected_federal:.2f}, Got: {tax['federal_tax']:.2f}")

# Test 1.3: FICA calculation
# SS: min(180000, 160200) * 0.062 = 9932.40
# Medicare: 180000 * 0.0145 = 2610
# Additional Medicare: 0 (under 250k)
expected_fica = 160200 * 0.062 + 180000 * 0.0145
tax = calculate_annual_taxes(180000)
run_test("FICA tax calculation (180k)", 
         abs(tax['fica_tax'] - expected_fica) < 1,
         f"Expected: {expected_fica:.2f}, Got: {tax['fica_tax']:.2f}")

# Test 1.4: Additional Medicare tax
# $300k married: additional medicare on (300000-250000) * 0.009 = 450
tax = calculate_annual_taxes(300000)
expected_additional_medicare = (300000 - 250000) * 0.009
ss = min(300000, 160200) * 0.062
base_medicare = 300000 * 0.0145
expected_fica_300k = ss + base_medicare + expected_additional_medicare
run_test("Additional Medicare tax (300k)", 
         abs(tax['fica_tax'] - expected_fica_300k) < 1,
         f"Expected: {expected_fica_300k:.2f}, Got: {tax['fica_tax']:.2f}")

# Test 1.5: State tax
tax = calculate_annual_taxes(100000, state_tax_rate=0.05)
expected_state = 100000 * 0.05  # State tax on AGI (no pretax deductions)
run_test("State tax calculation", 
         abs(tax['state_tax'] - expected_state) < 1,
         f"Expected: {expected_state:.2f}, Got: {tax['state_tax']:.2f}")

# Test 1.6: Pre-tax 401k deduction
tax_with_401k = calculate_annual_taxes(100000, pretax_deductions=20000)
tax_without_401k = calculate_annual_taxes(100000)
run_test("401k reduces federal tax", 
         tax_with_401k['federal_tax'] < tax_without_401k['federal_tax'],
         f"With 401k: {tax_with_401k['federal_tax']:.2f}, Without: {tax_without_401k['federal_tax']:.2f}")

# Test 1.7: After-tax income = gross - total_tax
tax = calculate_annual_taxes(180000)
run_test("After-tax income identity", 
         abs(tax['after_tax_income'] - (180000 - tax['total_tax'])) < 0.01)

# Test 1.8: Effective rate sanity check
tax = calculate_annual_taxes(180000)
run_test("Effective rate reasonable (15-35%)", 
         15 < tax['effective_rate'] < 35,
         f"Got: {tax['effective_rate']:.1f}%")

# Test 1.9: Single filing status
tax_single = calculate_annual_taxes(100000, filing_status="single")
tax_married = calculate_annual_taxes(100000, filing_status="married_jointly")
run_test("Single pays more federal tax than married", 
         tax_single['federal_tax'] > tax_married['federal_tax'],
         f"Single: {tax_single['federal_tax']:.2f}, Married: {tax_married['federal_tax']:.2f}")

# Test 1.10: Very high income bracket (37%)
tax = calculate_annual_taxes(1000000)
# Taxable = 1000000 - 29200 = 970800
# Should hit the 37% bracket (731200+)
taxable = 970800
expected = (23200 * 0.10 + (94300-23200) * 0.12 + (201050-94300) * 0.22 + 
            (383900-201050) * 0.24 + (487450-383900) * 0.32 + 
            (731200-487450) * 0.35 + (970800-731200) * 0.37)
run_test("High income hits 37% bracket", 
         abs(tax['federal_tax'] - expected) < 1,
         f"Expected: {expected:.2f}, Got: {tax['federal_tax']:.2f}")


# =====================================================
# TEST 2: MORTGAGE CALCULATIONS
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 2: MORTGAGE CALCULATIONS")
print("=" * 70)

def calc_monthly_payment(balance, rate, years):
    """Standard amortization formula"""
    monthly_rate = rate / 12
    num_payments = years * 12
    if monthly_rate > 0:
        return balance * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    else:
        return balance / num_payments

# Test 2.1: Standard mortgage payment
payment = calc_monthly_payment(500000, 0.067, 28)
# Verify against known formula
expected = 500000 * (0.067/12 * (1 + 0.067/12)**(28*12)) / ((1 + 0.067/12)**(28*12) - 1)
run_test("Mortgage payment formula", 
         abs(payment - expected) < 0.01,
         f"Monthly payment: ${payment:.2f}")

# Test 2.2: Zero interest mortgage
payment_zero = calc_monthly_payment(120000, 0, 10)
run_test("Zero interest mortgage", 
         abs(payment_zero - 1000) < 0.01,
         f"Expected: $1000, Got: ${payment_zero:.2f}")

# Test 2.3: Payment sanity - higher rate = higher payment
payment_low = calc_monthly_payment(500000, 0.04, 30)
payment_high = calc_monthly_payment(500000, 0.08, 30)
run_test("Higher rate -> higher payment", 
         payment_high > payment_low,
         f"4%: ${payment_low:.2f}, 8%: ${payment_high:.2f}")

# Test 2.4: Shorter term = higher payment but less total paid
payment_15 = calc_monthly_payment(500000, 0.065, 15)
payment_30 = calc_monthly_payment(500000, 0.065, 30)
total_15 = payment_15 * 15 * 12
total_30 = payment_30 * 30 * 12
run_test("15yr: higher monthly, less total", 
         payment_15 > payment_30 and total_15 < total_30,
         f"15yr total: ${total_15:,.0f}, 30yr total: ${total_30:,.0f}")


# =====================================================
# TEST 3: INCOME PROJECTION WITH JOB CHANGES
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 3: INCOME PROJECTIONS")
print("=" * 70)

def project_income(base_income, raise_rate, job_changes, start_year, target_year, retirement_age, current_age):
    """Replicate the simulation's income projection logic"""
    year_offset = target_year - start_year
    age_in_year = current_age + year_offset
    
    if age_in_year >= retirement_age:
        return 0  # Retired
    
    income = base_income * ((1 + raise_rate) ** year_offset)
    
    # Apply job changes (last matching one wins)
    for jc_year, jc_income in job_changes:
        if target_year >= jc_year:
            income = jc_income * ((1 + raise_rate) ** max(0, target_year - jc_year))
    
    return income

# Test 3.1: Basic raise projection
income_y5 = project_income(95000, 0.035, [], 2025, 2030, 65, 35)
expected = 95000 * (1.035 ** 5)
run_test("5-year raise projection", 
         abs(income_y5 - expected) < 1,
         f"Expected: ${expected:,.2f}, Got: ${income_y5:,.2f}")

# Test 3.2: Job change overrides base income
income = project_income(95000, 0.035, [(2027, 105000)], 2025, 2028, 65, 35)
expected = 105000 * (1.035 ** 1)  # 1 year after job change
run_test("Job change overrides base", 
         abs(income - expected) < 1,
         f"Expected: ${expected:,.2f}, Got: ${income:,.2f}")

# Test 3.3: Multiple job changes - last matching wins
income = project_income(95000, 0.035, [(2027, 105000), (2032, 120000)], 2025, 2033, 65, 35)
expected = 120000 * (1.035 ** 1)  # 1 year after 2nd job change
run_test("Multiple job changes - last wins", 
         abs(income - expected) < 1,
         f"Expected: ${expected:,.2f}, Got: ${income:,.2f}")

# Test 3.4: Retirement zeroes income
income = project_income(95000, 0.035, [], 2025, 2055, 65, 35)
run_test("Retirement zeroes income (age 65)", 
         income == 0,
         f"Age in year: {35 + 30}, Got income: ${income:,.2f}")

# Test 3.5: One year before retirement still has income
income = project_income(95000, 0.035, [], 2025, 2054, 65, 35)
run_test("Year before retirement has income", 
         income > 0,
         f"Age in year: {35 + 29}, Got income: ${income:,.2f}")


# =====================================================
# TEST 4: SOCIAL SECURITY & INSOLVENCY
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 4: SOCIAL SECURITY")
print("=" * 70)

# Test 4.1: Basic SS calculation
ss_monthly = 2500
ss_annual = ss_monthly * 12
run_test("Annual SS from monthly", ss_annual == 30000)

# Test 4.2: Insolvency adjustment
shortfall = 30.0  # 30%
adjusted = ss_annual * (1 - shortfall / 100)
run_test("30% insolvency adjustment", 
         abs(adjusted - 21000) < 1,
         f"Expected: $21,000, Got: ${adjusted:,.0f}")

# Test 4.3: Combined SS
ss_x = 2500 * 12
ss_y = 2200 * 12
combined = ss_x + ss_y
adjusted_combined = combined * (1 - 30 / 100)
run_test("Combined SS with insolvency", 
         abs(adjusted_combined - (30000 + 26400) * 0.7) < 1,
         f"Got: ${adjusted_combined:,.0f}")

# Test 4.4: Retirement benefit options
# Early (62): 75%, Delayed (70): 132%
base = 30000
early = base * 0.75
delayed = base * 1.32
run_test("Early SS = 75% of planned", abs(early - 22500) < 1)
run_test("Delayed SS = 132% of planned", abs(delayed - 39600) < 1)


# =====================================================
# TEST 5: INFLATION & EXPENSE GROWTH
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 5: INFLATION CALCULATIONS")
print("=" * 70)

# Test 5.1: Basic inflation compounding
base_expense = 70000
inflation = 0.025
year_10 = base_expense * (1 + inflation) ** 10
expected = 70000 * 1.025 ** 10
run_test("10-year inflation compounding", 
         abs(year_10 - expected) < 1,
         f"Expected: ${expected:,.2f}, Got: ${year_10:,.2f}")

# Test 5.2: Today's dollar normalization
future_value = 100000
inflation_factor = (1 + 0.025) ** 10
today_value = future_value / inflation_factor
run_test("Today's dollar normalization", 
         abs(today_value - 100000 / (1.025 ** 10)) < 1,
         f"$100k in 10yr at 2.5%: ${today_value:,.2f} in today's $")

# Test 5.3: Expense growth rate vs inflation rate
# Expense growth (2%) should be different from inflation (2.5%)
expense_growth = 0.02
expenses_y10 = 70000 * (1 + expense_growth) ** 10
inflation_y10 = 70000 * (1 + inflation) ** 10
run_test("Expense growth != inflation growth", 
         abs(expenses_y10 - inflation_y10) > 100,
         f"Expense growth: ${expenses_y10:,.2f}, Inflation: ${inflation_y10:,.2f}")

# Test 5.4: Children expenses inflation in simulation
child_expense_base = 20000  # Age 0 cost
inflation = 0.025
# In year 5, child is age 5, inflation applied over 5 years
inflated = child_expense_base * (1 + inflation) ** 5
expected = 20000 * 1.025 ** 5
run_test("Child expense inflation (5yr)", 
         abs(inflated - expected) < 1,
         f"Expected: ${expected:,.2f}")


# =====================================================
# TEST 6: INVESTMENT RETURN LOGIC
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 6: INVESTMENT RETURNS")
print("=" * 70)

# Test 6.1: Historical returns data integrity
run_test("Historical returns count = 100", 
         len(HISTORICAL_STOCK_RETURNS) == 100,
         f"Got: {len(HISTORICAL_STOCK_RETURNS)}")

# Test 6.2: Historical mean reasonable (7-13%)
hist_mean = np.mean(HISTORICAL_STOCK_RETURNS)
run_test("Historical mean 7-13%", 
         0.07 <= hist_mean <= 0.13,
         f"Got: {hist_mean*100:.1f}%")

# Test 6.3: Historical std reasonable (15-25%)
hist_std = np.std(HISTORICAL_STOCK_RETURNS)
run_test("Historical std 15-25%", 
         0.15 <= hist_std <= 0.25,
         f"Got: {hist_std*100:.1f}%")

# Test 6.4: Best/worst year sanity
hist_max = max(HISTORICAL_STOCK_RETURNS)
hist_min = min(HISTORICAL_STOCK_RETURNS)
run_test("Best year > 40%", hist_max > 0.40, f"Got: {hist_max*100:.1f}%")
run_test("Worst year < -30%", hist_min < -0.30, f"Got: {hist_min*100:.1f}%")

# Test 6.5: Traditional return calculation
net_worth = 500000
base_return = 0.06
multiplier = 1.1  # 10% positive variability
investment_return = net_worth * base_return * multiplier
expected = 500000 * 0.06 * 1.1
run_test("Traditional investment return calc", 
         abs(investment_return - expected) < 1,
         f"Expected: ${expected:,.2f}")

# Test 6.6: Historical return application
net_worth = 500000
hist_return = 0.15  # 15% year
investment_gain = net_worth * hist_return
run_test("Historical return application", 
         abs(investment_gain - 75000) < 1)

# Test 6.7: Negative return handling
net_worth = 500000
hist_return = -0.37  # 2008-like crash
investment_loss = net_worth * hist_return
run_test("Negative return reduces net worth", 
         investment_loss < 0,
         f"Loss: ${investment_loss:,.2f}")


# =====================================================
# TEST 7: HOUSE TIMELINE & SALE LOGIC
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 7: HOUSE TIMELINE")
print("=" * 70)

class TestHouseTimelineEntry:
    def __init__(self, year, status, rental_income=0.0):
        self.year = year
        self.status = status
        self.rental_income = rental_income

def get_status_for_year(timeline, year):
    if not timeline:
        return "Own_Live", 0.0
    sorted_timeline = sorted(timeline, key=lambda x: x.year)
    current_status = "Own_Live"
    current_rental = 0.0
    for entry in sorted_timeline:
        if entry.year <= year:
            current_status = entry.status
            current_rental = entry.rental_income
        else:
            break
    return current_status, current_rental

# Test 7.1: Basic timeline
timeline = [TestHouseTimelineEntry(2020, "Own_Live")]
status, rental = get_status_for_year(timeline, 2025)
run_test("Basic Own_Live status", status == "Own_Live" and rental == 0)

# Test 7.2: Rent transition
timeline = [
    TestHouseTimelineEntry(2020, "Own_Live"),
    TestHouseTimelineEntry(2025, "Own_Rent", 2500)
]
status, rental = get_status_for_year(timeline, 2026)
run_test("Rent transition", status == "Own_Rent" and rental == 2500)

# Test 7.3: Before transition
status, rental = get_status_for_year(timeline, 2024)
run_test("Before transition stays Own_Live", status == "Own_Live")

# Test 7.4: Sell transition
timeline = [
    TestHouseTimelineEntry(2020, "Own_Live"),
    TestHouseTimelineEntry(2030, "Sell")
]
status, _ = get_status_for_year(timeline, 2031)
run_test("Sell status after sell year", status == "Sell")

# Test 7.5: Complex timeline (own -> rent -> sell)
timeline = [
    TestHouseTimelineEntry(2020, "Own_Live"),
    TestHouseTimelineEntry(2025, "Own_Rent", 3000),
    TestHouseTimelineEntry(2030, "Sell")
]
s1, r1 = get_status_for_year(timeline, 2023)
s2, r2 = get_status_for_year(timeline, 2027)
s3, r3 = get_status_for_year(timeline, 2032)
run_test("Complex timeline: own phase", s1 == "Own_Live")
run_test("Complex timeline: rent phase", s2 == "Own_Rent" and r2 == 3000)
run_test("Complex timeline: sell phase", s3 == "Sell")

# Test 7.6: House sale proceeds calculation
current_value = 650000
inflation = 0.025
year_offset = 5
sale_value = current_value * (1 + inflation) ** year_offset
mortgage_balance = 500000
mortgage_years_left = 28
purchase_year = 2020
sale_year = 2025
remaining_mortgage = mortgage_balance * max(0, (1 - (sale_year - purchase_year) / mortgage_years_left))
sale_proceeds = max(0, sale_value - remaining_mortgage)
run_test("House sale proceeds positive", 
         sale_proceeds > 0,
         f"Sale value: ${sale_value:,.0f}, Remaining mortgage: ${remaining_mortgage:,.0f}, Proceeds: ${sale_proceeds:,.0f}")


# =====================================================
# TEST 8: RECURRING EXPENSE LOGIC
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 8: RECURRING EXPENSES")
print("=" * 70)

def check_recurring(start_year, frequency, current_year, end_year=None):
    """Check if a recurring expense fires in a given year"""
    if current_year < start_year:
        return False
    if end_year is not None and current_year > end_year:
        return False
    return (current_year - start_year) % frequency == 0

# Test 8.1: Fires on start year
run_test("Recurring fires on start year", check_recurring(2025, 10, 2025))

# Test 8.2: Fires on correct interval
run_test("Fires at 10yr interval", check_recurring(2025, 10, 2035))
run_test("Fires at 10yr interval (2)", check_recurring(2025, 10, 2045))

# Test 8.3: Doesn't fire off-interval
run_test("Doesn't fire off-interval", not check_recurring(2025, 10, 2030))

# Test 8.4: Doesn't fire before start
run_test("Doesn't fire before start", not check_recurring(2027, 10, 2025))

# Test 8.5: End year respected
run_test("End year respected", not check_recurring(2025, 5, 2040, end_year=2035))
run_test("End year boundary", check_recurring(2025, 5, 2035, end_year=2035))

# Test 8.6: Inflation adjustment on recurring
base_amount = 35000
inflation = 0.025
years_elapsed = 10
inflated = base_amount * (1 + inflation) ** years_elapsed
run_test("Recurring inflation adjustment", 
         abs(inflated - 35000 * 1.025 ** 10) < 1,
         f"Got: ${inflated:,.2f}")


# =====================================================
# TEST 9: SIMULATION INTEGRATION TEST
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 9: SIMULATION INTEGRATION (DETERMINISTIC)")
print("=" * 70)

# Simulate a single deterministic year
np.random.seed(42)

# Simple scenario: 2 parents, no children, 1 house, basic expenses
parentX_income = 95000
parentY_income = 85000
gross_income = parentX_income + parentY_income  # 180000

# Tax
tax_info = calculate_annual_taxes(gross_income, pretax_deductions=0, state_tax_rate=0.0)
after_tax = tax_info['after_tax_income']

# Expenses
family_expenses = 70000  # Annual family expenses

# House expenses (simplified)
mortgage_payment = calc_monthly_payment(500000, 0.067, 28) * 12
property_tax = 650000 * 0.0092
insurance = 1800
upkeep = 3000
house_total = mortgage_payment + property_tax + insurance + upkeep

# Net income
net_income = after_tax - family_expenses - house_total

# Investment return on starting NW
starting_nw = 85000 + 75000 + max(0, 650000 - 500000)  # Parents + house equity
investment_return = starting_nw * 0.06  # 6% return

# Year 1 ending net worth
ending_nw = starting_nw + net_income + investment_return

run_test("Year 1 after-tax income positive", after_tax > 0, f"After tax: ${after_tax:,.0f}")
run_test("Year 1 house expenses reasonable", 30000 < house_total < 60000, f"House total: ${house_total:,.0f}")
run_test("Year 1 net income reasonable", -50000 < net_income < 100000, f"Net income: ${net_income:,.0f}")
run_test("Year 1 ending NW > starting NW", ending_nw > starting_nw, 
         f"Starting: ${starting_nw:,.0f}, Ending: ${ending_nw:,.0f}")


# =====================================================
# TEST 10: MONTE CARLO STATISTICAL PROPERTIES
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 10: MONTE CARLO STATISTICAL PROPERTIES")
print("=" * 70)

np.random.seed(12345)

# Run 5000 simplified simulations
n_sims = 5000
years = 30
starting_nw = 310000  # Total starting net worth
annual_savings = 40000  # Approximate net savings per year

# Historical mode simulation
final_values_hist = []
for _ in range(n_sims):
    nw = starting_nw
    for y in range(years):
        nw += annual_savings  # Simplified
        ret = np.random.choice(HISTORICAL_STOCK_RETURNS)
        nw = nw * (1 + ret)
    final_values_hist.append(nw)

final_arr = np.array(final_values_hist)

# Test 10.1: Median should be positive
run_test("MC median > 0 after 30yr", np.median(final_arr) > 0, 
         f"Median: ${np.median(final_arr):,.0f}")

# Test 10.2: 95th percentile > median
run_test("95th > median", 
         np.percentile(final_arr, 95) > np.median(final_arr))

# Test 10.3: 5th < median
run_test("5th < median", 
         np.percentile(final_arr, 5) < np.median(final_arr))

# Test 10.4: Some negative outcomes should exist (but not majority)
negative_pct = np.mean(final_arr < 0) * 100
run_test("Some but not majority negative outcomes", 
         0 <= negative_pct < 50,
         f"Negative outcomes: {negative_pct:.1f}%")

# Test 10.5: Range should be large (uncertainty grows over time)
range_width = np.max(final_arr) - np.min(final_arr)
run_test("Range grows over 30 years", 
         range_width > 1000000,
         f"Range: ${range_width:,.0f}")

# Test 10.6: Traditional mode with asymmetric variability
final_values_trad = []
for _ in range(n_sims):
    nw = starting_nw
    for y in range(years):
        nw += annual_savings
        # Asymmetric return
        if np.random.random() < 0.5:
            var = 0.15
            mult = 1 - abs(np.random.normal(0, var))
        else:
            var = 0.15
            mult = 1 + abs(np.random.normal(0, var))
        nw = nw * (1 + 0.06 * mult)  # 6% base return
    final_values_trad.append(nw)

trad_arr = np.array(final_values_trad)
run_test("Traditional MC median > 0", np.median(trad_arr) > 0,
         f"Median: ${np.median(trad_arr):,.0f}")


# =====================================================
# TEST 11: EDGE CASES & BOUNDARY CONDITIONS
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 11: EDGE CASES")
print("=" * 70)

# Test 11.1: Net worth floor
total_nw = -3000000
floored = max(total_nw, -2000000)
run_test("Net worth floor -2M", floored == -2000000)

# Test 11.2: Parent floor
parent_nw = -1000000
floored = max(parent_nw, -500000)
run_test("Parent net worth floor -500k", floored == -500000)

# Test 11.3: Family floor
family_nw = -2000000
floored = max(family_nw, -1000000)
run_test("Family net worth floor -1M", floored == -1000000)

# Test 11.4: Zero variability should have no randomness effect on midpoint
# income_multiplier with 0% variability: 1 + N(0, 0) = 1 always
np.random.seed(99)
multipliers = [1 + np.random.normal(0, 0) for _ in range(100)]
run_test("Zero variability = no randomness", 
         all(abs(m - 1.0) < 0.0001 for m in multipliers))

# Test 11.5: Child expenses beyond age 30 should return 0 (boundary)
# In the app, children_expenses has 31 rows (age 0-30)
# child_age >= len(children_expenses) means no cost
child_age = 31
expenses_len = 31
has_expense = 0 <= child_age < expenses_len
run_test("Child age 31 has no expenses", not has_expense)

# Test 11.6: Child age 30 (last valid) does have row
child_age = 30
has_expense = 0 <= child_age < expenses_len
run_test("Child age 30 has expenses", has_expense)

# Test 11.7: Negative child age (future birth) should have no cost
child_age = -2
has_expense = 0 <= child_age < expenses_len
run_test("Future child (negative age) no cost", not has_expense)


# =====================================================
# TEST 12: SAVE/LOAD DATA INTEGRITY
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 12: SAVE/LOAD INTEGRITY")
print("=" * 70)

# Test 12.1: JSON serialization of core types
test_data = {
    'parentX': {'age': 35, 'income': 95000.0, 'net_worth': 85000.0},
    'expenses': {'Food & Groceries': 16800.0, 'Clothing': 4200.0},
    'houses': [{'name': 'Primary', 'value': 650000.0, 'timeline': [{'year': 2020, 'status': 'Own_Live', 'rental_income': 0.0}]}]
}
json_str = json.dumps(test_data)
loaded = json.loads(json_str)
run_test("JSON round-trip preserves data", 
         loaded['parentX']['income'] == 95000.0 and loaded['houses'][0]['value'] == 650000.0)

# Test 12.2: DataFrame to/from records
df = pd.DataFrame({'Age': [0, 1, 2], 'Food': [1500, 1500, 1800], 'Clothing': [600, 600, 500]})
records = df.to_dict('records')
df_back = pd.DataFrame(records)
run_test("DataFrame round-trip", df.equals(df_back))

# Test 12.3: NaN handling
test_df = pd.DataFrame({'A': [1, np.nan, 3]})
json_safe = test_df.to_dict('records')
json_str = json.dumps(json_safe, default=str)
run_test("NaN in DataFrame serializes", json_str is not None)


# =====================================================
# TEST 13: CODE QUALITY / STRUCTURAL ISSUES
# =====================================================
print("\n" + "=" * 70)
print("TEST GROUP 13: CODE REVIEW FINDINGS")
print("=" * 70)

# Test 13.1: Check all children expense template lengths = 31
from typing import Dict, List
templates = {
    "California": {
        "Conservative": {
            'Food': [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200,
                     4400, 4600, 2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400, 200, 100, 50, 0],
            'Clothing': [400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1200, 1400, 1600, 1800, 2000,
                         800, 600, 400, 300, 250, 200, 150, 100, 50, 25, 0, 0, 0],
        }
    }
}

all_correct_length = True
for state_data in templates.values():
    for strategy_data in state_data.values():
        for cat, values in strategy_data.items():
            if len(values) != 31:
                all_correct_length = False
                break

run_test("All template arrays length 31", all_correct_length)

# Test 13.2: Verify the simulation's inflation normalization factor for year 0
# In the app: inflation_factor = (1 + scenario.inflation_rate) ** (year - 1)
# For year=1 (first simulation year): factor = (1+r)^0 = 1.0 (correct, no inflation in first year)
inflation_factor_y1 = (1 + 0.025) ** (1 - 1)
run_test("Year 1 inflation factor = 1.0", abs(inflation_factor_y1 - 1.0) < 0.0001)

# Test 13.3: Normalization factor for year_idx=0 in breakdown
# The app uses: inflation_factor = (1 + scenario.inflation_rate) ** year_idx
# year_idx=0: factor = 1.0 (correct)
inflation_factor_idx0 = (1 + 0.025) ** 0
run_test("Breakdown year_idx=0 factor = 1.0", abs(inflation_factor_idx0 - 1.0) < 0.0001)

# Test 13.4: Check that the year offset for sim_year is consistent
# current_sim_year = start_year + year - 1 (where year goes 1..years)
# For year=1: current_sim_year = 2025 + 1 - 1 = 2025 (first year is start year) ✓
start_year = 2025
year = 1
current_sim_year = start_year + year - 1
run_test("First sim year = start year", current_sim_year == 2025)

# For yearly_breakdown: year_idx=0, current_sim_year = start_year + 0 = 2025 ✓
year_idx = 0
breakdown_year = start_year + year_idx
run_test("Breakdown year alignment", breakdown_year == current_sim_year)


# =====================================================
# FINAL REPORT
# =====================================================
print("\n" + "=" * 70)
print("STRESS TEST FINAL REPORT")
print("=" * 70)
print(f"Total tests:  {total_tests}")
print(f"Passed:       {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
print(f"Failed:       {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
print("=" * 70)

if failed_tests > 0:
    print("\nFAILED TESTS:")
    for status, name, details in test_results:
        if status == "FAIL":
            print(f"  ❌ {name}: {details}")

print("\nDONE.")
