"""Landing page."""

from __future__ import annotations

import streamlit as st

from creditsetu import store
from ui.common import lang

TEXT = {
    "en": {
        "eyebrow": "FOR INDIA'S 7 CRORE+ SMALL BUSINESSES",
        "title": "Credit<span class='acc'>Setu</span>: the bridge to formal credit",
        "sub": "Tell Setu about your business and share your bank statement. In minutes you get the loans and government schemes you qualify for, each with its official rule, an honest readiness score, and an application you approve.",
        "cta_chat": "💬 Chat with Setu", "cta_demo": "⚡ See the 60-second demo", "cta_guided": "🧭 Guided check",
        "stats": [("70–80%", "of schemes small businesses qualify for are missed"), ("24–36%", "interest charged by moneylenders"),
                  ("₹30 lakh cr", "MSME credit gap (SIDBI)"), ("5%", "PM Vishwakarma rate many artisans never hear about")],
        "how": "How it works",
        "steps": [("1 · Talk", "Chat in English, Hindi or Hinglish. Say what you do and how much you need."),
                  ("2 · Share", "Upload a bank statement (PDF/CSV) and a quotation photo. Read on-device, never stored."),
                  ("3 · Understand", "See every scheme you fit, with the official rule linked, plus an explained score."),
                  ("4 · Approve", "Review the ready-made application. Nothing goes to the bank until you press Approve.")],
        "trust": "Built to be trusted",
        "trust_items": [("🔗 Every claim cited", "Eligibility comes from encoded scheme rules with official sources, never from an AI guess."),
                        ("⚖️ Fair by design", "The score can't see gender, caste, religion or region. A test checks it on every change."),
                        ("🔒 Consent first", "Data stays in your session. You approve every application."),
                        ("🏦 Ready for banks", "Officers get complete, standard files with a cash-flow summary and scheme fit.")],
        "banks": "For banks and NBFCs", "banks_sub": "See the officer workspace: incoming owner-approved files, scores with reasons, documents, and one-click status updates the owner sees.",
        "cta_officer": "🏦 Open the bank officer view",
        "live": "{n} applications in the demo bank queue right now",
        "foot": "Hackathon build · MSME Finance and Compliance · Problem 3.2 · All demo data is synthetic.",
    },
    "hi": {
        "eyebrow": "भारत के 7 करोड़ से ज़्यादा छोटे कारोबारों के लिए",
        "title": "Credit<span class='acc'>Setu</span>: औपचारिक लोन तक पहुँचने का पुल",
        "sub": "सेतु को अपने कारोबार के बारे में बताइए और बैंक स्टेटमेंट दीजिए। कुछ ही मिनटों में आपको वे लोन और सरकारी योजनाएँ मिलेंगी जिनके लिए आप पात्र हैं, हर एक के आधिकारिक नियम के साथ, एक ईमानदार तैयारी स्कोर, और एक आवेदन जिसे आप मंज़ूर करते हैं।",
        "cta_chat": "💬 सेतु से बात करें", "cta_demo": "⚡ 60 सेकंड का डेमो देखें", "cta_guided": "🧭 चरण-दर-चरण जाँच",
        "stats": [("70–80%", "योजनाएँ जिनके लिए छोटे कारोबारी पात्र हैं, छूट जाती हैं"), ("24–36%", "साहूकारों का ब्याज"),
                  ("₹30 लाख करोड़", "MSME लोन की कमी (SIDBI)"), ("5%", "पीएम विश्वकर्मा की ब्याज दर, जिसके बारे में कई कारीगर नहीं जानते")],
        "how": "यह कैसे काम करता है",
        "steps": [("1 · बात करें", "हिंदी, अंग्रेज़ी या हिंग्लिश में बात करें। बताइए आप क्या करते हैं और कितना चाहिए।"),
                  ("2 · साझा करें", "बैंक स्टेटमेंट (PDF/CSV) और कोटेशन की फ़ोटो अपलोड करें। यहीं पढ़ा जाता है, सेव नहीं होता।"),
                  ("3 · समझें", "हर योजना जिसके लिए आप पात्र हैं, आधिकारिक नियम के लिंक के साथ, और समझाया गया स्कोर।"),
                  ("4 · मंज़ूरी दें", "तैयार आवेदन जाँचें। जब तक आप मंज़ूर नहीं करते, बैंक को कुछ नहीं जाता।")],
        "trust": "भरोसे के लिए बनाया गया",
        "trust_items": [("🔗 हर दावे का स्रोत", "पात्रता आधिकारिक स्रोतों वाले योजना नियमों से तय होती है, AI के अनुमान से नहीं।"),
                        ("⚖️ निष्पक्ष", "स्कोर लिंग, जाति, धर्म या इलाक़ा नहीं देख सकता। हर बदलाव पर एक टेस्ट इसे जाँचता है।"),
                        ("🔒 सहमति पहले", "डेटा आपके सेशन में रहता है। हर आवेदन आप मंज़ूर करते हैं।"),
                        ("🏦 बैंक के लिए तैयार", "अधिकारियों को पूरी, एक जैसी फ़ाइल मिलती है, नकदी प्रवाह और योजना के साथ।")],
        "banks": "बैंक और NBFC के लिए", "banks_sub": "अधिकारी का वर्कस्पेस देखें: मालिक द्वारा मंज़ूर फ़ाइलें, कारणों के साथ स्कोर, दस्तावेज़, और एक क्लिक में स्टेटस अपडेट जो मालिक को दिखता है।",
        "cta_officer": "🏦 बैंक अधिकारी व्यू खोलें",
        "live": "डेमो बैंक की कतार में अभी {n} आवेदन हैं",
        "foot": "हैकाथॉन बिल्ड · MSME फ़ाइनेंस और कंप्लायंस · समस्या 3.2 · सारा डेमो डेटा काल्पनिक है।",
    },
}


