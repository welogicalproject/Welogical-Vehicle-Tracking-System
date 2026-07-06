from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class StopEvent(BaseModel):
    start_time: datetime = Field(..., description="Timestamp when the vehicle stopped")
    end_time: datetime = Field(..., description="Timestamp when the vehicle resumed moving")
    duration: float = Field(..., description="Duration of stop in seconds")
    latitude: float = Field(..., description="Latitude coordinate of the stop")
    longitude: float = Field(..., description="Longitude coordinate of the stop")

class OverspeedEvent(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp when overspeed occurred")
    speed: float = Field(..., description="Vehicle speed at that point (km/h)")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")

class TripSummaryResponse(BaseModel):
    trip_id: int
    vehicle_id: int
    duration: float = Field(..., description="Total trip duration in seconds")
    distance: float = Field(..., description="Total trip distance in kilometers")
    average_speed: float = Field(..., description="Average speed across the entire trip (km/h)")
    moving_time: float = Field(..., description="Total duration vehicle was moving (seconds)")
    idle_time: float = Field(..., description="Total duration vehicle was idling (seconds)")
    average_moving_speed: float = Field(..., description="Average speed when moving (km/h)")
    maximum_speed: float = Field(..., description="Maximum speed recorded during the trip (km/h)")
    packet_count: int = Field(..., description="Total GPS coordinates in the trip")
    average_packet_interval: float = Field(..., description="Average seconds between packets")
    stop_count: int = Field(..., description="Total stopped events detected")
    longest_stop: float = Field(..., description="Duration of the longest stop (seconds)")
    overspeed_count: int = Field(..., description="Number of points exceeding speed limit")
    driving_score: int = Field(..., description="Driving behavior score (0-100)")
    stops: List[StopEvent] = Field(default=[], description="List of detected stops during the trip")
    overspeeds: List[OverspeedEvent] = Field(default=[], description="List of overspeed instances")

    class Config:
        from_attributes = True

class ReplayPoint(BaseModel):
    timestamp: datetime
    lat: float
    lon: float
    speed: float
    heading: Optional[float] = None
    ignition: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

class ReplayResponse(BaseModel):
    trip_id: int
    vehicle_id: int
    points: List[ReplayPoint]
    total_points: int
    downsampled: bool
    downsample_ratio: float
