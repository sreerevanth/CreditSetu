"""Draft a loan file for the owner to review. CreditSetu never submits on its own."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date

from .models import Applicant, CashFlowProfile, ReadinessScore, SchemeResult
from .score import _inr

# Documents lenders typically ask for on a micro loan. "auto" items are produced by CreditSetu.
BASE_DOCUMENTS = [
    ("aadhaar", "Aadhaar card (identity and address)"),
    ("pan", "PAN card"),
    ("bank_statement", "Bank statement for the last 6–12 months"),
    ("business_proof", "Proof of business address (rent agreement or utility bill)"),
    ("photo", "Recent passport-size photograph"),
    ("udyam", "Udyam registration certificate (or Udyam Assist certificate)"),
    ("quotation", "Quotation for machines or stock to be bought"),
]
AUTO_DOCUMENTS = [
    ("cashflow_summary", "Cash-flow summary from your statement (made by CreditSetu)"),
    ("project_report", "Short project report (draft made by CreditSetu)"),
]


def document_checklist(applicant: Applicant, have: set[str], plan: list[dict]) -> list[dict]:
    items = []
    for key, label in BASE_DOCUMENTS:
        if key == "udyam" and applicant.udyam_registered:
            have = have | {"udyam"}
        items.append({"key": key, "label": label, "status": "have" if key in have else "missing"})
    if any("Vishwakarma" in p["name"] for p in plan):
        items.append({"key": "vishwakarma_cert",
                      "label": "PM Vishwakarma certificate and basic-training completion",
                      "status": "have" if applicant.vishwakarma_trained else "missing"})
    for key, label in AUTO_DOCUMENTS:
        items.append({"key": key, "label": label, "status": "ready"})
    return items


def draft_application(applicant: Applicant, profile: CashFlowProfile, score: ReadinessScore,
                      plan: list[dict], results: list[SchemeResult], checklist: list[dict]) -> str:
    """Markdown loan file: business summary, request, scheme fit with sources, cash flow, documents."""
    a = applicant
    today = date.today().strftime("%d %B %Y")
    lines = [
        f"# Loan application draft – {a.business_name or 'My business'}",
        "",
        f"*Prepared with CreditSetu on {today}. Draft for the owner to review. Not submitted.*",
        "",
        "## 1. Applicant and business",
        f"- **Owner:** {a.owner_name or '[name]'}",
        f"- **Business:** {a.business_name or '[business name]'} ({(a.trade or '').replace('_', ' ')}, {a.sector or '[sector]'})",
        f"- **Location:** {', '.join(x for x in [a.district, a.state] if x) or '[district, state]'}",
        f"- **In business for:** {a.years_in_business or '[ ]'} years · {'new unit' if a.is_new_unit else 'existing unit'}",
        f"- **Udyam registration:** {'Yes' if a.udyam_registered else 'Not yet'}",
        "",
        "## 2. Loan request",
        f"- **Amount needed:** {_inr(a.loan_amount or 0)}",
        f"- **Purpose:** {a.loan_purpose or '[purpose]'}",
        "",
        "**Suggested financing plan** (the owner decides):",
        "",
        "| Scheme | Amount | Indicative rate | Tenure |",
        "|---|---|---|---|",
    ]
    for p in plan:
        lines.append(f"| {p['name']} | {_inr(p['amount'])} | ~{p['rate']:g}% a year | {p['tenure_months']} months |")
    lines += [
        "",
        f"Estimated total EMI: **{_inr(score.emi)} a month** (indicative; the lender sets the final rate).",
        "",
        "## 3. Why these schemes (with sources)",
    ]
    for r in results:
        if r.status == "not_fit":
            continue
        tag = "Eligible" if r.status == "eligible" else "Likely eligible – needs confirmation"
        lines.append(f"### {r.name} – {tag}")
        for c in r.criteria:
            mark = {"pass": "✔", "fail": "✘", "unknown": "?"}[c.status]
            lines.append(f"- {mark} {c.text} — [{c.source_title}]({c.source_url})")
        if r.status_note:
            lines.append(f"- Note: {r.status_note}")
        lines.append("")
    lines += [
        "## 4. Cash-flow summary (from bank statement)",
        f"- **Period:** {profile.start} to {profile.end} ({profile.months} months)",
        f"- **Average monthly income:** {_inr(profile.avg_monthly_inflow)}",
        f"- **Average monthly spending:** {_inr(profile.avg_monthly_outflow)}",
        f"- **Average monthly surplus:** {_inr(profile.avg_monthly_surplus)}",
        f"- **Busiest months:** {', '.join(profile.peak_months)} · **Slowest:** {', '.join(profile.low_months)}",
        f"- **Customers paying each month:** about {round(profile.avg_payers_per_month)}",
        f"- **Share of income received digitally:** {round(profile.digital_share * 100)}%",
        f"- **Bounced or returned payments:** {profile.bounced_count}",
        "",
        f"**Loan-readiness score:** {score.total}/100 ({score.band}). Factors:",
        "",
    ]
    for f in score.factors:
        lines.append(f"- {f.name}: {f.points:g}/{f.max_points:g} – {f.measured}")
    lines += [
        "",
        "*The score uses only cash-flow, registration and repayment information. It never uses gender, caste, religion or region. Weights are not yet calibrated on repayment data.*",
        "",
        "## 5. Documents",
    ]
    for item in checklist:
        mark = {"have": "✔ Have", "missing": "☐ Missing", "ready": "✔ Ready"}[item["status"]]
        lines.append(f"- {mark}: {item['label']}")
    lines += [
        "",
        "## 6. Owner's declaration",
        "I have reviewed this draft. The information is true to the best of my knowledge. "
        "I consented to CreditSetu reading my statement for this purpose only.",
        "",
        "Signature: ____________________    Date: ____________",
    ]
    return "\n".join(lines)


def loan_file_json(applicant: Applicant, profile: CashFlowProfile, score: ReadinessScore,
                   plan: list[dict], results: list[SchemeResult]) -> str:
    """Machine-readable loan file a lender's system could ingest."""
    payload = {
        "generated_by": "CreditSetu prototype",
        "generated_on": date.today().isoformat(),
        "applicant": {k: v for k, v in asdict(applicant).items()
                      if k not in {"gender", "social_category"}},  # shared only where a scheme needs it
        "cash_flow": asdict(profile),
        "readiness_score": asdict(score),
        "plan": plan,
        "scheme_results": [asdict(r) for r in results],
        "owner_approved": True,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)
