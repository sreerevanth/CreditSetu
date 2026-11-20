"""CreditSetu – Streamlit prototype.

Run:  streamlit run app.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

from creditsetu.application import document_checklist, draft_application, loan_file_json
from creditsetu.explain import llm_available, llm_summary, template_summary
from creditsetu.models import Applicant
from creditsetu.profile import build_profile
from creditsetu.schemes import load_rules, match_schemes, suggest_plan
from creditsetu.score import _inr, plan_emi, readiness_score
from creditsetu.statement import read_statement

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "data" / "sample_statement_sunita.csv"

st.set_page_config(page_title="CreditSetu", page_icon="🌉", layout="wide")

# ---------------------------------------------------------------- styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&display=swap');
:root { --ink:#16233F; --paper:#F7F4EC; --paper2:#EDE6D6; --accent:#E8A33D; --deep:#8F5410; --good:#23694A; --bad:#A13A24; --muted:#4A5568; }
html, body, [class*="css"], .stMarkdown, p, li, label { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; color: var(--ink); letter-spacing: -0.5px; }
.stApp { background: var(--paper); }
section[data-testid="stSidebar"] { background: var(--ink); }
section[data-testid="stSidebar"] * { color: #F7F4EC; }
section[data-testid="stSidebar"] .acc { color: var(--accent) !important; }
section[data-testid="stSidebar"] .stButton > button { background: transparent; border: 1px solid var(--accent); }
section[data-testid="stSidebar"] .stButton > button p { color: #F7F4EC !important; }
.cs-hero { background: var(--ink); color: var(--paper); border-radius: 20px; padding: 20px 28px; margin-bottom: 16px; }
.cs-hero h1 { color: var(--paper) !important; margin: 0; font-size: 2.6rem; }
.cs-hero h1 .acc, .acc { color: var(--accent) !important; }
.cs-hero p { color: #C5CEDF; margin: 6px 0 0; font-size: 1.05rem; }
.cs-card { background: #FFFDF8; border: 1px solid #E2DACA; border-radius: 16px; padding: 18px 20px; margin-bottom: 14px; }
.cs-stat { background: var(--paper2); border-radius: 14px; padding: 14px 16px; border-top: 4px solid var(--accent); }
.cs-stat .v { font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700; color: var(--ink); }
.cs-stat .l { color: var(--muted); font-size: .9rem; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .82rem; font-weight: 600; }
.pill.eligible { background: #DCEFE4; color: var(--good); }
.pill.needs_info { background: #FBEBCF; color: var(--deep); }
.pill.not_fit { background: #F6DDD6; color: var(--bad); }
.crit { margin: 2px 0; font-size: .95rem; }
.crit.pass::before { content: "✔ "; color: var(--good); font-weight: 700; }
.crit.fail::before { content: "✘ "; color: var(--bad); font-weight: 700; }
.crit.unknown::before { content: "? "; color: var(--deep); font-weight: 700; }
.crit a { color: var(--deep); font-size: .85rem; }
.factor { padding: 10px 0; border-bottom: 1px solid #ECE4D3; }
.factor:last-child { border-bottom: none; }
.factor .fh { display: flex; justify-content: space-between; color: var(--ink); }
.factor .bar { height: 8px; background: var(--paper2); border-radius: 99px; margin: 6px 0; overflow: hidden; }
.factor .bar div { height: 8px; background: var(--accent); border-radius: 99px; }
.factor .fm { font-size: .93rem; color: #2D3748; }
.score-big { font-family: 'Space Grotesk', sans-serif; font-size: 5rem; font-weight: 700; line-height: 1; color: var(--ink); }
.small { color: var(--muted); font-size: .9rem; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stFormSubmitButton > button { background: var(--ink); border: none; }
.stButton > button[kind="primary"] p, .stDownloadButton > button[kind="primary"] p, .stFormSubmitButton > button p { color: #F7F4EC !important; font-weight: 600; }
.stButton > button[kind="primary"]:disabled { opacity: .45; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- text
T = {
    "en": {
        "tagline": "Your guide to formal credit and the government schemes meant for you.",
        "steps": ["1 · Consent", "2 · Your business", "3 · Cash-flow profile", "4 · Schemes", "5 · Readiness score", "6 · Review & approve"],
        "next": "Next →",
    },
    "hi": {
        "tagline": "औपचारिक लोन और आपके लिए बनी सरकारी योजनाओं तक पहुँचने में आपका साथी।",
        "steps": ["1 · सहमति", "2 · आपका कारोबार", "3 · नकदी प्रवाह", "4 · योजनाएँ", "5 · तैयारी स्कोर", "6 · जाँचें और मंज़ूरी दें"],
        "next": "आगे →",
    },
}

TRADES = {
    "tailor": "Tailor (Darzi)", "barber": "Barber", "carpenter": "Carpenter", "mason": "Mason",
    "cobbler": "Cobbler / footwear", "potter": "Potter", "blacksmith": "Blacksmith", "goldsmith": "Goldsmith",
    "washerman": "Washerman (Dhobi)", "garland_maker": "Garland maker", "basket_mat_broom_maker": "Basket / mat / broom maker",
    "doll_toy_maker": "Traditional doll & toy maker", "fishing_net_maker": "Fishing net maker",
    "kirana": "Kirana / grocery shop", "fabrication": "Fabrication / welding", "dairy": "Dairy unit",
    "food_stall": "Food stall / catering", "beauty_parlour": "Beauty parlour", "repair_shop": "Repair shop", "other": "Other",
}
SECTORS = {"manufacturing": "Manufacturing / making things", "services": "Services",
           "trading": "Trading / shop", "allied_agriculture": "Dairy, poultry, fisheries, beekeeping"}
STATUS_LABEL = {"eligible": "Eligible", "needs_info": "Likely eligible – needs info", "not_fit": "Not a fit"}

# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("step", 0)
ss.setdefault("consent", False)
ss.setdefault("lang", "en")


def reset_all():
    for key in list(ss.keys()):
        del ss[key]


with st.sidebar:
    st.markdown("## Credit<span class='acc'>Setu</span>", unsafe_allow_html=True)
    ss.lang = "hi" if st.radio("Language / भाषा", ["English", "हिन्दी"], horizontal=True,
                               index=1 if ss.lang == "hi" else 0) == "हिन्दी" else "en"
    tx = T[ss.lang]
    unlocked = ss.consent
    choice = st.radio("Steps", tx["steps"], index=ss.step, label_visibility="collapsed",
                      disabled=not unlocked)
    if unlocked:
        ss.step = tx["steps"].index(choice)
    st.markdown("---")
    st.caption("Prototype. Your data stays in this browser session: nothing is stored or sent anywhere"
               + (" unless you turn on AI explanations." if llm_available() else "."))
    if st.button("Revoke consent and clear my data", width="stretch"):
        reset_all()
        st.rerun()

tx = T[ss.lang]
st.markdown(
    f"<div class='cs-hero'><h1>Credit<span class='acc'>Setu</span></h1><p>{tx['tagline']}</p></div>",
    unsafe_allow_html=True,
)


def go(step: int):
    ss.step = step
    st.rerun()


# ---------------------------------------------------------------- computations
def compute():
    """(Re)compute everything from the current applicant and statement."""
    a: Applicant = ss.applicant
    txns = ss.txns
    profile = build_profile(txns)
    results = match_schemes(a)
    plan = suggest_plan(a, results)
    monthly_emi = plan_emi(plan) if plan else 0.0
    score = readiness_score(profile, udyam_registered=a.udyam_registered,
                            has_default=a.has_default, monthly_emi=monthly_emi)
    ss.profile, ss.results, ss.plan, ss.score = profile, results, plan, score


def ready() -> bool:
    return all(k in ss for k in ("applicant", "txns"))


# ================================================================= STEP 1: CONSENT
if ss.step == 0:
    st.subheader("Before we start: your data, your choice")
    st.markdown(
        """
