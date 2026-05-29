from crewai import Agent

from app.agents.llm import get_llm


def build_reporter_agent() -> Agent:
    return Agent(
        role="Incident Reporter",
        goal="Generate structured Markdown incident reports",
        backstory=(
            "You are an expert incident manager responsible for creating "
            "clear Markdown reports for production incidents."
        ),
        llm=get_llm(),
        verbose=True,
    )
