import logging
import hashlib
from typing import List, Tuple, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database import get_db
from app.config import settings
from app.models.route_cache import RouteCache
from app.services.google_routes import call_google_routes_api, lock_registry
from app.services.route_cache import log_usage_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["Routes"])


class SnapPathRequest(BaseModel):
    waypoints: List[Tuple[float, float]] = Field(..., description="Ordered list of (latitude, longitude) waypoints to snap to road")
    travel_mode: str = Field("DRIVE", description="Travel mode (DRIVE, BICYCLE, WALK, etc.)")


class CoordinateResponse(BaseModel):
    lat: float
    lng: float


class SnapPathResponse(BaseModel):
    route_cache_id: int
    distance_meters: Optional[int]
    duration_seconds: Optional[int]
    status: str
    coordinates: List[CoordinateResponse]


def decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """Decodes a Google encoded polyline into a list of (lat, lon) tuples."""
    if not encoded:
        return []
    
    coordinates = []
    index = 0
    len_encoded = len(encoded)
    lat = 0
    lng = 0

    while index < len_encoded:
        # Decode latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if not (b & 0x20):
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Decode longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if not (b & 0x20):
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates


def calculate_waypoints_cache_key(waypoints: List[Tuple[float, float]], travel_mode: str = "DRIVE") -> Tuple[str, str, str, str]:
    """Calculate deterministic cache key and option hashes for waypoint sequence."""
    normalized_wps = [(round(wp[0], 5), round(wp[1], 5)) for wp in waypoints]
    wps_str = ";".join([f"{lat:.5f},{lon:.5f}" for lat, lon in normalized_wps])
    raw_key = f"google:routes:{travel_mode}:waypoints:{wps_str}"
    
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    options_hash = hashlib.md5(travel_mode.encode("utf-8")).hexdigest()
    request_hash = cache_key
    waypoint_hash = hashlib.md5(wps_str.encode("utf-8")).hexdigest()
    
    return cache_key, options_hash, request_hash, waypoint_hash


@router.post("/snap-path", response_model=SnapPathResponse)
async def snap_path(
    payload: SnapPathRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Snap waypoints list to road network.
    Checks central route cache before executing external Google Routes API calls.
    """
    if len(payload.waypoints) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 waypoints (origin and destination) are required to snap a path."
        )

    # 1. Compute Cache Keys
    cache_key, options_hash, request_hash, waypoint_hash = calculate_waypoints_cache_key(
        payload.waypoints, payload.travel_mode
    )

    # 2. Check Route Cache
    stmt = select(RouteCache).where(
        and_(
            RouteCache.cache_key == cache_key,
            RouteCache.status == "success"
        )
    )
    res = await db.execute(stmt)
    cached_entry = res.scalars().first()

    if cached_entry:
        await log_usage_event(
            db, event_type="CACHE_HIT", status="SUCCESS",
            cache_key=cache_key, route_cache_id=cached_entry.id
        )
        coords = decode_polyline(cached_entry.encoded_polyline or "")
        return SnapPathResponse(
            route_cache_id=cached_entry.id,
            distance_meters=cached_entry.distance_meters,
            duration_seconds=cached_entry.duration_seconds,
            status=cached_entry.status,
            coordinates=[CoordinateResponse(lat=c[0], lng=c[1]) for c in coords]
        )

    # 3. Cache Miss - Concurrency Lock on Cache Key
    lock = await lock_registry.get_lock(cache_key)
    async with lock:
        # Re-check cache inside lock to prevent stampede
        res = await db.execute(stmt)
        cached_entry = res.scalars().first()
        if cached_entry:
            await log_usage_event(
                db, event_type="CACHE_HIT", status="SUCCESS",
                cache_key=cache_key, route_cache_id=cached_entry.id
            )
            coords = decode_polyline(cached_entry.encoded_polyline or "")
            return SnapPathResponse(
                route_cache_id=cached_entry.id,
                distance_meters=cached_entry.distance_meters,
                duration_seconds=cached_entry.duration_seconds,
                status=cached_entry.status,
                coordinates=[CoordinateResponse(lat=c[0], lng=c[1]) for c in coords]
            )

        # Cache miss - call Google Routes API
        if not settings.GOOGLE_ROUTES_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Routes Integration is currently disabled."
            )

        start_time = datetime.now()
        api_status = "UNKNOWN"
        error_code = None

        try:
            origin_lat, origin_lon = payload.waypoints[0]
            dest_lat, dest_lon = payload.waypoints[-1]
            intermediates = payload.waypoints[1:-1]

            result = await call_google_routes_api(
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                destination_lat=dest_lat,
                destination_lon=dest_lon,
                waypoints=intermediates
            )

            api_status = result["status"]

            # Save in Route Cache table
            db_cache = RouteCache(
                cache_key=cache_key,
                provider="google",
                provider_api="routes",
                route_schema_version=1,
                travel_mode=payload.travel_mode,
                coordinate_precision=5,
                origin_lat_raw=origin_lat,
                origin_lon_raw=origin_lon,
                destination_lat_raw=dest_lat,
                destination_lon_raw=dest_lon,
                origin_lat_normalized=round(origin_lat, 5),
                origin_lon_normalized=round(origin_lon, 5),
                destination_lat_normalized=round(dest_lat, 5),
                destination_lon_normalized=round(dest_lon, 5),
                waypoint_hash=waypoint_hash,
                options_hash=options_hash,
                request_hash=request_hash,
                encoded_polyline=result.get("encoded_polyline"),
                distance_meters=result.get("distance_meters"),
                duration_seconds=result.get("duration_seconds"),
                static_duration_seconds=result.get("duration_seconds"),
                status="success" if api_status == "SUCCESS" else "failed",
                created_by="simulator"
            )

            db.add(db_cache)
            await db.commit()
            await db.refresh(db_cache)

            # Log usage event
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await log_usage_event(
                db, event_type="API_CALL", status="SUCCESS" if api_status == "SUCCESS" else "FAILED",
                cache_key=cache_key, route_cache_id=db_cache.id,
                response_time_ms=elapsed_ms, error_code="ZERO_RESULTS" if api_status == "ZERO_RESULTS" else None
            )

            if api_status != "SUCCESS":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google Routes snapping failed with status: {api_status}"
                )

            coords = decode_polyline(db_cache.encoded_polyline or "")
            return SnapPathResponse(
                route_cache_id=db_cache.id,
                distance_meters=db_cache.distance_meters,
                duration_seconds=db_cache.duration_seconds,
                status=db_cache.status,
                coordinates=[CoordinateResponse(lat=c[0], lng=c[1]) for c in coords]
            )

        except Exception as e:
            await db.rollback()
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await log_usage_event(
                db, event_type="API_CALL", status="FAILED",
                cache_key=cache_key, response_time_ms=elapsed_ms, error_code=str(e)[:50]
            )
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to snap path waypoints: {str(e)}"
            )
