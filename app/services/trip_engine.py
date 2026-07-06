from datetime import datetime, timezone
from typing import Optional
import logging
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.trip import Trip
from app.models.location import Location
from app.models.device_config import DeviceConfig
from app.models.enums import TripStatus
from app.utils.geo import haversine_distance_km

logger = logging.getLogger(__name__)

async def get_vehicle_speed_limit(db: AsyncSession, vehicle_id: int) -> float:
    """
    Retrieve the configured speed limit for a vehicle, or fallback to the default.
    """
    try:
        stmt = select(DeviceConfig).where(DeviceConfig.vehicle_id == vehicle_id)
        res = await db.execute(stmt)
        config = res.scalars().first()
        if config and config.speed_limit is not None:
            return float(config.speed_limit)
    except Exception as e:
        logger.warning(f"Error fetching vehicle speed limit: {e}")
    return settings.DEFAULT_SPEED_LIMIT

async def evaluate_coordinate_for_trip(
    db: AsyncSession,
    vehicle_id: int,
    lat: float,
    lon: float,
    speed: float,
    timestamp: datetime,
    ign: Optional[int] = None,
    speed_limit: Optional[float] = None
) -> Optional[Trip]:
    """
    Core state-machine of the Trip Engine. Processes a single coordinate log
    to update or close the current active trip, or initialize a new one.
    """
    # Defensive checks for malformed data
    if lat is None or lon is None or speed is None or timestamp is None:
        logger.warning(f"Skipping malformed coordinate telemetry in Trip Engine: lat={lat}, lon={lon}, speed={speed}, time={timestamp}")
        return None

    # Handle timezone differences defensively
    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    if speed_limit is None:
        speed_limit = await get_vehicle_speed_limit(db, vehicle_id)

    # Fetch active trip
    stmt = select(Trip).where(
        and_(
            Trip.vehicle_id == vehicle_id,
            Trip.is_active == True
        )
    ).limit(1)
    res = await db.execute(stmt)
    active_trip = res.scalars().first()

    if active_trip:
        gap_sec = (timestamp - active_trip.end_time).total_seconds()
        
        # 1. Edge Case: Same timestamp or out-of-order packet
        if gap_sec <= 0:
            logger.warning(f"Out-of-order or duplicate telemetry received in Trip Engine for vehicle={vehicle_id}. Current timestamp: {timestamp}, Active end_time: {active_trip.end_time}. Skipping state-machine evaluate.")
            return active_trip

        # 2. Edge Case: Long communication loss / gap timeout
        if gap_sec > settings.TRIP_GAP_TIMEOUT:
            logger.info(f"Trip gap timeout reached ({gap_sec}s > {settings.TRIP_GAP_TIMEOUT}s). Closing current trip ID={active_trip.id}.")
            active_trip.is_active = False
            active_trip.status = TripStatus.COMPLETED
            # Check if this new packet starts a new trip
            if speed >= settings.TRIP_START_SPEED_THRESHOLD or ign == 1:
                return await _start_new_trip(db, vehicle_id, lat, lon, speed, timestamp, speed_limit)
            return None

        # 3. Standard active trip update
        dist_delta = haversine_distance_km(active_trip.end_lat, active_trip.end_lon, lat, lon)
        
        # GPS Drift mitigation: Ignore tiny movements and speed spikes if ignition is Off
        if ign == 0 and speed < settings.TRIP_START_SPEED_THRESHOLD and dist_delta < 0.01:
            dist_delta = 0.0

        active_trip.distance += dist_delta
        active_trip.maximum_speed = max(active_trip.maximum_speed, speed)
        active_trip.packet_count += 1

        if speed > speed_limit:
            active_trip.overspeed_count += 1

        active_trip.end_time = timestamp
        active_trip.duration = (timestamp - active_trip.start_time).total_seconds()
        
        if speed <= 0.5:
            active_trip.idle_time += gap_sec

        active_trip.end_lat = lat
        active_trip.end_lon = lon

        if active_trip.duration > 0:
            active_trip.average_speed = active_trip.distance / (active_trip.duration / 3600.0)
        else:
            active_trip.average_speed = speed

        # 4. Evaluate End Trip conditions
        # Condition A: Ignition turns Off
        if ign == 0:
            logger.info(f"Ignition turned OFF. Closing trip ID={active_trip.id} for vehicle={vehicle_id}.")
            active_trip.is_active = False
            active_trip.status = TripStatus.COMPLETED
            
            # Post-completion drift cleanup: if trip distance/duration is too short, mark cancelled
            if active_trip.distance < 0.1 and active_trip.duration < 60:
                active_trip.status = TripStatus.CANCELLED
            return active_trip

        # Condition B: Speed below threshold for too long (without ignition pin)
        if ign is None or ign == 0:
            # Query last time vehicle was actively moving in this trip
            last_mov_stmt = select(Location.timestamp).where(
                and_(
                    Location.vehicle_id == vehicle_id,
                    Location.speed >= settings.TRIP_START_SPEED_THRESHOLD,
                    Location.timestamp >= active_trip.start_time
                )
            ).order_by(Location.timestamp.desc()).limit(1)
            last_mov_res = await db.execute(last_mov_stmt)
            last_moving_ts = last_mov_res.scalars().first()

            reference_time = last_moving_ts or active_trip.start_time
            idle_duration = (timestamp - reference_time).total_seconds()
            
            if idle_duration > settings.TRIP_END_TIMEOUT:
                logger.info(f"Vehicle idle for too long ({idle_duration}s > {settings.TRIP_END_TIMEOUT}s). Closing trip ID={active_trip.id} due to inactivity.")
                active_trip.is_active = False
                active_trip.status = TripStatus.COMPLETED
                
                # Check filter to prevent GPS drift trips
                if active_trip.distance < 0.1 and active_trip.duration < 60:
                    active_trip.status = TripStatus.CANCELLED

        return active_trip

    else:
        # No active trip. Check start condition
        if speed >= settings.TRIP_START_SPEED_THRESHOLD or ign == 1:
            return await _start_new_trip(db, vehicle_id, lat, lon, speed, timestamp, speed_limit)

    return None

