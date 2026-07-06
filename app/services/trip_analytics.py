from datetime import datetime
from typing import List, Tuple, Optional
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.trip import Trip
from app.models.location import Location
from app.utils.geo import haversine_distance_km
from app.schemas.trip_analytics import TripSummaryResponse, StopEvent, OverspeedEvent
from app.services.trip_scoring import calculate_driving_score
from app.services.trip_engine import get_vehicle_speed_limit
from app.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

async def calculate_trip_summary(db: AsyncSession, vehicle_id: int, trip_id: int) -> TripSummaryResponse:
    """
    Calculate advanced trip analytics, detect stops (with coordinate stability),
    extract overspeed events, and generate a driving score for a completed trip.
    """
    # 1. Fetch trip record
    stmt = select(Trip).where(and_(Trip.id == trip_id, Trip.vehicle_id == vehicle_id))
    res = await db.execute(stmt)
    trip = res.scalars().first()
    if not trip:
        raise EntityNotFoundError(f"Trip with ID {trip_id} not found for vehicle {vehicle_id}")

    # 2. Fetch all locations for this trip chronologically
    loc_stmt = select(Location).where(
        and_(
            Location.vehicle_id == vehicle_id,
            Location.timestamp >= trip.start_time,
            Location.timestamp <= trip.end_time
        )
    ).order_by(Location.timestamp.asc())
    
    loc_res = await db.execute(loc_stmt)
    locations = loc_res.scalars().all()
    packet_count = len(locations)

    if packet_count < 2:
        # Fallback for very short trips or empty location lists
        return TripSummaryResponse(
            trip_id=trip.id,
            vehicle_id=trip.vehicle_id,
            duration=trip.duration,
            distance=trip.distance,
            average_speed=trip.average_speed,
            moving_time=trip.duration,
            idle_time=trip.idle_time,
            average_moving_speed=trip.average_speed,
            maximum_speed=trip.maximum_speed,
            packet_count=packet_count,
            average_packet_interval=0.0,
            stop_count=0,
            longest_stop=0.0,
            overspeed_count=trip.overspeed_count,
            driving_score=100,
            stops=[],
            overspeeds=[]
        )

    # Get speed limit configuration
    speed_limit = await get_vehicle_speed_limit(db, vehicle_id)

    # 3. Process locations for stops and overspeeds
    stops: List[StopEvent] = []
    overspeeds: List[OverspeedEvent] = []
    
    # Variables for stop detection
    potential_stop_points: List[Location] = []
    
    # Variables for overspeed grouping (to count unique overspeed events for scoring)
    overspeed_groups_count = 0
    in_overspeed_group = False

    # Variables for average packet interval
    total_interval_seconds = 0.0

    # Variables for idle time periods (idle = speed <= 0.5)
    long_idle_events_count = 0
    potential_idle_start: Optional[datetime] = None

    for i, loc in enumerate(locations):
        # Calculate packet interval
        if i > 0:
            total_interval_seconds += (loc.timestamp - locations[i-1].timestamp).total_seconds()

        # Stop Detection with speed threshold and coordinate stability
        if loc.speed < settings.TRIP_STOP_SPEED:
            if not potential_stop_points:
                potential_stop_points.append(loc)
            else:
                # Check coordinate stability: distance from starting point of potential stop
                start_pt = potential_stop_points[0]
                dist_from_start = haversine_distance_km(
                    start_pt.latitude, start_pt.longitude,
                    loc.latitude, loc.longitude
                )
                
                # Stability threshold = 20 meters (0.02 km)
                if dist_from_start < 0.02:
                    potential_stop_points.append(loc)
                else:
                    # Coordinate stability violated - evaluate previous sequence
                    stops = _evaluate_and_add_stop(potential_stop_points, stops)
                    potential_stop_points = [loc]  # Reset with current point
        else:
            # Vehicle is moving - evaluate potential stop sequence
            if potential_stop_points:
                stops = _evaluate_and_add_stop(potential_stop_points, stops)
                potential_stop_points = []

        # Overspeed Detection & Grouping
        if loc.speed > speed_limit:
            overspeeds.append(
                OverspeedEvent(
                    timestamp=loc.timestamp,
                    speed=loc.speed,
                    latitude=loc.latitude,
                    longitude=loc.longitude
                )
            )
            if not in_overspeed_group:
                overspeed_groups_count += 1
                in_overspeed_group = True
        else:
            in_overspeed_group = False

        # Idle tracking: continuous period where speed <= 0.5 (or ignition pin is off if present)
        # We classify idle as speed <= 0.5
        is_idle = loc.speed <= 0.5
        if is_idle:
            if potential_idle_start is None:
                potential_idle_start = loc.timestamp
        else:
            if potential_idle_start is not None:
                idle_dur = (loc.timestamp - potential_idle_start).total_seconds()
                if idle_dur >= 300:  # Long idle: > 5 minutes (300 seconds)
                    long_idle_events_count += 1
                potential_idle_start = None

    # Handle lingering stop at end of trip
    if potential_stop_points:
        stops = _evaluate_and_add_stop(potential_stop_points, stops)
        
    # Handle lingering idle at end of trip
    if potential_idle_start is not None:
        idle_dur = (locations[-1].timestamp - potential_idle_start).total_seconds()
        if idle_dur >= 300:
            long_idle_events_count += 1

    # 4. Aggregations & Statistics
    duration = (trip.end_time - trip.start_time).total_seconds()
    distance = trip.distance
    average_speed = trip.average_speed
    maximum_speed = trip.maximum_speed
    average_packet_interval = total_interval_seconds / (packet_count - 1)

    # Stopped duration calculation
    stopped_duration = sum(s.duration for s in stops)
    moving_time = max(0.0, duration - stopped_duration)
    
    # Average moving speed (only when vehicle is actually moving)
    if moving_time > 0:
        average_moving_speed = distance / (moving_time / 3600.0)
    else:
        average_moving_speed = 0.0

    longest_stop = max((s.duration for s in stops), default=0.0)
    stop_count = len(stops)

    # 5. Calculate Driving Score
    driving_score = calculate_driving_score(
        overspeed_events_count=overspeed_groups_count,
        long_idle_events_count=long_idle_events_count
    )

    return TripSummaryResponse(
        trip_id=trip.id,
        vehicle_id=trip.vehicle_id,
        duration=duration,
        distance=distance,
        average_speed=average_speed,
        moving_time=moving_time,
        idle_time=trip.idle_time,
        average_moving_speed=min(average_moving_speed, maximum_speed),
        maximum_speed=maximum_speed,
        packet_count=packet_count,
        average_packet_interval=average_packet_interval,
        stop_count=stop_count,
        longest_stop=longest_stop,
        overspeed_count=len(overspeeds),
        driving_score=driving_score,
        stops=stops,
        overspeeds=overspeeds
    )

def _evaluate_and_add_stop(points: List[Location], stops: List[StopEvent]) -> List[StopEvent]:
    """Helper to check if a potential stop sequence satisfies the duration threshold."""
    if len(points) >= 2:
        start_time = points[0].timestamp
        end_time = points[-1].timestamp
        duration = (end_time - start_time).total_seconds()
        
        if duration >= settings.TRIP_STOP_DURATION:
            stops.append(
                StopEvent(
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    latitude=points[0].latitude,
                    longitude=points[0].longitude
                )
            )
    return stops
