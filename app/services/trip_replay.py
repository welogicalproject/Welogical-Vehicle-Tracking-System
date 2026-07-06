import logging
from typing import List, Callable
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location
from app.models.trip import Trip
from app.schemas.trip_analytics import ReplayResponse, ReplayPoint
from app.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

# Type definition for a downsampling algorithm
# Takes a list of Location models, a target max points count, and a multiplier, and returns a simplified list.
DownsamplingStrategy = Callable[[List[Location], int, int], List[Location]]

def simple_skipping_downsampler(points: List[Location], target_count: int, multiplier: int) -> List[Location]:
    """
    A basic, fast skipping algorithm that decimates coordinates based on a step size
    derived from the total points count, target count, and optional multiplier.
    """
    total = len(points)
    if total <= target_count:
        return points

    # Higher playback speeds or larger dataset sizes lead to larger skip steps
    step = max(1, int(total / target_count) * multiplier)
    
    # Decimate points
    sampled_points = points[::step]
    
    # Always include the last point to preserve the trip destination
    if sampled_points[-1].id != points[-1].id:
        sampled_points.append(points[-1])
        
    return sampled_points

# Default downsampler
DEFAULT_DOWNSAMPLER: DownsamplingStrategy = simple_skipping_downsampler

async def get_trip_replay_points(
    db: AsyncSession,
    vehicle_id: int,
    trip_id: int,
    multiplier: int = 1,
    target_max_points: int = 1000,
    downsample_strategy: DownsamplingStrategy = DEFAULT_DOWNSAMPLER
) -> ReplayResponse:
    """
    Retrieve chronologically ordered locations for a trip and downsample them
    using a pluggable decimation algorithm to remain responsive for large lists (100,000+ points).
    
    Future Extension Note:
    - You can swap the 'downsample_strategy' parameter to use Douglas-Peucker (Ramer-Douglas-Peucker)
      or Kalman-filter based adaptive sampling for smoother route simplifications.
    """
    # 1. Verify trip exists
    trip_stmt = select(Trip).where(and_(Trip.id == trip_id, Trip.vehicle_id == vehicle_id))
    trip_res = await db.execute(trip_stmt)
    trip = trip_res.scalars().first()
    if not trip:
        raise EntityNotFoundError(f"Trip with ID {trip_id} not found for vehicle {vehicle_id}")

    # 2. Fetch locations
    loc_stmt = select(Location).where(
        and_(
            Location.vehicle_id == vehicle_id,
            Location.timestamp >= trip.start_time,
            Location.timestamp <= trip.end_time
        )
    ).order_by(Location.timestamp.asc())
    
    loc_res = await db.execute(loc_stmt)
    locations = loc_res.scalars().all()
    total_count = len(locations)

    # 3. Apply pluggable downsampling
    sampled_locations = downsample_strategy(locations, target_max_points, multiplier)
    sampled_count = len(sampled_locations)

    # 4. Map to ReplayPoint schema
    points: List[ReplayPoint] = []
    for loc in sampled_locations:
        # Extract heading and ignition from extra_data if they exist
        heading = None
        ign = None
        extra = None
        if loc.extra_data:
            extra = loc.extra_data
            if "gps_details" in loc.extra_data:
                heading = loc.extra_data["gps_details"].get("dir")
            if "io" in loc.extra_data:
                ign = loc.extra_data["io"].get("ign")

        points.append(
            ReplayPoint(
                timestamp=loc.timestamp,
                lat=loc.latitude,
                lon=loc.longitude,
                speed=loc.speed,
                heading=heading,
                ignition=ign,
                extra=extra
            )
        )

    downsampled = sampled_count < total_count
    downsample_ratio = sampled_count / total_count if total_count > 0 else 1.0

    logger.info(
        f"Replay service: vehicle={vehicle_id}, trip={trip_id}, total_points={total_count}, "
        f"sampled_points={sampled_count}, ratio={downsample_ratio:.2f}, downsampled={downsampled}"
    )

    return ReplayResponse(
        trip_id=trip.id,
        vehicle_id=trip.vehicle_id,
        points=points,
        total_points=total_count,
        downsampled=downsampled,
        downsample_ratio=downsample_ratio
    )
