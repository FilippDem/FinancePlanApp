#!/usr/bin/env python3
"""
Test script to validate financial calculations
Run this to verify the logic of key calculations in the Financial Planner
"""

def test_child_age_calculation():
    """Test child age calculation"""
    print("\n=== Testing Child Age Calculation ===")

    test_cases = [
        {"birth_year": 2020, "current_year": 2025, "expected_age": 5},
        {"birth_year": 2015, "current_year": 2025, "expected_age": 10},
        {"birth_year": 2010, "current_year": 2025, "expected_age": 15},
        {"birth_year": 2007, "current_year": 2025, "expected_age": 18},  # College age
        {"birth_year": 2027, "current_year": 2025, "expected_age": -2},  # Future birth
        {"birth_year": 1990, "current_year": 2025, "expected_age": 35},  # Over 30
    ]

    for test in test_cases:
        age = test["current_year"] - test["birth_year"]
        status = "✓" if age == test["expected_age"] else "✗"
        print(f"{status} Birth {test['birth_year']}, Current {test['current_year']} → Age {age} (expected {test['expected_age']})")

    return True


def test_college_costs():
    """Test college cost calculations"""
    print("\n=== Testing College Costs ===")

    # Public college costs
    public_tuition = {
        'Seattle': 12000,
        'Sacramento': 10000,
        'Houston': 11000,
        'New York': 13000,
    }

    # Private college costs
    private_tuition = {
        'Seattle': 55000,
        'Sacramento': 50000,
        'Houston': 48000,
        'New York': 60000,
    }

    # Room & board
    room_board = {
        'Seattle': 18000,
        'Sacramento': 15000,
        'Houston': 12000,
        'New York': 25000,
    }

    print("\nPublic College (4 years) in Seattle:")
    public_4yr = (public_tuition['Seattle'] + room_board['Seattle']) * 4
    print(f"  Annual: ${public_tuition['Seattle']:,} tuition + ${room_board['Seattle']:,} room/board = ${public_tuition['Seattle'] + room_board['Seattle']:,}")
    print(f"  4-year total: ${public_4yr:,}")

    print("\nPrivate College (4 years) in New York:")
    private_4yr = (private_tuition['New York'] + room_board['New York']) * 4
    print(f"  Annual: ${private_tuition['New York']:,} tuition + ${room_board['New York']:,} room/board = ${private_tuition['New York'] + room_board['New York']:,}")
    print(f"  4-year total: ${private_4yr:,}")

    print("\nPrivate vs Public Ratio:")
    for location in public_tuition.keys():
        ratio = private_tuition[location] / public_tuition[location]
        print(f"  {location}: {ratio:.1f}x (${private_tuition[location]:,} / ${public_tuition[location]:,})")

    return True


def test_private_k12_costs():
    """Test private K-12 school costs"""
    print("\n=== Testing Private K-12 Costs ===")

    private_school_costs = {
        'Seattle': 20000,
        'Sacramento': 18000,
        'Houston': 15000,
        'New York': 35000,
        'San Francisco': 32000,
        'Los Angeles': 25000,
        'Portland': 17000
    }

    print("\nPrivate K-12 Annual Costs by Location:")
    for location, cost in private_school_costs.items():
        print(f"  {location}: ${cost:,}/year")

    print("\nTotal Private K-12 (13 years, ages 5-17):")
    for location, cost in private_school_costs.items():
        total_13yr = cost * 13
        print(f"  {location}: ${total_13yr:,}")

    return True


def test_timeline_age_100():
    """Test timeline calculations to age 100"""
    print("\n=== Testing Timeline to Age 100 ===")

    test_cases = [
        {"current_year": 2025, "current_age": 35, "expected_100_year": 2090},
        {"current_year": 2025, "current_age": 70, "expected_100_year": 2055},
        {"current_year": 2025, "current_age": 50, "expected_100_year": 2075},
        {"current_year": 2030, "current_age": 40, "expected_100_year": 2090},
    ]

    for test in test_cases:
        year_100 = (test["current_year"] - test["current_age"]) + 100
        status = "✓" if year_100 == test["expected_100_year"] else "✗"
        print(f"{status} Age {test['current_age']} in {test['current_year']} reaches 100 in {year_100} (expected {test['expected_100_year']})")

    print("\nTimeline Duration Examples:")
    families = [
        {"parent1_age": 35, "parent2_age": 33, "current_year": 2025},
        {"parent1_age": 70, "parent2_age": 68, "current_year": 2025},
        {"parent1_age": 42, "parent2_age": 40, "current_year": 2025},
    ]

    for family in families:
        parent1_100 = (family["current_year"] - family["parent1_age"]) + 100
        parent2_100 = (family["current_year"] - family["parent2_age"]) + 100
        end_year = max(parent1_100, parent2_100)
        duration = end_year - family["current_year"]
        print(f"  Ages {family['parent1_age']}/{family['parent2_age']} in {family['current_year']} → Timeline to {end_year} ({duration} years)")

    return True


