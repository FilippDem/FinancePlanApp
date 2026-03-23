"""Test merged v0.8 + auth features"""
import sys, json, os
sys.path.insert(0, "/app")
from FinancialPlanner_v0_8 import *

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

print("=== TEST 1: Auth System ===")
ensure_data_dirs()
success, msg = create_user("testuser", "testpass123", "Test User", household_name="Test Family")
# May already exist from prior run, that's ok
success_auth, result = authenticate_user("testuser", "testpass123")
check("Authentication works", success_auth)
check("Returns user data", "household_id" in result)
success_bad, _ = authenticate_user("testuser", "wrongpass")
check("Bad password rejected", not success_bad)

print("\n=== TEST 2: Household Persistence ===")
hid = result["household_id"]
save_household_plan(hid, json.dumps({"test": "data", "value": 42}))
loaded = load_household_plan(hid)
data = json.loads(loaded)
check("Household plan roundtrip", data.get("value") == 42)

members = get_household_members(hid)
check("Household has members", len(members) > 0)

info = get_household_info(hid)
check("Household info has last_saved", "last_saved" in info)

print("\n=== TEST 3: Scenario Persistence ===")
scenarios = {"Base": json.dumps({"income": 100000}), "Optimistic": json.dumps({"income": 150000})}
save_household_scenarios(hid, scenarios)
loaded_s = load_household_scenarios(hid)
check("Scenarios saved", len(loaded_s) == 2)
check("Scenario names correct", "Base" in loaded_s and "Optimistic" in loaded_s)

print("\n=== TEST 4: Password Hashing ===")
h1, salt = hash_password("mypassword")
h2, _ = hash_password("mypassword", salt)
h3, _ = hash_password("different", salt)
check("Same password same hash", h1 == h2)
check("Different password different hash", h1 != h3)
check("Hash is 64 chars hex", len(h1) == 64)

print("\n=== TEST 5: Tax Calculations ===")
tax = calculate_federal_income_tax(180000, "married")
check(f"Federal tax on 180k married: ${tax:,.0f}", 25000 < tax < 35000)
tax_single = calculate_federal_income_tax(180000, "single")
check("Single pays more than married", tax_single > tax)
tax_zero = calculate_federal_income_tax(0, "married")
check("Zero income zero tax", tax_zero == 0)

print("\n=== TEST 6: Mortgage Calculations ===")
h30 = House(name="Test30", purchase_year=2025, purchase_price=500000, current_value=500000,
            mortgage_balance=400000, mortgage_rate=0.065, mortgage_years_left=30,
            property_tax_rate=1.2, home_insurance=2000, maintenance_rate=1.0,
            upkeep_costs=0, owner="Shared", timeline=[])
monthly = calculate_monthly_house_payment(h30)
check(f"Mortgage payment > 0: ${monthly:,.0f}", monthly > 0)
h15 = House(name="Test15", purchase_year=2025, purchase_price=500000, current_value=500000,
            mortgage_balance=400000, mortgage_rate=0.065, mortgage_years_left=15,
            property_tax_rate=1.2, home_insurance=2000, maintenance_rate=1.0,
            upkeep_costs=0, owner="Shared", timeline=[])
monthly_15 = calculate_monthly_house_payment(h15)
check("15yr payment > 30yr payment", monthly_15 > monthly)

print("\n=== TEST 7: Historical Data ===")
check("100 years of returns", len(HISTORICAL_STOCK_RETURNS) == 100)
stats = get_historical_return_stats()
check(f"Mean return {stats['mean']:.1%} in range", 0.07 < stats["mean"] < 0.14)
check(f"Std dev {stats['std']:.1%} in range", 0.15 < stats["std"] < 0.25)

print("\n=== TEST 8: Dataclasses ===")
h = House(name="Test", purchase_year=2025, purchase_price=500000, current_value=500000,
          mortgage_balance=400000, mortgage_rate=0.065, mortgage_years_left=30,
          property_tax_rate=1.2, home_insurance=2000, maintenance_rate=1.0,
          upkeep_costs=0, owner="Shared", timeline=[])
check("House dataclass works", h.purchase_price == 500000)

mp = MajorPurchase(name="Car", amount=50000, year=2025)
check("MajorPurchase works", mp.amount == 50000)

re_exp = RecurringExpense(name="Insurance", category="Insurance", amount=5000, frequency_years=1, start_year=2025)
check("RecurringExpense works", re_exp.amount == 5000)

ep = EconomicParameters(investment_return=0.07, inflation_rate=0.03, expense_growth_rate=0.03, healthcare_inflation_rate=0.05)
check("EconomicParameters works", ep.investment_return == 0.07)

print("\n=== TEST 9: Feature Presence ===")
import inspect
source = inspect.getsource(sys.modules["FinancialPlanner_v0_8"])
check("login_page exists", "def login_page" in source)
check("user_management_tab exists", "def user_management_tab" in source)
check("save_data exists", "def save_data" in source)
check("load_data exists", "def load_data" in source)
check("save_household_plan exists", "def save_household_plan" in source)
check("save_household_scenarios exists", "def save_household_scenarios" in source)
check("monte_carlo_simulation_tab exists", "def monte_carlo_simulation_tab" in source)
check("deterministic_cashflow_tab exists", "def deterministic_cashflow_tab" in source)
check("stress_test_tab exists", "def stress_test_tab" in source)
check("report_export_tab exists", "def report_export_tab" in source)
check("healthcare_insurance_tab exists", "def healthcare_insurance_tab" in source)
check("Users tab in main", "user_management_tab" in source)

# Cleanup
users = load_users()
if "testuser" in users:
    del users["testuser"]
    save_users(users)
from pathlib import Path
hfile = Path(os.environ.get("DATA_DIR", "./data")) / "households" / (hid + ".json")
if hfile.exists():
    hfile.unlink()

print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed}")
print(f"{'='*50}")
if failed > 0:
    sys.exit(1)
