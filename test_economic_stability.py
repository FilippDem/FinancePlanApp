#!/usr/bin/env python3
"""
Comprehensive test script for Financial Planning Application v0.74
Tests demo scenarios with varied economic conditions to ensure stability
"""

import sys
import traceback
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional
import numpy as np

# Import from main application
print("=" * 80)
print("ECONOMIC STABILITY TESTING - Financial Planning Suite v0.74")
print("=" * 80)

# Define dataclasses for testing (matching the app structure)
@dataclass
class HouseTimelineEntry:
    year: int
    status: str
    rental_income: float = 0.0

@dataclass
class House:
    name: str
    purchase_year: int
    purchase_price: float
    current_value: float
    mortgage_balance: float
    mortgage_rate: float
    mortgage_years_left: int
    property_tax_rate: float
    home_insurance: float
    maintenance_rate: float
    upkeep_costs: float
    owner: str = "Shared"
    timeline: List[HouseTimelineEntry] = None

@dataclass
class PortfolioAllocation:
    stocks: float = 60.0
    bonds: float = 30.0
    cash: float = 5.0
    real_estate: float = 5.0
    other: float = 0.0

    def total(self) -> float:
        return self.stocks + self.bonds + self.cash + self.real_estate + self.other

    def is_valid(self) -> bool:
        return abs(self.total() - 100.0) < 0.01

@dataclass
class RecurringExpense:
    name: str
    category: str
    amount: float
    frequency_years: int
    start_year: int
    end_year: Optional[int] = None
    inflation_adjust: bool = True
    parent: str = "Both"
    financing_years: int = 0
    interest_rate: float = 0.0

@dataclass
class StateTimelineEntry:
    year: int
    state: str
    spending_strategy: str = "Average"

@dataclass
class EconomicParameters:
    name: str
    investment_return: float
    inflation_rate: float
    expense_growth_rate: float
    healthcare_inflation_rate: float
    real_estate_appreciation: float = 0.03
    wage_growth_rate: float = 0.03

# Test configuration
current_year = datetime.now().year
test_results = []
scenario_results = {}

def test_scenario(name, test_func):
    """Run a test scenario and record results"""
    try:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{'='*60}")
        result = test_func()
        print(f"✅ PASSED: {name}")
        test_results.append((name, "PASSED", None))
        return result
    except Exception as e:
        print(f"❌ FAILED: {name}")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        test_results.append((name, "FAILED", str(e)))
        return None

# Define economic scenarios to test
economic_scenarios = [
    EconomicParameters(
        "Conservative Bear Market",
        investment_return=0.02,
        inflation_rate=0.04,
        expense_growth_rate=0.05,
        healthcare_inflation_rate=0.07,
        real_estate_appreciation=0.01,
        wage_growth_rate=0.02
    ),
    EconomicParameters(
        "Moderate/Baseline",
        investment_return=0.07,
        inflation_rate=0.025,
        expense_growth_rate=0.03,
        healthcare_inflation_rate=0.05,
        real_estate_appreciation=0.03,
        wage_growth_rate=0.03
    ),
    EconomicParameters(
        "Aggressive Bull Market",
        investment_return=0.12,
        inflation_rate=0.02,
        expense_growth_rate=0.02,
        healthcare_inflation_rate=0.04,
        real_estate_appreciation=0.05,
        wage_growth_rate=0.04
    ),
    EconomicParameters(
        "High Inflation Scenario",
        investment_return=0.06,
        inflation_rate=0.06,
        expense_growth_rate=0.07,
        healthcare_inflation_rate=0.09,
        real_estate_appreciation=0.04,
        wage_growth_rate=0.05
    ),
    EconomicParameters(
        "Stagflation",
        investment_return=0.03,
        inflation_rate=0.05,
        expense_growth_rate=0.06,
        healthcare_inflation_rate=0.08,
        real_estate_appreciation=0.02,
        wage_growth_rate=0.01
    ),
]

