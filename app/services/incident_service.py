import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.incident import Incident

logger = logging.getLogger(__name__)


async def get_incident(db: AsyncSession, incident_id: str) -> Incident | None:
    """
    Fetch a single incident by its own ID, eagerly loading its parent event.
    Returns None if not found.
    """
    result = await db.execute(
        select(Incident).options(selectinload(Incident.event)).where(Incident.id == incident_id)
    )
    return result.scalar_one_or_none()


async def get_incident_by_event(db: AsyncSession, event_id: str) -> Incident | None:
    """
    Fetch the incident linked to a specific event ID.
    Returns None if not found.
    """
    result = await db.execute(select(Incident).where(Incident.event_id == event_id))
    return result.scalar_one_or_none()


async def list_incidents(
    db: AsyncSession,
    severity: str | None = None,
    escalated: bool | None = None,
    event_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, list[Incident]]:
    """
    Return a paginated list of incidents with optional filters.
    Returns (total_count, incidents).
    """
    from sqlalchemy import func

    query = select(Incident).options(selectinload(Incident.event))
    count_query = select(func.count()).select_from(Incident)

    if severity:
        query = query.where(Incident.severity == severity)
        count_query = count_query.where(Incident.severity == severity)
    if escalated is not None:
        query = query.where(Incident.escalated == escalated)
        count_query = count_query.where(Incident.escalated == escalated)
    if event_type:
        query = query.where(Incident.event_type == event_type)
        count_query = count_query.where(Incident.event_type == event_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Incident.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    incidents = list(result.scalars().all())

    return total, incidents


async def mark_escalated(db: AsyncSession, incident: Incident) -> Incident:
    """
    Mark an incident as escalated and fire the escalation webhook if configured.
    """
    incident.escalated = True
    await db.commit()
    await db.refresh(incident)

    webhook_url = settings.ESCALATION_WEBHOOK_URL
    if webhook_url:
        payload = {
            "incident_id": incident.id,
            "event_id": incident.event_id,
            "severity": incident.severity,
            "event_type": incident.event_type,
            "root_cause": incident.root_cause,
            "report_md": incident.report_md,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info(
                    "Escalation webhook fired for incident_id=%s → %s",
                    incident.id,
                    webhook_url,
                )
        except httpx.HTTPError as exc:
            logger.warning(
                "Escalation webhook failed for incident_id=%s: %s",
                incident.id,
                exc,
            )
    else:
        logger.info(
            "Incident %s marked escalated — no webhook URL configured.",
            incident.id,
        )

    return incident


async def retry_remediation(db: AsyncSession, incident: Incident) -> Incident:
    """
    Re-runs the full crew pipeline for an existing incident and updates the result.
    """
    import asyncio

    from app.services.crew_service import run_crew

    event = incident.event
    event_data = {
        "source": event.source,
        "service": event.service,
        "error_code": event.error_code,
        "error_message": event.error_message,
        "payload": event.payload,
        "metadata": event.metadata_,
    }

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_crew, event_data)

    incident.remediation_attempted = True
    incident.remediation_result = result.get("report", "Crew re-run completed.")
    incident.raw_agent_output = result
    await db.commit()
    await db.refresh(incident)

    logger.info("Crew re-run complete for incident_id=%s", incident.id)
    return incident
