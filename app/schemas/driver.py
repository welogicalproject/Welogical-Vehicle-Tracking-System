from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DriverStatus

class DriverBase(BaseModel):
    driver_name: str = Field(..., description="Full name of the driver")
    phone_number: str = Field(..., description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    license_number: str = Field(..., description="Driver license identification number")
    license_expiry: datetime = Field(..., description="License expiration date")
    emergency_contact: str = Field(..., description="Emergency contact phone number/name")
    status: Optional[DriverStatus] = Field(DriverStatus.ACTIVE, description="Status of the driver")

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    driver_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    emergency_contact: Optional[str] = None
    status: Optional[DriverStatus] = None

class DriverVehicleResponse(BaseModel):
    id: int
    device_uid: str
    vehicle_name: str
    vehicle_type: str
    vehicle_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DriverResponse(DriverBase):
    id: int
    created_at: datetime
    current_vehicle: Optional[DriverVehicleResponse] = None

    model_config = ConfigDict(from_attributes=True)
