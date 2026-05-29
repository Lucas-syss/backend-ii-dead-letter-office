from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Event(UUIDMixin, TimestampMixin, Base):
    """
    Represents a failed system event ingested into the Dead Letter Office.

    An event can be a failed webhook, a job that timed out, a failed API call,
    or any other system failure. Once ingested, a CrewAI crew is triggered to
    triage, diagnose, and remediate the event.
    """

    __tablename__ = "events"

    # Where the failure came from
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="webhook | job | api_call | unknown",
    )

    # Which service produced the failure
    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g. payment-service, auth-service",
    )

    # The error details
    error_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP or custom error code",
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Raw error string from the originating system",
    )

    # The original failed request or job body
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Original failed payload",
    )

    # Extra context (region, environment, etc.)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Extra context such as region, environment, retry count",
    )

    # Processing status — updated as the crew works through the event
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending | processing | resolved | escalated | failed",
    )

    # One-to-one relationship with the incident created by the crew
    incident: Mapped["Incident"] = relationship(  # noqa: F821
        "Incident",
        back_populates="event",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Event id={self.id} source={self.source} service={self.service} status={self.status}>"
        )
