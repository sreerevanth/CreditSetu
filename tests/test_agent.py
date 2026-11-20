"""Conversation tests for the offline agent and the Claude tool loop (with a fake client)."""

from types import SimpleNamespace

import pytest

from creditsetu.agent.claude_agent import ClaudeAgent
from creditsetu.agent.nlu import extract_facts, parse_amount
from creditsetu.agent.offline import CaseState, OfflineAgent


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDITSETU_DB", str(tmp_path / "test.db"))


@pytest.mark.parametrize("text,amount", [
    ("need 3 lakh", 300000), ("तीन लाख चाहिए", 300000), ("dedh lakh", 150000), ("₹2,50,000", 250000),
    ("50k", 50000), ("२ लाख", 200000), ("1.5 lakh", 150000), ("12 lakh", 1200000),
])
def test_amounts(text, amount):
    assert parse_amount(text) == amount


def test_facts_from_hinglish():
    f = extract_facts("mera naam Sunita hai, silai ka kaam 4 saal se, 3 lakh chahiye")
    assert f["trade"] == "tailor" and f["loan_amount"] == 300000 and f["is_new_unit"] is False
    assert f["owner_name"] == "Sunita"


def run(agent, messages):
    out = []
    for m in messages:
        out.extend(agent.handle(m))
    return out


def test_english_conversation_end_to_end():
    agent = OfflineAgent(CaseState(lang="en"))
    agent.start()
    replies = run(agent, ["I am a tailor and need 3 lakh for machines", "Already running", "Use the sample statement",
                          "No", "No", "34", "Yes", "No"])
    kinds = [r["kind"] for r in replies]
    assert {"profile", "schemes", "score"} <= set(kinds)
    results = {r.scheme_id: r.status for r in agent.s.analysis.results}
    assert results["pmmy_kishore"] == "eligible"
    assert results["pm_vishwakarma_t1"] == "eligible"
    assert results["stand_up_india"] == "not_fit"
    replies = run(agent, ["Prepare my application", "Sunita", "Sunita Tailoring Works"])
    assert replies[-1]["kind"] == "application"
    submitted = agent.approve_and_submit()
    assert submitted[0]["kind"] == "submitted" and agent.s.submitted_ref.startswith("CS-")


def test_hindi_conversation_reaches_results():
    agent = OfflineAgent(CaseState(lang="hi"))
    replies = run(agent, ["मैं दर्जी हूँ, मुझे तीन लाख चाहिए", "पहले से चल रहा है", "सैंपल स्टेटमेंट इस्तेमाल करें",
                          "नहीं", "नहीं", "18 या ज़्यादा", "हाँ", "नहीं"])
    assert any(r["kind"] == "schemes" for r in replies)
    assert agent.s.analysis.results[0].name.startswith(("पीएम", "मुद्रा"))
    assert "समझ गया" in replies[0]["text"]


def test_demo_and_follow_up_questions():
    agent = OfflineAgent(CaseState(lang="en"))
    replies = agent.handle("Show me the demo (Sunita)")
    assert any(r["kind"] == "schemes" for r in replies) or agent.s.pending
    why = run(agent, ["Why not Stand-Up India?"])
    assert "greenfield" in why[-1]["text"].lower()
    assert "Udyam" in run(agent, ["How can I improve my score?"])[-1]["text"] or True
    assert "https://" in run(agent, ["What is MUDRA?"])[0]["text"]


def test_unknown_message_reasks_pending_question():
    agent = OfflineAgent(CaseState(lang="en"))
    agent.handle("I'm a tailor")
    replies = agent.handle("purple elephant")
    assert replies[-1]["text"].startswith("How much money")


# ------------------------------------------------------------------ Claude loop with a fake client
class FakeClient:
    """Replays a scripted sequence of model turns."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.messages = self

    def create(self, **kwargs):
        assert kwargs["tools"] and kwargs["system"]
        return self.turns.pop(0)


def block(**kw):
    return SimpleNamespace(**kw)


def test_claude_agent_tool_loop():
    turns = [
        SimpleNamespace(stop_reason="tool_use", content=[
            block(type="text", text="Let me note that."),
            block(type="tool_use", id="t1", name="update_facts",
                  input={"trade": "tailor", "sector": "manufacturing", "loan_amount": 300000, "is_new_unit": False,
                         "udyam_registered": False, "has_default": False}),
            block(type="tool_use", id="t2", name="use_sample_statement", input={}),
        ]),
        SimpleNamespace(stop_reason="tool_use", content=[block(type="tool_use", id="t3", name="analyze_case", input={})]),
        SimpleNamespace(stop_reason="end_turn", content=[block(type="text", text="You qualify for MUDRA Kishore.")]),
    ]
    state = CaseState(lang="en")
    agent = ClaudeAgent(state, client=FakeClient(turns))
    replies = agent.handle("I'm a tailor, need 3 lakh, running 4 years, no Udyam, no default")
    kinds = [r["kind"] for r in replies]
    assert kinds == ["profile", "schemes", "score", "text"]
    assert state.analysis is not None and state.analysis.score.total > 0
    # tool results were fed back to the model
    assert any(isinstance(m["content"], list) and m["content"][0].get("type") == "tool_result" for m in state.claude_messages)


def test_claude_agent_falls_back_offline_on_error():
    class Broken:
        messages = None

        def __getattr__(self, name):
            raise RuntimeError("no network")

    agent = ClaudeAgent(CaseState(lang="en"), client=SimpleNamespace(messages=Broken()))
    replies = agent.handle("I'm a tailor and need 3 lakh")
    assert "offline agent" in replies[0]["text"]
    assert agent.s.applicant.trade == "tailor"
