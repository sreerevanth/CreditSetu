"""Shared UI: styling, language strings, session state, and the result cards used by
both the chat and the guided flow."""

from __future__ import annotations

import os
import re

import pandas as pd
import streamlit as st

from creditsetu.agent.offline import CaseState
from creditsetu.case import analyze
from creditsetu.schemes import load_rules
from creditsetu.score import MONTHS_HI, _inr

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&family=Noto+Sans+Devanagari:wght@400;600&display=swap');
:root { --ink:#16233F; --ink2:#22335C; --paper:#F7F4EC; --paper2:#EDE6D6; --accent:#E8A33D; --deep:#8F5410;
        --good:#23694A; --bad:#A13A24; --muted:#4A5568; }
html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea { font-family: 'Inter', 'Noto Sans Devanagari', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', 'Noto Sans Devanagari', sans-serif !important; color: var(--ink); letter-spacing: -0.4px; }
.stApp { background: var(--paper); }
section[data-testid="stSidebar"] { background: var(--ink); }
section[data-testid="stSidebar"] * { color: #F7F4EC; }
section[data-testid="stSidebar"] .acc { color: var(--accent) !important; }
section[data-testid="stSidebar"] input { color: var(--ink) !important; }
section[data-testid="stSidebar"] .stButton > button { background: transparent; border: 1px solid var(--accent); }
section[data-testid="stSidebar"] .stButton > button p { color: #F7F4EC !important; }
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span { color: #F7F4EC !important; }
.acc { color: var(--accent) !important; }
.cs-hero { background: var(--ink); color: var(--paper); border-radius: 22px; padding: 36px 40px; margin-bottom: 18px; position: relative; overflow: hidden; }
.cs-hero h1 { color: var(--paper) !important; margin: 0 0 6px; font-size: 3rem; line-height: 1.05; }
.cs-hero p { color: #C5CEDF; margin: 0; font-size: 1.15rem; max-width: 760px; }
.cs-hero .eyebrow { color: var(--accent); font-weight: 600; letter-spacing: 2px; font-size: .85rem; margin-bottom: 10px; }
.cs-band { background: var(--ink); color: var(--paper); border-radius: 18px; padding: 16px 22px; margin-bottom: 14px; }
.cs-band h3 { color: var(--paper) !important; margin: 0; }
.cs-band p { color: #C5CEDF; margin: 4px 0 0; }
.cs-card { background: #FFFDF8; border: 1px solid #E2DACA; border-radius: 16px; padding: 18px 20px; margin-bottom: 12px; }
.cs-feature { background: #FFFDF8; border: 1px solid #E2DACA; border-top: 5px solid var(--accent); border-radius: 16px; padding: 18px 20px; height: 100%; }
.cs-feature h4 { margin: 4px 0 6px; }
.cs-stat { background: var(--paper2); border-radius: 14px; padding: 14px 16px; border-top: 4px solid var(--accent); min-height: 112px; margin-bottom: 10px; }
.cs-stat .v { font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700; color: var(--ink); }
.cs-stat .l { color: var(--muted); font-size: .9rem; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .82rem; font-weight: 600; }
.pill.eligible, .pill.sanctioned { background: #DCEFE4; color: var(--good); }
.pill.needs_info, .pill.documents_requested, .pill.under_review { background: #FBEBCF; color: var(--deep); }
.pill.not_fit, .pill.not_sanctioned { background: #F6DDD6; color: var(--bad); }
.pill.received { background: #E3E8F2; color: var(--ink); }
.crit { margin: 3px 0; font-size: .94rem; }
.crit.pass::before { content: "✔ "; color: var(--good); font-weight: 700; }
.crit.fail::before { content: "✘ "; color: var(--bad); font-weight: 700; }
.crit.unknown::before { content: "? "; color: var(--deep); font-weight: 700; }
.crit a { color: var(--deep); font-size: .85rem; }
.small { color: var(--muted); font-size: .9rem; }
.factor { padding: 9px 0; border-bottom: 1px solid #ECE4D3; }
.factor:last-child { border-bottom: none; }
.factor .fh { display: flex; justify-content: space-between; color: var(--ink); }
.factor .bar { height: 8px; background: var(--paper2); border-radius: 99px; margin: 6px 0; overflow: hidden; }
.factor .bar div { height: 8px; background: var(--accent); border-radius: 99px; }
.factor .fm { font-size: .92rem; color: #2D3748; }
.score-big { font-family: 'Space Grotesk', sans-serif; font-size: 4.6rem; font-weight: 700; line-height: 1; color: var(--ink); }
.timeline { border-left: 3px solid var(--accent); margin-left: 8px; padding-left: 18px; }
.timeline .ev { margin-bottom: 14px; }
.timeline .ev .when { color: var(--muted); font-size: .82rem; }
.mode-badge { display:inline-block; padding: 2px 10px; border-radius: 99px; font-size: .78rem; font-weight: 600; background: #E3E8F2; color: var(--ink); }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stFormSubmitButton > button { background: var(--ink); border: none; }
.stButton > button[kind="primary"] p, .stDownloadButton > button[kind="primary"] p, .stFormSubmitButton > button p { color: #F7F4EC !important; font-weight: 600; }
.stButton > button[kind="primary"]:disabled { opacity: .45; }
div[data-testid="stChatMessage"] { background: transparent; }
</style>
"""

UI = {
    "en": {
        "nav_home": "Home", "nav_chat": "Ask Setu", "nav_guided": "Guided check", "nav_track": "Track application",
        "nav_officer": "Bank officer",
        "lang": "Language / भाषा",
        "privacy_note": "Your data stays in this session. Nothing is stored or sent until you approve an application.",
        "reset": "Start over and clear my data",
        "ai_mode": "AI mode",
        "ai_help": "Paste an Anthropic API key to let Claude run the conversation. Without a key, Setu's built-in offline agent handles everything.",
        "ai_key": "Anthropic API key (optional)",
        "mode_claude": "Claude agent", "mode_offline": "Offline agent",
        # cards
        "avg_in": "average money in each month", "avg_surplus": "average left over each month",
        "payers": "different customers pay monthly", "digital": "of income arrives by UPI / bank",
        "money_in": "Money in", "money_out": "Money out",
        "busiest": "Busiest months", "slowest": "Slowest", "bounced": "Bounced payments", "history": "months of history",
        "plan_title": "Suggested plan for your {amount}", "plan_note": "Cheapest options first. You choose; you can change this.",
        "covers": "covers", "a_year": "a year", "apply_via": "Apply via", "guarantee": "guarantee to your lender",
        "not_fit_group": "Not a fit ({n})", "status": {"eligible": "Eligible", "needs_info": "Likely eligible – needs info", "not_fit": "Not a fit"},
        "out_of": "out of 100", "emi_line": "Estimated EMI for the suggested plan: <b>{emi}</b> a month",
        "fair": "⚖️ <b>Fair by design.</b> This score only looks at cash flow, registration and repayment record. It cannot see gender, caste, religion or region.",
        "calib": "Weights are judgement-based and not yet calibrated on repayment outcomes.",
        "docs_title": "Documents", "draft_title": "Read the full draft application (English, for the bank)",
        "approve_box": "I have read this draft. It is correct, and I want to send it to the bank.",
        "approve_btn": "Approve and send to bank", "dl_md": "Download application", "dl_json": "Download loan file (JSON)",
        "sent": "Sent to the bank. Reference **{ref}**. Track it on the *Track application* page.",
        "doc_icons": {"have": "✅", "missing": "⬜", "ready": "✨"},
    },
    "hi": {
        "nav_home": "होम", "nav_chat": "सेतु से पूछें", "nav_guided": "चरण-दर-चरण जाँच", "nav_track": "आवेदन ट्रैक करें",
        "nav_officer": "बैंक अधिकारी",
        "lang": "Language / भाषा",
        "privacy_note": "आपका डेटा इसी सेशन में रहता है। आवेदन मंज़ूर करने तक कुछ भी सेव या भेजा नहीं जाता।",
        "reset": "फिर से शुरू करें और मेरा डेटा मिटाएँ",
        "ai_mode": "AI मोड",
        "ai_help": "Claude से बातचीत चलवाने के लिए Anthropic API key डालें। key के बिना सेतु का ऑफ़लाइन एजेंट सब संभालता है।",
        "ai_key": "Anthropic API key (वैकल्पिक)",
        "mode_claude": "Claude एजेंट", "mode_offline": "ऑफ़लाइन एजेंट",
        "avg_in": "हर महीने औसतन आने वाला पैसा", "avg_surplus": "हर महीने औसतन बचत",
        "payers": "अलग-अलग ग्राहक हर महीने", "digital": "आय UPI / बैंक से आती है",
        "money_in": "आया पैसा", "money_out": "गया पैसा",
        "busiest": "सबसे अच्छे महीने", "slowest": "सबसे धीमे", "bounced": "बाउंस हुए भुगतान", "history": "महीने का रिकॉर्ड",
        "plan_title": "आपके {amount} के लिए सुझाई गई योजना", "plan_note": "सबसे सस्ते विकल्प पहले। फ़ैसला आपका है, आप इसे बदल सकते हैं।",
        "covers": "कवर", "a_year": "सालाना", "apply_via": "आवेदन कहाँ करें", "guarantee": "आपके बैंक को गारंटी",
        "not_fit_group": "उपयुक्त नहीं ({n})", "status": {"eligible": "पात्र", "needs_info": "शायद पात्र – जानकारी चाहिए", "not_fit": "उपयुक्त नहीं"},
        "out_of": "100 में से", "emi_line": "सुझाई गई योजना की अनुमानित किस्त: <b>{emi}</b> महीना",
        "fair": "⚖️ <b>निष्पक्ष।</b> यह स्कोर सिर्फ़ नकदी प्रवाह, पंजीकरण और भुगतान रिकॉर्ड देखता है। यह लिंग, जाति, धर्म या इलाक़ा नहीं देख सकता।",
        "calib": "वज़न अभी अनुमान पर आधारित हैं, असली भुगतान आँकड़ों पर जाँचे नहीं गए हैं।",
        "docs_title": "दस्तावेज़", "draft_title": "पूरा आवेदन पढ़ें (बैंक के लिए अंग्रेज़ी में)",
        "approve_box": "मैंने यह आवेदन पढ़ लिया है। यह सही है और मैं इसे बैंक को भेजना चाहता/चाहती हूँ।",
        "approve_btn": "मंज़ूर करें और बैंक को भेजें", "dl_md": "आवेदन डाउनलोड करें", "dl_json": "लोन फ़ाइल डाउनलोड करें (JSON)",
        "sent": "बैंक को भेज दिया। रेफ़रेंस **{ref}**। इसे *आवेदन ट्रैक करें* पेज पर देखें।",
        "doc_icons": {"have": "✅", "missing": "⬜", "ready": "✨"},
    },
}

DOC_LABELS_HI = {"aadhaar": "आधार कार्ड", "pan": "PAN कार्ड", "bank_statement": "पिछले 6–12 महीने का बैंक स्टेटमेंट",
                 "business_proof": "कारोबार के पते का सबूत (किरायानामा या बिजली बिल)", "photo": "हाल की पासपोर्ट फ़ोटो",
                 "udyam": "उद्यम पंजीकरण प्रमाणपत्र (या उद्यम असिस्ट)", "quotation": "मशीन या माल का कोटेशन",
                 "vishwakarma_cert": "पीएम विश्वकर्मा प्रमाणपत्र और ट्रेनिंग", "cashflow_summary": "नकदी प्रवाह का सारांश (CreditSetu बनाएगा)",
                 "project_report": "छोटी प्रोजेक्ट रिपोर्ट (CreditSetu बनाएगा)"}


def lang() -> str:
    return st.session_state.get("lang", "en")


def u(key: str):
    return UI[lang()][key]


def case() -> CaseState:
    if "case" not in st.session_state:
        st.session_state.case = CaseState(lang=lang())
    c = st.session_state.case
    c.lang = lang()
    return c


def current_analysis():
    """Analysis for the case in the current language (recomputed if the language changed)."""
    c = case()
    if c.analysis is not None and getattr(c.analysis, "lang", "en") != c.lang and c.txns is not None:
        c.analysis = analyze(c.applicant, c.txns, c.lang)
    return c.analysis


def api_key() -> str:
    key = st.session_state.get("anthropic_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            key = ""
    return key


def md_bold(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def months(names: list) -> str:
    return ", ".join(MONTHS_HI.get(n, n) if lang() == "hi" else n for n in names)


# ------------------------------------------------------------------ cards
def render_profile(profile, key: str = "p") -> None:
    cols = st.columns(4)
    stats = [(_inr(profile.avg_monthly_inflow), u("avg_in")), (_inr(profile.avg_monthly_surplus), u("avg_surplus")),
             (f"{round(profile.avg_payers_per_month)}", u("payers")), (f"{round(profile.digital_share * 100)}%", u("digital"))]
    for col, (v, label) in zip(cols, stats):
        col.markdown(f"<div class='cs-stat'><div class='v'>{v}</div><div class='l'>{label}</div></div>", unsafe_allow_html=True)
    df = pd.DataFrame(profile.monthly).rename(columns={"inflow": u("money_in"), "outflow": u("money_out")}).set_index("month")
    st.bar_chart(df, color=["#E8A33D", "#16233F"], height=260, stack=False)
    st.markdown(f"<div class='small'>📈 <b>{u('busiest')}:</b> {months(profile.peak_months)} · 📉 <b>{u('slowest')}:</b> "
                f"{months(profile.low_months)} · <b>{u('bounced')}:</b> {profile.bounced_count} · "
                f"<b>{profile.months}</b> {u('history')}</div>", unsafe_allow_html=True)


def _scheme_card(r) -> str:
    covers = f" · {u('covers')} {_inr(r.covers_amount)}" if r.covers_amount and r.status != "not_fit" else ""
    rate = f" · ~{r.indicative_rate:g}% {u('a_year')}" if r.indicative_rate else ""
    kind = f" · {u('guarantee')}" if r.kind == "guarantee" else ""
    crit = "".join(
        f"<div class='crit {c.status}'>{c.text} <a href='{c.source_url}' target='_blank'>[{c.source_title}]</a>"
        + (f"<br><span class='small'>→ {c.fix}</span>" if c.fix and c.status != "pass" else "") + "</div>"
        for c in r.criteria)
    note = f"<div class='small' style='margin-top:6px'>⚠️ {r.status_note}</div>" if r.status_note else ""
    return (f"<div class='cs-card'><span class='pill {r.status}'>{u('status')[r.status]}</span>"
            f"<h4 style='margin:8px 0 2px'>{r.name}</h4><div class='small'>{r.scheme}{kind}{rate}{covers}</div>"
            f"<p style='margin:8px 0'>{r.benefit}</p>{crit}{note}"
            f"<div class='small' style='margin-top:8px'>{u('apply_via')}: {r.apply_via}</div></div>")


def render_schemes(analysis, amount: int) -> None:
    plan = analysis.plan
    if plan:
        parts = " + ".join(f"<b>{p['name']}</b> {_inr(p['amount'])} @ ~{p['rate']:g}%" for p in plan)
        st.markdown(f"<div class='cs-card' style='border-left:6px solid #E8A33D'>💡 <b>"
                    f"{u('plan_title').format(amount=_inr(amount))}:</b> {parts}<br>"
                    f"<span class='small'>{u('plan_note')}</span></div>", unsafe_allow_html=True)
    fits = [r for r in analysis.results if r.status != "not_fit"]
    nots = [r for r in analysis.results if r.status == "not_fit"]
    for r in fits:
        st.markdown(_scheme_card(r), unsafe_allow_html=True)
    if nots:
        with st.expander(u("not_fit_group").format(n=len(nots))):
            for r in nots:
                st.markdown(_scheme_card(r), unsafe_allow_html=True)
    rules = load_rules()
    disc = rules.get("disclaimer_hi") if lang() == "hi" else rules["disclaimer"]
    st.caption(f"{disc} ({rules['checked_on']})")


def render_score(score) -> None:
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div class='cs-card'><div class='score-big'>{score.total}</div><div class='small'>{u('out_of')}</div>"
                    f"<h4 style='margin-top:10px'>{score.band}</h4><div class='small'>{u('emi_line').format(emi=_inr(score.emi))}</div></div>"
                    f"<div class='cs-card small'>{u('fair')}</div>", unsafe_allow_html=True)
    with right:
        html = ""
        for f in score.factors:
            pct = max(0, f.points) / f.max_points * 100
            tip = f"<div class='small'>→ {f.improve}</div>" if f.improve else ""
            html += (f"<div class='factor'><div class='fh'><b>{f.name}</b><span>{f.points:g} / {f.max_points:g}</span></div>"
                     f"<div class='bar'><div style='width:{pct:.0f}%'></div></div><div class='fm'>{f.measured}</div>{tip}</div>")
        st.markdown(f"<div class='cs-card'>{html}</div>", unsafe_allow_html=True)
    st.caption(u("calib"))


def render_checklist(checklist: list) -> None:
    icons = u("doc_icons")
    cols = st.columns(2)
    for i, item in enumerate(checklist):
        label = DOC_LABELS_HI.get(item["key"], item["label"]) if lang() == "hi" else item["label"]
        cols[i % 2].markdown(f"{icons[item['status']]} {label}")


def render_application(pkg, key: str, on_submit) -> None:
    """Checklist, draft, approval gate and submit button. ``on_submit()`` returns a reference."""
    st.markdown(f"#### {u('docs_title')}")
    render_checklist(pkg.checklist)
    with st.expander(u("draft_title")):
        st.markdown(pkg.draft_md)
    sent_key = f"sent_{key}"
    if st.session_state.get(sent_key):
        st.success(u("sent").format(ref=st.session_state[sent_key]))
        c1, c2 = st.columns(2)
        c1.download_button(u("dl_md"), pkg.draft_md, file_name="creditsetu_application.md", key=f"dlm_{key}", width="stretch")
        c2.download_button(u("dl_json"), pkg.file_json, file_name="creditsetu_loan_file.json", key=f"dlj_{key}", width="stretch")
        return
    ok = st.checkbox(u("approve_box"), key=f"ok_{key}")
    if st.button(u("approve_btn"), type="primary", disabled=not ok, key=f"send_{key}"):
        ref = on_submit()
        st.session_state[sent_key] = ref
        st.rerun()
