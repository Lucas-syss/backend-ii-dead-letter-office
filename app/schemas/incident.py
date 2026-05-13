from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class IncidentResponse(BaseModel):
    """Response schema for an incident generated from a failed event."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: UUID = Field(..., examples=["7cb12a00-0000-4000-8000-000000000000"])
    event_id: UUID = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    event_type: str = Field(..., examples=["timeout_failure"])
    root_cause: str = Field(..., examples=["Payment gateway did not respond before timeout."])
    remediation_attempted: bool = Field(..., examples=[True])
    remediation_result: str | None = Field(None, examples=["Retry succeeded on attempt 2."])
    severity: Literal["P1", "P2", "P3", "P4"] = Field(..., examples=["P2"])
    report_md: str = Field(..., examples=["# Incident Report\n\n## Summary\n..."])
    escalated: bool = Field(..., examples=[False])
    created_at: datetime = Field(..., examples=["2025-05-10T14:32:00Z"])
    resolved_at: datetime | None = Field(None, examples=["2025-05-10T14:32:45Z"])