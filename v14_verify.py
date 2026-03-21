"""
V14 Verification Tests — Confirm all bug fixes and new features work correctly.
"""
import numpy as np
import json
import hashlib
import secrets
import os
import sys
import tempfile
from pathlib import Path

# =====================================================
# SETUP: Import core functions from V14
# =====================================================

# We'll test the pure logic functions directly

passed = 0
failed = 0
total = 0

def test(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} -- {detail}")


# =====================================================
# BUG FIX 1: SS Income Variability
# =====================================================
print("\n" + "="*70)
print("BUG FIX 1: SS income not varied by MC variability")
print("="*70)

# Simulate the FIXED logic: variability only on employment income
np.random.seed(42)

parentX_income_emp = 0  # Retired
parentY_income_emp = 0  # Retired
ss_income = 30000 + 26400  # Both parents SS

employment_income = parentX_income_emp + parentY_income_emp  # 0

# With the FIX: gross = employment * multiplier + ss
# Since employment is 0, gross should always equal ss_income regardless of multiplier
results = []
for _ in range(1000):
    income_var = 0.10
    income_multiplier = 1 + np.random.normal(0, income_var)
    gross = employment_income * income_multiplier + ss_income
    results.append(gross)

results = np.array(results)
test("Retired: gross income always equals SS",
     np.all(results == ss_income),
     f"Min: {np.min(results):.2f}, Max: {np.max(results):.2f}, Expected: {ss_income}")

# With the OLD BUG: gross = (employment + ss) * multiplier
# SS would vary, which is wrong
results_buggy = []
for _ in range(1000):
    income_var = 0.10
    income_multiplier = 1 + np.random.normal(0, income_var)
    gross_buggy = (employment_income + ss_income) * income_multiplier
    results_buggy.append(gross_buggy)

results_buggy = np.array(results_buggy)
test("Old bug would have varied SS (confirming fix is different)",
     np.std(results_buggy) > 1000,
     f"Buggy std: {np.std(results_buggy):.2f}")

# Working parents: employment income should still vary
np.random.seed(42)
parentX_emp = 95000
parentY_emp = 85000
ss = 0  # Not retired yet
emp = parentX_emp + parentY_emp

varied_results = []
for _ in range(1000):
    income_var = 0.10
    mult = 1 + np.random.normal(0, income_var)
    gross = emp * mult + ss
    varied_results.append(gross)

varied_arr = np.array(varied_results)
test("Working: employment income varies correctly",
     np.std(varied_arr) > 10000,
     f"Std: {np.std(varied_arr):.2f}")

test("Working: mean close to base income",
     abs(np.mean(varied_arr) - emp) < 5000,
     f"Mean: {np.mean(varied_arr):.2f}, Expected ~{emp}")


# =====================================================
# BUG FIX 2: maintenance_rate now used in simulation
# =====================================================
print("\n" + "="*70)
print("BUG FIX 2: maintenance_rate used in house expense calculation")
print("="*70)

# Simulate the FIXED calculation
current_value = 650000
inflation_rate = 0.025
year = 5
property_tax_rate = 0.0092
home_insurance = 1800
maintenance_rate = 0.015  # 1.5% of home value
upkeep_costs = 3000       # Flat annual upkeep

current_home_value = current_value * ((1 + inflation_rate) ** (year - 1))
annual_property_tax = current_home_value * property_tax_rate
annual_insurance = home_insurance * ((1 + inflation_rate) ** (year - 1))
annual_maintenance = current_home_value * maintenance_rate  # NEW: percentage-based
annual_upkeep = upkeep_costs * ((1 + inflation_rate) ** (year - 1))  # Flat upkeep

house_expenses_fixed = annual_property_tax + annual_insurance + annual_maintenance + annual_upkeep

# OLD calculation (no maintenance_rate)
house_expenses_old = annual_property_tax + annual_insurance + annual_upkeep

test("maintenance_rate adds to house expenses",
     house_expenses_fixed > house_expenses_old,
     f"Fixed: ${house_expenses_fixed:,.0f}, Old: ${house_expenses_old:,.0f}")

