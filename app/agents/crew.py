from crewai import Crew, Process, Task

from app.agents.diagnosis_agent import build_diagnosis_agent
from app.agents.remediation_agent import build_remediation_agent
from app.agents.reporter_agent import build_reporter_agent
from app.agents.severity_agent import build_severity_agent
from app.agents.triage_agent import build_triage_agent


def build_triage_diagnosis_crew() -> Crew:
    triage_agent = build_triage_agent()
    diagnosis_agent = build_diagnosis_agent()
    remediation_agent = build_remediation_agent()
    severity_agent = build_severity_agent()
    reporter_agent = build_reporter_agent()

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

    remediation_task = Task(
        description=(
            "Based on the triage classification and diagnosis, propose actionable "
            "remediation steps to resolve the incident and prevent future occurrences."
        ),
        expected_output=(
            "A list of clear, actionable remediation steps that can be taken to "
            "address the incident and prevent it from happening again."
        ),
        agent=remediation_agent,
        context=[triage_task, diagnosis_task],
    )

    severity_task = Task(
        description=(
            "Based on the triage classification, diagnosis, and remediation output, "
            "classify the severity of this incident.\n\n"
            "Severity rubric:\n"
            "- P1: Production down, revenue impacted, or many users affected\n"
            "- P2: Degraded production or partial outage\n"
            "- P3: Non-critical path failing with workaround available\n"
            "- P4: Minor issue or development/staging only\n\n"
            "Return only one value: P1, P2, P3, or P4."
        ),
        expected_output="One of: P1, P2, P3, or P4",
        agent=severity_agent,
        context=[triage_task, diagnosis_task, remediation_task],
    )

    reporter_task = Task(
        description=(
            "Generate a professional Markdown incident report using all "
            "previous agent outputs.\n\n"
            "The report must contain:\n"
            "# Summary\n"
            "# Timeline\n"
            "# Root Cause\n"
            "# Impact\n"
            "# Remediation\n"
            "# Follow-up Actions\n"
        ),
        expected_output="A complete Markdown incident report.",
        agent=reporter_agent,
        context=[
            triage_task,
            diagnosis_task,
            remediation_task,
            severity_task,
        ],
    )

    return Crew(
        agents=[triage_agent, diagnosis_agent, remediation_agent, severity_agent, reporter_agent],
        tasks=[triage_task, diagnosis_task, remediation_task, severity_task, reporter_task],
        process=Process.sequential,
        verbose=True,
    )


def run_triage_diagnosis(event_data: dict):
    crew = build_triage_diagnosis_crew()
    return crew.kickoff(inputs={"event": event_data})
