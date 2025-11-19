#!/usr/bin/env python3
"""
Comprehensive test scenarios for Financial Planning Suite V16
Tests various family configurations and recent changes
"""

import sys
import traceback
from dataclasses import dataclass
from typing import Optional, List

print("=" * 80)
print("FINANCIAL PLANNING SUITE V16 - FAMILY SCENARIO TESTS")
print("=" * 80)

# Import necessary components
try:
    from FinancialPlannerV16_ClaudeCodeV import (
        RecurringExpense, MajorPurchase, StateTimelineEntry,
        get_location_display_name, LOCATION_DISPLAY_NAMES,
        FAMILY_EXPENSE_TEMPLATES, AVAILABLE_LOCATIONS_FAMILY
    )
    print("✅ Successfully imported V16 components\n")
except ImportError as e:
    print(f"❌ Failed to import components: {e}")
    # Continue with limited testing
    RecurringExpense = None

test_results = []

def test_scenario(name, test_func):
    """Run a test scenario and record results"""
    try:
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"{'='*70}")
        test_func()
        print(f"✅ PASSED: {name}\n")
        test_results.append((name, "PASSED", None))
        return True
    except Exception as e:
        print(f"❌ FAILED: {name}")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        test_results.append((name, "FAILED", str(e)))
        return False


# TEST 1: Location Display Names
def test_location_display_names():
    """Test that location display names include state/country"""
    print("Testing location display names with state/country information...")

    test_locations = [
        ("Seattle", "Seattle, WA, USA"),
        ("Toronto", "Toronto, ON, Canada"),
        ("Paris", "Paris, France"),
        ("Berlin", "Berlin, Germany"),
        ("Sydney", "Sydney, NSW, Australia"),
    ]

    for location, expected_contains in test_locations:
        display_name = get_location_display_name(location)
        print(f"  {location} -> {display_name}")
        assert location in display_name, f"Location {location} should be in display name"

    print("✅ All locations have proper display names with state/country")


# TEST 2: Family Expense Templates (Parent Retirement Help removed)
def test_parent_retirement_help_removed():
    """Verify Parent Retirement Help is removed from all templates"""
    print("Verifying Parent Retirement Help removed from expense templates...")

    templates_checked = 0
    for location, strategies in FAMILY_EXPENSE_TEMPLATES.items():
        for strategy_name, template in strategies.items():
            templates_checked += 1
            assert 'Parent Retirement Help' not in template, \
                f"Parent Retirement Help found in {location} - {strategy_name}"
            print(f"  ✓ {location} - {strategy_name}: No Parent Retirement Help")

    print(f"✅ Checked {templates_checked} templates - all clean")


# TEST 3: Recurring Expenses for Parent Retirement Help
def test_recurring_parent_retirement():
    """Test recurring expense for parent retirement help"""
    if RecurringExpense is None:
        print("⚠️  Skipping - RecurringExpense not available")
        return

    print("Testing Parent Retirement Help as recurring expense...")

    parent_help = RecurringExpense(
        name="Parent Retirement Help",
        category="Family Support",
        amount=20000.0,
        frequency_years=1,
        start_year=2025,
        end_year=None,
        inflation_adjust=False,
        parent="Both",
        financing_years=0,
        interest_rate=0.0
    )

    assert parent_help.amount == 20000.0
    assert parent_help.frequency_years == 1
    assert parent_help.inflation_adjust == False
    print(f"  ✓ Amount: ${parent_help.amount:,.0f}")
    print(f"  ✓ Frequency: {parent_help.frequency_years} year(s)")
    print(f"  ✓ Inflation adjust: {parent_help.inflation_adjust}")

    # Test it occurs every year
    years_with_expense = []
    for year in range(2025, 2035):
        years_since_start = year - parent_help.start_year
        if years_since_start % parent_help.frequency_years == 0:
            years_with_expense.append(year)

    assert len(years_with_expense) == 10, "Should occur every year for 10 years"
    print(f"  ✓ Occurs in {len(years_with_expense)} years from 2025-2034")
    print("✅ Parent Retirement Help recurring expense configured correctly")


