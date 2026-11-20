"""Track an application: status and the bank's notes, for the owner."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from creditsetu import store
from creditsetu.score import _inr
from ui.common import case, lang

T = {
    "en": {"title": "Track your application", "ref": "Reference number", "find": "Show status", "none": "No application found with that reference.",
           "hint": "Your reference looks like CS-2611-12345. You get it after you approve and send an application.",
           "amount": "Amount", "score": "Readiness score", "bank_note": "Note from the bank", "timeline": "Timeline",
           "demo_hint": "Try one from the demo queue:"},
    "hi": {"title": "अपना आवेदन ट्रैक करें", "ref": "रेफ़रेंस नंबर", "find": "स्टेटस देखें", "none": "इस रेफ़रेंस से कोई आवेदन नहीं मिला।",
           "hint": "आपका रेफ़रेंस CS-2611-12345 जैसा दिखता है। यह आवेदन मंज़ूर करके भेजने के बाद मिलता है।",
           "amount": "रक़म", "score": "तैयारी स्कोर", "bank_note": "बैंक का संदेश", "timeline": "समयरेखा",
           "demo_hint": "डेमो कतार से कोई आज़माएँ:"},
}
STEPS = ["received", "under_review", "documents_requested", "sanctioned"]


def _when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return iso


def render() -> None:
    t = T[lang()]
    labels = store.STATUS_LABELS[lang()]
    st.markdown(f"## {t['title']}")
    default = case().submitted_ref or st.session_state.get("track_ref", "")
    c1, c2 = st.columns([3, 1])
    ref = c1.text_input(t["ref"], default, placeholder="CS-2611-12345", label_visibility="collapsed")
    c2.button(t["find"], type="primary", width="stretch")
    if not ref:
        st.caption(t["hint"])
        try:
            demo = [r["ref"] for r in store.list_all()][:3]
        except Exception:
            demo = []
        if demo:
            st.caption(t["demo_hint"] + " " + " · ".join(f"`{d}`" for d in demo))
        return
    app = store.get(ref)
    if not app:
        st.warning(t["none"])
        return
    st.session_state.track_ref = app["ref"]
    status = app["status"]
    st.markdown(f"<div class='cs-band'><h3>{app['business_name']} · {app['ref']}</h3>"
                f"<p>{t['amount']}: {_inr(app['amount'])} · {t['score']}: {app['score']}/100</p></div>", unsafe_allow_html=True)
    # progress
    reached = {e["status"] for e in app["events"]}
    current = STEPS.index(status) if status in STEPS else len(STEPS) - 1
    cols = st.columns(len(STEPS))
    for i, (col, s) in enumerate(zip(cols, STEPS)):
        done = s in reached or (i < current and not (s == "documents_requested" and s not in reached))
        if s == "sanctioned" and status == "not_sanctioned":
            col.markdown(f"<span class='pill not_sanctioned'>✘ {labels['not_sanctioned']}</span>", unsafe_allow_html=True)
        else:
            col.markdown(f"<span class='pill {s if done else ''}'>{'●' if done else '○'} {labels[s]}</span>", unsafe_allow_html=True)
    if app.get("officer_note"):
        st.markdown(f"<div class='cs-card' style='border-left:6px solid #E8A33D'><b>{t['bank_note']}:</b> {app['officer_note']}</div>",
                    unsafe_allow_html=True)
    st.markdown(f"#### {t['timeline']}")
    html = "".join(f"<div class='ev'><span class='pill {e['status']}'>{labels.get(e['status'], e['status'])}</span> "
                   f"<span class='when'>{_when(e['at'])}</span><div>{e['note'] or ''}</div></div>"
                   for e in reversed(app["events"]))
    st.markdown(f"<div class='timeline'>{html}</div>", unsafe_allow_html=True)
