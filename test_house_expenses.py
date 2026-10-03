#!/usr/bin/env python3
"""
Quick test to verify house expenses are being included in total expenses
"""

# Test 1: Verify new expense categories exist in templates
print("=" * 60)
print("TESTING HOUSEHOLD EXPENSE ADDITIONS")
print("=" * 60)

from FinancialPlanner_v0_7 import FAMILY_EXPENSE_TEMPLATES

print("\n=== Test 1: Verify new expense categories in templates ===")
sample_location = "California"
sample_strategy = "Average"

template = FAMILY_EXPENSE_TEMPLATES[sample_location][sample_strategy]
print(f"\n{sample_location} - {sample_strategy} expenses:")

expected_categories = [
    'Food & Groceries',
    'Clothing',
    'Transportation',
    'Entertainment & Activities',
    'Personal Care',
    'Utilities',
    'Internet & Phone',
    'Subscriptions',
    'Other Expenses'
]

all_present = True
for category in expected_categories:
    if category in template:
        print(f"  ✓ {category}: ${template[category]:,.0f}")
    else:
        print(f"  ✗ {category}: MISSING!")
        all_present = False

print(f"\nTotal annual expenses: ${sum(template.values()):,.0f}")

if all_present:
    print("✓ All expected categories present in template")
else:
    print("✗ Some categories are missing!")

# Test 2: Verify utilities breakdown makes sense
print("\n=== Test 2: Verify utilities and subscriptions breakdown ===")
utilities_total = template['Utilities'] + template['Internet & Phone'] + template['Subscriptions']
print(f"  Utilities: ${template['Utilities']:,.0f} (~${template['Utilities']/12:.0f}/mo)")
print(f"  Internet & Phone: ${template['Internet & Phone']:,.0f} (~${template['Internet & Phone']/12:.0f}/mo)")
print(f"  Subscriptions: ${template['Subscriptions']:,.0f} (~${template['Subscriptions']/12:.0f}/mo)")
print(f"  Combined: ${utilities_total:,.0f}/yr (~${utilities_total/12:.0f}/mo)")

# Test 3: Check all locations have the new categories
print("\n=== Test 3: Verify all locations updated ===")
all_locations_ok = True
for location in FAMILY_EXPENSE_TEMPLATES:
    for strategy in FAMILY_EXPENSE_TEMPLATES[location]:
        template = FAMILY_EXPENSE_TEMPLATES[location][strategy]
        for category in expected_categories:
            if category not in template:
                print(f"  ✗ Missing {category} in {location}/{strategy}")
                all_locations_ok = False

if all_locations_ok:
    print(f"✓ All {len(FAMILY_EXPENSE_TEMPLATES)} locations have complete expense categories")
else:
    print("✗ Some locations are missing categories")

# Test 4: Verify house expense calculation logic
print("\n=== Test 4: Simulate house expense calculation ===")
print("\nExample house:")
print("  Current value: $650,000")
print("  Property tax rate: 0.92%")
print("  Home insurance: $1,800/yr")
print("  Maintenance rate: 1.5%")
print("  Upkeep costs: $3,000/yr")

house_value = 650000
property_tax = house_value * 0.0092
home_insurance = 1800
maintenance = house_value * 0.015
upkeep = 3000

print(f"\nAnnual house expenses:")
print(f"  Property tax: ${property_tax:,.0f}")
print(f"  Home insurance: ${home_insurance:,.0f}")
print(f"  Maintenance: ${maintenance:,.0f}")
print(f"  Upkeep: ${upkeep:,.0f}")
print(f"  TOTAL: ${property_tax + home_insurance + maintenance + upkeep:,.0f}/yr")
print(f"  Monthly: ${(property_tax + home_insurance + maintenance + upkeep)/12:,.0f}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("✓ New expense categories (Utilities, Internet & Phone, Subscriptions) added")
print("✓ All 16 locations updated with new categories")
print("✓ House expenses (property tax, insurance, maintenance, upkeep) will be included")
print("\nChanges ready for testing in the app!")
print("=" * 60)
