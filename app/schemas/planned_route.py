from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PlannedRoutePointBase(BaseModel):
    sequence_number: int = Field(..., description="Sequence order of the coordinate on the path")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the route point")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the route point")


class PlannedRoutePointCreate(PlannedRoutePointBase):
    pass


class PlannedRoutePointResponse(PlannedRoutePointBase):
    id: int
    route_id: int

    model_config = ConfigDict(from_attributes=True)


class PlannedRouteBase(BaseModel):
    name: str = Field(..., description="Name of the planned route")
    start_location: str = Field(..., description="Name of the starting location")
    destination: str = Field(..., description="Name of the destination")
    distance: float = Field(..., description="Total distance of the route in kilometers")
    estimated_duration: int = Field(..., description="Estimated travel duration in seconds")


class PlannedRouteCreate(PlannedRouteBase):
    points: List[PlannedRoutePointCreate] = Field(..., description="Ordered list of route points")


class PlannedRouteResponse(PlannedRouteBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    points: List[PlannedRoutePointResponse]
    current_point_index: Optional[int] = 0
    progress_percentage: Optional[float] = 0.0
    last_coordinate_index: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class VehicleRouteAssignmentBase(BaseModel):
    vehicle_id: int
    route_id: int


class VehicleRouteAssignmentCreate(VehicleRouteAssignmentBase):
    pass


class VehicleRouteAssignmentResponse(VehicleRouteAssignmentBase):
    id: int
    assigned_at: datetime
    is_active: bool
    current_point_index: int
    progress_percentage: float
    last_coordinate_index: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteProgressUpdate(BaseModel):
    current_point_index: int
    progress_percentage: float
    last_coordinate_index: int



class PlannedRouteStatusUpdate(BaseModel):
    status: str = Field(..., description="New status of the route (Pending, Assigned, Running, Completed)")