<div class='cs-card'>
CreditSetu reads your <b>bank or UPI statement</b> and a few answers about your business to:
<ul>
<li>find the loan schemes you qualify for, with the official rule for each one,</li>
<li>work out an explainable loan-readiness score,</li>
<li>prepare a loan application for <b>you</b> to review.</li>
</ul>
<b>What we never do:</b> store your statement, share it, or submit anything without your approval.
Your gender, caste category and location are asked only because some schemes are reserved by law
for certain groups. They are <b>never</b> used in your score.
</div>
""",
        unsafe_allow_html=True,
    )
    c1 = st.checkbox("I agree to CreditSetu reading my bank / UPI statement for this check")
    c2 = st.checkbox("I agree to CreditSetu using my answers about my business")
    ai = False
    if llm_available():
        ai = st.checkbox("Optional: use AI to explain my results in simple words "
                         "(sends only the results, never the statement, to an AI service)")
    if st.button("Continue", type="primary", disabled=not (c1 and c2)):
        ss.consent = True
        ss.ai_ok = ai
        go(1)

# ================================================================= STEP 2: BUSINESS
elif ss.step == 1:
    st.subheader("Tell us about your business")
    if st.button("⚡ Fill in the demo: Sunita's tailoring unit"):
        ss.applicant = Applicant(
            business_name="Sunita Tailoring Works", owner_name="Sunita", trade="tailor",
            sector="manufacturing", enterprise_size="micro", is_new_unit=False, years_in_business=4,
            loan_amount=300000, loan_purpose="Two new sewing machines and fabric stock before wedding season",
            age=34, has_default=False, udyam_registered=False, vishwakarma_trained=None,
            prior_scheme_loan=False, gender="female", social_category="obc", area="urban",
            district="Bhilwara", state="Rajasthan")
        ss.txns = read_statement(SAMPLE)
        ss.statement_name = "Sample statement (synthetic data)"
        compute()
        go(2)

    a: Applicant = ss.get("applicant", Applicant())
    with st.form("business"):
        c1, c2 = st.columns(2)
        business_name = c1.text_input("Business name", a.business_name)
        owner_name = c2.text_input("Your name", a.owner_name)
        trade_keys = list(TRADES)
        trade = c1.selectbox("What work do you do?", trade_keys, format_func=TRADES.get,
                             index=trade_keys.index(a.trade) if a.trade in trade_keys else 0)
        sector_keys = list(SECTORS)
        sector = c2.selectbox("Type of business", sector_keys, format_func=SECTORS.get,
                              index=sector_keys.index(a.sector) if a.sector in sector_keys else 0)
        is_new = c1.radio("Is this a new business you're starting?", ["No, it's already running", "Yes, it's new"],
                          index=1 if a.is_new_unit else 0, horizontal=True) == "Yes, it's new"
        years = c2.number_input("Years in business", 0.0, 60.0, float(a.years_in_business or 0), 0.5)
        loan_amount = c1.number_input("How much do you need? (₹)", 10000, 10000000, int(a.loan_amount or 300000), 10000)
        purpose = c2.text_input("What is it for?", a.loan_purpose)
        age = c1.number_input("Your age", 18, 90, int(a.age or 30))
        district = c2.text_input("District", a.district)
        state_name = c1.text_input("State", a.state)

        st.markdown("**A few yes/no questions**")
        yn = {"Yes": True, "No": False, "Not sure": None}

        def yn_index(v):
            return 0 if v is True else 1 if v is False else 2

        q1, q2, q3 = st.columns(3)
        udyam = yn[q1.radio("Registered on Udyam?", list(yn), index=yn_index(a.udyam_registered))]
        default = yn[q2.radio("Any unpaid loan in default?", list(yn), index=yn_index(a.has_default))]
        prior = yn[q3.radio("Took a PMEGP / SVANidhi / MUDRA loan in the last 5 years?", list(yn),
                            index=yn_index(a.prior_scheme_loan))]
        q4, q5, _ = st.columns(3)
        trained = yn[q4.radio("Done PM Vishwakarma basic training?", list(yn), index=yn_index(a.vishwakarma_trained))]
        tarun = yn[q5.radio("Repaid a MUDRA Tarun loan before?", list(yn), index=yn_index(a.prior_tarun_repaid))]

        with st.expander("Optional: details some schemes require by law (never used in your score)"):
            g1, g2, g3 = st.columns(3)
            genders = {"Prefer not to say": None, "Woman": "female", "Man": "male", "Other": "other"}
            gender = genders[g1.selectbox("Gender", list(genders),
                                          index=list(genders.values()).index(a.gender) if a.gender in genders.values() else 0)]
            cats = {"Prefer not to say": None, "General": "general", "OBC": "obc", "SC": "sc", "ST": "st"}
            category = cats[g2.selectbox("Category", list(cats),
                                         index=list(cats.values()).index(a.social_category) if a.social_category in cats.values() else 0)]
            areas = {"Prefer not to say": None, "Urban": "urban", "Rural": "rural"}
            area = areas[g3.selectbox("Area", list(areas),
                                      index=list(areas.values()).index(a.area) if a.area in areas.values() else 0)]

        st.markdown("**Your bank or UPI statement (CSV)**")
        upload = st.file_uploader("Upload a CSV export from your bank", type=["csv"],
                                  help="Columns like Date, Narration, Withdrawal, Deposit, Balance work. PDF support is on the roadmap.")
        use_sample = st.checkbox("No statement handy? Use the synthetic sample statement", value=upload is None and "txns" not in ss)
        submitted = st.form_submit_button("Check my options", type="primary")

    if submitted:
        try:
            if upload is not None:
                ss.txns = read_statement(upload.getvalue())
                ss.statement_name = upload.name
            elif use_sample or "txns" not in ss:
                ss.txns = read_statement(SAMPLE)
                ss.statement_name = "Sample statement (synthetic data)"
        except ValueError as e:
            st.error(f"Couldn't read that statement: {e}")
            st.stop()
        ss.applicant = Applicant(
            business_name=business_name, owner_name=owner_name, trade=trade, sector=sector,
            enterprise_size="micro", is_new_unit=is_new, years_in_business=years, loan_amount=int(loan_amount),
            loan_purpose=purpose, age=int(age), has_default=default, udyam_registered=udyam,
            vishwakarma_trained=trained, prior_scheme_loan=prior, prior_tarun_repaid=tarun,
            gender=gender, social_category=category, area=area, district=district, state=state_name)
        compute()
        go(2)

# ================================================================= STEP 3: PROFILE
elif ss.step == 2:
    if not ready():
        st.info("Fill in step 2 first.")
        st.stop()
    p = ss.profile
    st.subheader("What your statement shows")
    st.caption(f"From: {ss.get('statement_name', 'your statement')} · {p.start} to {p.end}")
    cols = st.columns(4)
    stats = [
        (_inr(p.avg_monthly_inflow), "average money in each month"),
        (_inr(p.avg_monthly_surplus), "average left over each month"),
        (f"{round(p.avg_payers_per_month)}", "different customers pay you monthly"),
        (f"{round(p.digital_share * 100)}%", "of income arrives by UPI / bank"),
    ]
    for col, (v, label) in zip(cols, stats):
        col.markdown(f"<div class='cs-stat'><div class='v'>{v}</div><div class='l'>{label}</div></div>",
                     unsafe_allow_html=True)
    st.markdown("&nbsp;")
    df = pd.DataFrame(p.monthly).rename(columns={"inflow": "Money in", "outflow": "Money out"}).set_index("month")
    st.bar_chart(df, color=["#E8A33D", "#16233F"], height=320)
    st.markdown(
        f"<div class='cs-card'>📈 <b>Busiest months:</b> {', '.join(p.peak_months)} &nbsp;·&nbsp; "
        f"📉 <b>Slowest:</b> {', '.join(p.low_months)} &nbsp;·&nbsp; "
        f"<b>Bounced payments:</b> {p.bounced_count} &nbsp;·&nbsp; <b>{p.months}</b> months of history</div>",
        unsafe_allow_html=True)
    st.caption("This is the kind of income a bank can't see from an ITR you don't have, "
               "but can see from your statement.")
    if st.button(tx["next"], type="primary"):
        go(3)

# ================================================================= STEP 4: SCHEMES
elif ss.step == 3:
    if not ready():
        st.info("Fill in step 2 first.")
        st.stop()
    a, results, plan = ss.applicant, ss.results, ss.plan
    rules = load_rules()
    st.subheader("Schemes you can use")
    st.caption(f"Rules checked against official sources on {rules['checked_on']}. {rules['disclaimer']}")

    if plan:
        total = sum(p["amount"] for p in plan)
        parts = " + ".join(f"<b>{p['name']}</b> {_inr(p['amount'])} at ~{p['rate']:g}%" for p in plan)
        st.markdown(
            f"<div class='cs-card' style='border-left:6px solid #E8A33D'>💡 <b>Suggested plan for your "
            f"{_inr(a.loan_amount)}:</b> {parts}"
            + ("" if total >= (a.loan_amount or 0) else f" (covers {_inr(total)})")
            + "<br><span class='small'>Cheapest options first. You choose; you can change this.</span></div>",
            unsafe_allow_html=True)

    for r in results:
        with st.container():
            covers = f" · covers {_inr(r.covers_amount)}" if r.covers_amount and r.status != "not_fit" else ""
            rate = f" · ~{r.indicative_rate:g}% a year" if r.indicative_rate else ""
            crit_html = "".join(
                f"<div class='crit {c.status}'>{c.text} "
                f"<a href='{c.source_url}' target='_blank'>[{c.source_title}]</a>"
                + (f"<br><span class='small'>→ {c.fix}</span>" if c.fix and c.status != 'pass' else "")
                + "</div>"
                for c in r.criteria)
            note = f"<div class='small' style='margin-top:6px'>⚠️ {r.status_note}</div>" if r.status_note else ""
            kind = " · guarantee to your lender" if r.kind == "guarantee" else ""
            st.markdown(
                f"<div class='cs-card'><span class='pill {r.status}'>{STATUS_LABEL[r.status]}</span>"
                f"<h4 style='margin:8px 0 2px'>{r.name}</h4>"
                f"<div class='small'>{r.scheme}{kind}{rate}{covers}</div>"
                f"<p style='margin:8px 0'>{r.benefit}</p>{crit_html}{note}"
                f"<div class='small' style='margin-top:8px'>Apply via: {r.apply_via}</div></div>",
                unsafe_allow_html=True)

    if st.button(tx["next"], type="primary"):
        go(4)

# ================================================================= STEP 5: SCORE
elif ss.step == 4:
    if not ready():
        st.info("Fill in step 2 first.")
        st.stop()
    s, a = ss.score, ss.applicant
    st.subheader("Your loan-readiness score")
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div class='cs-card'><div class='score-big'>{s.total}</div>"
                    f"<div class='small'>out of 100</div><h4 style='margin-top:10px'>{s.band}</h4>"
                    f"<div class='small'>Estimated EMI for the suggested plan: <b>{_inr(s.emi)}</b> a month</div></div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div class='cs-card'>⚖️ <b>Fair by design.</b> This score only looks at your cash flow, "
            "registration and repayment record. It cannot see your gender, caste, religion or region.</div>",
            unsafe_allow_html=True)
    with right:
        html = ""
        for f in s.factors:
            pct = max(0, f.points) / f.max_points * 100
            tip = f"<div class='small'>→ {f.improve}</div>" if f.improve else ""
            html += (f"<div class='factor'><div class='fh'><b>{f.name}</b><span>{f.points:g} / {f.max_points:g}</span></div>"
                     f"<div class='bar'><div style='width:{pct:.0f}%'></div></div>"
                     f"<div class='fm'>{f.measured}</div>{tip}</div>")
        st.markdown(f"<div class='cs-card'>{html}</div>", unsafe_allow_html=True)

    with st.expander("Check it yourself: does changing gender, category or region change the score?"):
        from dataclasses import replace

        g = st.selectbox("Pretend the owner is…", ["a man", "a woman", "another gender"])
        c = st.selectbox("…in category", ["General", "OBC", "SC", "ST"])
        reg = st.selectbox("…in a", ["rural area", "urban area"])
        variant = replace(a, gender={"a man": "male", "a woman": "female"}.get(g, "other"),
                          social_category=c.lower(), area=reg.split()[0])
        # The score function doesn't even accept these fields: we pass the same cash-flow inputs.
        s2 = readiness_score(ss.profile, udyam_registered=variant.udyam_registered,
                             has_default=variant.has_default, monthly_emi=s.emi)
        st.markdown(f"Score for this variant: **{s2.total}** (original: **{s.total}**). "
                    + ("✔ Identical." if s2.total == s.total else "✘ Different – this would be a bug."))
        st.caption("Scheme eligibility can still differ, because some schemes are reserved by law "
                   "(for example Stand-Up India for SC/ST and women). That's the scheme's rule, not the score.")
    st.caption("Weights are judgement-based and not yet calibrated on repayment outcomes. "
               "A pilot would calibrate them against real repayments.")
    if st.button(tx["next"], type="primary"):
        go(5)

# ================================================================= STEP 6: APPLICATION
elif ss.step == 5:
    if not ready():
        st.info("Fill in step 2 first.")
        st.stop()
    a, p, s, plan, results = ss.applicant, ss.profile, ss.score, ss.plan, ss.results
    st.subheader("Review your application")

    summary = (llm_summary if ss.get("ai_ok") else template_summary)(results, plan, s, ss.lang)
    summary = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", summary)  # markdown bold inside an HTML card
    st.markdown(f"<div class='cs-card' style='border-left:6px solid #16233F'>{summary}</div>",
                unsafe_allow_html=True)

    st.markdown("#### Documents")
    have_opts = {k: label for k, label in [
        ("aadhaar", "Aadhaar"), ("pan", "PAN"), ("bank_statement", "Bank statement"),
        ("business_proof", "Business address proof"), ("photo", "Photograph"),
        ("udyam", "Udyam certificate"), ("quotation", "Quotation for machines/stock")]}
    have = set(st.multiselect("Tick what you already have", list(have_opts), format_func=have_opts.get,
                              default=["aadhaar", "pan", "bank_statement"]))
    checklist = document_checklist(a, have, plan)
    missing = [i["label"] for i in checklist if i["status"] == "missing"]
    cols = st.columns(2)
    for i, item in enumerate(checklist):
        icon = {"have": "✅", "missing": "⬜", "ready": "✨"}[item["status"]]
        cols[i % 2].markdown(f"{icon} {item['label']}")
    if missing:
        st.info(f"{len(missing)} document(s) still to collect. The draft marks them so the branch knows they're coming.")

    draft = draft_application(a, p, s, plan, results, checklist)
    with st.expander("Read the full draft application", expanded=False):
        st.markdown(draft)

    st.markdown("#### Your approval")
    approve = st.checkbox("I have read this draft. It is correct, and I want to use it for my loan application.")
    c1, c2 = st.columns(2)
    c1.download_button("Download application (Markdown)", draft, file_name="creditsetu_application.md",
                       disabled=not approve, type="primary", width="stretch")
    c2.download_button("Download loan file for the lender (JSON)", loan_file_json(a, p, s, plan, results),
                       file_name="creditsetu_loan_file.json", disabled=not approve, width="stretch")
    st.caption("Submission is simulated in this prototype. In a pilot, the approved file goes to the lender, "
               "JanSamarth or Udyamimitra, and CreditSetu tracks follow-ups.")
