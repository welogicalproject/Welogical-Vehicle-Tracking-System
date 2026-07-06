from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinates")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinates")
    speed: float = Field(..., ge=0.0, description="Vehicle speed in km/h")
    altitude: float = Field(..., description="Altitude in meters")
    timestamp: datetime = Field(..., description="Date and time when telemetry was recorded")


class LocationCreate(LocationBase):
    vehicle_id: int = Field(..., description="ID of the associated vehicle")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Optional extra metadata fields")


class LocationResponse(LocationBase):
    id: int
    vehicle_id: int
    extra_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
