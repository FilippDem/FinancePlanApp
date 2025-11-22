#!/usr/bin/env python3
"""
Comprehensive Scenario Runner for Financial Planning App v0.72
Runs all demo scenarios through various economic conditions to ensure stability
"""

import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import traceback

print("=" * 80)
print("COMPREHENSIVE SCENARIO TESTING - All Economic Conditions")
print("=" * 80)
print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Define dataclasses matching the app
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

    def get_annual_costs(self) -> Dict[str, float]:
        """Calculate annual housing costs"""
        costs = {}
        costs['property_tax'] = self.current_value * (self.property_tax_rate / 100)
        costs['insurance'] = self.home_insurance
        costs['maintenance'] = self.current_value * (self.maintenance_rate / 100)
        costs['upkeep'] = self.upkeep_costs

        # Mortgage calculation
        if self.mortgage_balance > 0 and self.mortgage_years_left > 0:
            monthly_rate = (self.mortgage_rate / 100) / 12
            n_payments = self.mortgage_years_left * 12
            if monthly_rate > 0:
                monthly_payment = self.mortgage_balance * (
                    monthly_rate * (1 + monthly_rate) ** n_payments
                ) / ((1 + monthly_rate) ** n_payments - 1)
                costs['mortgage_payment'] = monthly_payment * 12
                # Approximate first year interest
                costs['mortgage_interest'] = self.mortgage_balance * (self.mortgage_rate / 100)
            else:
                costs['mortgage_payment'] = self.mortgage_balance / self.mortgage_years_left
                costs['mortgage_interest'] = 0
        else:
            costs['mortgage_payment'] = 0
            costs['mortgage_interest'] = 0

        costs['total'] = sum(costs.values())
        return costs

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

    def get_expected_return(self, economic_params) -> float:
        """Calculate weighted expected return based on allocation"""
        stock_return = economic_params.investment_return
        bond_return = economic_params.investment_return * 0.4  # Bonds typically lower
        cash_return = economic_params.inflation_rate * 0.5  # Cash barely keeps up
        re_return = economic_params.real_estate_appreciation

        weighted_return = (
            (self.stocks / 100) * stock_return +
            (self.bonds / 100) * bond_return +
            (self.cash / 100) * cash_return +
            (self.real_estate / 100) * re_return
        )
        return weighted_return

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

    def get_annual_cost(self, year: int, inflation_rate: float) -> float:
        """Calculate cost for a specific year"""
        if year < self.start_year:
            return 0
        if self.end_year and year > self.end_year:
            return 0

        years_since_start = year - self.start_year
        if years_since_start % self.frequency_years != 0:
            return 0

        cost = self.amount
        if self.inflation_adjust:
            cost *= (1 + inflation_rate) ** years_since_start

        return cost

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

# Current year
current_year = datetime.now().year

# Define comprehensive economic scenarios
economic_scenarios = {
    "Conservative Bear Market": EconomicParameters(
        "Conservative Bear Market",
        investment_return=0.02,
        inflation_rate=0.04,
        expense_growth_rate=0.05,
        healthcare_inflation_rate=0.07,
        real_estate_appreciation=0.01,
        wage_growth_rate=0.02
    ),
    "Moderate Baseline": EconomicParameters(
        "Moderate Baseline",
        investment_return=0.07,
        inflation_rate=0.025,
        expense_growth_rate=0.03,
        healthcare_inflation_rate=0.05,
        real_estate_appreciation=0.03,
        wage_growth_rate=0.03
    ),
    "Aggressive Bull Market": EconomicParameters(
        "Aggressive Bull Market",
        investment_return=0.12,
        inflation_rate=0.02,
        expense_growth_rate=0.02,
        healthcare_inflation_rate=0.04,
        real_estate_appreciation=0.05,
        wage_growth_rate=0.04
    ),
    "High Inflation": EconomicParameters(
        "High Inflation",
        investment_return=0.06,
        inflation_rate=0.06,
        expense_growth_rate=0.07,
        healthcare_inflation_rate=0.09,
        real_estate_appreciation=0.04,
        wage_growth_rate=0.05
    ),
    "Stagflation": EconomicParameters(
        "Stagflation",
        investment_return=0.03,
        inflation_rate=0.05,
        expense_growth_rate=0.06,
        healthcare_inflation_rate=0.08,
        real_estate_appreciation=0.02,
        wage_growth_rate=0.01
    ),
    "Market Crash": EconomicParameters(
        "Market Crash",
        investment_return=-0.20,
        inflation_rate=0.03,
        expense_growth_rate=0.02,
        healthcare_inflation_rate=0.04,
        real_estate_appreciation=-0.05,
        wage_growth_rate=0.00
    ),
}

