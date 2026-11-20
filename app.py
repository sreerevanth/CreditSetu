"""CreditSetu – the bridge to formal credit for India's small businesses.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="CreditSetu", page_icon="🌉", layout="wide")

from creditsetu import demo_seed  # noqa: E402
from ui import chat, guided, home, officer, track  # noqa: E402
from ui.common import CSS, UI, api_key, lang  # noqa: E402

st.markdown(CSS, unsafe_allow_html=True)
st.session_state.setdefault("lang", "en")

# Make sure the bank queue has demo files from the first visit.
try:
    demo_seed.seed()
except Exception:
    pass

with st.sidebar:
    choice = st.radio(UI["en"]["lang"], ["English", "हिन्दी"], horizontal=True,
                      index=1 if st.session_state.lang == "hi" else 0)
    st.session_state.lang = "hi" if choice == "हिन्दी" else "en"

u = UI[lang()]
pages = {}
pages["home"] = st.Page(lambda: home.render(pages), title=u["nav_home"], icon="🏠", default=True)
pages["chat"] = st.Page(chat.render, title=u["nav_chat"], icon="💬", url_path="chat")
pages["guided"] = st.Page(guided.render, title=u["nav_guided"], icon="🧭", url_path="guided")
pages["track"] = st.Page(track.render, title=u["nav_track"], icon="📦", url_path="track")
pages["officer"] = st.Page(officer.render, title=u["nav_officer"], icon="🏦", url_path="bank")
st.session_state["_pages"] = pages
nav = st.navigation(list(pages.values()), position="top")
st.logo("assets/logo.svg", size="large", icon_image="assets/icon.svg")

with st.sidebar:
    st.markdown("---")
    with st.expander(u["ai_mode"]):
        st.caption(u["ai_help"])
        key = st.text_input(u["ai_key"], type="password", value=st.session_state.get("anthropic_key", ""))
        st.session_state.anthropic_key = key.strip()
        st.markdown(f"<span class='mode-badge'>{u['mode_claude'] if api_key() else u['mode_offline']}</span>",
                    unsafe_allow_html=True)
    st.caption(u["privacy_note"])
    if st.button(u["reset"], width="stretch"):
        keep = {"lang": st.session_state.lang}
        st.session_state.clear()
        st.session_state.update(keep)
        st.rerun()

nav.run()
