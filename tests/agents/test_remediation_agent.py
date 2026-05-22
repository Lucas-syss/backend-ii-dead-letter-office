from app.agents import remediation_agent


def test_remediation_agent_builds_expected_agent(patch_agent_builder, fake_llm):
    patch_agent_builder(remediation_agent)

    agent = remediation_agent.build_remediation_agent()

    assert agent.role == "Incident Remediation Specialist"
    assert "remediation steps" in agent.goal
    assert "remediation strategies" in agent.backstory
    assert agent.llm is fake_llm
    assert agent.verbose is True