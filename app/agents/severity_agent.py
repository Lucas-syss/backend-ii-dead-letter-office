from crewai import Agent

from app.agents.llm import get_llm


def build_severity_agent() -> Agent:
    return Agent(
        role="Incident Severity Classifier",
        goal="Classify the severity of incidents based on event data",
        backstory=(
            "You are an expert SRE responsible for classifying the severity of "
            "incidents to help prioritize response efforts."
        ),
        llm=get_llm(),
        verbose=True,
    )