def render(pages: dict) -> None:
    t = TEXT[lang()]
    st.markdown(f"<div class='cs-hero'><div class='eyebrow'>{t['eyebrow']}</div><h1>{t['title']}</h1><p>{t['sub']}</p></div>",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button(t["cta_chat"], type="primary", width="stretch"):
        st.switch_page(pages["chat"])
    if c2.button(t["cta_demo"], width="stretch"):
        st.session_state.chat_autostart = "demo"
        st.switch_page(pages["chat"])
    if c3.button(t["cta_guided"], width="stretch"):
        st.switch_page(pages["guided"])

    st.markdown("&nbsp;")
    cols = st.columns(4)
    for col, (v, label) in zip(cols, t["stats"]):
        col.markdown(f"<div class='cs-stat'><div class='v'>{v}</div><div class='l'>{label}</div></div>", unsafe_allow_html=True)

    st.markdown(f"### {t['how']}")
    cols = st.columns(4)
    for col, (title, body) in zip(cols, t["steps"]):
        col.markdown(f"<div class='cs-feature'><h4>{title}</h4><div class='small'>{body}</div></div>", unsafe_allow_html=True)

    st.markdown(f"### {t['trust']}")
    cols = st.columns(4)
    for col, (title, body) in zip(cols, t["trust_items"]):
        col.markdown(f"<div class='cs-feature'><h4>{title}</h4><div class='small'>{body}</div></div>", unsafe_allow_html=True)

    st.markdown("&nbsp;")
    try:
        n = store.count()
    except Exception:
        n = 0
    st.markdown(f"<div class='cs-band'><h3>{t['banks']}</h3><p>{t['banks_sub']}</p>"
                f"<p style='color:#E8A33D;margin-top:8px'>● {t['live'].format(n=n)}</p></div>", unsafe_allow_html=True)
    if st.button(t["cta_officer"]):
        st.switch_page(pages["officer"])
    st.caption(t["foot"])