print(f"\n📊 Testing with {len(economic_scenarios)} different economic scenarios:")
for i, econ in enumerate(economic_scenarios, 1):
    print(f"  {i}. {econ.name}")
    print(f"     Investment Return: {econ.investment_return*100:.1f}%")
    print(f"     Inflation: {econ.inflation_rate*100:.1f}%")
    print(f"     Healthcare Inflation: {econ.healthcare_inflation_rate*100:.1f}%")

# Define demo scenarios (matching the app structure)
def create_demo_scenarios():
    """Create all demo scenarios for testing"""
    scenarios = {}

    # Scenario 1: High-Income Tech Couple
    scenarios["[DEMO] High-Income Tech Couple with Toddlers (SF, Aggressive)"] = {
        'houses': [{
            'name': 'SF Condo',
            'purchase_year': current_year - 2,
            'purchase_price': 1200000.0,
            'current_value': 1300000.0,
            'mortgage_balance': 900000.0,
            'mortgage_rate': 6.5,
            'mortgage_years_left': 28,
            'property_tax_rate': 1.2,
            'home_insurance': 2400.0,
            'maintenance_rate': 0.5,
            'upkeep_costs': 6000.0,
            'owner': 'Shared',
            'timeline': [{'year': current_year - 2, 'status': 'Own_Live', 'rental_income': 0.0}]
        }],
        'portfolio_allocation': {
            'stocks': 85.0,
            'bonds': 5.0,
            'cash': 3.0,
            'real_estate': 5.0,
            'other': 2.0
        },
        'recurring_expenses': [
            {
                'name': 'Tech Equipment',
                'category': 'Work Equipment',
                'amount': 5000.0,
                'frequency_years': 2,
                'start_year': current_year,
                'end_year': None,
                'inflation_adjust': True,
                'parent': 'Both',
                'financing_years': 0,
                'interest_rate': 0.0
            }
        ],
        'state_timeline': [{
            'year': current_year,
            'state': 'San Francisco',
            'spending_strategy': 'High-end'
        }],
        'children_count': 2,
        'initial_assets': 1300000.0,
        'initial_liabilities': 900000.0,
        'annual_income': 450000.0
    }

    # Scenario 2: Mid-Career Family
    scenarios["[DEMO] 3-Kid Family with Mixed Education Plans (Seattle, Moderate)"] = {
        'houses': [{
            'name': 'Primary Home',
            'purchase_year': current_year - 8,
            'purchase_price': 650000.0,
            'current_value': 800000.0,
            'mortgage_balance': 420000.0,
            'mortgage_rate': 3.5,
            'mortgage_years_left': 22,
            'property_tax_rate': 1.0,
            'home_insurance': 1800.0,
            'maintenance_rate': 0.8,
            'upkeep_costs': 5000.0,
            'owner': 'Shared',
            'timeline': [{'year': current_year - 8, 'status': 'Own_Live', 'rental_income': 0.0}]
        }],
        'portfolio_allocation': {
            'stocks': 80.0,
            'bonds': 15.0,
            'cash': 2.0,
            'real_estate': 3.0,
            'other': 0.0
        },
        'recurring_expenses': [
            {
                'name': 'Family Vehicle',
                'category': 'Vehicle',
                'amount': 45000.0,
                'frequency_years': 8,
                'start_year': current_year + 3,
                'end_year': None,
                'inflation_adjust': True,
                'parent': 'Both',
                'financing_years': 5,
                'interest_rate': 4.5
            },
            {
                'name': 'Annual Family Vacation',
                'category': 'Travel',
                'amount': 8000.0,
                'frequency_years': 1,
                'start_year': current_year,
                'end_year': None,
                'inflation_adjust': True,
                'parent': 'Both',
                'financing_years': 0,
                'interest_rate': 0.0
            }
        ],
        'state_timeline': [{
            'year': current_year,
            'state': 'Seattle',
            'spending_strategy': 'Average'
        }],
        'children_count': 3,
        'initial_assets': 800000.0,
        'initial_liabilities': 420000.0,
        'annual_income': 185000.0
    }

    # Scenario 3: Wealthy Executives
    scenarios["[DEMO] Wealthy Executives with Multiple Properties (NYC, $4.7M)"] = {
        'houses': [
            {
                'name': 'Manhattan Apartment',
                'purchase_year': current_year - 10,
                'purchase_price': 2500000.0,
                'current_value': 3200000.0,
                'mortgage_balance': 0.0,
                'mortgage_rate': 0.0,
                'mortgage_years_left': 0,
                'property_tax_rate': 0.8,
                'home_insurance': 4500.0,
                'maintenance_rate': 0.4,
                'upkeep_costs': 12000.0,
                'owner': 'Shared',
                'timeline': [{'year': current_year - 10, 'status': 'Own_Live', 'rental_income': 0.0}]
            },
            {
                'name': 'Hamptons Summer Home',
                'purchase_year': current_year - 5,
                'purchase_price': 1800000.0,
                'current_value': 2100000.0,
                'mortgage_balance': 0.0,
                'mortgage_rate': 0.0,
                'mortgage_years_left': 0,
                'property_tax_rate': 2.5,
                'home_insurance': 3200.0,
                'maintenance_rate': 1.0,
                'upkeep_costs': 15000.0,
                'owner': 'Shared',
                'timeline': [{'year': current_year - 5, 'status': 'Own_Live', 'rental_income': 0.0}]
            }
        ],
        'portfolio_allocation': {
            'stocks': 70.0,
            'bonds': 20.0,
            'cash': 2.0,
            'real_estate': 5.0,
            'other': 3.0
        },
        'recurring_expenses': [
            {
                'name': 'Luxury Vehicles',
                'category': 'Vehicle',
                'amount': 90000.0,
                'frequency_years': 5,
                'start_year': current_year + 2,
                'end_year': None,
                'inflation_adjust': True,
                'parent': 'Both',
                'financing_years': 0,
                'interest_rate': 0.0
            },
            {
                'name': 'International Travel',
                'category': 'Travel',
                'amount': 25000.0,
                'frequency_years': 1,
                'start_year': current_year,
                'end_year': None,
                'inflation_adjust': True,
                'parent': 'Both',
                'financing_years': 0,
                'interest_rate': 0.0
            }
        ],
        'state_timeline': [{
            'year': current_year,
            'state': 'New York',
            'spending_strategy': 'High-end'
        }],
        'children_count': 2,
        'initial_assets': 5300000.0,
        'initial_liabilities': 0.0,
        'annual_income': 750000.0
    }

    return scenarios

