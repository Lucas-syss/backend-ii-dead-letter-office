import pytest
from sqlalchemy import select

from app.models.event import Event
from app.models.incident import Incident


@pytest.mark.asyncio
async def test_event_crud(db_session):
    event = Event(
        source="webhook",
        service="payment-service",
        error_code=503,
        error_message="Upstream timeout after 30s",
        payload={"endpoint": "/charge"},
        metadata_={"environment": "test"},
        status="pending",
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    assert event.id is not None
    assert event.source == "webhook"
    assert event.service == "payment-service"
    assert event.status == "pending"

    event.status = "resolved"
    await db_session.commit()
    await db_session.refresh(event)

    assert event.status == "resolved"

    result = await db_session.execute(select(Event).where(Event.id == event.id))
    saved_event = result.scalar_one_or_none()

    assert saved_event is not None
    assert saved_event.id == event.id

    await db_session.delete(saved_event)
    await db_session.commit()

    result = await db_session.execute(select(Event).where(Event.id == event.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_incident_crud(db_session):
    event = Event(
        source="api_call",
        service="orders-service",
        error_code=500,
        error_message="Internal error",
        payload={"order_id": "123"},
        metadata_={"environment": "test"},
        status="resolved",
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    incident = Incident(
        event_id=event.id,
        event_type="dependency_unavailable",
        root_cause="Downstream service unavailable.",
        remediation_attempted=True,
        remediation_result="Retry suggested.",
        severity="P3",
        report_md="# Incident Report\n\nDownstream service unavailable.",
        escalated=False,
        raw_agent_output={"severity": "P3"},
    )

    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    assert incident.id is not None
    assert incident.event_id == event.id
    assert incident.event_type == "dependency_unavailable"
    assert incident.severity == "P3"
    assert incident.escalated is False

    incident.escalated = True
    await db_session.commit()
    await db_session.refresh(incident)

    assert incident.escalated is True

    result = await db_session.execute(select(Incident).where(Incident.id == incident.id))
    saved_incident = result.scalar_one_or_none()

    assert saved_incident is not None
    assert saved_incident.id == incident.id

    await db_session.delete(saved_incident)
    await db_session.commit()

    result = await db_session.execute(select(Incident).where(Incident.id == incident.id))
    assert result.scalar_one_or_none() is None
