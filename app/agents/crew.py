from crewai import Crew, Process, Task

from app.agents.triage_agent import build_triage_agent


triage_task = Task(
    description="Classify the incoming failed event",
    expected_output="Structured event classification",
    agent=build_triage_agent(),
)

crew = Crew(
    agents=[build_triage_agent()],
    tasks=[triage_task],
    process=Process.sequential,
    verbose=True,
)