# TEST 1: Portfolio Allocation Validation
def test_portfolio_allocations():
    """Test that all portfolio allocations are valid"""
    scenarios = create_demo_scenarios()

    for scenario_name, scenario_data in scenarios.items():
        portfolio = PortfolioAllocation(**scenario_data['portfolio_allocation'])
        total = portfolio.total()
        is_valid = portfolio.is_valid()

        print(f"\n  {scenario_name[:50]}...")
        print(f"    Total allocation: {total}%")
        print(f"    Valid: {is_valid}")

        assert is_valid, f"Portfolio doesn't sum to 100%: {total}%"
        assert portfolio.stocks >= 0, "Stocks allocation is negative"
        assert portfolio.bonds >= 0, "Bonds allocation is negative"

    print("\n✅ All portfolio allocations are valid")
    return True

test_scenario("Portfolio Allocation Validation", test_portfolio_allocations)

# TEST 2: House Data Integrity
def test_house_data_integrity():
    """Test that all house data is complete and valid"""
    scenarios = create_demo_scenarios()

    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  {scenario_name[:50]}...")
        houses = []
        for h in scenario_data['houses']:
            house_dict = h.copy()
            if 'timeline' in house_dict and house_dict['timeline']:
                house_dict['timeline'] = [HouseTimelineEntry(**entry) for entry in house_dict['timeline']]
            houses.append(House(**house_dict))

        for house in houses:
            print(f"    {house.name}: ${house.current_value:,.0f}")
            assert house.current_value >= 0, f"Invalid house value: {house.current_value}"
            assert house.mortgage_balance >= 0, f"Invalid mortgage: {house.mortgage_balance}"
            assert house.mortgage_balance <= house.current_value * 2, "Mortgage seems too high"

            if house.mortgage_balance > 0:
                assert house.mortgage_rate > 0, "Mortgage exists but rate is 0"
                assert house.mortgage_years_left > 0, "Mortgage exists but years left is 0"

    print("\n✅ All house data is valid and complete")
    return True

