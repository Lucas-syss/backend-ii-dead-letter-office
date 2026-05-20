import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.api.deps import get_db
from app.schemas.event import (
    EventIngestResponse,
    EventListResponse,
    EventResponse,
    FailedEventCreate,
)
from app.services import event_service
from app.schemas.incident import IncidentResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────

def _build_event_response(event) -> EventResponse:
    incident = None
    if event.incident:
        inc = event.incident
        incident = IncidentResponse(
            incident_id=inc.id,
            event_id=inc.event_id,
            event_type=inc.event_type,
            root_cause=inc.root_cause,
            remediation_attempted=inc.remediation_attempted,
            remediation_result=inc.remediation_result,
            severity=inc.severity,
            report_md=inc.report_md,
            escalated=inc.escalated,
            created_at=inc.created_at,
            resolved_at=inc.resolved_at,
        )
    return EventResponse(
        event_id=event.id,
        source=event.source,
        service=event.service,
        error_code=event.error_code,
        error_message=event.error_message,
        status=event.status,
        payload=event.payload,
        metadata=event.metadata_,
        created_at=event.created_at,
        updated_at=event.updated_at,
        incident=incident,
    )

async def _trigger_crew(event_id: str) -> None:
    """Background task — runs the CrewAI crew for a given event."""
    import asyncio
    from app.models.incident import Incident
    from app.services.crew_service import run_crew

    async with AsyncSessionLocal() as db:
        event = await event_service.get_event(db, event_id)
        if not event:
            logger.warning("_trigger_crew: event_id=%s not found", event_id)
            return
        await event_service.update_event_status(db, event_id, "processing")
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

    async with AsyncSessionLocal() as db:
        incident = Incident(
            event_id=event_id,
            event_type=result.get("event_type", "unknown"),
            root_cause=result.get("root_cause", "See report."),
            remediation_attempted=True,
            remediation_result=result.get("remediation", "See report."),
            severity=result.get("severity", "P3"),
            report_md=result.get("report", ""),
            escalated=False,
            raw_agent_output=result,
        )
        db.add(incident)
        await db.commit()
        await event_service.update_event_status(db, event_id, "resolved")
        logger.info("Incident saved for event_id=%s", event_id)
# ── Routes ────────────────────────────────────────────────────────────────

@router.post(
    "/ingest",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventIngestResponse,
    summary="Ingest a failed event",
    description=(
        "Accepts a failed system event, persists it to the database, and "
        "immediately triggers the CrewAI triage crew as a background task. "
        "Returns 202 Accepted — the crew runs asynchronously."
    ),
)
async def ingest_event(
    payload: FailedEventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EventIngestResponse:
    event = await event_service.create_event(db, payload)
    background_tasks.add_task(_trigger_crew, event.id)
    return EventIngestResponse(
        event_id=event.id,
        status="processing",
        message="Event accepted. Crew triage started asynchronously.",
    )


@router.get(
    "",
    response_model=EventListResponse,
    summary="List all events",
    description="Returns a paginated list of events. Filter by status, severity, or source.",
)
async def list_events(
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status: pending | processing | resolved | escalated | failed",
    ),
    severity: str | None = Query(
        default=None,
        description="Filter by incident severity: P1 | P2 | P3 | P4",
    ),
    source: str | None = Query(
        default=None,
        description="Filter by source: webhook | job | api_call | unknown",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> EventListResponse:
    total, events = await event_service.list_events(
        db,
        status=status_filter,
        severity=severity,
        source=source,
        limit=limit,
        offset=offset,
    )
    return EventListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_build_event_response(e) for e in events],
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get a single event",
    description="Returns full event detail including its incident report if the crew has finished.",
)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    event = await event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )
    return _build_event_response(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="Deletes an event and its linked incident (cascade). Returns 204 No Content.",
)
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await event_service.delete_event(db, event_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )