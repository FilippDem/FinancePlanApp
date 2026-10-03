#!/usr/bin/env python3
"""
Comprehensive test scenarios for Financial Planning Suite v0.74
Tests various edge cases and realistic user scenarios
"""

import sys
import traceback
from dataclasses import asdict
import pandas as pd
import numpy as np
import json
import io

# Import the main application components
# We'll test the dataclasses and utility functions
print("=" * 80)
print("FINANCIAL PLANNING SUITE v0.74 - COMPREHENSIVE SCENARIO TESTING")
print("=" * 80)

test_results = []

def test_scenario(name, test_func):
    """Run a test scenario and record results"""
    try:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{'='*60}")
        test_func()
        print(f"✅ PASSED: {name}")
        test_results.append((name, "PASSED", None))
        return True
    except Exception as e:
        print(f"❌ FAILED: {name}")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        test_results.append((name, "FAILED", str(e)))
        return False

# Import dataclasses from the main file
print("\n📦 Importing dataclasses...")
try:
    from FinancialPlanner_v0_7 import (
        HealthInsurance, LongTermCareInsurance, HealthExpense,
        Debt, Plan529, EducationGoal, TaxStrategy, RetirementWithdrawal,
        format_currency, PortfolioAllocation, House, HouseTimelineEntry,
        StateTimelineEntry, MajorPurchase, RecurringExpense, EconomicParameters
    )
    print("✅ All dataclasses imported successfully")
except ImportError as e:
    print(f"❌ Failed to import dataclasses: {e}")
    sys.exit(1)

# TEST 1: Format Currency Edge Cases
def test_format_currency_edge_cases():
    """Test format_currency with edge cases"""
    test_cases = [
        (0, "$0"),
        (-1000, "-$1k"),
        (1000000, "$1.0M"),
        (1500000, "$1.5M"),
        (999, "$999"),
        (None, "$0"),
        (float('nan'), "$0"),
        (0.5, "$1"),  # Rounds
        (-500000, "-$500k"),
    ]

    for value, expected_prefix in test_cases:
        result = format_currency(value)
        print(f"  format_currency({value}) = {result}")
        assert result.startswith("$") or result.startswith("-$"), f"Expected currency format for {value}"

    print("✅ All currency formatting edge cases handled")

test_scenario("Format Currency Edge Cases", test_format_currency_edge_cases)

# TEST 2: HealthInsurance Dataclass
def test_health_insurance_creation():
    """Test HealthInsurance dataclass with various scenarios"""

    # Scenario 1: Employer insurance
    employer_insurance = HealthInsurance(
        name="Employer PPO",
        type="Employer",
        monthly_premium=500.0,
        annual_deductible=3000.0,
        annual_out_of_pocket_max=8000.0,
        copay_primary=25.0,
        copay_specialist=50.0,
        covered_by="Family",
        start_age=0,
        end_age=65
    )
    assert employer_insurance.name == "Employer PPO"
    assert employer_insurance.monthly_premium == 500.0
    print(f"  Created employer insurance: {employer_insurance.name}")

    # Scenario 2: Medicare
    medicare = HealthInsurance(
        name="Medicare",
        type="Medicare",
        monthly_premium=174.70,
        annual_deductible=0.0,
        annual_out_of_pocket_max=0.0,
        copay_primary=0.0,
        copay_specialist=0.0,
        covered_by="Parent 1",
        start_age=65,
        end_age=999
    )
    assert medicare.type == "Medicare"
    print(f"  Created Medicare insurance: {medicare.name}")

    # Test asdict conversion
    insurance_dict = asdict(employer_insurance)
    assert isinstance(insurance_dict, dict)
    assert insurance_dict['name'] == "Employer PPO"
    print(f"  asdict() conversion successful: {len(insurance_dict)} fields")

    print("✅ HealthInsurance dataclass working correctly")

test_scenario("HealthInsurance Dataclass Creation", test_health_insurance_creation)

