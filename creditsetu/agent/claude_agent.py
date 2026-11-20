"""Setu powered by Claude (optional).

Same case state and the same deterministic tools as the offline agent. Claude handles
the conversation (any phrasing, any mix of Hindi and English) and decides which tool to
call next, but it can only *report* what the tools return:

- eligibility comes from the rule engine, with sources
- the score comes from the score function, which can't see protected attributes
- submission is not a tool: only the owner's "Approve" button can submit

If the API call fails for any reason, the message is handled by the offline agent so the
demo never breaks.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from ..case import analyze, build_package
from ..models import Applicant
from ..schemes import load_rules
from ..statement import read_statement
from .offline import CaseState, OfflineAgent

DEFAULT_MODEL = "claude-sonnet-5-5"
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample_statement_sunita.csv"

FACT_FIELDS = {
    "owner_name": {"type": "string"}, "business_name": {"type": "string"},
    "trade": {"type": "string", "description": "e.g. tailor, barber, carpenter, mason, cobbler, potter, dairy, kirana, fabrication, repair_shop, food_stall, beauty_parlour, other"},
    "sector": {"type": "string", "enum": ["manufacturing", "trading", "services", "allied_agriculture"]},
    "is_new_unit": {"type": "boolean"}, "years_in_business": {"type": "number"},
    "loan_amount": {"type": "integer", "description": "Rupees"}, "loan_purpose": {"type": "string"},
    "age": {"type": "integer"}, "has_default": {"type": "boolean"}, "udyam_registered": {"type": "boolean"},
    "vishwakarma_trained": {"type": "boolean"}, "prior_scheme_loan": {"type": "boolean"},
    "prior_tarun_repaid": {"type": "boolean"},
    "gender": {"type": "string", "enum": ["female", "male", "other"],
               "description": "Only if the owner volunteers it; used only for schemes reserved by law"},
    "social_category": {"type": "string", "enum": ["general", "obc", "sc", "st"],
                        "description": "Only if the owner volunteers it; used only for schemes reserved by law"},
    "area": {"type": "string", "enum": ["urban", "rural"]},
    "district": {"type": "string"}, "state": {"type": "string"},
}

TOOLS = [
    {"name": "update_facts", "description": "Record facts the owner has told you about their business or loan need.",
     "input_schema": {"type": "object", "properties": FACT_FIELDS}},
    {"name": "use_sample_statement", "description": "Load the synthetic sample bank statement when the owner asks to use it.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "analyze_case", "description": "Run the cash-flow profile, scheme rule engine and readiness score. Needs trade, loan_amount, is_new_unit and a statement. Shows result cards to the owner.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "explain_scheme", "description": "Get the official rules, benefits and sources for one scheme.",
     "input_schema": {"type": "object", "properties": {"scheme_id": {"type": "string", "enum": [
         "pm_vishwakarma_t1", "pmmy_shishu", "pmmy_kishore", "pmmy_tarun", "pmmy_tarun_plus", "pmegp",
         "stand_up_india", "cgfmu", "cgtmse"]}}, "required": ["scheme_id"]}},
    {"name": "prepare_application", "description": "Draft the loan application and document checklist for the owner to review. Needs owner_name and business_name.",
     "input_schema": {"type": "object", "properties": {}}},
]


def system_prompt(lang: str) -> str:
    language = "Hindi in Devanagari script (simple, everyday words)" if lang == "hi" else "simple English"
    return f"""You are Setu, CreditSetu's assistant for small business owners in India (tailors, dairy farmers, kirana shops, repair shops and similar).
Your job: understand their business, read their statement through tools, find the loans and government schemes they qualify for, explain an honest readiness score, and prepare an application they approve.

Reply in {language}. Short messages, one question at a time, warm and respectful. Use ₹ and Indian digit grouping (₹3,00,000).

Hard rules:
1. Never decide or guess eligibility yourself. Only report what analyze_case or explain_scheme returns, and include the source link for any eligibility claim.
2. If a tool says a fact is unknown ("needs info"), ask the owner for it instead of assuming.
3. Gender, caste category and area are used ONLY for schemes that the law reserves for certain groups (Stand-Up India, PMEGP subsidy rates). Never ask for them unless a reserved scheme is relevant, and say they never affect the score.
4. You cannot submit anything. When the application is ready, tell the owner to review it and press the "Approve and send to bank" button.
5. Don't give financial advice beyond the tool results; the bank sets the final rate.

