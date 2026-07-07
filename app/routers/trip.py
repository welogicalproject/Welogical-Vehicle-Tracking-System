from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.trip import Trip
from app.models.enums import TripStatus
from app.models.route_cache import RouteCache, TripRouteCacheLink
from app.schemas.trip import TripResponse
from app.schemas.trip_analytics import TripSummaryResponse, ReplayResponse
from app.schemas.route_cache import RouteCacheResponse
from app.services.trip_engine import rebuild_vehicle_trips
from app.services.trip_analytics import calculate_trip_summary
from app.services.trip_replay import get_trip_replay_points
from app.services.trip_export import serialize_trip_to_geojson, get_trip_csv_content
from app.services.route_cache import get_or_compute_trip_route
from app.crud.vehicle import get_vehicle
from app.exceptions import EntityNotFoundError

router = APIRouter(tags=["Trips"])

@router.get("/vehicles/{vehicle_id}/trips", response_model=List[TripResponse])
async def get_vehicle_trips(
    vehicle_id: int,
    start_time: Optional[datetime] = Query(None, description="ISO-formatted UTC timestamp filter (e.g. 2026-06-23T00:00:00Z)"),
    end_time: Optional[datetime] = Query(None, description="ISO-formatted UTC timestamp filter"),
    status_filter: Optional[TripStatus] = Query(None, alias="status", description="Filter trips by status (ACTIVE, COMPLETED, CANCELLED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve trip logs history for a specific vehicle with filters.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)

    query = select(Trip).where(Trip.vehicle_id == vehicle_id)

    if start_time:
        query = query.where(Trip.start_time >= start_time)
    if end_time:
        query = query.where(Trip.end_time <= end_time)
    if status_filter:
        query = query.where(Trip.status == status_filter)

    query = query.order_by(Trip.start_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("/vehicles/{vehicle_id}/trips/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_trips(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Idempotently recalculate and rebuild all trips for a vehicle from historical location records.
    Returns the total number of trips generated.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    
    trip_count = await rebuild_vehicle_trips(db, vehicle_id)
    await db.commit()
    return {
        "result": True,
        "vehicle_id": vehicle_id,
        "trips_created": trip_count,
        "msg": "Trip history successfully rebuilt from coordinate logs"
    }

@router.get("/vehicles/{vehicle_id}/trips/{trip_id}/summary", response_model=TripSummaryResponse)
async def get_trip_summary(
    vehicle_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve advanced analytics summary for a specific trip, including stop events,
    overspeeds, and driver score calculation.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    return await calculate_trip_summary(db, vehicle_id, trip_id)

@router.get("/vehicles/{vehicle_id}/trips/{trip_id}/replay", response_model=ReplayResponse)
async def get_trip_replay(
    vehicle_id: int,
    trip_id: int,
    multiplier: int = Query(1, ge=1, le=8, description="Playback speed multiplier (1x, 2x, 4x, 8x) for downsampling calculations"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve ordered coordinates and telemetry data points for route playback,
    with built-in downsampling logic to support larger tracks.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    return await get_trip_replay_points(db, vehicle_id, trip_id, multiplier)

@router.get("/vehicles/{vehicle_id}/trips/{trip_id}/geojson")
async def get_trip_geojson(
    vehicle_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve trip route formatted as a GeoJSON Feature containing a LineString geometry
    for direct integration with Leaflet, Mapbox, or OpenLayers.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    geojson_data = await serialize_trip_to_geojson(db, vehicle_id, trip_id)
    return geojson_data

@router.get("/vehicles/{vehicle_id}/trips/{trip_id}/export")
async def export_trip_csv(
    vehicle_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Export trip coordinate logging and telemetry as a downloadable CSV.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    csv_data = await get_trip_csv_content(db, vehicle_id, trip_id)
    
    filename = f"trip_{trip_id}_vehicle_{vehicle_id}_export.csv"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "text/csv"
    }
    return Response(content=csv_data, headers=headers)

@router.get("/vehicles/{vehicle_id}/trips/{trip_id}/google-route", response_model=RouteCacheResponse)
async def get_trip_google_route(
    vehicle_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch the cached snapped Google route for a completed trip.
    Returns HTTP 404 if not generated yet.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    
    # Check if a link exists
    link_stmt = select(TripRouteCacheLink).where(
        and_(
            TripRouteCacheLink.trip_id == trip_id,
            TripRouteCacheLink.is_current == True
        )
    )
    link_res = await db.execute(link_stmt)
    link = link_res.scalars().first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google route has not been generated for this trip. Use POST to trigger generation."
        )
        
    cache_stmt = select(RouteCache).where(RouteCache.id == link.route_cache_id)
    cache_res = await db.execute(cache_stmt)
    route_cache = cache_res.scalars().first()
    
    if not route_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cached route cache entry not found for this trip link."
        )
        
    return route_cache

@router.post("/vehicles/{vehicle_id}/trips/{trip_id}/google-route", response_model=RouteCacheResponse, status_code=status.HTTP_201_CREATED)
async def generate_trip_google_route(
    vehicle_id: int,
    trip_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger Google Route API snapping and caching for a completed trip.
    Returns the cached route directly (200 OK) if already generated.
    """
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    
    try:
        route_cache = await get_or_compute_trip_route(db, vehicle_id, trip_id)
        return route_cache
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"External route calculation failed: {e}")

