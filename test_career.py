"""Test career phases feature"""
import sys
sys.path.insert(0, "/app")
from FinancialPlanner_v0_8 import *

# Test CareerPhase dataclass
cp = CareerPhase(start_age=30, end_age=45, philosophy="Climbing the Ladder",
                 base_salary=150000, annual_raise_pct=5.0, annual_bonus_pct=15.0,
                 rsu_annual_grant=30000)
assert cp.base_salary == 150000, "CareerPhase creation failed"
print("[PASS] CareerPhase dataclass")

# Test year 0 income
r = get_career_income_for_year([cp], 30, 2026, 2026)
assert r["base_salary"] == 150000, f"Expected 150000, got {r['base_salary']}"
assert r["bonus"] == 22500, f"Expected 22500 bonus, got {r['bonus']}"
assert r["rsu_income"] == 0, "RSU should be 0 in year 0"
print(f"[PASS] Year 0: total=${r['total_employment_income']:,.0f}")

# Test year 5 with raises and RSU vesting
r5 = get_career_income_for_year([cp], 30, 2026, 2031)
expected_base = 150000 * (1.05 ** 5)
assert abs(r5["base_salary"] - expected_base) < 1, f"Base mismatch: {r5['base_salary']} vs {expected_base}"
assert r5["rsu_income"] == 30000, f"RSU should be 30000, got {r5['rsu_income']}"
print(f"[PASS] Year 5: base=${r5['base_salary']:,.0f}, rsu=${r5['rsu_income']:,.0f}")

# Test multi-phase career
phases = [
    CareerPhase(start_age=30, end_age=40, philosophy="Climbing the Ladder",
                base_salary=100000, annual_raise_pct=5.0, annual_bonus_pct=10.0),
    CareerPhase(start_age=40, end_age=55, philosophy="Startup",
                base_salary=80000, annual_raise_pct=2.0,
                stock_options_grant=500000, stock_options_growth_pct=20.0,
                stock_options_liquidity_year=2041)
]

# Phase 1 at age 39
r1 = get_career_income_for_year(phases, 30, 2026, 2035)
assert r1["base_salary"] > 100000, "Should have raises after 9 years"
print(f"[PASS] Phase 1 (age 39): ${r1['total_employment_income']:,.0f}")

# Phase 2 at age 40
r2 = get_career_income_for_year(phases, 30, 2026, 2036)
assert r2["base_salary"] == 80000, f"Phase 2 base should be 80000, got {r2['base_salary']}"
print(f"[PASS] Phase 2 (age 40): ${r2['total_employment_income']:,.0f}")

# IPO year at age 45
r_ipo = get_career_income_for_year(phases, 30, 2026, 2041)
assert r_ipo["options_income"] > 500000, "Options should have appreciated"
print(f"[PASS] IPO year: options=${r_ipo['options_income']:,.0f}, total=${r_ipo['total_employment_income']:,.0f}")

# Past last phase (age 56)
r_done = get_career_income_for_year(phases, 30, 2026, 2052)
assert r_done["total_employment_income"] == 0, "Should be 0 after last phase"
print(f"[PASS] Post-career: ${r_done['total_employment_income']:,.0f}")

# Test single phase (backward compat default)
simple = [CareerPhase(start_age=30, end_age=65, philosophy="Stable",
                      base_salary=75000, annual_raise_pct=3.0)]
r_simple = get_career_income_for_year(simple, 30, 2026, 2046)
expected = 75000 * (1.03 ** 20)
assert abs(r_simple["base_salary"] - expected) < 1
print(f"[PASS] Simple stable career year 20: ${r_simple['base_salary']:,.0f}")

print("\nALL 8 TESTS PASSED")