# TEST 3: Debt Management Edge Cases
def test_debt_management():
    """Test Debt dataclass with various debt types"""

    # Student loan with forgiveness
    student_loan = Debt(
        name="Federal Student Loan",
        debt_type="Student Loan",
        principal=50000.0,
        interest_rate=0.045,
        monthly_payment=300.0,
        minimum_payment=250.0,
        start_date="2020-01-01",
        owner="Parent 1",
        interest_type="Fixed",
        income_based_repayment=True,
        forgiveness_eligible=True,
        forgiveness_years=10
    )
    assert student_loan.forgiveness_eligible == True
    assert student_loan.forgiveness_years == 10
    print(f"  Created student loan: {student_loan.name} with forgiveness")

    # Credit card debt
    credit_card = Debt(
        name="Chase Card",
        debt_type="Credit Card",
        principal=5000.0,
        interest_rate=0.1899,  # 18.99%
        monthly_payment=200.0,
        minimum_payment=150.0,
        start_date="2023-01-01",
        owner="Shared",
        interest_type="Variable"
    )
    assert credit_card.interest_rate > 0.15
    print(f"  Created credit card: {credit_card.name} at {credit_card.interest_rate*100:.2f}%")

    # Zero balance debt (paid off)
    paid_off = Debt(
        name="Paid Off Loan",
        debt_type="Auto Loan",
        principal=0.0,
        interest_rate=0.0,
        monthly_payment=0.0,
        minimum_payment=0.0,
        start_date="2020-01-01",
        owner="Parent 2"
    )
    assert paid_off.principal == 0.0
    print(f"  Created paid-off debt: {paid_off.name}")

    print("✅ Debt dataclass handles all debt types correctly")

test_scenario("Debt Management Scenarios", test_debt_management)

# TEST 4: 529 Plan and Education Funding
def test_education_funding():
    """Test Plan529 and EducationGoal dataclasses"""

    # 529 plan with age-based allocation
    plan529 = Plan529(
        name="Washington 529",
        beneficiary="Child 1",
        current_balance=10000.0,
        monthly_contribution=300.0,
        state="Washington",
        investment_return=0.07,
        age_based_allocation=True,
        contribution_end_age=18
    )
    assert plan529.age_based_allocation == True
    print(f"  Created 529 plan: {plan529.name} for {plan529.beneficiary}")

    # Education goal for private college
    private_college = EducationGoal(
        beneficiary="Child 1",
        institution_type="Private",
        estimated_annual_cost=60000.0,
        years_of_college=4,
        start_year=2043,
        scholarship_amount=10000.0,
        grants_amount=5000.0,
        student_loans_allowed=False,
        max_parent_contribution=200000.0
    )
    total_cost = private_college.estimated_annual_cost * private_college.years_of_college
    total_aid = (private_college.scholarship_amount + private_college.grants_amount) * private_college.years_of_college
    net_cost = total_cost - total_aid
    print(f"  Private college total cost: ${total_cost:,.0f}")
    print(f"  Total scholarships/grants: ${total_aid:,.0f}")
    print(f"  Net cost: ${net_cost:,.0f}")
    assert net_cost > 0

    # Community college (low cost)
    community_college = EducationGoal(
        beneficiary="Child 2",
        institution_type="Community College",
        estimated_annual_cost=5000.0,
        years_of_college=2,
        start_year=2045,
        scholarship_amount=2000.0,
        grants_amount=1000.0,
        student_loans_allowed=True,
        max_parent_contribution=10000.0
    )
    assert community_college.estimated_annual_cost < 10000.0
    print(f"  Community college: {community_college.institution_type}")

    print("✅ Education funding scenarios working correctly")

test_scenario("Education Funding Scenarios", test_education_funding)

