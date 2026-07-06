from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.driver import DriverResponse

class DriverAssignmentBase(BaseModel):
    vehicle_id: int
    driver_id: int
    status: Optional[str] = "Active"

class DriverAssignmentCreate(DriverAssignmentBase):
    pass

class DriverAssignmentResponse(DriverAssignmentBase):
    id: int
    assigned_at: datetime
    released_at: Optional[datetime] = None
    driver: Optional[DriverResponse] = None

    model_config = ConfigDict(from_attributes=True)
