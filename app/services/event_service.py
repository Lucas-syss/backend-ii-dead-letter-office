import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.schemas.event import FailedEventCreate

logger = logging.getLogger(__name__)


async def create_event(db: AsyncSession, data: FailedEventCreate) -> Event:
    """
    Persist a new failed event to the database.
    Status starts as 'pending' — updated to 'processing' when the crew starts.
    """
    event = Event(
        source=data.source,
        service=data.service,
        error_code=data.error_code,
        error_message=data.error_message,
        payload=data.payload,
        metadata_=data.metadata,
        status="pending",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    logger.info("Event created: id=%s service=%s source=%s", event.id, event.service, event.source)
    return event


async def get_event(db: AsyncSession, event_id: str) -> Event | None:
    """
    Fetch a single event by ID, eagerly loading its incident.
    Returns None if not found.
    """
    result = await db.execute(
        select(Event).options(selectinload(Event.incident)).where(Event.id == event_id)
    )
    return result.scalar_one_or_none()


async def list_events(
    db: AsyncSession,
    status: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, list[Event]]:
    """
    Return a paginated list of events with optional filters.
    Also returns the total count (before pagination) for the response envelope.
    """
    query = select(Event).options(selectinload(Event.incident))
    count_query = select(func.count()).select_from(Event)

    if status:
        query = query.where(Event.status == status)
        count_query = count_query.where(Event.status == status)
    if source:
        query = query.where(Event.source == source)
        count_query = count_query.where(Event.source == source)

    if severity:
        from app.models.incident import Incident

        query = query.join(Incident, Event.id == Incident.event_id).where(
            Incident.severity == severity
        )
        count_query = count_query.join(Incident, Event.id == Incident.event_id).where(
            Incident.severity == severity
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Event.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    events = list(result.scalars().all())

    return total, events


async def delete_event(db: AsyncSession, event_id: str) -> bool:
    """
    Delete an event by ID (cascade deletes its incident too).
    Returns True if deleted, False if not found.
    """
    event = await get_event(db, event_id)
    if not event:
        return False
    await db.delete(event)
    await db.commit()
    logger.info("Event deleted: id=%s", event_id)
    return True


async def update_event_status(db: AsyncSession, event_id: str, status: str) -> Event | None:
    """
    Update the status of an event.
    Called by the crew runner to move from pending → processing → resolved/failed.
    """
    event = await get_event(db, event_id)
    if not event:
        return None
    event.status = status
    event.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(event)
    return event
