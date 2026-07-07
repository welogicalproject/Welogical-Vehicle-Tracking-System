from datetime import datetime, timezone, timedelta
from app.utils.datetime import normalize_datetime
from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device_command import DeviceCommand
from app.models.device_config import DeviceConfig
from app.models.event import Event
from app.models.location import Location
from app.models.vehicle import Vehicle
from app.models.driver_assignment import DriverAssignment
from app.schemas.vehicle import VehicleTrackingSnapshot
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.exceptions import DuplicateEntityError, EntityNotFoundError


async def get_vehicle(db: AsyncSession, vehicle_id: int) -> Vehicle:
    result = await db.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.assignments).selectinload(DriverAssignment.driver))
        .where(Vehicle.id == vehicle_id)
    )
    vehicle = result.scalars().first()
    if not vehicle:
        raise EntityNotFoundError(f"Vehicle with ID {vehicle_id} not found")
    return vehicle


async def get_vehicle_by_device_uid(db: AsyncSession, device_uid: str) -> Optional[Vehicle]:
    result = await db.execute(select(Vehicle).where(Vehicle.device_uid == device_uid))
    return result.scalars().first()


async def get_vehicles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Vehicle]:
    result = await db.execute(
        select(Vehicle)
        .options(selectinload(Vehicle.assignments).selectinload(DriverAssignment.driver))
        .where(Vehicle.status != "Archived")
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


def _vehicle_health(last_seen: Optional[datetime]) -> str:
    if not last_seen:
        return "Offline"

    normalized_last_seen = last_seen
    if normalized_last_seen.tzinfo is not None:
        normalized_last_seen = normalized_last_seen.astimezone(timezone.utc).replace(tzinfo=None)

    age_minutes = (datetime.now(timezone.utc).replace(tzinfo=None) - normalized_last_seen).total_seconds() / 60
    if age_minutes < 2:
        return "Healthy"
    if age_minutes <= 5:
        return "Warning"
    return "Offline"


def _movement_status(location: Optional[Location]) -> str:
    if not location:
        return "Offline"
    return "Moving" if location.speed > 0.1 else "Stopped"


async def get_tracking_snapshots(
    db: AsyncSession,
    vehicle_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit_per_vehicle: int = 500
) -> List[VehicleTrackingSnapshot]:
    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    vehicle_query = (
        select(Vehicle)
        .options(selectinload(Vehicle.assignments).selectinload(DriverAssignment.driver))
        .where(Vehicle.status != "Archived")
        .order_by(Vehicle.id.asc())
    )
    if vehicle_id is not None:
        vehicle_query = (
            select(Vehicle)
            .options(selectinload(Vehicle.assignments).selectinload(DriverAssignment.driver))
            .where(Vehicle.id == vehicle_id)
        ) # Allow loading archived vehicle detail for historical records

    vehicle_result = await db.execute(vehicle_query)
    vehicles = list(vehicle_result.scalars().all())
    if vehicle_id is not None and not vehicles:
        raise EntityNotFoundError(f"Vehicle with ID {vehicle_id} not found")
    if not vehicles:
        return []

    vehicle_ids = [vehicle.id for vehicle in vehicles]

    latest_locations: Dict[int, Location] = {}
    latest_location_result = await db.execute(
        select(Location)
        .where(Location.vehicle_id.in_(vehicle_ids))
        .order_by(Location.vehicle_id.asc(), Location.timestamp.desc())
    )
    for location in latest_location_result.scalars().all():
        latest_locations.setdefault(location.vehicle_id, location)

    route_query = (
        select(Location)
        .where(Location.vehicle_id.in_(vehicle_ids))
        .order_by(Location.vehicle_id.asc(), Location.timestamp.asc())
    )
    if start_time:
        route_query = route_query.where(Location.timestamp >= start_time)
    if end_time:
        route_query = route_query.where(Location.timestamp <= end_time)

    route_result = await db.execute(route_query)
    route_history: Dict[int, List[Location]] = {vehicle.id: [] for vehicle in vehicles}
    for location in route_result.scalars().all():
        history = route_history.setdefault(location.vehicle_id, [])
        if len(history) < limit_per_vehicle:
            history.append(location)

    latest_events: Dict[int, Event] = {}
    event_result = await db.execute(
        select(Event)
        .options(selectinload(Event.vehicle))
        .where(Event.vehicle_id.in_(vehicle_ids))
        .order_by(Event.vehicle_id.asc(), Event.created_at.desc())
    )
    for event in event_result.scalars().all():
        latest_events.setdefault(event.vehicle_id, event)

    latest_commands: Dict[int, DeviceCommand] = {}
    command_result = await db.execute(
        select(DeviceCommand)
        .options(selectinload(DeviceCommand.vehicle))
        .where(DeviceCommand.vehicle_id.in_(vehicle_ids))
        .order_by(DeviceCommand.vehicle_id.asc(), DeviceCommand.created_at.desc())
    )
    for command in command_result.scalars().all():
        latest_commands.setdefault(command.vehicle_id, command)

    config_result = await db.execute(
        select(DeviceConfig).where(DeviceConfig.vehicle_id.in_(vehicle_ids))
    )
    configs = {config.vehicle_id: config for config in config_result.scalars().all()}

    packet_counts_result = await db.execute(
        select(Location.vehicle_id, func.count(Location.id))
        .where(Location.vehicle_id.in_(vehicle_ids))
        .group_by(Location.vehicle_id)
    )
    packet_counts = {row[0]: row[1] for row in packet_counts_result.all()}

    return [
        VehicleTrackingSnapshot(
            vehicle=vehicle,
            latest_location=latest_locations.get(vehicle.id),
            route_history=route_history.get(vehicle.id, []),
            latest_event=latest_events.get(vehicle.id),
            latest_command=latest_commands.get(vehicle.id),
            device_config=configs.get(vehicle.id),
            health_status=_vehicle_health(vehicle.last_seen),
            movement_status=_movement_status(latest_locations.get(vehicle.id)),
            packet_count=packet_counts.get(vehicle.id, 0),
            current_driver=vehicle.current_driver
        )
        for vehicle in vehicles
    ]


async def create_vehicle(db: AsyncSession, vehicle_in: VehicleCreate) -> Vehicle:
    # Check if a vehicle with the same device_uid already exists
    existing = await get_vehicle_by_device_uid(db, vehicle_in.device_uid)
    if existing:
        raise DuplicateEntityError(f"A vehicle with device UID '{vehicle_in.device_uid}' already exists")
    
    db_vehicle = Vehicle(
        device_uid=vehicle_in.device_uid,
        vehicle_name=vehicle_in.vehicle_name,
        vehicle_type=vehicle_in.vehicle_type,
        vehicle_number=vehicle_in.vehicle_number,
        manufacturer=vehicle_in.manufacturer,
        model=vehicle_in.model,
        year=vehicle_in.year,
        vin=vehicle_in.vin,
        imei=vehicle_in.imei,
        sim_number=vehicle_in.sim_number,
        fuel_type=vehicle_in.fuel_type,
        capacity=vehicle_in.capacity,
        status=vehicle_in.status or "Enabled",
        notes=vehicle_in.notes
    )
    db.add(db_vehicle)
    await db.flush() # flush to get auto-generated ID
    await db.commit()
    return await get_vehicle(db, db_vehicle.id)


async def update_vehicle(db: AsyncSession, vehicle_id: int, vehicle_in: VehicleUpdate) -> Vehicle:
    db_vehicle = await get_vehicle(db, vehicle_id)
    
    update_data = vehicle_in.model_dump(exclude_unset=True)
    if "device_uid" in update_data and update_data["device_uid"] != db_vehicle.device_uid:
        # Check if the new device_uid conflicts with another vehicle
        conflict = await get_vehicle_by_device_uid(db, update_data["device_uid"])
        if conflict:
            raise DuplicateEntityError(f"A vehicle with device UID '{update_data['device_uid']}' already exists")
            
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
        
    await db.commit()
    return await get_vehicle(db, db_vehicle.id)


async def delete_vehicle(db: AsyncSession, vehicle_id: int) -> Vehicle:
    db_vehicle = await get_vehicle(db, vehicle_id)
    # Perform soft delete by archiving vehicle
    db_vehicle.status = "Archived"
    await db.commit()
    return await get_vehicle(db, db_vehicle.id)