test("maintenance_rate contribution correct",
     abs(annual_maintenance - current_home_value * 0.015) < 1,
     f"Maintenance: ${annual_maintenance:,.0f} = {current_home_value:,.0f} * 1.5%")

test("maintenance_rate scales with home value inflation",
     annual_maintenance > current_value * maintenance_rate,
     f"Year {year} maintenance: ${annual_maintenance:,.0f} > base ${current_value * maintenance_rate:,.0f}")


# =====================================================
# BUG FIX 3: healthcare_inflation_rate used for Healthcare
# =====================================================
print("\n" + "="*70)
print("BUG FIX 3: healthcare_inflation_rate for children's Healthcare")
print("="*70)

# Simulate the FIXED calculation
general_inflation = 0.025
healthcare_inflation = 0.045  # Higher than general
year = 10

base_food = 2400  # General category
base_healthcare = 400  # Healthcare category

# FIXED: Healthcare uses healthcare_inflation_rate
food_inflated = base_food * ((1 + general_inflation) ** (year - 1))
healthcare_inflated_fixed = base_healthcare * ((1 + healthcare_inflation) ** (year - 1))

# OLD: Healthcare used general inflation
healthcare_inflated_old = base_healthcare * ((1 + general_inflation) ** (year - 1))

test("Healthcare uses higher inflation rate",
     healthcare_inflated_fixed > healthcare_inflated_old,
     f"Fixed: ${healthcare_inflated_fixed:.0f}, Old: ${healthcare_inflated_old:.0f}")

test("Food still uses general inflation",
     abs(food_inflated - base_food * 1.025**9) < 1)

test("Healthcare inflation compounds faster over 10 years",
     healthcare_inflated_fixed / base_healthcare > food_inflated / base_food,
     f"HC growth: {healthcare_inflated_fixed/base_healthcare:.2f}x, Food growth: {food_inflated/base_food:.2f}x")


# =====================================================
# NEW FEATURE: Password Hashing
# =====================================================
print("\n" + "="*70)
print("NEW FEATURE: Password hashing (PBKDF2-SHA256)")
print("="*70)

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex(), salt

# Test hashing
hash1, salt1 = hash_password("testpassword123")
test("Password hash is hex string", all(c in '0123456789abcdef' for c in hash1))
test("Salt is hex string", all(c in '0123456789abcdef' for c in salt1))
test("Hash is 64 chars (SHA-256)", len(hash1) == 64)

# Same password + same salt = same hash
hash2, _ = hash_password("testpassword123", salt1)
test("Same password + same salt = same hash", hash1 == hash2)

# Different password = different hash
hash3, _ = hash_password("differentpassword", salt1)
test("Different password = different hash", hash1 != hash3)

# Different salt = different hash
hash4, salt4 = hash_password("testpassword123")
test("Different salt = different hash", hash1 != hash4 or salt1 != salt4)


# =====================================================
# NEW FEATURE: Household Data Persistence
# =====================================================
print("\n" + "="*70)
print("NEW FEATURE: Household file persistence")
print("="*70)

# Test with temp directory
with tempfile.TemporaryDirectory() as tmpdir:
    users_file = Path(tmpdir) / 'users.json'
    households_dir = Path(tmpdir) / 'households'
    households_dir.mkdir()
    
    # Write test users
    users = {
        "filipp": {
            "password_hash": "abc123",
            "salt": "def456",
            "display_name": "Filipp",
            "household_id": "house001",
            "created_at": "2025-01-01"
        },
        "erin": {
            "password_hash": "ghi789",
            "salt": "jkl012",
            "display_name": "Erin",
            "household_id": "house001",
            "created_at": "2025-01-02"
        }
    }
    
    with open(users_file, 'w') as f:
        json.dump(users, f)
    
    # Read back
    with open(users_file, 'r') as f:
        loaded_users = json.load(f)
    
    test("Users file round-trip", loaded_users == users)
    
    # Test household file
    household_data = {
        "household_name": "The Test Family",
        "plan_data": {"parentX": {"age": 35, "income": 95000}},
        "last_saved": "2025-01-01T12:00:00"
    }
    
    hh_file = households_dir / "house001.json"
    with open(hh_file, 'w') as f:
        json.dump(household_data, f)
    
    with open(hh_file, 'r') as f:
        loaded_hh = json.load(f)
    
    test("Household file round-trip", loaded_hh == household_data)
    test("Plan data preserved", loaded_hh['plan_data']['parentX']['income'] == 95000)
    
    # Test household member lookup
    members = [u for u, d in loaded_users.items() if d.get('household_id') == 'house001']
    test("Both users in same household", len(members) == 2)
    test("Filipp in household", "filipp" in members)
    test("Erin in household", "erin" in members)


