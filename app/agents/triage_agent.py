from crewai import Agent

from app.agents.llm import get_llm


def build_triage_agent() -> Agent:
    return Agent(
        role="Incident Triage Specialist",
        goal="Classify failures and extract structured metadata",
        backstory=(
            "You are an expert SRE focused on identifying "
            "incident categories and affected systems."
        ),
        llm=get_llm(),
        verbose=True,
    )