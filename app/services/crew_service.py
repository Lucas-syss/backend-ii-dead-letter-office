import re
from pathlib import Path

from app.agents.crew import run_triage_diagnosis


def _parse_triage(raw: str) -> dict:
    """Extract event_type, service_tier, affected_component from triage output."""
    result = {}
    for line in raw.splitlines():
        if "event_type:" in line:
            result["event_type"] = line.split("event_type:")[-1].strip()
        elif "service_tier:" in line:
            result["service_tier"] = line.split("service_tier:")[-1].strip()
        elif "affected_component:" in line:
            result["affected_component"] = line.split("affected_component:")[-1].strip()
    return result


def _parse_severity(raw: str) -> str:
    """Extract P1/P2/P3/P4 from severity output."""
    match = re.search(r"\b(P[1-4])\b", raw)
    return match.group(1) if match else "P3"


def run_crew(event_data: dict) -> dict:
    crew_result = run_triage_diagnosis(event_data)

    outputs = crew_result.tasks_output

    triage = _parse_triage(outputs[0].raw) if len(outputs) > 0 else {}
    root_cause = outputs[1].raw.strip() if len(outputs) > 1 else "Unknown"
    remediation = outputs[2].raw.strip() if len(outputs) > 2 else "None"
    severity = _parse_severity(outputs[3].raw) if len(outputs) > 3 else "P3"
    report_md = outputs[4].raw.strip() if len(outputs) > 4 else str(crew_result)

    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "incident_report.md").write_text(report_md, encoding="utf-8")

    return {
        "success": True,
        "event_type": triage.get("event_type", "unknown"),
        "service_tier": triage.get("service_tier", "unknown"),
        "affected_component": triage.get("affected_component", "unknown"),
        "root_cause": root_cause,
        "remediation": remediation,
        "severity": severity,
        "report": report_md,
        "report_path": str(reports_dir / "incident_report.md"),
    }
