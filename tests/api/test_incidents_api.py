import pytest
import pytest_asyncio

from app.models.event import Event
from app.models.incident import Incident


@pytest_asyncio.fixture
async def sample_incident(db_session):
    event = Event(
        source="webhook",
        service="payment-service",
        error_code=503,
        error_message="Timeout",
        payload={"endpoint": "/charge"},
        metadata_={"environment": "test"},
        status="resolved",
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    incident = Incident(
        event_id=event.id,
        event_type="timeout_failure",
        root_cause="Payment gateway timeout.",
        remediation_attempted=True,
        remediation_result="Retry completed.",
        severity="P2",
        report_md="# Incident Report\n\nPayment gateway timeout.",
        escalated=False,
        raw_agent_output={"severity": "P2"},
    )

    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    return incident


@pytest.mark.asyncio
async def test_get_incidents_list(client, sample_incident):
    response = await client.get("/api/v1/incidents")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["severity"] == "P2"
    assert data["items"][0]["event_type"] == "timeout_failure"


@pytest.mark.asyncio
async def test_get_incident_by_id(client, sample_incident):
    response = await client.get(f"/api/v1/incidents/{sample_incident.id}")

    assert response.status_code == 200

    data = response.json()
    assert data["incident_id"] == sample_incident.id
    assert data["event_type"] == "timeout_failure"
    assert data["severity"] == "P2"
    assert data["escalated"] is False


@pytest.mark.asyncio
async def test_get_incident_not_found(client):
    response = await client.get("/api/v1/incidents/not-a-real-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_incident(client, sample_incident, monkeypatch):
    def fake_run_crew(event_data: dict) -> dict:
        return {
            "report": "Mocked remediation retry completed.",
            "severity": "P2",
        }

    monkeypatch.setattr("app.services.crew_service.run_crew", fake_run_crew)

    response = await client.post(f"/api/v1/incidents/{sample_incident.id}/retry")

    assert response.status_code == 200

    data = response.json()
    assert data["incident_id"] == sample_incident.id
    assert data["remediation_attempted"] is True
    assert data["remediation_result"] == "Mocked remediation retry completed."


@pytest.mark.asyncio
async def test_retry_incident_not_found(client):
    response = await client.post("/api/v1/incidents/not-a-real-id/retry")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_escalate_incident(client, sample_incident):
    response = await client.post(f"/api/v1/incidents/{sample_incident.id}/escalate")

    assert response.status_code == 200

    data = response.json()
    assert data["incident_id"] == sample_incident.id
    assert data["escalated"] is True


@pytest.mark.asyncio
async def test_escalate_already_escalated_returns_409(client, sample_incident):
    first_response = await client.post(f"/api/v1/incidents/{sample_incident.id}/escalate")
    assert first_response.status_code == 200

    second_response = await client.post(f"/api/v1/incidents/{sample_incident.id}/escalate")
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_escalate_incident_not_found(client):
    response = await client.post("/api/v1/incidents/not-a-real-id/escalate")

    assert response.status_code == 404
