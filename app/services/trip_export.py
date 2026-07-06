import csv
import io
import logging
from typing import Dict, Any, Generator
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location
from app.models.trip import Trip
from app.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

async def serialize_trip_to_geojson(db: AsyncSession, vehicle_id: int, trip_id: int) -> Dict[str, Any]:
    """
    Generate GeoJSON LineString for a trip's GPS coordinate trail.
    GeoJSON coordinates format requires: [longitude, latitude].
    """
    # 1. Fetch trip record
    trip_stmt = select(Trip).where(and_(Trip.id == trip_id, Trip.vehicle_id == vehicle_id))
    trip_res = await db.execute(trip_stmt)
    trip = trip_res.scalars().first()
    if not trip:
        raise EntityNotFoundError(f"Trip with ID {trip_id} not found for vehicle {vehicle_id}")

    # 2. Fetch locations chronologically
    loc_stmt = select(Location).where(
        and_(
            Location.vehicle_id == vehicle_id,
            Location.timestamp >= trip.start_time,
            Location.timestamp <= trip.end_time
        )
    ).order_by(Location.timestamp.asc())
    
    loc_res = await db.execute(loc_stmt)
    locations = loc_res.scalars().all()

    # 3. Format coordinates and properties
    coordinates = []
    timestamps = []
    speeds = []
    
    for loc in locations:
        # GeoJSON is [longitude, latitude]
        coordinates.append([loc.longitude, loc.latitude])
        timestamps.append(loc.timestamp.isoformat() + "Z")
        speeds.append(loc.speed)

    # Return standard GeoJSON Feature Collection
    geojson_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        },
        "properties": {
            "trip_id": trip.id,
            "vehicle_id": trip.vehicle_id,
            "start_time": trip.start_time.isoformat() + "Z",
            "end_time": trip.end_time.isoformat() + "Z",
            "distance_km": trip.distance,
            "duration_sec": trip.duration,
            "average_speed_kmh": trip.average_speed,
            "maximum_speed_kmh": trip.maximum_speed,
            "timestamps": timestamps,
            "speeds": speeds
        }
    }

    return geojson_feature

def generate_trip_csv_stream(db: AsyncSession, vehicle_id: int, trip_id: int) -> Generator[str, None, None]:
    """
    Generate and stream CSV representation of a trip's points in chunks
    to avoid heavy memory footprint for large point sets.
    """
    # Note: Since standard async DB operations don't allow clean yielding inside standard generator
    # within fastapi StreamingResponse easily, we query locations, then write generator stream.
    # To keep memory footprint low, we retrieve coordinates using a generator or execute in a block.
    # We will fetch the locations and build an in-memory string iterator/yield block.
    pass

async def get_trip_csv_content(db: AsyncSession, vehicle_id: int, trip_id: int) -> str:
    """
    Build complete CSV text contents for a trip's coordinates.
    Headers: Timestamp, Latitude, Longitude, Speed, Heading, Ignition, Status
    """
    # 1. Fetch trip record
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

    # 3. Generate CSV String
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed", "Heading", "Ignition", "Status"])
    
    for loc in locations:
        heading = None
        ign = None
        if loc.extra_data:
            if "gps_details" in loc.extra_data:
                heading = loc.extra_data["gps_details"].get("dir")
            if "io" in loc.extra_data:
                ign = loc.extra_data["io"].get("ign")

        writer.writerow([
            loc.timestamp.isoformat() + "Z",
            loc.latitude,
            loc.longitude,
            loc.speed,
            heading if heading is not None else "",
            ign if ign is not None else "",
            trip.status.value
        ])
        
    return output.getvalue()
