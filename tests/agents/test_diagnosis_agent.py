from app.agents import diagnosis_agent


def test_diagnosis_agent_builds_expected_agent(patch_agent_builder, fake_llm):
    patch_agent_builder(diagnosis_agent)

    agent = diagnosis_agent.build_diagnosis_agent()

    assert agent.role == "Root Cause Analyst"
    assert "root cause" in agent.goal
    assert "backend reliability engineer" in agent.backstory
    assert agent.llm is fake_llm
    assert agent.verbose is True