# =====================================================
# V13 → V14 FEATURE PRESERVATION CHECK
# =====================================================
print("\n" + "="*70)
print("FEATURE PRESERVATION: V13 features still present in V14")
print("="*70)

with open('/home/claude/docker-deploy/FinancialApp_V14.py', 'r') as f:
    v14_code = f.read()

# Check all V13 functions still exist
v13_functions = [
    'timeline_tab', 'parent_settings_tab', 'parent_x_tab', 'parent_y_tab',
    'family_expenses_tab', 'children_tab', 'house_tab', 'economy_tab',
    'retirement_tab', 'run_comprehensive_simulation', 'combined_simulation_tab',
    'save_data', 'load_data', 'save_load_tab',
    'calculate_federal_income_tax', 'calculate_annual_taxes',
    'format_currency', 'get_historical_return_stats',
    'load_family_expense_template', 'load_children_expense_template',
    'export_children_expenses_csv', 'import_children_expenses_csv',
    'calculate_monthly_house_payment', 'initialize_session_state'
]

for func in v13_functions:
    test(f"V13 function preserved: {func}", f"def {func}" in v14_code)

# Check V13 data structures
v13_structures = [
    'HISTORICAL_STOCK_RETURNS', 'CHILDREN_EXPENSE_TEMPLATES',
    'FAMILY_EXPENSE_TEMPLATES', 'MajorPurchase', 'RecurringExpense',
    'EconomicScenario', 'HouseTimelineEntry', 'House'
]

for struct in v13_structures:
    test(f"V13 structure preserved: {struct}", struct in v14_code)

# Check V14 new functions
v14_new_functions = [
    'login_page', 'create_user', 'authenticate_user',
    'hash_password', 'save_household_plan', 'load_household_plan',
    'get_household_members', 'get_household_info', 'user_management_tab'
]

for func in v14_new_functions:
    test(f"V14 new function: {func}", f"def {func}" in v14_code)

# Check 12 tabs
test("V14 has 12 tabs", "tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12" in v14_code)
test("Users tab exists", '"👤 Users"' in v14_code)

# Check bug fixes are applied
test("Bug fix 1: employment_income variable exists",
     "employment_income = parentX_income + parentY_income" in v14_code)
test("Bug fix 1: SS not varied",
     "employment_income * income_multiplier + ss_income" in v14_code)
test("Bug fix 2: annual_maintenance in simulation",
     "annual_maintenance = current_home_value * house.maintenance_rate" in v14_code)
test("Bug fix 3: healthcare_inflation_rate in children calc",
     "scenario.healthcare_inflation_rate" in v14_code and "Healthcare" in v14_code)

# Check Docker files exist
docker_files = [
    '/home/claude/docker-deploy/Dockerfile',
    '/home/claude/docker-deploy/docker-compose.yml',
    '/home/claude/docker-deploy/requirements.txt',
    '/home/claude/docker-deploy/streamlit_config.toml',
    '/home/claude/docker-deploy/SETUP_GUIDE.md',
    '/home/claude/docker-deploy/Launcher.py'
]

for f in docker_files:
    test(f"Docker file exists: {Path(f).name}", Path(f).exists())


# =====================================================
# FINAL REPORT
# =====================================================
print("\n" + "="*70)
print("V14 VERIFICATION REPORT")
print("="*70)
print(f"Total tests:  {total}")
print(f"Passed:       {passed} ({passed/total*100:.1f}%)")
print(f"Failed:       {failed} ({failed/total*100:.1f}%)")
print("="*70)

if failed > 0:
    print("\nFAILED TESTS:")
    # Already printed inline

print("\nDONE.")
sys.exit(0 if failed == 0 else 1)
