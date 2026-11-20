"""Smoke test: the Streamlit app runs through every step with the demo data."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_demo_flow_runs_without_errors():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    at.checkbox[0].check()
    at.checkbox[1].check()
    at.run()                            # "Continue" is enabled only after both consents
    next(b for b in at.button if b.label == "Continue").click().run()
    assert not at.exception
    assert at.session_state.consent is True
    demo = next(b for b in at.button if "Sunita" in b.label)
    demo.click().run()
    assert not at.exception
    for step in range(2, 6):
        at.session_state.step = step
        at.run()
        assert not at.exception, step
    assert "MUDRA Kishore" in str([m.value for m in at.markdown])