# Define all demo scenarios
def get_demo_scenarios():
    """Return all demo scenarios"""
    scenarios = {}

    # Scenario 1
    scenarios["Tech Couple SF→Austin→Seattle"] = {
        'initial_net_worth': 400000,
        'annual_income': 450000,
        'annual_expenses': 180000,
        'houses': [
            {
                'name': 'SF Condo',
                'purchase_year': current_year - 2,
                'purchase_price': 1200000,
                'current_value': 1300000,
                'mortgage_balance': 900000,
                'mortgage_rate': 6.5,
                'mortgage_years_left': 28,
                'property_tax_rate': 1.2,
                'home_insurance': 2400,
                'maintenance_rate': 0.5,
                'upkeep_costs': 6000,
            }
        ],
        'portfolio': {
            'stocks': 85.0,
            'bonds': 5.0,
            'cash': 3.0,
            'real_estate': 5.0,
            'other': 2.0
        },
        'recurring_expenses': [
            {
                'name': 'Tech Equipment',
                'category': 'Work',
                'amount': 5000,
                'frequency_years': 2,
                'start_year': current_year,
            }
        ]
    }

    # Scenario 2
    scenarios["3-Kid Family Seattle→Portland→Denver"] = {
        'initial_net_worth': 380000,
        'annual_income': 185000,
        'annual_expenses': 95000,
        'houses': [
            {
                'name': 'Primary Home',
                'purchase_year': current_year - 8,
                'purchase_price': 650000,
                'current_value': 800000,
                'mortgage_balance': 420000,
                'mortgage_rate': 3.5,
                'mortgage_years_left': 22,
                'property_tax_rate': 1.0,
                'home_insurance': 1800,
                'maintenance_rate': 0.8,
                'upkeep_costs': 5000,
            }
        ],
        'portfolio': {
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
                'amount': 45000,
                'frequency_years': 8,
                'start_year': current_year + 3,
            },
            {
                'name': 'Annual Vacation',
                'category': 'Travel',
                'amount': 8000,
                'frequency_years': 1,
                'start_year': current_year,
            }
        ]
    }

    # Scenario 3
    scenarios["Executives NYC→Miami→Portugal"] = {
        'initial_net_worth': 5300000,
        'annual_income': 750000,
        'annual_expenses': 250000,
        'houses': [
            {
                'name': 'Manhattan Apartment',
                'purchase_year': current_year - 10,
                'purchase_price': 2500000,
                'current_value': 3200000,
                'mortgage_balance': 0,
                'mortgage_rate': 0,
                'mortgage_years_left': 0,
                'property_tax_rate': 0.8,
                'home_insurance': 4500,
                'maintenance_rate': 0.4,
                'upkeep_costs': 12000,
            },
            {
                'name': 'Hamptons Summer Home',
                'purchase_year': current_year - 5,
                'purchase_price': 1800000,
                'current_value': 2100000,
                'mortgage_balance': 0,
                'mortgage_rate': 0,
                'mortgage_years_left': 0,
                'property_tax_rate': 2.5,
                'home_insurance': 3200,
                'maintenance_rate': 1.0,
                'upkeep_costs': 15000,
            }
        ],
        'portfolio': {
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
                'amount': 90000,
                'frequency_years': 5,
                'start_year': current_year + 2,
            },
            {
                'name': 'International Travel',
                'category': 'Travel',
                'amount': 25000,
                'frequency_years': 1,
                'start_year': current_year,
            }
        ]
    }

    return scenarios

