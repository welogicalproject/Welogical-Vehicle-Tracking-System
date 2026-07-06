from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    txn: str = Field(..., description="VTS transaction identifier code (e.g. A-Z)")
    event_type: str = Field(..., description="Human-readable event category")
    description: str = Field(..., description="Detailed description of the event")
    severity: str = Field(..., description="Severity level: Critical, Warning, Info")
    msgid: Optional[int] = Field(None, description="Optional sequential message ID from VTS packet")


class EventCreate(EventBase):
    vehicle_id: int = Field(..., description="ID of the associated vehicle")


class EventResponse(EventBase):
    id: int
    vehicle_id: int
    created_at: datetime
    # Optional nested field for vehicle name in dashboard queries
    vehicle_name: Optional[str] = Field(None, description="Name of the vehicle associated with the event")
    device_uid: Optional[str] = Field(None, description="Device UID of the vehicle associated with the event")

    model_config = ConfigDict(from_attributes=True)
