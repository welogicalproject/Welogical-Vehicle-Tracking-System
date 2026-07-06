from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CommandStatus


class DeviceCommandBase(BaseModel):
    command_name: str = Field(..., description="VTS command code name (e.g. PRD, STOPV)")
    command_value: Optional[str] = Field(None, description="Arguments or parameter value configuration parameter")


class DeviceCommandCreate(DeviceCommandBase):
    vehicle_id: int = Field(..., description="ID of the vehicle target")


class DeviceCommandUpdate(BaseModel):
    status: CommandStatus = Field(..., description="Update execution status of command")
    message: Optional[str] = Field(None, description="Audit logging descriptive details")


class DeviceCommandResponse(DeviceCommandBase):
    id: int
    vehicle_id: int
    status: CommandStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    vehicle_name: Optional[str] = Field(None, description="Name of the vehicle associated with the command")

    model_config = ConfigDict(from_attributes=True)
