from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Incident(UUIDMixin, TimestampMixin, Base):
    """
    Represents the AI crew's analysis of a failed event.

    Created automatically after the CrewAI crew finishes processing an Event.
    Contains the triage classification, root cause, remediation result,
    severity score, and the full Markdown incident report.
    """

    __tablename__ = "incidents"

    # Foreign key back to the event that triggered this incident
    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="The event that triggered this incident",
    )

    # ── TriageAgent output ───────────────────────────────────
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="e.g. timeout_failure, auth_error, payload_validation_error",
    )

    # ── DiagnosisAgent output ────────────────────────────────
    root_cause: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable root cause determined by DiagnosisAgent",
    )

    # ── RemediationAgent output ──────────────────────────────
    remediation_attempted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether RemediationAgent attempted a fix",
    )
    remediation_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of what was attempted and the outcome",
    )

    # ── SeverityAgent output ─────────────────────────────────
    severity: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
        comment="P1 (critical) | P2 (high) | P3 (medium) | P4 (low)",
    )

    # ── ReporterAgent output ─────────────────────────────────
    report_md: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full Markdown incident report written by ReporterAgent",
    )

    # ── Escalation ───────────────────────────────────────────
    escalated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether an escalation webhook was fired",
    )

    # ── Raw agent output for debugging ───────────────────────
    raw_agent_output: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Full CrewAI crew output stored for debugging",
    )

    # Timestamp for when the incident was resolved
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set when the parent event status moves to resolved",
    )

    # Relationship back to the event
    event: Mapped["Event"] = relationship(  # noqa: F821
        "Event",
        back_populates="incident",
    )

    def __repr__(self) -> str:
        return f"<Incident id={self.id} severity={self.severity} event_id={self.event_id}>"