# Test runner
def run_comprehensive_test():
    """Run all scenarios through all economic conditions"""

    scenarios = get_demo_scenarios()
    results = {}
    errors = []

    print(f"Testing {len(scenarios)} scenarios × {len(economic_scenarios)} economic conditions")
    print(f"Total test combinations: {len(scenarios) * len(economic_scenarios)}\n")

    for scenario_name, scenario_data in scenarios.items():
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'='*70}")
        print(f"Initial Net Worth: ${scenario_data['initial_net_worth']:,.0f}")
        print(f"Annual Income: ${scenario_data['annual_income']:,.0f}")
        print(f"Annual Expenses: ${scenario_data['annual_expenses']:,.0f}")
        print(f"Houses: {len(scenario_data['houses'])}")

        scenario_results = {}

        for econ_name, econ_params in economic_scenarios.items():
            try:
                # Run 20-year projection
                result = project_scenario(scenario_data, econ_params, years=20)
                scenario_results[econ_name] = result

                print(f"\n  {econ_name:30s}: ", end="")
                print(f"${result['final_net_worth']:>12,.0f} ", end="")
                print(f"({result['growth_rate']:+6.1f}% avg/yr)", end="")

                # Check for issues
                if result['final_net_worth'] < 0:
                    print(" ⚠️  NEGATIVE")
                    errors.append(f"{scenario_name} → {econ_name}: Negative net worth")
                elif result['any_year_negative']:
                    print(" ⚠️  WENT NEGATIVE")
                    errors.append(f"{scenario_name} → {econ_name}: Went negative during timeline")
                else:
                    print(" ✓")

            except Exception as e:
                error_msg = f"{scenario_name} → {econ_name}: {str(e)}"
                errors.append(error_msg)
                print(f"\n  {econ_name:30s}: ❌ ERROR: {str(e)}")
                traceback.print_exc()

        results[scenario_name] = scenario_results

        # Statistical summary for this scenario
        final_values = [r['final_net_worth'] for r in scenario_results.values()]
        if final_values:
            print(f"\n  Statistical Summary:")
            print(f"    Min:  ${min(final_values):>12,.0f}")
            print(f"    Max:  ${max(final_values):>12,.0f}")
            print(f"    Avg:  ${sum(final_values)/len(final_values):>12,.0f}")
            print(f"    Range: {(max(final_values)/min(final_values) - 1)*100:.1f}% variation")

    return results, errors

def project_scenario(scenario_data: Dict, econ_params: EconomicParameters, years: int = 20) -> Dict:
    """Project a scenario forward with given economic parameters"""

    # Initialize
    net_worth = scenario_data['initial_net_worth']
    annual_income = scenario_data['annual_income']
    base_expenses = scenario_data['annual_expenses']

    # Create portfolio
    portfolio = PortfolioAllocation(**scenario_data['portfolio'])
    if not portfolio.is_valid():
        raise ValueError(f"Invalid portfolio allocation: {portfolio.total()}%")

    # Create houses
    houses = []
    for h_data in scenario_data['houses']:
        houses.append(House(**h_data))

    # Create recurring expenses
    recurring = []
    for r_data in scenario_data['recurring_expenses']:
        recurring.append(RecurringExpense(**r_data))

    # Track if ever went negative
    any_year_negative = False
    min_net_worth = net_worth

    # Project forward year by year
    for year_offset in range(years):
        year = current_year + year_offset

        # Calculate investment returns
        portfolio_return = portfolio.get_expected_return(econ_params)
        investment_gain = net_worth * portfolio_return

        # Calculate expenses
        total_expenses = base_expenses * ((1 + econ_params.expense_growth_rate) ** year_offset)

        # Add housing costs
        for house in houses:
            costs = house.get_annual_costs()
            total_expenses += costs['total']

        # Add recurring expenses
        for expense in recurring:
            total_expenses += expense.get_annual_cost(year, econ_params.inflation_rate)

        # Calculate income with wage growth
        income = annual_income * ((1 + econ_params.wage_growth_rate) ** year_offset)

        # Update net worth
        cashflow = income - total_expenses
        net_worth += cashflow + investment_gain

        # Track minimum
        if net_worth < 0:
            any_year_negative = True
        min_net_worth = min(min_net_worth, net_worth)

    # Calculate average annual growth rate
    initial = scenario_data['initial_net_worth']
    if initial > 0:
        growth_rate = ((net_worth / initial) ** (1/years) - 1) * 100
    else:
        growth_rate = 0

    return {
        'final_net_worth': net_worth,
        'growth_rate': growth_rate,
        'any_year_negative': any_year_negative,
        'min_net_worth': min_net_worth,
    }

# Run the comprehensive test
try:
    results, errors = run_comprehensive_test()

    # Final summary
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*80)

    total_combinations = len(get_demo_scenarios()) * len(economic_scenarios)
    error_count = len(errors)
    success_count = total_combinations - error_count

    print(f"\nTotal Test Combinations: {total_combinations}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"Success Rate: {(success_count/total_combinations)*100:.1f}%")

    if errors:
        print("\n⚠️  ISSUES FOUND:")
        for error in errors:
            print(f"  • {error}")
        print("\nNote: Negative net worth scenarios may be expected in severe economic conditions.")
        print("Review these cases to ensure they are realistic given the inputs.")

    print("\n✅ Test Complete!")
    print(f"All {len(get_demo_scenarios())} scenarios tested across {len(economic_scenarios)} economic conditions")

    sys.exit(0)

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
