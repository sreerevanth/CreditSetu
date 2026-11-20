"""Chat with Setu: the agent experience."""

from __future__ import annotations

import streamlit as st

from creditsetu.agent.claude_agent import ClaudeAgent
from creditsetu.agent.offline import OfflineAgent
from creditsetu.documents import read_quotation_image, read_statement_file
from ui.common import api_key, case, lang, render_application, render_profile, render_schemes, render_score, u

TEXT = {
    "en": {"title": "Ask Setu", "sub": "Chat in English, Hindi or Hinglish. Attach a bank statement (PDF/CSV) or a photo of a quotation with the 📎 button.",
           "placeholder": "Type here… e.g. “I'm a tailor and need ₹3 lakh”", "reading": "Reading your document…",
           "bad_file": "I couldn't read that file: {e}", "you_sent": "📎 Sent {name}", "thinking": "Setu is thinking…"},
    "hi": {"title": "सेतु से पूछें", "sub": "हिंदी, अंग्रेज़ी या हिंग्लिश में बात करें। 📎 बटन से बैंक स्टेटमेंट (PDF/CSV) या कोटेशन की फ़ोटो लगाएँ।",
           "placeholder": "यहाँ लिखें… जैसे “मैं दर्जी हूँ, ₹3 लाख चाहिए”", "reading": "आपका दस्तावेज़ पढ़ रहे हैं…",
           "bad_file": "वह फ़ाइल नहीं पढ़ पाया: {e}", "you_sent": "📎 {name} भेजा", "thinking": "सेतु सोच रहा है…"},
}


def _agent():
    c = case()
    if api_key():
        import os
        os.environ["ANTHROPIC_API_KEY"] = api_key()
        return ClaudeAgent(c), "claude"
    return OfflineAgent(c), "offline"


def _push(replies: list) -> None:
    """Attach a snapshot of the analysis/package to card replies so old cards don't change later."""
    c = case()
    for r in replies:
        r = dict(r)
        if r["kind"] in ("profile", "schemes", "score"):
            r["analysis"] = c.analysis
            r["amount"] = c.applicant.loan_amount
        if r["kind"] == "application":
            r["package"] = c.package
        st.session_state.chat.append({"role": "assistant", "reply": r})


def _user(text: str) -> None:
    st.session_state.chat.append({"role": "user", "reply": {"kind": "text", "text": text, "quick": []}})


def _render_reply(i: int, r: dict, agent) -> None:
    kind = r["kind"]
    if r.get("text"):
        st.markdown(r["text"])
    if kind == "profile" and r.get("analysis"):
        render_profile(r["analysis"].profile, key=f"p{i}")
    elif kind == "schemes" and r.get("analysis"):
        render_schemes(r["analysis"], r.get("amount") or 0)
    elif kind == "score" and r.get("analysis"):
        render_score(r["analysis"].score)
    elif kind == "submitted":
        if st.button("📦 " + u("nav_track"), key=f"trk{i}"):
            st.switch_page(st.session_state["_pages"]["track"])
    elif kind == "application" and r.get("package"):
        def submit():
            replies = agent.offline.approve_and_submit() if hasattr(agent, "offline") else agent.approve_and_submit()
            _push(replies)
            return case().submitted_ref
        render_application(r["package"], key=f"chat{i}", on_submit=submit)


def render() -> None:
    t = TEXT[lang()]
    agent, mode = _agent()
    st.markdown(f"## {t['title']} <span class='mode-badge'>{u('mode_claude') if mode == 'claude' else u('mode_offline')}</span>",
                unsafe_allow_html=True)
    st.caption(t["sub"])

    if "chat" not in st.session_state:
        st.session_state.chat = []
    if not st.session_state.chat:
        st.session_state.chat_lang = lang()
        base = agent.offline if mode == "claude" else agent
        _push(base.start())
        if st.session_state.pop("chat_autostart", None) == "demo":
            _user("Show me the demo (Sunita)" if lang() == "en" else "डेमो दिखाइए (सुनीता)")
            _push(base.load_demo())

    # incoming quick reply
    queued = st.session_state.pop("chat_queued", None)

    for i, msg in enumerate(st.session_state.chat):
        with st.chat_message(msg["role"], avatar="🌉" if msg["role"] == "assistant" else "🧵"):
            _render_reply(i, msg["reply"], agent)

    last = st.session_state.chat[-1] if st.session_state.chat else None
    if last and last["role"] == "assistant" and last["reply"].get("quick"):
        cols = st.columns(min(4, len(last["reply"]["quick"])))
        for j, q in enumerate(last["reply"]["quick"]):
            if cols[j % len(cols)].button(q, key=f"q_{len(st.session_state.chat)}_{j}", width="stretch"):
                st.session_state.chat_queued = q
                st.rerun()

    prompt = st.chat_input(t["placeholder"], accept_file=True, file_type=["pdf", "csv", "jpg", "jpeg", "png", "webp"])
    text, files = None, []
    if prompt is not None:
        text = (prompt.text or "").strip() if hasattr(prompt, "text") else str(prompt)
        files = list(getattr(prompt, "files", []) or [])
    if queued:
        text = queued

    if files:
        for f in files:
            _user(t["you_sent"].format(name=f.name))
            data = f.getvalue()
            with st.spinner(t["reading"]):
                try:
                    base = agent.offline if mode == "claude" else agent
                    if f.name.lower().endswith((".pdf", ".csv")):
                        txns = read_statement_file(f.name, data)
                        _push(base.statement_loaded(txns, f.name))
                    else:
                        reading = read_quotation_image(data)
                        _push(base.quotation_loaded(reading))
                except Exception as e:  # show a friendly error, keep the chat alive
                    _push([{"kind": "text", "text": t["bad_file"].format(e=e), "quick": []}])
    if text:
        _user(text)
        with st.spinner(t["thinking"]):
            _push(agent.handle(text))
    if files or text:
        st.rerun()
