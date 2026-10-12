"""Engine results checked against published figures (2026-10-12 validation). If one of these fails after a data
refresh, update the benchmark together with its source, don't loosen the tolerance."""
import numpy as np
import pytest

from finplan import taxes as TX
from finplan.plan import normalize_plan
from finplan.engine import project, rmd_divisor, rmd_age, _hist
from finplan.mortgage import monthly_payment


def _tax(w1, w2, loc, year=2026):
    return TX.total_taxes(np.array([float(w1)]), np.array([float(w2)]), np.array([0.0]), np.array([0.0]), 0.0, year, 0.03, loc)


@pytest.mark.parametrize('wages,expected', [(100_000, 7_640), (200_000, 26_340), (400_000, 73_468)])
def test_federal_tax_2026_mfj(wages, expected):
    # IRS Rev. Proc. 2025-32: std deduction $32,200; 10/12/22/24% to 24,800/100,800/211,400/403,550
    assert float(_tax(wages, 0, 'Texas')['federal'][0]) == pytest.approx(expected, abs=1)


def test_fica_2026_with_joint_additional_medicare():
    # SSA 2026 wage base $184,500; 0.9% on couple's combined wages above $250,000
    assert float(_tax(200_000, 0, 'Texas')['fica'][0]) == pytest.approx(184_500 * .062 + 200_000 * .0145, abs=1)
    assert float(_tax(200_000, 200_000, 'Texas')['fica'][0]) == pytest.approx(30_028, abs=1)


def test_state_income_tax_brackets():
    # CA FTB 2025 MFJ schedule, std deduction $11,080, 2 x $149 exemption credits
    assert float(_tax(200_000, 0, 'California')['state'][0]) == pytest.approx(10_349.5, abs=2)
    assert float(_tax(200_000, 0, 'San Francisco')['state'][0]) == pytest.approx(10_349.5, abs=2)
    # OR 2025 MFJ: 4.75/6.75/8.75% to 8,800/22,100/250,000, std $5,600, $500 credit
    assert float(_tax(150_000, 0, 'Oregon')['state'][0]) == pytest.approx(11_517, abs=2)
    assert float(_tax(200_000, 0, 'Washington')['state'][0]) == 0
    # flat states: Colorado 4.4% after a deduction
    assert 5_000 < float(_tax(150_000, 0, 'Colorado')['state'][0]) < 5_400


def test_mortgage_rmd_and_social_security_rules():
    assert monthly_payment(800_000, 0.065, 30) == pytest.approx(5_056.54, abs=0.01)
    assert [rmd_divisor(a) for a in (73, 75, 80, 90)] == [26.5, 24.6, 20.2, 12.2]
    assert (rmd_age(1955), rmd_age(1962)) == (73, 75)
    for claim, factor in ((62, 0.70), (67, 1.00), (70, 1.24)):
        p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 60, 'parentX_retirement_age': 60,
                            'parentX_ss_benefit': 2000, 'parentX_ss_claim_age': claim, 'ss_insolvency_enabled': False,
                            'parentX_career_phases': [], 'parentX_income': 0, 'parentX_net_worth': 5e6, 'ss_cola': False})
        r = next(r for r in project(p)['rows'] if r['age1'] == 71)
        assert r['ss1'] / 24000 == pytest.approx(factor, abs=0.005)
    d = normalize_plan({})
    assert (d['ss_insolvency_year'], d['ss_shortfall_percentage']) == (2034, 17.0)   # 2026 Trustees: 83% payable


def test_compound_growth_and_single_person_ignores_partner_savings():
    p = normalize_plan({'parent1_name': 'A', 'parent2_name': 'N/A', 'parentX_age': 40, 'parentX_retirement_age': 99,
                        'parentX_death_age': 70, 'parentX_net_worth': 100_000, 'parentX_income': 0, 'parentX_career_phases': [],
                        'parentX_expenses': {}, 'family_shared_expenses': {}, 'auto_health_coverage': False,
                        'parentX_ss_benefit': 0, 'capital_gains_enabled': False, 'parentY_net_worth': 40_000,
                        'medicare_part_b_premium': 0, 'medicare_part_d_premium': 0, 'medigap_premium': 0,
                        'economic_params': {'investment_return': 0.06, 'inflation_rate': 0.03}})
    pr = project(p)
    assert pr['rows'][29]['investable'] == pytest.approx(100_000 * 1.06 ** 30, rel=1e-6)
    assert pr['summary']['investable_now'] == 100_000


def test_historical_sp500_statistics():
    H = np.array(_hist())
    assert H.mean() == pytest.approx(0.118, abs=0.006)                       # Damodaran 1928-2024 arithmetic 11.79%
    assert np.prod(1 + H) ** (1 / len(H)) - 1 == pytest.approx(0.099, abs=0.005)   # geometric 9.94%
