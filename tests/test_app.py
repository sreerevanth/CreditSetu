"""UI smoke tests: every page renders, the chat demo reaches results, and the officer
dashboard opens with seeded files."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDITSETU_DB", str(tmp_path / "ui.db"))
    monkeypatch.chdir(ROOT)


def test_home_renders():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception
    labels = [b.label for b in at.button]
    assert any("Chat with Setu" in l for l in labels)


@pytest.mark.parametrize("page", ["chat", "guided", "track", "officer"])
def test_page_renders(page):
    def script(page_name):
        import sys
        import streamlit as st
        sys.path.insert(0, ".")
        st.session_state.setdefault("lang", "en")
        st.session_state.setdefault("_pages", {})
        mod = __import__(f"ui.{page_name}", fromlist=["render"])
        mod.render()
    at = AppTest.from_function(script, args=(page,), default_timeout=60).run()
    assert not at.exception, at.exception


def test_chat_demo_reaches_results_in_hindi_and_english():
    def script():
        import sys
        import streamlit as st
        sys.path.insert(0, ".")
        st.session_state.setdefault("_pages", {})
        from ui import chat
        chat.render()
    for lang, expect in (("en", "MUDRA Kishore"), ("hi", "मुद्रा किशोर")):
        at = AppTest.from_function(script, default_timeout=60)
        at.session_state["lang"] = lang
        at.session_state["chat_autostart"] = "demo"
        at.run()
        assert not at.exception
        text = " ".join(str(m.value) for m in at.markdown)
        assert expect in text, lang


def test_officer_queue_is_seeded():
    def script():
        import sys
        import streamlit as st
        sys.path.insert(0, ".")
        st.session_state.setdefault("lang", "en")
        from ui import officer
        officer.render()
    at = AppTest.from_function(script, default_timeout=60).run()
    assert not at.exception
    from creditsetu import store
    assert store.count() >= 6
