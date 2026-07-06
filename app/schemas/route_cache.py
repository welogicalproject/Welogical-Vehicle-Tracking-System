from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class RouteCacheBase(BaseModel):
    cache_key: str = Field(..., description="Deterministic normalized route request cache key")
    provider: str = Field("google", description="Routing provider name")
    provider_api: str = Field("routes", description="Provider API family")
    provider_version: Optional[str] = None
    route_schema_version: int = 1
    travel_mode: str = "DRIVE"
    routing_preference: Optional[str] = None
    polyline_quality: Optional[str] = None
    coordinate_precision: int = 5
    origin_lat_raw: float
    origin_lon_raw: float
    destination_lat_raw: float
    destination_lon_raw: float
    origin_lat_normalized: float
    origin_lon_normalized: float
    destination_lat_normalized: float
    destination_lon_normalized: float
    waypoint_hash: Optional[str] = None
    options_hash: str
    request_hash: str
    encoded_polyline: Optional[str] = None
    polyline_format: Optional[str] = None
    distance_meters: Optional[int] = None
    duration_seconds: Optional[int] = None
    static_duration_seconds: Optional[int] = None
    traffic_duration_seconds: Optional[int] = None
    bounds: Optional[Dict[str, Any]] = None
    provider_response_summary: Optional[Dict[str, Any]] = None
    status: str = "pending"
    created_by: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    invalidated_reason: Optional[str] = None


class RouteCacheCreate(RouteCacheBase):
    pass


class RouteCacheUpdate(BaseModel):
    encoded_polyline: Optional[str] = None
    polyline_format: Optional[str] = None
    distance_meters: Optional[int] = None
    duration_seconds: Optional[int] = None
    static_duration_seconds: Optional[int] = None
    traffic_duration_seconds: Optional[int] = None
    bounds: Optional[Dict[str, Any]] = None
    provider_response_summary: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    invalidated_reason: Optional[str] = None


class RouteCacheResponse(RouteCacheBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripRouteCacheLinkBase(BaseModel):
    trip_id: int
    route_cache_id: int
    trip_fingerprint: Optional[str] = None
    route_source: str = "cache_hit"
    is_current: bool = True


class TripRouteCacheLinkCreate(TripRouteCacheLinkBase):
    pass


class TripRouteCacheLinkUpdate(BaseModel):
    route_cache_id: Optional[int] = None
    trip_fingerprint: Optional[str] = None
    route_source: Optional[str] = None
    is_current: Optional[bool] = None


class TripRouteCacheLinkResponse(TripRouteCacheLinkBase):
    id: int
    linked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoogleRouteUsageEventBase(BaseModel):
    period_month: str = Field(..., description="Usage month in YYYY-MM format")
    event_type: str
    cache_key: Optional[str] = None
    route_cache_id: Optional[int] = None
    trip_id: Optional[int] = None
    status: str
    response_time_ms: Optional[int] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, validation_alias="metadata_json")


class GoogleRouteUsageEventCreate(GoogleRouteUsageEventBase):
    model_config = ConfigDict(populate_by_name=True)


class GoogleRouteUsageEventResponse(GoogleRouteUsageEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