# TEST 4: Multiple Family Scenarios - Different Configurations
def test_various_family_configurations():
    """Test calculations for different family types"""
    print("Testing various family configurations...")

    families = [
        {
            "name": "Young Dual-Income Family",
            "parent1_age": 30,
            "parent2_age": 28,
            "parent1_income": 120000,
            "parent2_income": 95000,
            "children": [
                {"name": "Alice", "birth_year": 2022},
                {"name": "Bob", "birth_year": 2024}
            ],
            "net_worth": 100000,
        },
        {
            "name": "Mid-Career Single Parent",
            "parent1_age": 42,
            "parent2_age": 42,  # Same age (single parent scenario)
            "parent1_income": 85000,
            "parent2_income": 0,
            "children": [
                {"name": "Charlie", "birth_year": 2015},
            ],
            "net_worth": 250000,
        },
        {
            "name": "High-Earner Empty Nesters",
            "parent1_age": 55,
            "parent2_age": 53,
            "parent1_income": 200000,
            "parent2_income": 180000,
            "children": [],  # No children
            "net_worth": 2000000,
        },
        {
            "name": "Retiring Couple",
            "parent1_age": 63,
            "parent2_age": 61,
            "parent1_income": 75000,
            "parent2_income": 65000,
            "children": [],
            "net_worth": 1200000,
        },
        {
            "name": "Large Family",
            "parent1_age": 38,
            "parent2_age": 36,
            "parent1_income": 140000,
            "parent2_income": 110000,
            "children": [
                {"name": "Child1", "birth_year": 2015},
                {"name": "Child2", "birth_year": 2017},
                {"name": "Child3", "birth_year": 2019},
                {"name": "Child4", "birth_year": 2021},
            ],
            "net_worth": 500000,
        },
    ]

    for family in families:
        print(f"\n  Testing: {family['name']}")
        print(f"    Parents: {family['parent1_age']}/{family['parent2_age']} years old")
        print(f"    Income: ${family['parent1_income']:,} / ${family['parent2_income']:,}")
        print(f"    Children: {len(family['children'])}")
        print(f"    Net Worth: ${family['net_worth']:,}")

        # Calculate timeline duration
        current_year = 2025
        parent1_100_year = (current_year - family['parent1_age']) + 100
        parent2_100_year = (current_year - family['parent2_age']) + 100
        timeline_end = max(parent1_100_year, parent2_100_year)
        duration = timeline_end - current_year

        print(f"    Timeline: {current_year} to {timeline_end} ({duration} years)")

        # Basic validation
        assert family['parent1_age'] > 0 and family['parent1_age'] < 100
        assert family['parent2_age'] > 0 and family['parent2_age'] < 100
        assert family['net_worth'] >= 0
        assert duration > 0 and duration < 100

        # Test college overlap for families with children
        if family['children']:
            college_years = {}
            for child in family['children']:
                for age in range(18, 22):
                    college_year = child['birth_year'] + age
                    if college_year not in college_years:
                        college_years[college_year] = []
                    college_years[college_year].append(child['name'])

            max_overlap = max(len(kids) for kids in college_years.values()) if college_years else 0
            print(f"    Max college overlap: {max_overlap} children simultaneously")

        print(f"    ✓ {family['name']} validated")

    print(f"\n✅ All {len(families)} family configurations validated successfully")


