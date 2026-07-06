from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceConfigBase(BaseModel):
    server_ip: Optional[str] = Field(None, description="IP Address/Domain of ingestion endpoint server")
    server_port: Optional[int] = Field(None, description="TCP Port of ingestion server")
    apn: Optional[str] = Field(None, description="Cellular Access Point Name")
    timezone: Optional[str] = Field(None, description="Device timezone offset (e.g. +05:30)")
    reporting_interval: Optional[int] = Field(None, description="Ingestion reporting rate (PRD in seconds)")
    speed_limit: Optional[float] = Field(None, description="Vehicle speed limit threshold (ESS in km/h)")
    feature_flags: Optional[Dict[str, Any]] = Field(None, description="Peripheral feature toggles")
    firmware_version: Optional[str] = Field(None, description="Configured firmware target version")
    hardware_version: Optional[str] = Field(None, description="Configured hardware target version")


class DeviceConfigCreate(DeviceConfigBase):
    vehicle_id: int = Field(..., description="ID of the associated vehicle")


class DeviceConfigUpdate(DeviceConfigBase):
    pass


class DeviceConfigResponse(DeviceConfigBase):
    id: int
    vehicle_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
