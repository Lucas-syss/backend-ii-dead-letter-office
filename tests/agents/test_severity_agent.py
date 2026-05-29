from app.agents import severity_agent


def test_severity_agent_builds_expected_agent(patch_agent_builder, fake_llm):
    patch_agent_builder(severity_agent)

    agent = severity_agent.build_severity_agent()

    assert agent.role == "Incident Severity Classifier"
    assert "severity" in agent.goal
    assert "classifying the severity" in agent.backstory
    assert agent.llm is fake_llm
    assert agent.verbose is True
