from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CommandStatus


class CommandLogResponse(BaseModel):
    id: int
    command_id: int
    vehicle_id: int
    status: CommandStatus
    message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
