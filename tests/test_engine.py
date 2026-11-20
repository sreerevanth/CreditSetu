from pathlib import Path

import pytest

from creditsetu.models import Applicant
from creditsetu.profile import build_profile
from creditsetu.schemes import match_schemes, suggest_plan
from creditsetu.score import emi, plan_emi, readiness_score
from creditsetu.statement import read_statement

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_statement_sunita.csv"


def sunita(**overrides) -> Applicant:
    base = dict(business_name="Sunita Tailoring Works", owner_name="Sunita", trade="tailor",
                sector="manufacturing", is_new_unit=False, loan_amount=300000, age=34,
                has_default=False, udyam_registered=False, prior_scheme_loan=False,
                gender="female", social_category="obc", area="urban")
    base.update(overrides)
    return Applicant(**base)


def by_name(results):
    return {r.name: r for r in results}


def test_reads_sample_statement():
    txns = read_statement(SAMPLE)
    assert len(txns) > 500
    assert {t.direction for t in txns} == {"CR", "DR"}


def test_reads_bank_style_export():
    csv = (b"Date,Narration,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
           b"01/04/2026,UPI-RAVI KUMAR-ravi@okaxis,,1200.00,5200.00\n"
           b"02/04/2026,ATM CASH WDL,2000.00,,3200.00\n"
           b"03/04/2026,ACH RETURN INSUFFICIENT FUNDS,500.00,,2700.00\n")
    txns = read_statement(csv)
    assert [t.direction for t in txns] == ["CR", "DR", "DR"]
    assert txns[0].mode == "UPI" and txns[1].mode == "ATM"
    assert build_profile(txns).bounced_count == 1


def test_profile_shape():
    p = build_profile(read_statement(SAMPLE))
    assert p.months == 14
    assert p.avg_monthly_surplus > 0
    assert "July" in p.low_months or "August" in p.low_months
    assert 0 < p.digital_share <= 1


def test_sunita_scheme_results():
    results = by_name(match_schemes(sunita()))
    assert results["MUDRA Kishore"].status == "eligible"
    assert results["Stand-Up India"].status == "not_fit"            # existing unit, below ₹10 lakh
    assert results["PMEGP – new unit subsidy"].status == "not_fit"  # existing unit
    assert results["PM Vishwakarma – first loan"].status == "needs_info"  # training unknown
    assert results["PM Vishwakarma – first loan"].covers_amount == 100000


def test_every_criterion_has_a_source():
    for r in match_schemes(sunita()):
        for c in r.criteria:
            assert c.source_url.startswith("https://"), (r.name, c.text)


def test_unknown_facts_give_needs_info_not_a_guess():
    r = by_name(match_schemes(sunita(has_default=None)))["MUDRA Kishore"]
    assert r.status == "needs_info"


def test_only_one_mudra_category_shown():
    names = [r.name for r in match_schemes(sunita())]
    assert sum(n.startswith("MUDRA") for n in names) == 1


def test_stand_up_india_for_new_women_led_unit():
    r = by_name(match_schemes(sunita(is_new_unit=True, loan_amount=1500000)))["Stand-Up India"]
    assert r.status == "eligible"


def test_plan_uses_cheapest_first_and_repicks_mudra_category():
    a = sunita(vishwakarma_trained=True)
    plan = suggest_plan(a, match_schemes(a))
    assert plan[0]["name"].startswith("PM Vishwakarma") and plan[0]["amount"] == 100000
    assert plan[1]["name"] == "MUDRA Kishore" and plan[1]["amount"] == 200000
    a2 = sunita(loan_amount=130000, vishwakarma_trained=True)
    plan2 = suggest_plan(a2, match_schemes(a2))
    assert plan2[1]["name"] == "MUDRA Shishu" and plan2[1]["amount"] == 30000


def test_emi_matches_formula():
    assert emi(100000, 12, 12) == pytest.approx(8884.88, abs=0.01)
    assert emi(0, 10, 12) == 0


def test_score_is_explained_and_bounded():
    p = build_profile(read_statement(SAMPLE))
    a = sunita()
    s = readiness_score(p, udyam_registered=False, has_default=False,
                        monthly_emi=plan_emi(suggest_plan(a, match_schemes(a))))
    assert 0 <= s.total <= 100
    assert sum(f.max_points for f in s.factors) == 100
    assert all(f.measured for f in s.factors)
    assert s.calibrated is False
    reg = readiness_score(p, udyam_registered=True, has_default=False, monthly_emi=s.emi)
    assert reg.total == s.total + 10  # registering on Udyam is a concrete, visible fix
