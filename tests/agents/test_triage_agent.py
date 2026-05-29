from app.agents import triage_agent


def test_triage_agent_builds_expected_agent(patch_agent_builder, fake_llm):
    patch_agent_builder(triage_agent)

    agent = triage_agent.build_triage_agent()

    assert agent.role == "Incident Triage Specialist"
    assert "Classify failed backend events" in agent.goal
    assert "experienced SRE" in agent.backstory
    assert agent.llm is fake_llm
    assert agent.verbose is True
