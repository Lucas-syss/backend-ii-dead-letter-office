from pathlib import Path

from app.agents.crew import run_triage_diagnosis


def run_crew(event_data: dict):
    result = run_triage_diagnosis(event_data)

    report_content = str(result)

    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_file = reports_dir / "incident_report.md"
    report_file.write_text(report_content, encoding="utf-8")

    return {
        "success": True,
        "report_path": str(report_file),
        "report": report_content,
    }