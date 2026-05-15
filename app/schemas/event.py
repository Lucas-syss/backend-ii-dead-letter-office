from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.incident import IncidentResponse


EventSource = Literal["webhook", "job", "api_call", "unknown"]
EventStatus = Literal["pending", "processing", "resolved", "escalated", "failed"]


class FailedEventCreate(BaseModel):
    """Request schema for creating a failed event."""

    source: EventSource = Field(..., examples=["webhook"])
    service: str = Field(..., min_length=1, examples=["payment-service"])
    error_code: int | None = Field(None, ge=100, le=599, examples=[503])
    error_message: str = Field(..., min_length=1, examples=["Upstream timeout after 30s"])
    payload: dict[str, Any] = Field(default_factory=dict, examples=[{"endpoint": "/charge"}])
    metadata: dict[str, Any] = Field(default_factory=dict, examples=[{"environment": "production"}])

    @field_validator("service")
    @classmethod
    def validate_service(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("service must not be empty")
        return value


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    source: EventSource = Field(..., examples=["webhook"])
    service: str = Field(..., examples=["payment-service"])
    error_code: int | None = Field(None, examples=[503])
    error_message: str = Field(..., examples=["Upstream timeout after 30s"])
    status: EventStatus = Field(..., examples=["processing"])
    payload: dict[str, Any] = Field(default_factory=dict)  
    metadata: dict[str, Any] = Field(default_factory=dict)  
    created_at: datetime = Field(..., examples=["2025-05-10T14:32:00Z"])
    updated_at: datetime | None = None                       
    incident: IncidentResponse | None = None


class EventListResponse(BaseModel):
    """Paginated response schema for event lists."""

    total: int = Field(..., examples=[1])
    limit: int = Field(..., examples=[20])
    offset: int = Field(..., examples=[0])
    items: list[EventResponse]
    

class EventIngestResponse(BaseModel):
    """Returned immediately after POST /ingest (202 Accepted)."""
    event_id: str
    status: str
    message: str