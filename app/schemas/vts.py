from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class VTSInfo(BaseModel):
    dt: int = Field(..., description="Unix Timestamp represented in Unix format (seconds since 1 Jan 1970)")
    txn: str = Field(..., description="Transmission Reason packet identifier, e.g., 'E', 'A', 'F'")
    msgkey: Optional[int] = Field(0, description="Reserved key number info")
    msgid: Optional[int] = Field(None, description="Numeric sequential message ID counter")
    cmdkey: Optional[str] = Field("", description="Command key identifier")
    cmdval: Optional[str] = Field("", description="Command key parameter value")


class VTSGps(BaseModel):
    fix: str = Field(..., description="GPS fix status: A (valid), V (invalid)")
    loc: List[float] = Field(..., min_length=2, max_length=2, description="Array of numbers: [Latitude, Longitude]")
    speed: float = Field(..., description="GPS speed parameter in km/h")
    sat: Optional[int] = Field(0, description="Number of GPS satellites in view")
    alt: float = Field(..., description="GPS altitude in meters")
    dir: Optional[float] = Field(0.0, description="GPS direction/bearing in degrees")
    odo: Optional[float] = Field(0.0, description="Device odometer in meters")


class VTSIo(BaseModel):
    box: Optional[int] = Field(0, description="Device enclosure open (1) or close (0) status")
    ign: Optional[int] = Field(0, description="Vehicle ignition status: 1 = On, 0 = Off")
    gpi: Optional[int] = Field(0, description="General purpose inputs represented in binary format")
    status: Optional[int] = Field(0, description="Bitwise status flags")
    analog: Optional[List[int]] = Field(default_factory=list, description="Analog input values in millivolts")


class VTSPwr(BaseModel):
    main: Optional[int] = Field(0, description="Mains input availability: 1 = Available, 0 = Unavailable")
    batt: Optional[int] = Field(0, description="Battery connection status: 1 = Connected, 0 = Unconnected")
    volt: Optional[float] = Field(0.0, description="Battery voltage in millivolts")
    mvolt: Optional[float] = Field(0.0, description="Main battery input voltage in volts")


class VTSDbg(BaseModel):
    status: Optional[List[int]] = Field(default_factory=list, description="Debug array status list")
    ver: Optional[List[str]] = Field(default_factory=list, description="Application software version and hardware version")
    lib: Optional[str] = Field("", description="Device firmware library version")


class VTSPacket(BaseModel):
    uid: Union[str, int] = Field(..., description="Unique unit/device hardware ID (software selectable or IMEI)")
    info: VTSInfo = Field(..., description="VTS packet transaction and timing info object")
    gps: VTSGps = Field(..., description="GPS positioning coordinates and speed metrics object")
    io: Optional[VTSIo] = Field(None, description="Digital and analog IO state object")
    pwr: Optional[VTSPwr] = Field(None, description="Power and voltage status object")
    dbg: Optional[VTSDbg] = Field(None, description="Debugging and system hardware version object")


class VTSResponse(BaseModel):
    result: bool = Field(True, description="Indicates if telemetry packet was successfully recorded")
    msg: str = Field("Data Success", description="Message response for the VTS tracker device")


class RawPacketResponse(BaseModel):
    id: int
    device_uid: Optional[str] = None
    message_id: Optional[int] = None
    packet_data: dict = Field(..., description="Full raw packet payload")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