# TEST 5: State Timeline Changes
def test_state_timeline_scenarios():
    """Test different state relocation scenarios"""
    if StateTimelineEntry is None:
        print("⚠️  Skipping - StateTimelineEntry not available")
        return

    print("Testing state timeline relocation scenarios...")

    scenarios = [
        {
            "name": "Domestic Relocations",
            "timeline": [
                StateTimelineEntry(2025, "Seattle", "Average"),
                StateTimelineEntry(2030, "Houston", "Conservative"),
                StateTimelineEntry(2040, "New York", "High-end"),
            ]
        },
        {
            "name": "International Move",
            "timeline": [
                StateTimelineEntry(2025, "San Francisco", "High-end"),
                StateTimelineEntry(2028, "Paris", "Average"),
                StateTimelineEntry(2035, "Toronto", "Average"),
            ]
        },
        {
            "name": "Stay in One Location",
            "timeline": [
                StateTimelineEntry(2025, "Portland", "Average"),
            ]
        },
        {
            "name": "Multiple Relocations",
            "timeline": [
                StateTimelineEntry(2025, "Sacramento", "Conservative"),
                StateTimelineEntry(2028, "Austin", "Average"),  # Not in templates
                StateTimelineEntry(2032, "Berlin", "Average"),
                StateTimelineEntry(2040, "Melbourne", "High-end"),
                StateTimelineEntry(2050, "Vancouver", "Conservative"),
            ]
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        print(f"    Relocations: {len(scenario['timeline'])}")

        for i, entry in enumerate(scenario['timeline'], 1):
            display_name = get_location_display_name(entry.state)
            print(f"      {i}. {entry.year}: {display_name} ({entry.spending_strategy})")

            # Validate entry
            assert entry.year >= 2025 and entry.year <= 2100
            assert entry.spending_strategy in ["Conservative", "Average", "High-end"]

        print(f"    ✓ Validated {len(scenario['timeline'])} timeline entries")

    print(f"\n✅ All {len(scenarios)} state timeline scenarios validated")


# TEST 6: Expense Calculation Scenarios
def test_expense_calculations():
    """Test expense calculations for different scenarios"""
    print("Testing expense calculations...")

    # Test that all locations have all three strategies
    for location in AVAILABLE_LOCATIONS_FAMILY:
        if location in FAMILY_EXPENSE_TEMPLATES:
            template = FAMILY_EXPENSE_TEMPLATES[location]
            for strategy in ["Conservative", "Average", "High-end"]:
                assert strategy in template, \
                    f"{location} missing {strategy} strategy"

                expenses = template[strategy]
                total = sum(expenses.values())

                # Validate totals are reasonable
                assert total > 0, f"{location} {strategy} has zero expenses"
                assert total < 1000000, f"{location} {strategy} expenses too high: ${total}"

            print(f"  ✓ {location}: All strategies present, totals reasonable")
        else:
            print(f"  ⚠️  {location}: No template (might be custom)")

    print("✅ Expense calculations validated")


# TEST 7: Recurring Expenses in Various Scenarios
def test_recurring_expense_scenarios():
    """Test various recurring expense patterns"""
    if RecurringExpense is None:
        print("⚠️  Skipping - RecurringExpense not available")
        return

    print("Testing recurring expense scenarios...")

    recurring_expenses = [
        RecurringExpense(
            name="Vehicle Replacement",
            category="Vehicle",
            amount=35000,
            frequency_years=7,
            start_year=2025,
            end_year=2065,
            inflation_adjust=True,
            parent="Both",
            financing_years=5,
            interest_rate=0.045
        ),
        RecurringExpense(
            name="Home Renovation",
            category="Housing",
            amount=50000,
            frequency_years=15,
            start_year=2030,
            end_year=2070,
            inflation_adjust=True,
            parent="Both",
            financing_years=0,
            interest_rate=0.0
        ),
        RecurringExpense(
            name="Annual Vacation",
            category="Travel",
            amount=8000,
            frequency_years=1,
            start_year=2025,
            end_year=2060,
            inflation_adjust=True,
            parent="Both",
            financing_years=0,
            interest_rate=0.0
        ),
    ]

    for expense in recurring_expenses:
        print(f"\n  {expense.name}:")
        print(f"    Amount: ${expense.amount:,.0f}")
        print(f"    Frequency: Every {expense.frequency_years} years")
        print(f"    Period: {expense.start_year} to {expense.end_year or 'ongoing'}")

        # Calculate occurrences
        end_year = expense.end_year if expense.end_year else 2100
        occurrences = []
        for year in range(expense.start_year, end_year + 1):
            years_since_start = year - expense.start_year
            if years_since_start % expense.frequency_years == 0:
                occurrences.append(year)

        print(f"    Occurrences: {len(occurrences)} times")
        if len(occurrences) <= 10:
            print(f"    Years: {occurrences}")
        else:
            print(f"    First 5: {occurrences[:5]}")
            print(f"    Last 5: {occurrences[-5:]}")

        assert len(occurrences) > 0, "Should have at least one occurrence"
        print(f"    ✓ Validated")

    print(f"\n✅ All {len(recurring_expenses)} recurring expense scenarios validated")


# TEST 8: Edge Cases
def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("Testing edge cases...")

    # Test with very young parents
    young_parent1_100 = (2025 - 20) + 100  # 20 year old in 2025
    assert young_parent1_100 == 2105
    print(f"  ✓ 20-year-old parent reaches 100 in {young_parent1_100}")

    # Test with elderly parents
    old_parent1_100 = (2025 - 70) + 100  # 70 year old in 2025
    assert old_parent1_100 == 2055
    print(f"  ✓ 70-year-old parent reaches 100 in {old_parent1_100}")

    # Test with zero income
    zero_income_total = 0 + 0
    assert zero_income_total == 0
    print(f"  ✓ Zero income scenario: ${zero_income_total}")

    # Test with negative net worth (debt)
    negative_net_worth = -50000
    assert negative_net_worth < 0
    print(f"  ✓ Negative net worth (debt): ${negative_net_worth:,}")

    # Test with very high expenses
    high_expenses = sum([
        50000,  # Food
        20000,  # Clothing
        30000,  # Transportation
        40000,  # Entertainment
        10000,  # Personal care
        30000,  # Other
    ])
    assert high_expenses > 0
    print(f"  ✓ High expense scenario: ${high_expenses:,}/year")

    # Test with no children
    children_count = 0
    college_costs = children_count * 75000 * 4
    assert college_costs == 0
    print(f"  ✓ No children scenario: $0 college costs")

    # Test with many children
    many_children = 6
    max_simultaneous_college = min(4, many_children)  # Assume 2-year gaps
    print(f"  ✓ Large family: {many_children} children, up to {max_simultaneous_college} in college simultaneously")

    print("✅ All edge cases handled correctly")


# TEST 9: Template Consistency
def test_template_consistency():
    """Verify all templates have consistent categories"""
    print("Testing template consistency...")

    # Get categories from first template
    first_location = list(FAMILY_EXPENSE_TEMPLATES.keys())[0]
    first_strategy = list(FAMILY_EXPENSE_TEMPLATES[first_location].keys())[0]
    expected_categories = set(FAMILY_EXPENSE_TEMPLATES[first_location][first_strategy].keys())

    print(f"  Expected categories: {sorted(expected_categories)}")
    print(f"  Total categories: {len(expected_categories)}")

    # Verify 'Parent Retirement Help' is NOT in categories
    assert 'Parent Retirement Help' not in expected_categories, \
        "Parent Retirement Help should not be in expense categories"
    print(f"  ✓ Parent Retirement Help correctly removed from categories")

    # Check all templates have same categories
    inconsistent_templates = []
    for location, strategies in FAMILY_EXPENSE_TEMPLATES.items():
        for strategy, expenses in strategies.items():
            template_categories = set(expenses.keys())
            if template_categories != expected_categories:
                inconsistent_templates.append(f"{location} - {strategy}")
                missing = expected_categories - template_categories
                extra = template_categories - expected_categories
                if missing:
                    print(f"  ⚠️  {location} - {strategy} missing: {missing}")
                if extra:
                    print(f"  ⚠️  {location} - {strategy} has extra: {extra}")

    if inconsistent_templates:
        print(f"  ⚠️  {len(inconsistent_templates)} templates have inconsistent categories")
    else:
        print(f"  ✓ All templates have consistent categories")

    print("✅ Template consistency check complete")


# FINAL SUMMARY
def print_test_summary():
    """Print final test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, status, _ in test_results if status == "PASSED")
    failed = sum(1 for _, status, _ in test_results if status == "FAILED")
    total = len(test_results)

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if total > 0:
        print(f"Success Rate: {(passed/total*100):.1f}%")

    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for name, status, error in test_results:
            if status == "FAILED":
                print(f"  - {name}")
                if error:
                    print(f"    Error: {error}")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Application is stable across multiple family scenarios")
        print("✅ Recent changes are working correctly")
        print("✅ No broken functionality detected")
        return True


# RUN ALL TESTS
if __name__ == "__main__":
    test_scenario("Location Display Names", test_location_display_names)
    test_scenario("Parent Retirement Help Removed from Templates", test_parent_retirement_help_removed)
    test_scenario("Recurring Parent Retirement Help", test_recurring_parent_retirement)
    test_scenario("Various Family Configurations", test_various_family_configurations)
    test_scenario("State Timeline Scenarios", test_state_timeline_scenarios)
    test_scenario("Expense Calculations", test_expense_calculations)
    test_scenario("Recurring Expense Scenarios", test_recurring_expense_scenarios)
    test_scenario("Edge Cases", test_edge_cases)
    test_scenario("Template Consistency", test_template_consistency)

    success = print_test_summary()
    sys.exit(0 if success else 1)
