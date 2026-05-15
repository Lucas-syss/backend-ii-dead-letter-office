import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

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
    """
    Background task — runs the CrewAI crew for a given event.

    This stub will be replaced with the real crew call once
    Miguel completes Cards 2.1–2.3. For now it just logs.

    To integrate: replace the body with:
        from app.services.crew_service import run_crew
        await run_crew(event_id)
    """
    logger.info("Crew trigger called for event_id=%s (stub — crew not yet wired)", event_id)

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