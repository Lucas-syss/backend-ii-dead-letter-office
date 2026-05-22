from app.agents import crew


def test_crew_builds_five_agents_and_five_tasks(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()

    assert built_crew.agents == [
        patch_crew_dependencies["triage"],
        patch_crew_dependencies["diagnosis"],
        patch_crew_dependencies["remediation"],
        patch_crew_dependencies["severity"],
        patch_crew_dependencies["reporter"],
    ]

    assert len(built_crew.tasks) == 5
    assert built_crew.verbose is True


def test_triage_task_has_valid_classification_contract(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()
    triage_task = built_crew.tasks[0]

    assert "{event}" in triage_task.description

    allowed_event_types = [
        "timeout_failure",
        "auth_error",
        "payload_validation_error",
        "rate_limit",
        "dependency_unavailable",
        "unknown",
    ]

    for event_type in allowed_event_types:
        assert event_type in triage_task.description

    required_fields = [
        "event_type",
        "service_tier",
        "affected_component",
    ]

    for field in required_fields:
        assert field in triage_task.description


def test_diagnosis_task_uses_triage_context_and_original_event(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()

    triage_task = built_crew.tasks[0]
    diagnosis_task = built_crew.tasks[1]

    assert diagnosis_task.context == [triage_task]
    assert "{event}" in diagnosis_task.description
    assert "root cause" in diagnosis_task.description
    assert "what most likely went wrong" in diagnosis_task.description


def test_remediation_task_uses_previous_agent_context(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()

    triage_task = built_crew.tasks[0]
    diagnosis_task = built_crew.tasks[1]
    remediation_task = built_crew.tasks[2]

    assert remediation_task.context == [triage_task, diagnosis_task]
    assert "remediation steps" in remediation_task.description
    assert "prevent future occurrences" in remediation_task.description


def test_severity_task_uses_priority_rubric(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()
    severity_task = built_crew.tasks[3]

    assert "P1" in severity_task.description
    assert "P2" in severity_task.description
    assert "P3" in severity_task.description
    assert "P4" in severity_task.description
    assert "Production down" in severity_task.description
    assert "Degraded production" in severity_task.description
    assert severity_task.expected_output == "One of: P1, P2, P3, or P4"


def test_reporter_task_requires_markdown_incident_sections(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()
    reporter_task = built_crew.tasks[4]

    required_sections = [
        "# Summary",
        "# Timeline",
        "# Root Cause",
        "# Impact",
        "# Remediation",
        "# Follow-up Actions",
    ]

    for section in required_sections:
        assert section in reporter_task.description

    assert "Markdown incident report" in reporter_task.expected_output


def test_tasks_are_chained_in_correct_order(patch_crew_dependencies):
    built_crew = crew.build_triage_diagnosis_crew()

    triage_task = built_crew.tasks[0]
    diagnosis_task = built_crew.tasks[1]
    remediation_task = built_crew.tasks[2]
    severity_task = built_crew.tasks[3]
    reporter_task = built_crew.tasks[4]

    assert diagnosis_task.context == [triage_task]
    assert remediation_task.context == [triage_task, diagnosis_task]
    assert severity_task.context == [triage_task, diagnosis_task, remediation_task]
    assert reporter_task.context == [
        triage_task,
        diagnosis_task,
        remediation_task,
        severity_task,
    ]


def test_run_triage_diagnosis_passes_event_to_crew(monkeypatch):
    fake_crew = type(
        "FakeRunnableCrew",
        (),
        {
            "kickoff": lambda self, inputs: {
                "status": "mocked",
                "inputs": inputs,
            }
        },
    )()

    monkeypatch.setattr(crew, "build_triage_diagnosis_crew", lambda: fake_crew)

    event = {
        "source": "webhook",
        "service": "payment-service",
        "error_code": 503,
        "error_message": "Upstream timeout after 30s",
    }

    result = crew.run_triage_diagnosis(event)

    assert result == {
        "status": "mocked",
        "inputs": {"event": event},
    }