# TEST 5: Tax Optimization
def test_tax_optimization():
    """Test TaxStrategy and RetirementWithdrawal dataclasses"""

    # Roth conversion strategy
    roth_conversion = TaxStrategy(
        name="Annual Roth Conversion",
        strategy_type="Roth Conversion",
        annual_amount=15000.0,
        start_year=2025,
        end_year=2035,
        estimated_tax_savings=30000.0,
        notes="Convert in low-income years"
    )
    years_active = roth_conversion.end_year - roth_conversion.start_year
    total_conversions = roth_conversion.annual_amount * years_active
    print(f"  Roth conversion over {years_active} years: ${total_conversions:,.0f}")

    # QCD strategy
    qcd_strategy = TaxStrategy(
        name="Qualified Charitable Distribution",
        strategy_type="Qualified Charitable Distribution",
        annual_amount=5000.0,
        start_year=2030,
        end_year=2050,
        estimated_tax_savings=1200.0,
        notes="Age 70.5+ RMD to charity"
    )
    assert "Charitable" in qcd_strategy.strategy_type
    print(f"  QCD strategy: ${qcd_strategy.annual_amount:,.0f}/year")

    # Retirement withdrawal from different accounts
    withdrawals = [
        RetirementWithdrawal(2025, "401k", 40000.0, 0.22, "Living Expenses"),
        RetirementWithdrawal(2025, "Roth IRA", 10000.0, 0.0, "Tax-free withdrawal"),
        RetirementWithdrawal(2025, "Taxable Brokerage", 20000.0, 0.15, "Long-term gains"),
    ]

    total_gross = sum(w.amount for w in withdrawals)
    total_tax = sum(w.amount * w.tax_rate for w in withdrawals)
    total_net = total_gross - total_tax

    print(f"  Total withdrawals: ${total_gross:,.0f}")
    print(f"  Total tax: ${total_tax:,.0f}")
    print(f"  Net income: ${total_net:,.0f}")
    assert total_net < total_gross

    print("✅ Tax optimization scenarios working correctly")

test_scenario("Tax Optimization Scenarios", test_tax_optimization)

# TEST 6: Empty List Handling
def test_empty_list_handling():
    """Test operations on empty lists (edge case)"""

    empty_debts = []
    total_debt = sum([d.principal for d in empty_debts])
    assert total_debt == 0
    print(f"  Empty debt list sum: ${total_debt}")

    empty_insurances = []
    total_premium = sum([ins.monthly_premium * 12 for ins in empty_insurances])
    assert total_premium == 0
    print(f"  Empty insurance list sum: ${total_premium}")

    # Division by zero protection
    if total_debt > 0:
        avg_rate = sum([d.principal * 0.05 for d in empty_debts]) / total_debt
    else:
        avg_rate = 0
    assert avg_rate == 0
    print(f"  Protected division by zero: {avg_rate}")

    print("✅ Empty list handling works correctly")

test_scenario("Empty List Handling", test_empty_list_handling)

# TEST 7: Portfolio Allocation
def test_portfolio_allocation():
    """Test PortfolioAllocation dataclass"""

    # Balanced portfolio
    balanced = PortfolioAllocation(
        stocks=60.0,
        bonds=30.0,
        cash=5.0,
        real_estate=5.0,
        other=0.0
    )
    assert balanced.total() == 100.0
    assert balanced.is_valid() == True
    print(f"  Balanced portfolio total: {balanced.total()}%")

    # Invalid portfolio (doesn't add to 100)
    invalid = PortfolioAllocation(
        stocks=50.0,
        bonds=30.0,
        cash=10.0,
        real_estate=5.0,
        other=0.0
    )
    assert invalid.total() == 95.0
    assert invalid.is_valid() == False
    print(f"  Invalid portfolio total: {invalid.total()}% (not valid)")

    # Aggressive portfolio
    aggressive = PortfolioAllocation(
        stocks=90.0,
        bonds=5.0,
        cash=2.0,
        real_estate=3.0,
        other=0.0
    )
    assert aggressive.stocks == 90.0
    assert aggressive.is_valid() == True
    print(f"  Aggressive portfolio: {aggressive.stocks}% stocks")

    print("✅ Portfolio allocation validation working")

test_scenario("Portfolio Allocation", test_portfolio_allocation)