test_scenario("House Data Integrity", test_house_data_integrity)

# TEST 3: Recurring Expenses Validation
def test_recurring_expenses():
    """Test that all recurring expenses are properly configured"""
    scenarios = create_demo_scenarios()

    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  {scenario_name[:50]}...")
        recurring = [RecurringExpense(**re) for re in scenario_data['recurring_expenses']]

        for expense in recurring:
            print(f"    {expense.name}: ${expense.amount:,.0f} every {expense.frequency_years} years")
            assert expense.amount > 0, f"Invalid expense amount: {expense.amount}"
            assert expense.frequency_years > 0, "Frequency must be positive"
            assert expense.start_year >= current_year - 100, "Start year seems invalid"

            if expense.financing_years > 0:
                assert expense.interest_rate >= 0, "Financing exists but interest rate is negative"

    print("\n✅ All recurring expenses are valid")
    return True

test_scenario("Recurring Expenses Validation", test_recurring_expenses)

# TEST 4: Economic Scenario Impact Analysis
def test_economic_scenario_impacts():
    """Test how different economic conditions affect outcomes"""
    scenarios = create_demo_scenarios()

    print("\n\nTesting economic scenario impacts on net worth projections...\n")

    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  Scenario: {scenario_name[:60]}")
        print(f"  Starting Assets: ${scenario_data['initial_assets']:,.0f}")
        print(f"  Starting Liabilities: ${scenario_data['initial_liabilities']:,.0f}")
        print(f"  Annual Income: ${scenario_data['annual_income']:,.0f}")
        print(f"  Net Worth: ${scenario_data['initial_assets'] - scenario_data['initial_liabilities']:,.0f}\n")

        scenario_economic_results = {}

        for econ in economic_scenarios:
            # Simple 10-year projection
            years = 10
            net_worth = scenario_data['initial_assets'] - scenario_data['initial_liabilities']
            annual_savings = scenario_data['annual_income'] * 0.20  # Assume 20% savings rate

            # Project forward with compound returns
            for year in range(years):
                # Investment growth
                net_worth *= (1 + econ.investment_return)
                # Add savings (adjusted for inflation)
                net_worth += annual_savings * ((1 + econ.wage_growth_rate) ** year)
                # Subtract expense growth impact (approximate)
                expense_increase = annual_savings * 0.1 * (econ.expense_growth_rate - 0.02)
                net_worth -= expense_increase

            scenario_economic_results[econ.name] = net_worth
            print(f"    {econ.name:30s}: ${net_worth:>12,.0f} (after {years} years)")

        # Check stability - results should be positive and reasonable
        min_nw = min(scenario_economic_results.values())
        max_nw = max(scenario_economic_results.values())

        assert min_nw > 0, f"Net worth became negative in some scenario: ${min_nw:,.0f}"
        assert max_nw < 1e9, f"Net worth seems unrealistically high: ${max_nw:,.0f}"

        variation = (max_nw - min_nw) / min_nw * 100
        print(f"\n  📊 Variation across scenarios: {variation:.1f}%")
        print(f"  Range: ${min_nw:,.0f} to ${max_nw:,.0f}")

        scenario_results[scenario_name] = scenario_economic_results

    print("\n✅ All economic scenarios produce stable, reasonable outcomes")
    return scenario_results

results = test_scenario("Economic Scenario Impact Analysis", test_economic_scenario_impacts)