async def _start_new_trip(
    db: AsyncSession,
    vehicle_id: int,
    lat: float,
    lon: float,
    speed: float,
    timestamp: datetime,
    speed_limit: float
) -> Trip:
    """Helper to initialize a new Trip database record."""
    logger.info(f"Trip Engine: Starting a new trip for vehicle={vehicle_id} at {timestamp}.")
    new_trip = Trip(
        vehicle_id=vehicle_id,
        start_time=timestamp,
        end_time=timestamp,
        duration=0.0,
        distance=0.0,
        average_speed=speed,
        maximum_speed=speed,
        idle_time=0.0,
        start_lat=lat,
        start_lon=lon,
        end_lat=lat,
        end_lon=lon,
        packet_count=1,
        overspeed_count=1 if speed > speed_limit else 0,
        status=TripStatus.ACTIVE,
        is_active=True
    )
    db.add(new_trip)
    await db.flush()
    return new_trip

async def rebuild_vehicle_trips(db: AsyncSession, vehicle_id: int) -> int:
    """
    Idempotent logic to clear existing trips for a vehicle and sequentially rebuild
    them chronologically from saved location records.
    """
    logger.info(f"Rebuilding trip history for vehicle={vehicle_id}.")
    
    # 1. Clear existing trips
    del_stmt = delete(Trip).where(Trip.vehicle_id == vehicle_id)
    await db.execute(del_stmt)
    await db.flush()

    # 2. Query location logs chronologically
    loc_stmt = select(Location).where(Location.vehicle_id == vehicle_id).order_by(Location.timestamp.asc())
    loc_res = await db.execute(loc_stmt)
    locations = loc_res.scalars().all()

    # Fetch speed limit config
    speed_limit = await get_vehicle_speed_limit(db, vehicle_id)

    # 3. Sequential evaluation
    trip_count = 0
    for loc in locations:
        # Extract ignition from extra_data if available
        ign = None
        if loc.extra_data and "io" in loc.extra_data:
            ign = loc.extra_data["io"].get("ign")

        await evaluate_coordinate_for_trip(
            db,
            vehicle_id=vehicle_id,
            lat=loc.latitude,
            lon=loc.longitude,
            speed=loc.speed,
            timestamp=loc.timestamp,
            ign=ign,
            speed_limit=speed_limit
        )

    # Close any lingering active trip at the end of history
    stmt = select(Trip).where(
        and_(
            Trip.vehicle_id == vehicle_id,
            Trip.is_active == True
        )
    ).limit(1)
    active_res = await db.execute(stmt)
    active_trip = active_res.scalars().first()
    if active_trip:
        active_trip.is_active = False
        active_trip.status = TripStatus.COMPLETED

    # Flush changes
    await db.flush()
    
    # Query final count of completed trips
    cnt_stmt = select(Trip).where(Trip.vehicle_id == vehicle_id)
    cnt_res = await db.execute(cnt_stmt)
    final_count = len(cnt_res.scalars().all())
    
    logger.info(f"Rebuild completed for vehicle={vehicle_id}. Generated {final_count} trips.")
    return final_count