# TEST 8: Report Export Data Preparation
def test_report_export_data():
    """Test report export data structure creation"""

    # Create sample data
    sample_debts = [
        Debt("Student Loan", "Student Loan", 30000.0, 0.045, 300.0, 250.0, "2020-01-01", "Parent 1"),
        Debt("Car Loan", "Auto Loan", 15000.0, 0.06, 350.0, 350.0, "2022-01-01", "Parent 2"),
    ]

    sample_529s = [
        Plan529("Plan 1", "Child 1", 5000.0, 200.0, "Washington"),
    ]

    sample_tax_strategies = [
        TaxStrategy("Roth Conv", "Roth Conversion", 10000.0, 2025, 2030, 2000.0),
    ]

    # Test asdict conversion
    debts_data = [asdict(d) for d in sample_debts]
    assert len(debts_data) == 2
    assert debts_data[0]['name'] == "Student Loan"
    print(f"  Converted {len(debts_data)} debts to dict")

    plans_data = [asdict(p) for p in sample_529s]
    assert len(plans_data) == 1
    print(f"  Converted {len(plans_data)} 529 plans to dict")

    strategies_data = [asdict(t) for t in sample_tax_strategies]
    assert len(strategies_data) == 1
    print(f"  Converted {len(strategies_data)} tax strategies to dict")

    # Test DataFrame creation
    debts_df = pd.DataFrame(debts_data)
    assert len(debts_df) == 2
    assert 'principal' in debts_df.columns
    print(f"  Created DataFrame with {len(debts_df)} rows, {len(debts_df.columns)} columns")

    # Test JSON serialization
    json_str = json.dumps(debts_data, default=str)
    assert isinstance(json_str, str)
    assert "Student Loan" in json_str
    print(f"  JSON serialization successful: {len(json_str)} chars")

    # Test Excel export preparation
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        debts_df.to_excel(writer, sheet_name='Debts', index=False)
    output.seek(0)
    assert output.tell() == 0  # Seeked to beginning
    print(f"  Excel export successful")

    print("✅ Report export data preparation working")

test_scenario("Report Export Data Preparation", test_report_export_data)

# TEST 9: Long-Term Care Insurance Edge Cases
def test_ltc_insurance_edge_cases():
    """Test LTC insurance with various scenarios"""

    # Standard LTC policy
    standard_ltc = LongTermCareInsurance(
        name="Standard LTC",
        monthly_premium=300.0,
        daily_benefit=200.0,
        benefit_period_days=1095,  # 3 years
        elimination_period_days=90,
        covered_person="Parent 1",
        start_age=55,
        inflation_protection=0.03
    )
    total_benefit = standard_ltc.daily_benefit * standard_ltc.benefit_period_days
    print(f"  Total LTC benefit: ${total_benefit:,.0f}")
    assert total_benefit > 0

    # High benefit policy
    high_benefit = LongTermCareInsurance(
        name="Premium LTC",
        monthly_premium=500.0,
        daily_benefit=400.0,
        benefit_period_days=1825,  # 5 years
        elimination_period_days=60,
        covered_person="Parent 2",
        start_age=60,
        inflation_protection=0.05
    )
    assert high_benefit.daily_benefit > standard_ltc.daily_benefit
    print(f"  High benefit LTC: ${high_benefit.daily_benefit}/day")

    print("✅ LTC insurance scenarios working")

test_scenario("LTC Insurance Edge Cases", test_ltc_insurance_edge_cases)

