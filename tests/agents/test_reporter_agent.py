from app.agents import reporter_agent


def test_reporter_agent_builds_expected_agent(patch_agent_builder, fake_llm):
    patch_agent_builder(reporter_agent)

    agent = reporter_agent.build_reporter_agent()

    assert agent.role == "Incident Reporter"
    assert "Markdown incident reports" in agent.goal
    assert "incident manager" in agent.backstory
    assert agent.llm is fake_llm
    assert agent.verbose is True