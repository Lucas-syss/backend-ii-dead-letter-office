import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.incident import IncidentResponse
from app.services import incident_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────


def _build_incident_response(incident) -> IncidentResponse:
    """Map an Incident ORM object to an IncidentResponse schema."""
    return IncidentResponse(
        incident_id=incident.id,
        event_id=incident.event_id,
        event_type=incident.event_type,
        root_cause=incident.root_cause,
        remediation_attempted=incident.remediation_attempted,
        remediation_result=incident.remediation_result,
        severity=incident.severity,
        report_md=incident.report_md,
        escalated=incident.escalated,
        created_at=incident.created_at,
        resolved_at=incident.resolved_at,
    )


# ── Routes ────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=dict,
    summary="List all incidents",
    description="Returns a paginated list of incidents. Filter by severity, escalation status, or event type.",
    tags=["Incidents"],
)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    severity: str | None = Query(
        default=None,
        description="Filter by severity: P1 | P2 | P3 | P4",
    ),
    escalated: bool | None = Query(
        default=None,
        description="Filter by escalation status: true | false",
    ),
    event_type: str | None = Query(
        default=None,
        description="Filter by event type e.g. timeout_failure, auth_error",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> dict:
    total, incidents = await incident_service.list_incidents(
        db,
        severity=severity,
        escalated=escalated,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_build_incident_response(i).model_dump() for i in incidents],
    }


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get a single incident",
    description="Returns full incident detail including the Markdown report written by the ReporterAgent.",
    tags=["Incidents"],
)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    incident = await incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return _build_incident_response(incident)


@router.post(
    "/{incident_id}/retry",
    response_model=IncidentResponse,
    summary="Retry remediation",
    description=(
        "Re-runs the RemediationAgent for this incident. "
        "Useful when a previous remediation attempt failed or circumstances have changed."
    ),
    tags=["Incidents"],
)
async def retry_remediation(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    incident = await incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    incident = await incident_service.retry_remediation(db, incident)
    return _build_incident_response(incident)


@router.post(
    "/{incident_id}/escalate",
    response_model=IncidentResponse,
    summary="Escalate an incident",
    description=(
        "Marks the incident as escalated and fires a POST to ESCALATION_WEBHOOK_URL "
        "if configured in the environment. Safe to call multiple times."
    ),
    tags=["Incidents"],
)
async def escalate_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    incident = await incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    if incident.escalated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Incident '{incident_id}' is already escalated.",
        )
    incident = await incident_service.mark_escalated(db, incident)
    return _build_incident_response(incident)