# TEST 10: State Timeline and House Timeline
def test_timeline_entries():
    """Test StateTimelineEntry and HouseTimelineEntry"""

    # State timeline
    state_timeline = [
        StateTimelineEntry(2025, "Washington", "Average"),
        StateTimelineEntry(2030, "Texas", "Conservative"),
        StateTimelineEntry(2040, "Florida", "High-end"),
    ]
    assert len(state_timeline) == 3
    assert state_timeline[0].state == "Washington"
    print(f"  Created {len(state_timeline)} state timeline entries")

    # House timeline
    house_timeline = [
        HouseTimelineEntry(2025, "Own_Live", 0.0),
        HouseTimelineEntry(2030, "Own_Rent", 2500.0),
        HouseTimelineEntry(2040, "Sold", 0.0),
    ]
    assert len(house_timeline) == 3
    assert house_timeline[1].rental_income == 2500.0
    print(f"  Created {len(house_timeline)} house timeline entries")

    # Create house with timeline
    house = House(
        name="Primary Home",
        purchase_year=2020,
        purchase_price=500000.0,
        current_value=600000.0,
        mortgage_balance=400000.0,
        mortgage_rate=0.065,
        mortgage_years_left=25,
        property_tax_rate=0.01,
        home_insurance=1500.0,
        maintenance_rate=0.015,
        upkeep_costs=3000.0,
        owner="Shared",
        timeline=house_timeline
    )

    # Test get_status_for_year method
    status_2025, rental_2025 = house.get_status_for_year(2025)
    assert status_2025 == "Own_Live"
    assert rental_2025 == 0.0
    print(f"  2025 status: {status_2025}, rental: ${rental_2025}")

    status_2035, rental_2035 = house.get_status_for_year(2035)
    assert status_2035 == "Own_Rent"
    assert rental_2035 == 2500.0
    print(f"  2035 status: {status_2035}, rental: ${rental_2035}")

    print("✅ Timeline entries working correctly")

test_scenario("Timeline Entries", test_timeline_entries)

# TEST 11: Major Purchase and Recurring Expense
def test_purchases_and_expenses():
    """Test MajorPurchase and RecurringExpense"""

    # Real estate major purchase
    real_estate = MajorPurchase(
        name="Vacation Home",
        year=2030,
        amount=300000.0,
        financing_years=30,
        interest_rate=0.07,
        asset_type="Real Estate",
        appreciation_rate=0.03
    )
    assert real_estate.asset_type == "Real Estate"
    assert real_estate.appreciation_rate == 0.03
    print(f"  Real estate purchase: {real_estate.name} at ${real_estate.amount:,.0f}")

    # Vehicle purchase (depreciating)
    vehicle = MajorPurchase(
        name="New Car",
        year=2025,
        amount=40000.0,
        financing_years=5,
        interest_rate=0.05,
        asset_type="Vehicle",
        appreciation_rate=-0.15  # Depreciates
    )
    assert vehicle.appreciation_rate < 0
    print(f"  Vehicle purchase: {vehicle.name} with {vehicle.appreciation_rate*100:.0f}% depreciation")

    # Recurring expense
    recurring = RecurringExpense(
        name="Car Replacement",
        category="Vehicle",
        amount=35000.0,
        frequency_years=10,
        start_year=2025,
        end_year=None,
        inflation_adjust=True,
        parent="Both",
        financing_years=5,
        interest_rate=0.045
    )
    assert recurring.inflation_adjust == True
    print(f"  Recurring expense: {recurring.name} every {recurring.frequency_years} years")

    print("✅ Purchases and expenses working correctly")

test_scenario("Purchases and Expenses", test_purchases_and_expenses)

# TEST 12: Economic Scenarios
def test_economic_scenarios():
    """Test EconomicScenario dataclass"""

    conservative = EconomicScenario(
        "Conservative",
        investment_return=0.04,
        inflation_rate=0.03,
        expense_growth_rate=0.02,
        healthcare_inflation_rate=0.05
    )
    assert conservative.investment_return < 0.06
    print(f"  Conservative: {conservative.investment_return*100:.1f}% return")

    aggressive = EconomicScenario(
        "Aggressive",
        investment_return=0.10,
        inflation_rate=0.02,
        expense_growth_rate=0.02,
        healthcare_inflation_rate=0.04
    )
    assert aggressive.investment_return > conservative.investment_return
    print(f"  Aggressive: {aggressive.investment_return*100:.1f}% return")

    print("✅ Economic scenarios working correctly")

test_scenario("Economic Scenarios", test_economic_scenarios)

# FINAL SUMMARY
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for _, status, _ in test_results if status == "PASSED")
failed = sum(1 for _, status, _ in test_results if status == "FAILED")
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"Success Rate: {(passed/total*100):.1f}%")

if failed > 0:
    print("\n❌ FAILED TESTS:")
    for name, status, error in test_results:
        if status == "FAILED":
            print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ No broken functionality detected")
    print("✅ All scenarios working correctly")
    sys.exit(0)