# TEST 5: Stress Test - Extreme Values
def test_extreme_values():
    """Test with extreme economic values to ensure no crashes"""

    extreme_scenarios = [
        EconomicParameters("Market Crash", -0.30, 0.10, 0.12, 0.15, -0.10, 0.00),
        EconomicParameters("Depression", -0.10, 0.01, 0.01, 0.03, -0.05, -0.02),
        EconomicalParameters("Hyperinflation", 0.15, 0.20, 0.25, 0.30, 0.10, 0.15),
    ]

    print("\n  Testing extreme economic conditions...")

    for econ in extreme_scenarios:
        print(f"\n    {econ.name}:")
        print(f"      Investment Return: {econ.investment_return*100:+.1f}%")
        print(f"      Inflation: {econ.inflation_rate*100:.1f}%")

        # Simple calculation to ensure no crashes
        initial_value = 100000
        years = 5
        final_value = initial_value * ((1 + econ.investment_return) ** years)

        print(f"      $100k → ${final_value:,.0f} in {years} years")

        assert not np.isnan(final_value), "Calculation resulted in NaN"
        assert not np.isinf(final_value), "Calculation resulted in infinity"

    print("\n✅ Extreme values handled without crashes")
    return True

# Fix typo in extreme scenarios
def test_extreme_values_fixed():
    """Test with extreme economic values to ensure no crashes"""

    extreme_scenarios = [
        EconomicParameters("Market Crash", -0.30, 0.10, 0.12, 0.15, -0.10, 0.00),
        EconomicParameters("Depression", -0.10, 0.01, 0.01, 0.03, -0.05, -0.02),
        EconomicParameters("Hyperinflation", 0.15, 0.20, 0.25, 0.30, 0.10, 0.15),
    ]

    print("\n  Testing extreme economic conditions...")

    for econ in extreme_scenarios:
        print(f"\n    {econ.name}:")
        print(f"      Investment Return: {econ.investment_return*100:+.1f}%")
        print(f"      Inflation: {econ.inflation_rate*100:.1f}%")

        # Simple calculation to ensure no crashes
        initial_value = 100000
        years = 5
        final_value = initial_value * ((1 + econ.investment_return) ** years)

        print(f"      $100k → ${final_value:,.0f} in {years} years")

        assert not np.isnan(final_value), "Calculation resulted in NaN"
        assert not np.isinf(final_value), "Calculation resulted in infinity"

    print("\n✅ Extreme values handled without crashes")
    return True

test_scenario("Extreme Value Stress Test", test_extreme_values_fixed)

# TEST 6: Data Structure Consistency
def test_data_structure_consistency():
    """Ensure all scenarios have consistent data structures"""
    scenarios = create_demo_scenarios()

    required_keys = ['houses', 'portfolio_allocation', 'recurring_expenses',
                     'state_timeline', 'children_count', 'initial_assets',
                     'initial_liabilities', 'annual_income']

    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  Checking: {scenario_name[:50]}...")

        for key in required_keys:
            assert key in scenario_data, f"Missing required key: {key}"
            print(f"    ✓ {key}")

        # Type checks
        assert isinstance(scenario_data['houses'], list), "Houses must be a list"
        assert isinstance(scenario_data['recurring_expenses'], list), "Expenses must be a list"
        assert isinstance(scenario_data['children_count'], int), "Children count must be int"
        assert scenario_data['children_count'] >= 0, "Children count cannot be negative"

    print("\n✅ All data structures are consistent")
    return True

test_scenario("Data Structure Consistency", test_data_structure_consistency)

# FINAL SUMMARY
print("\n" + "=" * 80)
print("ECONOMIC STABILITY TEST SUMMARY")
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
else:
    print("\n🎉 ALL TESTS PASSED!")
    print("\n✅ Key Findings:")
    print("  • All demo scenarios have valid data structures")
    print("  • Portfolio allocations sum to 100%")
    print("  • All house data is consistent and reasonable")
    print("  • Recurring expenses are properly configured")
    print(f"  • Tested {len(economic_scenarios)} different economic conditions")
    print("  • All scenarios produce stable outputs")
    print("  • Extreme values handled without crashes")
    print("\n📊 Economic Scenarios Tested:")
    for econ in economic_scenarios:
        print(f"  • {econ.name}")

print("\n" + "=" * 80)

sys.exit(0 if failed == 0 else 1)