Gather, in order: what work they do, amount needed, whether the business is new or running, their bank/UPI statement (they upload it in the app, or you can use_sample_statement if they ask), Udyam registration, any loan default. For listed artisan trades also ask about PM Vishwakarma basic training and recent PMEGP/SVANidhi/MUDRA loans. Then call analyze_case. The app shows result cards; you summarise them in two or three sentences and suggest next steps."""


class ClaudeAgent:
    def __init__(self, state: CaseState, client=None, model: Optional[str] = None):
        self.s = state
        self.offline = OfflineAgent(state)
        self.model = model or os.environ.get("CREDITSETU_MODEL", DEFAULT_MODEL)
        self._client = client
        if not hasattr(self.s, "claude_messages"):
            self.s.claude_messages = []

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    # -------------------------------------------------------------- tools
    def _tool(self, name: str, args: dict) -> tuple[str, list[dict]]:
        cards: list[dict] = []
        s = self.s
        if name == "update_facts":
            for k, v in args.items():
                if k in FACT_FIELDS and v is not None:
                    setattr(s.applicant, k, v)
            s.analysis = None
            return json.dumps({"ok": True, "facts": {k: v for k, v in asdict(s.applicant).items() if v not in (None, "")}},
                              ensure_ascii=False), cards
        if name == "use_sample_statement":
            s.txns = read_statement(SAMPLE)
            s.statement_name = "sample statement"
            s.have_docs.add("bank_statement")
            return json.dumps({"ok": True, "transactions": len(s.txns)}), cards
        if name == "analyze_case":
            missing = [k for k in ("trade", "loan_amount", "is_new_unit") if getattr(s.applicant, k) in (None, "")]
            if s.txns is None:
                missing.append("statement")
            if missing:
                return json.dumps({"ok": False, "missing": missing}), cards
            s.analysis = analyze(s.applicant, s.txns, s.lang)
            s.stage = "analyzed"
            a = s.analysis
            cards = [{"kind": "profile", "text": "", "quick": []}, {"kind": "schemes", "text": "", "quick": []},
                     {"kind": "score", "text": "", "quick": []}]
            payload = {
                "profile": {k: v for k, v in asdict(a.profile).items() if k != "monthly"},
                "schemes": [{"id": r.scheme_id, "name": r.name, "status": r.status, "covers": r.covers_amount,
                             "criteria": [{"text": c.text, "status": c.status, "source": c.source_url} for c in r.criteria],
                             "note": r.status_note} for r in a.results],
                "plan": a.plan,
                "score": {"total": a.score.total, "band": a.score.band, "emi": a.score.emi,
                          "factors": [asdict(f) for f in a.score.factors], "calibrated": False},
            }
            return json.dumps(payload, ensure_ascii=False, default=str), cards
        if name == "explain_scheme":
            rule = next((r for r in load_rules()["schemes"] if r["id"] == args.get("scheme_id")), None)
            return json.dumps(rule or {"error": "unknown scheme"}, ensure_ascii=False), cards
        if name == "prepare_application":
            if s.analysis is None:
                return json.dumps({"ok": False, "error": "run analyze_case first"}), cards
            missing = [k for k in ("owner_name", "business_name") if not getattr(s.applicant, k)]
            if missing:
                return json.dumps({"ok": False, "missing": missing}), cards
            s.package = build_package(s.applicant, s.txns, s.have_docs)
            s.stage = "application"
            cards = [{"kind": "application", "text": "", "quick": []}]
            return json.dumps({"ok": True, "checklist": s.package.checklist}, ensure_ascii=False), cards
        return json.dumps({"error": f"unknown tool {name}"}), cards

    # -------------------------------------------------------------- loop
    def handle(self, text: str, max_turns: int = 6) -> list[dict]:
        msgs = self.s.claude_messages
        msgs.append({"role": "user", "content": text})
        replies: list[dict] = []
        try:
            for _ in range(max_turns):
                resp = self.client.messages.create(model=self.model, max_tokens=1200, system=system_prompt(self.s.lang),
                                                   tools=TOOLS, messages=msgs)
                content = []
                for block in resp.content:
                    if block.type == "text":
                        content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                msgs.append({"role": "assistant", "content": content})
                if resp.stop_reason != "tool_use":
                    final = "\n\n".join(c["text"] for c in content if c["type"] == "text").strip()
                    if final:
                        replies.append({"kind": "text", "text": final, "quick": []})
                    break
                results = []
                for c in content:
                    if c["type"] == "tool_use":
                        out, cards = self._tool(c["name"], c["input"] or {})
                        replies.extend(cards)
                        results.append({"type": "tool_result", "tool_use_id": c["id"], "content": out})
                msgs.append({"role": "user", "content": results})
            return replies
        except Exception as exc:  # network/auth/quota: fall back so the demo never breaks
            msgs.pop() if msgs and msgs[-1].get("role") == "user" and msgs[-1].get("content") == text else None
            note = {"kind": "text", "quick": [],
                    "text": ("_(Claude is unavailable right now, so the offline agent answered.)_" if self.s.lang == "en"
                             else "_(Claude अभी उपलब्ध नहीं है, इसलिए ऑफ़लाइन एजेंट ने जवाब दिया।)_")}
            self.last_error = repr(exc)
            return [note] + self.offline.handle(text)
