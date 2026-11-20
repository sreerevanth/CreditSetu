"""Explainable loan-readiness score (0–100).

Fairness by construction: ``readiness_score`` only accepts cash-flow metrics,
registration status and a declared-default flag. It has no way to see gender,
caste category, religion or region. ``tests/test_fairness.py`` checks this.

The weights are judgement-based and NOT yet calibrated on repayment outcomes;
the result says so (``calibrated=False``).
"""

from __future__ import annotations

from typing import Optional

from .models import CashFlowProfile, ReadinessScore, ScoreFactor


def emi(principal: float, annual_rate_pct: float, months: int) -> float:
    """Equated monthly instalment for a reducing-balance loan."""
    if principal <= 0 or months <= 0:
        return 0.0
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / months
    growth = (1 + r) ** months
    return principal * r * growth / (growth - 1)


def _inr(x: float) -> str:
    """Indian digit grouping: 1234567 -> ₹12,34,567."""
    n = int(round(x))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups) + "," + tail
    return f"{sign}₹{s}"


def readiness_score(profile: CashFlowProfile, *, udyam_registered: Optional[bool],
                    has_default: Optional[bool], monthly_emi: float) -> ReadinessScore:
    factors: list[ScoreFactor] = []

    # 1. Income stability (25)
    cv = profile.inflow_cv
    if cv <= 0.20:
        pts = 25
    elif cv <= 0.35:
        pts = 18
    elif cv <= 0.50:
        pts = 10
    else:
        pts = 4
    factors.append(ScoreFactor(
        "Income stability", pts, 25,
        f"Monthly income varies by about {round(cv * 100)}% around its average "
        f"(busiest: {', '.join(profile.peak_months)}; slowest: {', '.join(profile.low_months)}).",
        "" if pts == 25 else "Steadier monthly income helps. Plan the loan's EMI dates after your busy months, and keep some savings for slow months."))

    # 2. Track record (15)
    m = profile.months
    pts = 15 if m >= 12 else 8 if m >= 6 else 3
    factors.append(ScoreFactor(
        "Track record", pts, 15, f"{m} months of statement history.",
        "" if pts == 15 else "Share a longer statement (12 months or more) if you have one."))

    # 3. Repayment capacity (25)
    surplus = profile.avg_monthly_surplus
    ratio = (monthly_emi / surplus) if surplus > 0 else None
    if ratio is None:
        pts = 0
        measured = "Money out is equal to or more than money in, so there's no surplus to pay an EMI from."
    else:
        pts = 25 if ratio <= 0.35 else 15 if ratio <= 0.50 else 8 if ratio <= 0.70 else 2
        measured = (f"The estimated EMI of {_inr(monthly_emi)} is {round(ratio * 100)}% of your average "
                    f"monthly surplus of {_inr(surplus)}.")
    factors.append(ScoreFactor(
        "Repayment capacity", pts, 25, measured,
        "" if pts == 25 else "A longer tenure, a smaller first loan, or a cheaper scheme (such as a 5% PM Vishwakarma loan) lowers the EMI."))

    # 4. Customer base (10)
    payers = profile.avg_payers_per_month
    pts = 10 if payers >= 25 else 6 if payers >= 10 else 2
    factors.append(ScoreFactor(
        "Customer base", pts, 10, f"About {round(payers)} different customers pay you each month.",
        "" if pts == 10 else "Income from many customers is seen as lower risk than income from a few."))

    # 5. Digital footprint (10)
    share = profile.digital_share
    pts = 10 if share >= 0.60 else 5 if share >= 0.30 else 1
    factors.append(ScoreFactor(
        "Digital footprint", pts, 10, f"{round(share * 100)}% of your income arrives by UPI or bank transfer.",
        "" if pts == 10 else "Ask customers to pay by UPI. Digital payments are proof of income a bank can see."))

    # 6. Formal registration (10)
    if udyam_registered:
        pts, measured, improve = 10, "Registered on Udyam / Udyam Assist.", ""
    else:
        pts = 0
        measured = "Not yet registered on Udyam." if udyam_registered is False else "Udyam registration not confirmed."
        improve = "Register on Udyam (free, online). If you don't have a PAN or GST, a designated agency can register you on the Udyam Assist Platform."
    factors.append(ScoreFactor("Formal registration", pts, 10, measured, improve))

    # 7. Clean record (5, can go negative for bounces)
    pts = 5 if has_default is False else 0
    pts -= 3 * profile.bounced_count
    pts = max(pts, -10)
    bits = []
    bits.append("No default declared." if has_default is False else
                "Declared an existing default." if has_default else "Default status not confirmed.")
    bits.append(f"{profile.bounced_count} bounced or returned payments in the statement.")
    factors.append(ScoreFactor(
        "Clean record", pts, 5, " ".join(bits),
        "" if pts == 5 else "Avoid bounced payments by keeping a small buffer before EMI or cheque dates."))

    total = int(max(0, min(100, round(sum(f.points for f in factors)))))
    band = "Strong" if total >= 75 else "Good, with a few fixes" if total >= 55 else "Needs work first"
    return ReadinessScore(total=total, band=band, factors=factors, emi=round(monthly_emi, 2),
                          emi_to_surplus=round(ratio, 3) if ratio is not None else None,
                          calibrated=False)


def plan_emi(plan: list[dict]) -> float:
    return sum(emi(p["amount"], p["rate"] or 10.0, p["tenure_months"] or 36) for p in plan)
