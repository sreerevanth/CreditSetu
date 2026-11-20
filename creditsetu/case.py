"""One place that runs the whole engine for a case, so the chat agent, the guided flow
and the demo seeder all produce exactly the same results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .application import document_checklist, draft_application, loan_file_json
from .models import Applicant, CashFlowProfile, ReadinessScore
from .profile import build_profile
from .schemes import match_schemes, suggest_plan
from .score import plan_emi, readiness_score


@dataclass
class Analysis:
    profile: CashFlowProfile
    results: list
    plan: list
    score: ReadinessScore
    lang: str = "en"


def analyze(applicant: Applicant, txns: list, lang: str = "en") -> Analysis:
    profile = build_profile(txns)
    results = match_schemes(applicant, lang=lang)
    plan = suggest_plan(applicant, results, lang=lang)
    score = readiness_score(profile, udyam_registered=applicant.udyam_registered,
                            has_default=applicant.has_default,
                            monthly_emi=plan_emi(plan) if plan else 0.0, lang=lang)
    return Analysis(profile, results, plan, score, lang)


@dataclass
class LoanPackage:
    """Everything a lender receives. Always built in English (the bank's working language)."""
    draft_md: str
    file_json: str
    checklist: list
    analysis: Analysis
    applicant: Applicant
    have: set = field(default_factory=set)


def build_package(applicant: Applicant, txns: list, have: Optional[set] = None) -> LoanPackage:
    a = analyze(applicant, txns, "en")
    have = set(have or set())
    checklist = document_checklist(applicant, have, a.plan)
    draft = draft_application(applicant, a.profile, a.score, a.plan, a.results, checklist)
    file_json = loan_file_json(applicant, a.profile, a.score, a.plan, a.results)
    return LoanPackage(draft, file_json, checklist, a, applicant, have)


def submission_kwargs(pkg: LoanPackage) -> dict:
    ap, an = pkg.applicant, pkg.analysis
    return dict(business_name=ap.business_name, owner_name=ap.owner_name, trade=ap.trade or "",
                district=ap.district, state=ap.state, amount=int(ap.loan_amount or 0),
                score=an.score.total, band=an.score.band, plan=an.plan, file_json=pkg.file_json,
                draft_md=pkg.draft_md, documents=pkg.checklist)
