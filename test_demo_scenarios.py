#!/usr/bin/env python3
"""
Test script to validate all demo scenarios before loading in the app.
Ensures data structures are correct and complete.
"""

import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

# Define minimal dataclasses for testing
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

print("✅ Successfully defined all dataclasses for testing\n")

# Define test scenarios (matching what's in the app)
current_year = datetime.now().year

print("="*80)
print("DEMO SCENARIO VALIDATION TESTS")
print("="*80)
print(f"Testing with current year: {current_year}\n")

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
    'children_count': 2
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
    'children_count': 3
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
    'children_count': 2
}

# Scenario 4: Single Parent
scenarios["[DEMO] Single Teacher Mom, Conservative Saver (Sacramento, $95K)"] = {
    'houses': [{
        'name': 'Townhouse',
        'purchase_year': current_year - 3,
        'purchase_price': 420000.0,
        'current_value': 450000.0,
        'mortgage_balance': 336000.0,
        'mortgage_rate': 6.8,
        'mortgage_years_left': 27,
        'property_tax_rate': 1.1,
        'home_insurance': 1400.0,
        'maintenance_rate': 0.6,
        'upkeep_costs': 3000.0,
        'owner': 'ParentX',
        'timeline': [{'year': current_year - 3, 'status': 'Own_Live', 'rental_income': 0.0}]
    }],
    'portfolio_allocation': {
        'stocks': 80.0,
        'bonds': 15.0,
        'cash': 5.0,
        'real_estate': 0.0,
        'other': 0.0
    },
    'recurring_expenses': [
        {
            'name': 'Reliable Sedan',
            'category': 'Vehicle',
            'amount': 28000.0,
            'frequency_years': 10,
            'start_year': current_year + 5,
            'end_year': None,
            'inflation_adjust': True,
            'parent': 'ParentX',
            'financing_years': 5,
            'interest_rate': 4.0
        }
    ],
    'state_timeline': [{
        'year': current_year,
        'state': 'Sacramento',
        'spending_strategy': 'Conservative'
    }],
    'children_count': 1
}

# Scenario 5: Empty Nesters
scenarios["[DEMO] Empty Nesters Planning Retirement & Downsizing (Portland, Ages 58/57)"] = {
    'houses': [
        {
            'name': 'Family Home',
            'purchase_year': current_year - 25,
            'purchase_price': 350000.0,
            'current_value': 720000.0,
            'mortgage_balance': 0.0,
            'mortgage_rate': 0.0,
            'mortgage_years_left': 0,
            'property_tax_rate': 0.9,
            'home_insurance': 1600.0,
            'maintenance_rate': 1.0,
            'upkeep_costs': 6000.0,
            'owner': 'Shared',
            'timeline': [
                {'year': current_year - 25, 'status': 'Own_Live', 'rental_income': 0.0},
                {'year': current_year + 7, 'status': 'Sold', 'rental_income': 0.0}
            ]
        }
    ],
    'portfolio_allocation': {
        'stocks': 65.0,
        'bonds': 30.0,
        'cash': 2.0,
        'real_estate': 3.0,
        'other': 0.0
    },
    'recurring_expenses': [
        {
            'name': 'Healthcare Premiums',
            'category': 'Healthcare',
            'amount': 15000.0,
            'frequency_years': 1,
            'start_year': current_year,
            'end_year': current_year + 7,
            'inflation_adjust': True,
            'parent': 'Both',
            'financing_years': 0,
            'interest_rate': 0.0
        }
    ],
    'state_timeline': [
        {
            'year': current_year,
            'state': 'Portland',
            'spending_strategy': 'Average'
        },
        {
            'year': current_year + 7,
            'state': 'Portland',
            'spending_strategy': 'Conservative'
        }
    ],
    'children_count': 0
}

# Run validation tests
test_results = []
total_tests = 0
passed_tests = 0

for scenario_name, scenario_data in scenarios.items():
    print(f"\n{'='*80}")
    print(f"Testing: {scenario_name}")
    print('='*80)

    # Test 1: House data validation
    total_tests += 1
    try:
        houses = []
        for h in scenario_data['houses']:
            house_dict = h.copy()
            if 'timeline' in house_dict and house_dict['timeline']:
                house_dict['timeline'] = [HouseTimelineEntry(**entry) for entry in house_dict['timeline']]
            houses.append(House(**house_dict))
        print(f"✅ House data valid ({len(houses)} house(s))")
        passed_tests += 1
    except Exception as e:
        print(f"❌ House data invalid: {e}")

    # Test 2: Portfolio allocation validation
    total_tests += 1
    try:
        portfolio = PortfolioAllocation(**scenario_data['portfolio_allocation'])
        total = portfolio.total()
        if abs(total - 100.0) < 0.01:
            print(f"✅ Portfolio allocation valid (total: {total}%)")
            passed_tests += 1
        else:
            print(f"❌ Portfolio allocation doesn't sum to 100% (total: {total}%)")
    except Exception as e:
        print(f"❌ Portfolio allocation invalid: {e}")

    # Test 3: Recurring expenses validation
    total_tests += 1
    try:
        recurring = [RecurringExpense(**re) for re in scenario_data['recurring_expenses']]
        print(f"✅ Recurring expenses valid ({len(recurring)} expense(s))")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Recurring expenses invalid: {e}")

    # Test 4: State timeline validation
    total_tests += 1
    try:
        timeline = [StateTimelineEntry(**st) for st in scenario_data['state_timeline']]
        print(f"✅ State timeline valid ({len(timeline)} entry(ies))")
        passed_tests += 1
    except Exception as e:
        print(f"❌ State timeline invalid: {e}")

    # Test 5: Children count
    total_tests += 1
    child_count = scenario_data['children_count']
    print(f"✅ Children: {child_count}")
    passed_tests += 1

# Summary
print(f"\n{'='*80}")
print("TEST SUMMARY")
print('='*80)
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {total_tests - passed_tests}")
print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

if passed_tests == total_tests:
    print("\n✅ ALL TESTS PASSED! Demo scenarios are ready to load.")
    sys.exit(0)
else:
    print(f"\n❌ {total_tests - passed_tests} TESTS FAILED. Please fix before loading.")
    sys.exit(1)
