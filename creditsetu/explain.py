"""Plain-language summaries in English or Hindi.

Default: deterministic templates (no network, no data leaves the session).
Optional: if ANTHROPIC_API_KEY is set, the ``anthropic`` package is installed and the
owner opts in, Claude rephrases the SAME facts more naturally. It's told to add no
new facts and to keep every source link. Raw statements are never sent, only results.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict

from .models import ReadinessScore, SchemeResult
from .score import _inr

STATUS_WORDS = {
    "en": {"eligible": "you qualify", "needs_info": "you probably qualify (we need one or two answers)", "not_fit": "not a fit"},
    "hi": {"eligible": "आप पात्र हैं", "needs_info": "आप शायद पात्र हैं, एक-दो जानकारी चाहिए", "not_fit": "उपयुक्त नहीं"},
}


FACTOR_NAMES_HI = {
    "Income stability": "आय में स्थिरता",
    "Track record": "कारोबार का रिकॉर्ड",
    "Repayment capacity": "किस्त चुकाने की क्षमता",
    "Customer base": "ग्राहकों की संख्या",
    "Digital footprint": "डिजिटल लेन-देन",
    "Formal registration": "उद्यम पंजीकरण",
    "Clean record": "साफ़ रिकॉर्ड",
}


def template_summary(results: list[SchemeResult], plan: list[dict], score: ReadinessScore, lang: str = "en") -> str:
    words = STATUS_WORDS["hi" if lang == "hi" else "en"]
    good = [r for r in results if r.kind == "loan" and r.status != "not_fit"]
    if lang == "hi":
        lines = [f"आपका लोन-तैयारी स्कोर **{score.total}/100** है।"]
        if good:
            lines.append("योजनाएँ: " + ", ".join(f"**{r.name}** ({words[r.status]})" for r in good) + "।")
        if plan:
            lines.append("सुझाई गई योजना: " + " + ".join(f"{p['name']} {_inr(p['amount'])}" for p in plan)
                         + f"। अनुमानित मासिक किस्त (EMI) लगभग {_inr(score.emi)}।")
        fixes = sorted((f for f in score.factors if f.improve), key=lambda f: f.points - f.max_points)
        if fixes:
            lines.append("सबसे पहले सुधारें: " + FACTOR_NAMES_HI.get(fixes[0].name, fixes[0].name) + "।")
        lines.append("अंतिम फ़ैसला आपका है। कुछ भी आपकी मंज़ूरी के बिना जमा नहीं होगा।")
        return " ".join(lines)

    lines = [f"Your loan-readiness score is **{score.total}/100** ({score.band.lower()})."]
    if good:
        lines.append("Schemes: " + "; ".join(f"**{r.name}**: {words[r.status]}" for r in good) + ".")
    if plan:
        lines.append("Suggested plan: " + " + ".join(f"{p['name']} for {_inr(p['amount'])}" for p in plan)
                     + f", with an estimated EMI of about {_inr(score.emi)} a month.")
    fixes = sorted((f for f in score.factors if f.improve), key=lambda f: f.points - f.max_points)
    if fixes:
        lines.append(f"Biggest quick win: {fixes[0].improve}")
    lines.append("You decide. Nothing is submitted without your approval.")
    return " ".join(lines)


def llm_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def llm_summary(results: list[SchemeResult], plan: list[dict], score: ReadinessScore, lang: str = "en") -> str:
    """Rephrase results with Claude. Falls back to the template on any error."""
    if not llm_available():
        return template_summary(results, plan, score, lang)
    import anthropic

    facts = {
        "scheme_results": [asdict(r) for r in results],
        "plan": plan,
        "score": asdict(score),
    }
    language = "simple Hindi (Devanagari script)" if lang == "hi" else "simple English"
    prompt = (
        "You are CreditSetu, helping a small business owner in India understand their loan options.\n"
        f"Write a short, warm explanation in {language}, under 150 words, for someone who is not used to banking terms.\n"
        "Rules: use ONLY the facts in the JSON below. Do not add schemes, numbers or rules that are not there. "
        "Mention each scheme's result and keep its source link. End by saying the owner decides and nothing is submitted without approval.\n\n"
        + json.dumps(facts, ensure_ascii=False, default=str)
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get("CREDITSETU_MODEL", "claude-sonnet-5-5"),
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    except Exception:  # network, auth or quota problems: never break the demo
        return template_summary(results, plan, score, lang)
