from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import TripStatus

class TripBase(BaseModel):
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    duration: float
    distance: float
    average_speed: float
    maximum_speed: float
    idle_time: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    packet_count: int
    overspeed_count: int
    status: TripStatus
    is_active: bool

class TripResponse(TripBase):
    id: int
    created_at: datetime
    updated_at: datetime
    driver_id: Optional[int] = None
    driver_snapshot: Optional[dict] = None
    fuel_used: Optional[float] = None
    engine_hours: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
