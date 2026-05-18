from crewai import Agent

from app.agents.llm import get_llm

def build_remediation_agent() -> Agent:
    return Agent(
        role="Incident Remediation Specialist",
        goal="Propose actionable remediation steps for classified incidents",
        backstory=(
            "You are an expert SRE focused on proposing effective "
            "remediation strategies based on incident classifications."
        ),
        llm=get_llm(),
        verbose=True,
    )