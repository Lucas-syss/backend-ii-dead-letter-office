from crewai import Crew, Process, Task

from app.agents.triage_agent import build_triage_agent

triage_agent = build_triage_agent()

triage_task = Task(
    description=("Analyze this failed event:\n{event}\n\nClassify the incident type."),
    expected_output="Short classification of the incident",
    agent=triage_agent,
)

crew = Crew(
    agents=[triage_agent],
    tasks=[triage_task],
    process=Process.sequential,
    verbose=True,
)

response = crew.kickoff(
    inputs={
        "event": {
            "service": "payment-service",
            "error_message": "Timeout after 30s",
        }
    }
)

print("\n===== RESPONSE =====\n")
print(response)
