from crewai import Agent

from app.agents.llm import get_llm


def build_diagnosis_agent() -> Agent:
    return Agent(
        role="Root Cause Analyst",
        goal="Determine the most likely root cause of a failed backend event",
        backstory=(
            "You are a backend reliability engineer specialized in diagnosing "
            "production failures using logs, payloads, and triage metadata."
        ),
        llm=get_llm(),
        verbose=True,
    )
