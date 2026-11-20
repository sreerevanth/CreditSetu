"""The readiness score must not change with gender, caste category or region.

Two layers:
1. Structural: ``readiness_score`` has no parameter that could carry a protected attribute.
2. Behavioural: running the full pipeline for every combination of protected attributes,
   with the same business and statement, gives exactly the same score.
"""

import inspect
import itertools
from dataclasses import replace
from pathlib import Path

from creditsetu.models import Applicant
from creditsetu.profile import build_profile
from creditsetu.score import readiness_score
from creditsetu.statement import read_statement

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_statement_sunita.csv"
PROTECTED = {"gender", "social_category", "area", "district", "state", "religion", "caste", "region"}


def test_score_function_cannot_see_protected_attributes():
    params = set(inspect.signature(readiness_score).parameters)
    assert params.isdisjoint(PROTECTED), params & PROTECTED


def score_for(applicant: Applicant, profile) -> int:
    # Mirrors app.py: only cash-flow, registration and default status reach the score.
    return readiness_score(profile, udyam_registered=applicant.udyam_registered,
                           has_default=applicant.has_default, monthly_emi=12000).total


def test_score_identical_across_all_protected_combinations():
    profile = build_profile(read_statement(SAMPLE))
    base = Applicant(trade="tailor", sector="manufacturing", is_new_unit=False, loan_amount=300000,
                     age=34, has_default=False, udyam_registered=False)
    scores = set()
    for gender, category, area, state in itertools.product(
            ["female", "male", "other", None], ["general", "obc", "sc", "st", None],
            ["urban", "rural", None], ["Rajasthan", "Kerala", "Assam", ""]):
        variant = replace(base, gender=gender, social_category=category, area=area, state=state)
        scores.add(score_for(variant, profile))
    assert len(scores) == 1, scores