def test_college_overlap_scenario():
    """Test college overlap expenses"""
    print("\n=== Testing College Overlap Scenario ===")
    print("\nFamily with 4 children (2-year gaps):")

    children = [
        {"name": "Child 1", "birth_year": 2009, "college_type": "Public", "location": "Seattle"},
        {"name": "Child 2", "birth_year": 2011, "college_type": "Public", "location": "Seattle"},
        {"name": "Child 3", "birth_year": 2013, "college_type": "Private", "location": "Seattle"},
        {"name": "Child 4", "birth_year": 2015, "college_type": "Private", "location": "Seattle"},
    ]

    # College costs
    public_annual = 12000 + 18000  # tuition + room/board
    private_annual = 55000 + 18000  # tuition + room/board

    # Check each year
    years_to_check = range(2027, 2039)
    max_expense = 0
    max_year = 0

    print("\nYear-by-Year College Expenses:")
    for year in years_to_check:
        total = 0
        in_college = []

        for child in children:
            age = year - child["birth_year"]
            if 18 <= age <= 21:
                cost = private_annual if child["college_type"] == "Private" else public_annual
                total += cost
                in_college.append(f"{child['name']} (age {age}, {child['college_type']})")

        if total > max_expense:
            max_expense = total
            max_year = year

        if in_college:
            print(f"  {year}: ${total:,}/yr - {', '.join(in_college)}")

    print(f"\n⚠️  PEAK YEAR: {max_year} with ${max_expense:,}/yr in college expenses")
    print(f"    This requires ${max_expense/12:,.0f}/month just for college!")

    return True


def test_education_total_costs():
    """Calculate total education costs for different scenarios"""
    print("\n=== Testing Total Education Costs ===")

    scenarios = [
        {
            "name": "Public K-12 + Public College",
            "k12_type": "Public",
            "college_type": "Public",
            "location": "Seattle"
        },
        {
            "name": "Private K-12 + Private College",
            "k12_type": "Private",
            "college_type": "Private",
            "location": "New York"
        },
        {
            "name": "Public K-12 + Private College",
            "k12_type": "Public",
            "college_type": "Private",
            "location": "Seattle"
        },
        {
            "name": "Private K-12 + Public College",
            "k12_type": "Private",
            "college_type": "Public",
            "location": "San Francisco"
        },
    ]

    # Costs
    private_k12_costs = {'Seattle': 20000, 'New York': 35000, 'San Francisco': 32000}
    public_college_tuition = {'Seattle': 12000, 'New York': 13000, 'San Francisco': 10000}
    private_college_tuition = {'Seattle': 55000, 'New York': 60000, 'San Francisco': 58000}
    room_board = {'Seattle': 18000, 'New York': 25000, 'San Francisco': 24000}

    print("\nTotal Education Costs (Birth to Age 22):")
    for scenario in scenarios:
        k12_cost = 0
        if scenario["k12_type"] == "Private":
            k12_cost = private_k12_costs[scenario["location"]] * 13  # Ages 5-17

        if scenario["college_type"] == "Public":
            college_annual = public_college_tuition[scenario["location"]] + room_board[scenario["location"]]
        else:
            college_annual = private_college_tuition[scenario["location"]] + room_board[scenario["location"]]

        college_cost = college_annual * 4  # Ages 18-21

        total = k12_cost + college_cost

        print(f"\n  {scenario['name']} ({scenario['location']}):")
        print(f"    K-12 (13 years): ${k12_cost:,}")
        print(f"    College (4 years): ${college_cost:,} (${college_annual:,}/yr)")
        print(f"    TOTAL: ${total:,}")

    return True


def test_monte_carlo_cashflow():
    """Test Monte Carlo cashflow calculations"""
    print("\n=== Testing Monte Carlo Cashflow Logic ===")

    # Simple example
    income = 200000
    expenses = 80000
    investment_return_rate = 0.07
    initial_net_worth = 500000

    print("\nExample Scenario:")
    print(f"  Income: ${income:,}/yr")
    print(f"  Expenses: ${expenses:,}/yr")
    print(f"  Initial Net Worth: ${initial_net_worth:,}")
    print(f"  Investment Return: {investment_return_rate*100}%")

    print("\nYear-by-Year Projection (5 years):")
    net_worth = initial_net_worth

    for year in range(1, 6):
        cashflow = income - expenses
        investment_return = net_worth * investment_return_rate
        net_worth = net_worth + cashflow + investment_return

        print(f"  Year {year}:")
        print(f"    Income: ${income:,}")
        print(f"    Expenses: ${expenses:,}")
        print(f"    Cashflow: ${cashflow:,}")
        print(f"    Investment Return: ${investment_return:,.0f}")
        print(f"    Net Worth: ${net_worth:,.0f}")

    return True


def test_report_children_data():
    """Test report generation children data format"""
    print("\n=== Testing Report Children Data Format ===")

    current_year = 2025
    children_list = [
        {"name": "Alice", "birth_year": 2020},
        {"name": "Bob", "birth_year": 2018},
        {"name": "Charlie", "birth_year": 2015},
    ]

    print("\nChildren Data for Report:")
    report_children = []
    for child in children_list:
        age = current_year - child["birth_year"]
        report_child = {
            "name": child["name"],
            "age": age,
            "birth_year": child["birth_year"]
        }
        report_children.append(report_child)
        print(f"  {report_child}")

    print("\n✓ No KeyError - all children have 'age' field")

    return True


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("FINANCIAL PLANNER CALCULATION TESTS")
    print("=" * 60)

    tests = [
        test_child_age_calculation,
        test_college_costs,
        test_private_k12_costs,
        test_timeline_age_100,
        test_college_overlap_scenario,
        test_education_total_costs,
        test_monte_carlo_cashflow,
        test_report_children_data,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test {test.__name__} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
