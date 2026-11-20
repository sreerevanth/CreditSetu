"""Guided check: the same engine as the chat, as a step-by-step form."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from creditsetu import store
from creditsetu.case import analyze, build_package, submission_kwargs
from creditsetu.documents import read_quotation_image, read_statement_file
from creditsetu.explain import template_summary
from creditsetu.models import Applicant
from creditsetu.score import _inr
from creditsetu.statement import read_statement
from ui.common import case, lang, md_bold, render_application, render_profile, render_schemes, render_score, u

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_statement_sunita.csv"

TRADES = ["tailor", "barber", "carpenter", "mason", "cobbler", "potter", "blacksmith", "goldsmith", "washerman",
          "garland_maker", "basket_mat_broom_maker", "doll_toy_maker", "fishing_net_maker", "kirana", "fabrication",
          "dairy", "food_stall", "beauty_parlour", "repair_shop", "other"]
TRADE_LABELS = {
    "en": {"tailor": "Tailor (Darzi)", "barber": "Barber", "carpenter": "Carpenter", "mason": "Mason", "cobbler": "Cobbler / footwear",
           "potter": "Potter", "blacksmith": "Blacksmith", "goldsmith": "Goldsmith", "washerman": "Washerman (Dhobi)",
           "garland_maker": "Garland maker", "basket_mat_broom_maker": "Basket / mat / broom maker", "doll_toy_maker": "Traditional doll & toy maker",
           "fishing_net_maker": "Fishing net maker", "kirana": "Kirana / grocery shop", "fabrication": "Fabrication / welding",
           "dairy": "Dairy unit", "food_stall": "Food stall / catering", "beauty_parlour": "Beauty parlour", "repair_shop": "Repair shop", "other": "Other"},
    "hi": {"tailor": "दर्जी", "barber": "नाई", "carpenter": "बढ़ई", "mason": "राजमिस्त्री", "cobbler": "मोची / जूते", "potter": "कुम्हार",
           "blacksmith": "लोहार", "goldsmith": "सुनार", "washerman": "धोबी", "garland_maker": "माला बनाने वाले",
           "basket_mat_broom_maker": "टोकरी / चटाई / झाड़ू", "doll_toy_maker": "पारंपरिक खिलौने", "fishing_net_maker": "मछली का जाल",
           "kirana": "किराना दुकान", "fabrication": "फैब्रिकेशन / वेल्डिंग", "dairy": "डेयरी", "food_stall": "खाने का स्टॉल / कैटरिंग",
           "beauty_parlour": "ब्यूटी पार्लर", "repair_shop": "रिपेयर की दुकान", "other": "अन्य"},
}
SECTORS = ["manufacturing", "services", "trading", "allied_agriculture"]
SECTOR_LABELS = {"en": {"manufacturing": "Making things", "services": "Services", "trading": "Trading / shop", "allied_agriculture": "Dairy, poultry, fisheries"},
                 "hi": {"manufacturing": "सामान बनाना", "services": "सेवाएँ", "trading": "व्यापार / दुकान", "allied_agriculture": "डेयरी, मुर्ग़ीपालन, मछली"}}

T = {
    "en": {
        "title": "Guided check", "steps": ["Consent", "Business", "Cash flow", "Schemes", "Score", "Approve"],
        "consent_h": "Before we start: your data, your choice",
        "consent_body": "CreditSetu reads your <b>bank or UPI statement</b> and a few answers to find the schemes you qualify for (with the official rule for each), work out an explainable score, and prepare an application for <b>you</b> to approve.<br><br><b>We never</b> store your statement, share it, or send anything without your approval. Gender, caste category and area are asked only because some schemes are reserved by law. They are <b>never</b> used in your score.",
        "c1": "I agree to CreditSetu reading my bank / UPI statement for this check", "c2": "I agree to CreditSetu using my answers about my business",
        "continue": "Continue", "demo": "⚡ Fill in the demo: Sunita's tailoring unit",
        "name": "Your name", "business": "Business name", "trade": "What work do you do?", "sector": "Type of business",
        "new": "Is this a new business?", "new_opts": ["No, it's already running", "Yes, it's new"], "years": "Years in business",
        "amount": "How much do you need? (₹)", "purpose": "What is it for?", "age": "Your age", "district": "District", "state": "State",
        "yn_title": "A few yes/no questions", "yn": ["Yes", "No", "Not sure"],
        "q_udyam": "Registered on Udyam?", "q_default": "Any loan in default?", "q_prior": "PMEGP / SVANidhi / MUDRA loan in last 5 years?",
        "q_trained": "Done PM Vishwakarma basic training?", "q_tarun": "Repaid a MUDRA Tarun loan before?",
        "opt_h": "Optional: details some schemes require by law (never used in your score)",
        "gender": "Gender", "genders": ["Prefer not to say", "Woman", "Man", "Other"], "category": "Category",
        "cats": ["Prefer not to say", "General", "OBC", "SC", "ST"], "area": "Area", "areas": ["Prefer not to say", "Urban", "Rural"],
        "docs_h": "Your documents", "stmt": "Bank or UPI statement (PDF or CSV)", "quote": "Photo of a quotation or invoice (optional)",
        "use_sample": "No statement handy? Use the synthetic sample", "submit": "Check my options",
        "quote_read": "Read quotation from **{v}**: total **{t}**", "err": "Couldn't read that statement: {e}",
        "profile_h": "What your statement shows", "schemes_h": "Schemes you can use", "score_h": "Your loan-readiness score",
        "review_h": "Review and approve", "next": "Next →", "first": "Fill in your business details first.",
        "have_h": "Tick what you already have",
        "have_opts": {"aadhaar": "Aadhaar", "pan": "PAN", "bank_statement": "Bank statement", "business_proof": "Business address proof",
                      "photo": "Photograph", "udyam": "Udyam certificate", "quotation": "Quotation"},
    },
    "hi": {
        "title": "चरण-दर-चरण जाँच", "steps": ["सहमति", "कारोबार", "नकदी प्रवाह", "योजनाएँ", "स्कोर", "मंज़ूरी"],
        "consent_h": "शुरू करने से पहले: आपका डेटा, आपकी मर्ज़ी",
        "consent_body": "CreditSetu आपका <b>बैंक या UPI स्टेटमेंट</b> और कुछ जवाब पढ़ता है, ताकि वे योजनाएँ मिलें जिनके लिए आप पात्र हैं (हर एक के आधिकारिक नियम के साथ), एक समझाया गया स्कोर बने, और <b>आपकी</b> मंज़ूरी के लिए आवेदन तैयार हो।<br><br><b>हम कभी</b> आपका स्टेटमेंट सेव या साझा नहीं करते, और आपकी मंज़ूरी के बिना कुछ नहीं भेजते। लिंग, जाति वर्ग और इलाक़ा सिर्फ़ इसलिए पूछे जाते हैं कि कुछ योजनाएँ क़ानून के तहत आरक्षित हैं। इनका इस्तेमाल आपके स्कोर में <b>कभी नहीं</b> होता।",
        "c1": "मैं सहमत हूँ कि CreditSetu इस जाँच के लिए मेरा बैंक / UPI स्टेटमेंट पढ़े", "c2": "मैं सहमत हूँ कि CreditSetu मेरे कारोबार के बारे में मेरे जवाब इस्तेमाल करे",
        "continue": "आगे बढ़ें", "demo": "⚡ डेमो भरें: सुनीता की सिलाई यूनिट",
        "name": "आपका नाम", "business": "कारोबार का नाम", "trade": "आप क्या काम करते हैं?", "sector": "कारोबार का प्रकार",
        "new": "क्या यह नया कारोबार है?", "new_opts": ["नहीं, पहले से चल रहा है", "हाँ, नया है"], "years": "कितने साल से",
        "amount": "कितने पैसे चाहिए? (₹)", "purpose": "किस काम के लिए?", "age": "आपकी उम्र", "district": "ज़िला", "state": "राज्य",
        "yn_title": "कुछ हाँ/नहीं सवाल", "yn": ["हाँ", "नहीं", "पता नहीं"],
        "q_udyam": "उद्यम पर पंजीकृत?", "q_default": "कोई लोन डिफ़ॉल्ट में?", "q_prior": "पिछले 5 साल में PMEGP / स्वनिधि / मुद्रा लोन?",
        "q_trained": "पीएम विश्वकर्मा की बुनियादी ट्रेनिंग की?", "q_tarun": "पहले मुद्रा तरुण लोन चुकाया?",
        "opt_h": "वैकल्पिक: कुछ योजनाओं के लिए क़ानूनन ज़रूरी जानकारी (स्कोर में कभी इस्तेमाल नहीं)",
        "gender": "लिंग", "genders": ["नहीं बताना", "महिला", "पुरुष", "अन्य"], "category": "वर्ग",
        "cats": ["नहीं बताना", "सामान्य", "OBC", "SC", "ST"], "area": "इलाक़ा", "areas": ["नहीं बताना", "शहरी", "ग्रामीण"],
        "docs_h": "आपके दस्तावेज़", "stmt": "बैंक या UPI स्टेटमेंट (PDF या CSV)", "quote": "कोटेशन या बिल की फ़ोटो (वैकल्पिक)",
        "use_sample": "स्टेटमेंट नहीं है? काल्पनिक सैंपल इस्तेमाल करें", "submit": "मेरे विकल्प देखें",
        "quote_read": "**{v}** का कोटेशन पढ़ा: कुल **{t}**", "err": "वह स्टेटमेंट नहीं पढ़ पाया: {e}",
        "profile_h": "आपका स्टेटमेंट क्या दिखाता है", "schemes_h": "आपके लिए योजनाएँ", "score_h": "आपका लोन-तैयारी स्कोर",
        "review_h": "जाँचें और मंज़ूरी दें", "next": "आगे →", "first": "पहले अपने कारोबार की जानकारी भरें।",
        "have_h": "जो आपके पास पहले से है, उस पर टिक करें",
        "have_opts": {"aadhaar": "आधार", "pan": "PAN", "bank_statement": "बैंक स्टेटमेंट", "business_proof": "कारोबार के पते का सबूत",
                      "photo": "फ़ोटो", "udyam": "उद्यम प्रमाणपत्र", "quotation": "कोटेशन"},
    },
}


def _go(step: int):
    st.session_state.g_step = step
    st.rerun()


def _yn_index(v):
    return 0 if v is True else 1 if v is False else 2


def render() -> None:
    t, c = T[lang()], case()
    ss = st.session_state
    ss.setdefault("g_step", 0)
    st.markdown(f"## {t['title']}")
    labels = [f"{i + 1} · {s}" for i, s in enumerate(t["steps"])]
    if ss.get("g_consent"):
        pick = st.segmented_control("step", labels, default=labels[ss.g_step], label_visibility="collapsed", key=f"seg_{ss.g_step}_{lang()}")
        if pick and labels.index(pick) != ss.g_step:
            _go(labels.index(pick))
    step = ss.g_step

    if step == 0:
        st.markdown(f"#### {t['consent_h']}")
        st.markdown(f"<div class='cs-card'>{t['consent_body']}</div>", unsafe_allow_html=True)
        a1 = st.checkbox(t["c1"])
        a2 = st.checkbox(t["c2"])
        if st.button(t["continue"], type="primary", disabled=not (a1 and a2)):
            ss.g_consent = True
            _go(1)
        return

    if not ss.get("g_consent"):
        _go(0)

    if step == 1:
        if st.button(t["demo"]):
            c.applicant = Applicant(business_name="Sunita Tailoring Works", owner_name="Sunita", trade="tailor",
                                    sector="manufacturing", enterprise_size="micro", is_new_unit=False, years_in_business=4,
                                    loan_amount=300000, loan_purpose="Two sewing machines and fabric stock before wedding season",
                                    age=34, has_default=False, udyam_registered=False, vishwakarma_trained=None,
                                    prior_scheme_loan=False, district="Bhilwara", state="Rajasthan")
            c.txns, c.statement_name = read_statement(SAMPLE), "sample statement"
            c.have_docs |= {"bank_statement"}
            c.analysis = analyze(c.applicant, c.txns, c.lang)
            _go(2)
        a = c.applicant
        tl, sl = TRADE_LABELS[lang()], SECTOR_LABELS[lang()]
        with st.form("biz"):
            c1, c2 = st.columns(2)
            owner = c1.text_input(t["name"], a.owner_name)
            business = c2.text_input(t["business"], a.business_name)
            trade = c1.selectbox(t["trade"], TRADES, format_func=tl.get, index=TRADES.index(a.trade) if a.trade in TRADES else 0)
            sector = c2.selectbox(t["sector"], SECTORS, format_func=sl.get, index=SECTORS.index(a.sector) if a.sector in SECTORS else 0)
            new = c1.radio(t["new"], t["new_opts"], index=1 if a.is_new_unit else 0, horizontal=True) == t["new_opts"][1]
            years = c2.number_input(t["years"], 0.0, 60.0, float(a.years_in_business or 0), 0.5)
            amount = c1.number_input(t["amount"], 10000, 10000000, int(a.loan_amount or 300000), 10000)
            purpose = c2.text_input(t["purpose"], a.loan_purpose)
            age = c1.number_input(t["age"], 18, 90, int(a.age or 30))
            district = c2.text_input(t["district"], a.district)
            state_name = c1.text_input(t["state"], a.state)
            st.markdown(f"**{t['yn_title']}**")
            yn_vals = [True, False, None]
            q = st.columns(5)
            udyam = yn_vals[t["yn"].index(q[0].radio(t["q_udyam"], t["yn"], index=_yn_index(a.udyam_registered)))]
            default = yn_vals[t["yn"].index(q[1].radio(t["q_default"], t["yn"], index=_yn_index(a.has_default)))]
            prior = yn_vals[t["yn"].index(q[2].radio(t["q_prior"], t["yn"], index=_yn_index(a.prior_scheme_loan)))]
            trained = yn_vals[t["yn"].index(q[3].radio(t["q_trained"], t["yn"], index=_yn_index(a.vishwakarma_trained)))]
            tarun = yn_vals[t["yn"].index(q[4].radio(t["q_tarun"], t["yn"], index=_yn_index(a.prior_tarun_repaid)))]
            with st.expander(t["opt_h"]):
                g1, g2, g3 = st.columns(3)
                gender = [None, "female", "male", "other"][t["genders"].index(g1.selectbox(t["gender"], t["genders"]))]
                cat = [None, "general", "obc", "sc", "st"][t["cats"].index(g2.selectbox(t["category"], t["cats"]))]
                area = [None, "urban", "rural"][t["areas"].index(g3.selectbox(t["area"], t["areas"]))]
            st.markdown(f"**{t['docs_h']}**")
            d1, d2 = st.columns(2)
            stmt = d1.file_uploader(t["stmt"], type=["pdf", "csv"])
            quote = d2.file_uploader(t["quote"], type=["jpg", "jpeg", "png", "webp"])
            use_sample = st.checkbox(t["use_sample"], value=c.txns is None)
            go = st.form_submit_button(t["submit"], type="primary")
        if go:
            try:
                if stmt is not None:
                    c.txns, c.statement_name = read_statement_file(stmt.name, stmt.getvalue()), stmt.name
                    c.have_docs.add("bank_statement")
                elif use_sample or c.txns is None:
                    c.txns, c.statement_name = read_statement(SAMPLE), "sample statement"
                    c.have_docs.add("bank_statement")
            except Exception as e:
                st.error(t["err"].format(e=e))
                st.stop()
            if quote is not None:
                reading = read_quotation_image(quote.getvalue())
                if reading.total:
                    c.quotation = reading
                    c.have_docs.add("quotation")
                    st.toast(t["quote_read"].format(v=reading.vendor.title(), t=_inr(reading.total)))
            c.applicant = Applicant(business_name=business, owner_name=owner, trade=trade, sector=sector, enterprise_size="micro",
                                    is_new_unit=new, years_in_business=years, loan_amount=int(amount), loan_purpose=purpose,
                                    age=int(age), has_default=default, udyam_registered=udyam, vishwakarma_trained=trained,
                                    prior_scheme_loan=prior, prior_tarun_repaid=tarun, gender=gender, social_category=cat,
                                    area=area, district=district, state=state_name)
            c.analysis = analyze(c.applicant, c.txns, c.lang)
            _go(2)
        return

    if c.txns is None or not c.applicant.loan_amount:
        st.info(t["first"])
        return
    if c.analysis is None or c.analysis.lang != c.lang:
        c.analysis = analyze(c.applicant, c.txns, c.lang)
    an = c.analysis

    if step == 2:
        st.markdown(f"#### {t['profile_h']}")
        render_profile(an.profile, key="g")
    elif step == 3:
        st.markdown(f"#### {t['schemes_h']}")
        render_schemes(an, c.applicant.loan_amount)
    elif step == 4:
        st.markdown(f"#### {t['score_h']}")
        render_score(an.score)
    elif step == 5:
        st.markdown(f"#### {t['review_h']}")
        st.markdown(f"<div class='cs-card' style='border-left:6px solid #16233F'>"
                    f"{md_bold(template_summary(an.results, an.plan, an.score, c.lang))}</div>", unsafe_allow_html=True)
        opts = t["have_opts"]
        have = set(st.multiselect(t["have_h"], list(opts), format_func=opts.get, default=sorted(c.have_docs & set(opts))))
        c.have_docs = have | ({"quotation"} if c.quotation else set())
        pkg = build_package(c.applicant, c.txns, c.have_docs)

        def submit():
            ref = store.submit(**submission_kwargs(pkg))
            c.submitted_ref = ref
            return ref
        render_application(pkg, key="guided", on_submit=submit)
        return
    if st.button(t["next"], type="primary"):
        _go(step + 1)
