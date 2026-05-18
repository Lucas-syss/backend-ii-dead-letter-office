from crewai import Agent

from app.agents.llm import get_llm

def build_triage_agent() -> Agent:
    return Agent(
        role="Incident Triage Specialist",
        goal="Classify failed backend events into structured incident types",
        backstory=(
            "You are an experienced SRE. Your job is to inspect failed system "
            "events and classify them into a precise incident category."
        ),
        llm=get_llm(),
        verbose=True,
    )