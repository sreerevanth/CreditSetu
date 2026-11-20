"""Bank officer workspace: the lender side of CreditSetu."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from creditsetu import demo_seed, store
from creditsetu.score import _inr
from ui.common import lang

T = {
    "en": {
        "title": "Bank officer workspace", "branch": "Demo Co-operative Bank · Bhilwara branch (fictional) · demo mode, no login",
        "k_files": "Files in queue", "k_new": "New today", "k_amount": "Total requested", "k_score": "Average readiness",
        "k_complete": "Complete files",
        "queue": "Incoming owner-approved files", "filter": "Filter by status", "all": "All",
        "cols": {"ref": "Reference", "business_name": "Business", "trade": "Trade", "district": "District", "amount": "Amount",
                 "score": "Score", "status": "Status", "missing_docs": "Missing docs", "created_at": "Received"},
        "pick": "Select a file in the table to open it.",
        "summary": "Summary", "cashflow": "Cash flow", "schemes": "Schemes & sources", "docs": "Documents", "full": "Full application",
        "owner_ok": "✅ Owner reviewed and approved this file before sending.",
        "plan": "Requested plan", "score": "Readiness score", "why": "Score factors",
        "action": "Update status", "status": "Status", "note": "Note to the owner (they see this)", "save": "Save and notify owner",
        "saved": "Updated. The owner sees this on their tracking page.",
        "reset": "Reset demo queue", "reset_done": "Demo queue reset.",
        "privacy": "Gender and caste category are not shared with the bank unless the owner applies under a scheme that requires them by law.",
        "avg_in": "Avg monthly income", "surplus": "Avg monthly surplus", "digital": "Digital share", "bounces": "Bounced payments",
    },
    "hi": {
        "title": "बैंक अधिकारी वर्कस्पेस", "branch": "डेमो को-ऑपरेटिव बैंक · भीलवाड़ा शाखा (काल्पनिक) · डेमो मोड, लॉगिन नहीं",
        "k_files": "कतार में फ़ाइलें", "k_new": "आज नई", "k_amount": "कुल माँगी रक़म", "k_score": "औसत तैयारी स्कोर",
        "k_complete": "पूरी फ़ाइलें",
        "queue": "मालिक द्वारा मंज़ूर आने वाली फ़ाइलें", "filter": "स्टेटस से छाँटें", "all": "सभी",
        "cols": {"ref": "रेफ़रेंस", "business_name": "कारोबार", "trade": "काम", "district": "ज़िला", "amount": "रक़म",
                 "score": "स्कोर", "status": "स्टेटस", "missing_docs": "बाक़ी दस्तावेज़", "created_at": "प्राप्त"},
        "pick": "फ़ाइल खोलने के लिए टेबल में उसे चुनें।",
        "summary": "सारांश", "cashflow": "नकदी प्रवाह", "schemes": "योजनाएँ और स्रोत", "docs": "दस्तावेज़", "full": "पूरा आवेदन",
        "owner_ok": "✅ मालिक ने भेजने से पहले इस फ़ाइल को जाँचा और मंज़ूर किया।",
        "plan": "माँगी गई योजना", "score": "तैयारी स्कोर", "why": "स्कोर के कारण",
        "action": "स्टेटस अपडेट करें", "status": "स्टेटस", "note": "मालिक के लिए संदेश (उन्हें दिखेगा)", "save": "सेव करें और मालिक को बताएँ",
        "saved": "अपडेट हो गया। मालिक इसे अपने ट्रैकिंग पेज पर देखेंगे।",
        "reset": "डेमो कतार रीसेट करें", "reset_done": "डेमो कतार रीसेट हो गई।",
        "privacy": "लिंग और जाति वर्ग बैंक को तभी दिखते हैं जब मालिक किसी ऐसी योजना में आवेदन करे जिसमें क़ानूनन इनकी ज़रूरत हो।",
        "avg_in": "औसत मासिक आय", "surplus": "औसत मासिक बचत", "digital": "डिजिटल हिस्सा", "bounces": "बाउंस भुगतान",
    },
}


def _ago(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    days = (datetime.now() - d).days
    if days <= 0:
        return d.strftime("Today %H:%M") if lang() == "en" else d.strftime("आज %H:%M")
    return f"{days}d ago" if lang() == "en" else f"{days} दिन पहले"


def render() -> None:
    t = T[lang()]
    labels = store.STATUS_LABELS[lang()]
    demo_seed.seed()
    head, btn = st.columns([4, 1])
    head.markdown(f"## 🏦 {t['title']}")
    head.caption(t["branch"])
    if btn.button(t["reset"], width="stretch"):
        demo_seed.seed(force=True)
        st.session_state.pop("officer_sel", None)
        st.toast(t["reset_done"])
        st.rerun()

    apps = store.list_all()
    today = datetime.now().date().isoformat()
    k = st.columns(5)
    kpis = [(len(apps), t["k_files"]), (sum(a["created_at"][:10] == today for a in apps), t["k_new"]),
            (_inr(sum(a["amount"] or 0 for a in apps)), t["k_amount"]),
            (round(sum(a["score"] or 0 for a in apps) / len(apps)) if apps else 0, t["k_score"]),
            (f"{sum(a['missing_docs'] == 0 for a in apps)}/{len(apps)}", t["k_complete"])]
    for col, (v, l) in zip(k, kpis):
        col.markdown(f"<div class='cs-stat'><div class='v'>{v}</div><div class='l'>{l}</div></div>", unsafe_allow_html=True)

    st.markdown(f"#### {t['queue']}")
    status_filter = st.segmented_control(t["filter"], [t["all"]] + [labels[s] for s in store.STATUSES], default=t["all"],
                                         label_visibility="collapsed")
    if status_filter and status_filter != t["all"]:
        key = next(s for s in store.STATUSES if labels[s] == status_filter)
        apps = [a for a in apps if a["status"] == key]
    df = pd.DataFrame([{**{c: a[c] for c in t["cols"]}, "status": labels[a["status"]], "amount": _inr(a["amount"] or 0),
                        "created_at": _ago(a["created_at"]), "trade": (a["trade"] or "").replace("_", " ")} for a in apps])
    if df.empty:
        st.info("—")
        return
    df = df.rename(columns=t["cols"])
    event = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                         column_config={t["cols"]["score"]: st.column_config.ProgressColumn(t["cols"]["score"], min_value=0, max_value=100, format="%d")},
                         key="queue_table")
    rows = event.selection.rows if event and event.selection else []
    if rows:
        st.session_state.officer_sel = apps[rows[0]]["ref"]
    ref = st.session_state.get("officer_sel")
    if not ref or not any(a["ref"] == ref for a in apps):
        st.caption(t["pick"])
        return

    app = store.get(ref)
    f = app["file"]
    cf, sc = f.get("cash_flow", {}), f.get("readiness_score", {})
    st.markdown(f"<div class='cs-band'><h3>{app['business_name']} · {app['owner_name']} · {app['ref']}</h3>"
                f"<p>{(app['trade'] or '').replace('_', ' ').title()} · {app['district']}, {app['state']} · {_inr(app['amount'])} · "
                f"<span class='pill {app['status']}'>{labels[app['status']]}</span></p></div>", unsafe_allow_html=True)
    st.caption(t["owner_ok"] + " " + t["privacy"])

    tabs = st.tabs([t["summary"], t["cashflow"], t["schemes"], t["docs"], t["full"]])
    with tabs[0]:
        a, b = st.columns([1, 2])
        a.markdown(f"<div class='cs-card'><div class='score-big'>{sc.get('total', '–')}</div><div class='small'>{t['score']} · {sc.get('band', '')}</div>"
                   f"<div class='small' style='margin-top:8px'>EMI ≈ {_inr(sc.get('emi', 0))}/month</div></div>", unsafe_allow_html=True)
        plan_rows = "".join(f"<li><b>{p['name']}</b>: {_inr(p['amount'])} @ ~{p['rate']:g}% · {p['tenure_months']} months</li>" for p in app["plan"])
        b.markdown(f"<div class='cs-card'><b>{t['plan']}</b><ul>{plan_rows}</ul></div>", unsafe_allow_html=True)
        html = "".join(f"<div class='factor'><div class='fh'><b>{x['name']}</b><span>{x['points']:g} / {x['max_points']:g}</span></div>"
                       f"<div class='bar'><div style='width:{max(0, x['points']) / x['max_points'] * 100:.0f}%'></div></div>"
                       f"<div class='fm'>{x['measured']}</div></div>" for x in sc.get("factors", []))
        st.markdown(f"<div class='cs-card'><b>{t['why']}</b>{html}</div>", unsafe_allow_html=True)
    with tabs[1]:
        k = st.columns(4)
        for col, (v, l) in zip(k, [(_inr(cf.get("avg_monthly_inflow", 0)), t["avg_in"]), (_inr(cf.get("avg_monthly_surplus", 0)), t["surplus"]),
                                   (f"{round(cf.get('digital_share', 0) * 100)}%", t["digital"]), (cf.get("bounced_count", 0), t["bounces"])]):
            col.markdown(f"<div class='cs-stat'><div class='v'>{v}</div><div class='l'>{l}</div></div>", unsafe_allow_html=True)
        if cf.get("monthly"):
            mdf = pd.DataFrame(cf["monthly"]).set_index("month")
            st.bar_chart(mdf, color=["#E8A33D", "#16233F"], height=280, stack=False)
    with tabs[2]:
        for r in f.get("scheme_results", []):
            if r["status"] == "not_fit":
                continue
            crit = "".join(f"<div class='crit {c['status']}'>{c['text']} <a href='{c['source_url']}' target='_blank'>[{c['source_title']}]</a></div>"
                           for c in r["criteria"])
            st.markdown(f"<div class='cs-card'><span class='pill {r['status']}'>{r['status'].replace('_', ' ')}</span>"
                        f"<h4 style='margin:6px 0'>{r['name']}</h4>{crit}</div>", unsafe_allow_html=True)
    with tabs[3]:
        icons = {"have": "✅", "missing": "⬜", "ready": "✨"}
        for d in app["documents"]:
            st.markdown(f"{icons.get(d['status'], '•')} {d['label']}")
    with tabs[4]:
        st.markdown(app["draft_md"] or "")
        st.download_button("Download JSON loan file", app["file_json"] or "{}", file_name=f"{app['ref']}.json")

    st.markdown(f"#### {t['action']}")
    with st.form(f"act_{ref}"):
        c1, c2 = st.columns([1, 2])
        new_status = c1.selectbox(t["status"], store.STATUSES, index=store.STATUSES.index(app["status"]), format_func=labels.get)
        note = c2.text_input(t["note"], app.get("officer_note") or "")
        if st.form_submit_button(t["save"], type="primary"):
            store.update_status(ref, new_status, note)
            st.toast(t["saved"])
            st.rerun()
