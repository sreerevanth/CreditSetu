"""Deterministic scheme-eligibility engine with a citation on every criterion.

Rules live in ``data/schemes.json``. Each criterion is checked against the
applicant's facts and returns pass / fail / unknown. A scheme is:

- ``not_fit``    if any applicable criterion fails
- ``needs_info`` if none fail but at least one depends on a fact we don't have
- ``eligible``   if every applicable criterion passes

The LLM never decides eligibility; it can only rephrase these results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import Applicant, CriterionResult, SchemeResult

DEFAULT_RULES = Path(__file__).resolve().parent.parent / "data" / "schemes.json"

UNKNOWN = "unknown"


def load_rules(path: Optional[Path] = None) -> dict:
    with open(path or DEFAULT_RULES, encoding="utf-8") as f:
        return json.load(f)


def _check(check: dict, facts: dict):
    """Return True, False, or UNKNOWN for a single check (or an ``any`` group)."""
    if "any" in check:
        results = [_check(c, facts) for c in check["any"]]
        if any(r is True for r in results):
            return True
        if any(r == UNKNOWN for r in results):
            return UNKNOWN
        return False

    value = facts.get(check["field"])
    if value is None or value == "":
        return UNKNOWN
    op, target = check["op"], check["value"]
    if op == "eq":
        return value == target
    if op == "in":
        return value in target
    if op == "gte":
        return value >= target
    if op == "lte":
        return value <= target
    if op == "between":
        low, high = target
        return low <= value <= high
    raise ValueError(f"Unknown operator: {op}")


def evaluate_scheme(rule: dict, applicant: Applicant) -> SchemeResult:
    facts = applicant.as_facts()
    sources = rule.get("sources", [])
    results: list[CriterionResult] = []

    for crit in rule["criteria"]:
        if "when" in crit and _check(crit["when"], facts) is not True:
            continue  # criterion doesn't apply to this applicant
        outcome = _check(crit["check"], facts)
        status = "pass" if outcome is True else ("unknown" if outcome == UNKNOWN else "fail")
        src = sources[crit.get("source", 0)] if sources else {"title": "", "url": ""}
        results.append(CriterionResult(text=crit["text"], status=status,
                                       source_title=src["title"], source_url=src["url"],
                                       fix=crit.get("fix", "")))

    if any(r.status == "fail" for r in results):
        overall = "not_fit"
    elif any(r.status == "unknown" for r in results):
        overall = "needs_info"
    else:
        overall = "eligible"

    covers = None
    if rule["kind"] == "loan" and applicant.loan_amount and rule.get("max_amount"):
        covers = min(applicant.loan_amount, rule["max_amount"])

    return SchemeResult(
        scheme_id=rule["id"], scheme=rule["scheme"], name=rule["name"], kind=rule["kind"],
        status=overall, summary=rule["summary"], benefit=rule["benefit"],
        apply_via=rule.get("apply_via", ""), criteria=results, covers_amount=covers,
        indicative_rate=rule.get("indicative_rate"), tenure_months=rule.get("tenure_months"),
        status_note=rule.get("status_note", ""),
    )


STATUS_ORDER = {"eligible": 0, "needs_info": 1, "not_fit": 2}


def match_schemes(applicant: Applicant, rules: Optional[dict] = None) -> list[SchemeResult]:
    """Evaluate every scheme. Loans first (cheapest indicative rate first), then guarantees.

    MUDRA categories that don't match the loan amount are dropped from the list
    instead of shown as "not a fit", so the owner sees one MUDRA answer.
    """
    rules = rules or load_rules()
    results = [evaluate_scheme(r, applicant) for r in rules["schemes"]]

    mudra = [r for r in results if r.scheme == "PM MUDRA Yojana"]
    keep_mudra = [r for r in mudra if r.status != "not_fit"] or mudra[:1]
    results = [r for r in results if r.scheme != "PM MUDRA Yojana"] + keep_mudra

    def key(r: SchemeResult):
        return (STATUS_ORDER[r.status], r.kind != "loan", r.indicative_rate or 99)

    return sorted(results, key=key)


def suggest_plan(applicant: Applicant, results: list[SchemeResult]) -> list[dict]:
    """Greedy plan: fill the loan need from the cheapest eligible / likely-eligible loans first.

    Returns [{"name", "amount", "rate", "tenure_months", "status"}]. The owner decides.
    """
    need = applicant.loan_amount or 0
    plan = []
    candidates = [r for r in results if r.kind == "loan" and r.status in ("eligible", "needs_info")]
    candidates.sort(key=lambda r: (r.indicative_rate or 99, STATUS_ORDER[r.status]))
    used_schemes = set()
    for r in candidates:
        if need <= 0:
            break
        if r.scheme in used_schemes:
            continue
        amount = min(need, r.covers_amount or need)
        plan.append({"name": r.name, "amount": amount, "rate": r.indicative_rate,
                     "tenure_months": r.tenure_months, "status": r.status})
        used_schemes.add(r.scheme)
        need -= amount

    # A MUDRA category is chosen by the original amount; if part of the need is
    # covered elsewhere, re-pick the MUDRA category that fits the remainder.
    rules = load_rules()
    for item in plan:
        if item["name"].startswith("MUDRA"):
            for rule in rules["schemes"]:
                if rule["scheme"] != "PM MUDRA Yojana":
                    continue
                amt_rule = next(c for c in rule["criteria"] if c["id"] == "amount")["check"]["value"]
                if amt_rule[0] <= item["amount"] <= amt_rule[1]:
                    item["name"] = rule["name"]
                    item["tenure_months"] = rule.get("tenure_months")
                    break
    return plan
