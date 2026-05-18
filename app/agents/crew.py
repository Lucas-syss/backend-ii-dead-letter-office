from crewai import Crew, Process, Task

from app.agents.diagnosis_agent import build_diagnosis_agent
from app.agents.triage_agent import build_triage_agent


def build_triage_diagnosis_crew() -> Crew:
    triage_agent = build_triage_agent()
    diagnosis_agent = build_diagnosis_agent()

    triage_task = Task(
        description=(
            "Analyze this failed event:\n"
            "{event}\n\n"
            "Classify it into exactly one of these event types:\n"
            "- timeout_failure\n"
            "- auth_error\n"
            "- payload_validation_error\n"
            "- rate_limit\n"
            "- dependency_unavailable\n"
            "- unknown\n\n"
            "Return only this structure:\n"
            "event_type: one valid event type\n"
            "service_tier: critical, high, medium, or low\n"
            "affected_component: the affected service or component"
        ),
        expected_output=(
            "A structured classification containing event_type, "
            "service_tier, and affected_component."
        ),
        agent=triage_agent,
    )

    diagnosis_task = Task(
        description=(
            "Using the triage result and the original event payload, write a short "
            "root cause diagnosis.\n\n"
            "Original event:\n"
            "{event}\n\n"
            "Explain what most likely went wrong and why."
        ),
        expected_output="One concise paragraph explaining the likely root cause.",
        agent=diagnosis_agent,
        context=[triage_task],
    )

    return Crew(
        agents=[triage_agent, diagnosis_agent],
        tasks=[triage_task, diagnosis_task],
        process=Process.sequential,
        verbose=True,
    )


def run_triage_diagnosis(event_data: dict):
    crew = build_triage_diagnosis_crew()
    return crew.kickoff(inputs={"event": event_data})