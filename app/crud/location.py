from datetime import datetime, timezone
from app.utils.datetime import normalize_datetime
from typing import Any, Dict, List, Optional
import logging
from sqlalchemy import select, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.location import Location
from app.models.vehicle import Vehicle
from app.models.raw_packet import RawPacket
from app.models.device_command import DeviceCommand
from app.models.enums import CommandStatus
from app.schemas.location import LocationCreate
from app.schemas.vts import VTSPacket
from app.schemas.device_command import DeviceCommandUpdate
from app.crud.vehicle import get_vehicle, get_vehicle_by_device_uid
import app.crud.device_command as crud_command
from app.services.event_decoder import decode_and_save_event
from app.services.trip_engine import evaluate_coordinate_for_trip
from app.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


async def get_latest_location(db: AsyncSession, vehicle_id: int) -> Location:
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    
    result = await db.execute(
        select(Location)
        .where(Location.vehicle_id == vehicle_id)
        .order_by(Location.timestamp.desc())
        .limit(1)
    )
    location = result.scalars().first()
    if not location:
        raise EntityNotFoundError(f"No location history found for vehicle ID {vehicle_id}")
    return location


async def get_location_history(
    db: AsyncSession,
    vehicle_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Location]:
    # Verify vehicle exists
    await get_vehicle(db, vehicle_id)
    
    query = select(Location).where(Location.vehicle_id == vehicle_id)
    
    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)
    if start_time:
        query = query.where(Location.timestamp >= start_time)
    if end_time:
        query = query.where(Location.timestamp <= end_time)
        
    query = query.order_by(Location.timestamp.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())



async def create_location(db: AsyncSession, location_in: LocationCreate) -> Location:
    # Verify vehicle exists and update last_seen
    vehicle = await get_vehicle(db, location_in.vehicle_id)
    
    loc_ts = location_in.timestamp
    if loc_ts.tzinfo is not None:
        loc_ts = loc_ts.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        loc_ts = loc_ts.replace(tzinfo=None)

    db_location = Location(
        vehicle_id=location_in.vehicle_id,
        latitude=location_in.latitude,
        longitude=location_in.longitude,
        speed=location_in.speed,
        altitude=location_in.altitude,
        timestamp=loc_ts,
        extra_data=location_in.extra_data
    )
    db.add(db_location)
    
    # Update last_seen timestamp
    db_last_seen = vehicle.last_seen
    if db_last_seen and db_last_seen.tzinfo is not None:
        db_last_seen = db_last_seen.astimezone(timezone.utc).replace(tzinfo=None)
    elif db_last_seen:
        db_last_seen = db_last_seen.replace(tzinfo=None)

    if not db_last_seen or loc_ts > db_last_seen:
        vehicle.last_seen = loc_ts

    # Evaluate coordinate for ongoing trips
    ign = None
    if location_in.extra_data and "io" in location_in.extra_data:
        ign = location_in.extra_data["io"].get("ign")
    await evaluate_coordinate_for_trip(
        db,
        vehicle_id=location_in.vehicle_id,
        lat=location_in.latitude,
        lon=location_in.longitude,
        speed=location_in.speed,
        timestamp=loc_ts,
        ign=ign
    )
        
    await db.commit()
    await db.refresh(db_location)
    return db_location


async def check_duplicate_packet(
    db: AsyncSession,
    device_uid: str,
    message_id: Optional[int],
    packet_data: Dict[str, Any]
) -> bool:
    if message_id is None:
        return False
    
    result = await db.execute(
        select(RawPacket).where(
            and_(
                RawPacket.device_uid == device_uid,
                RawPacket.message_id == message_id,
                RawPacket.packet_data == packet_data
            )
        )
    )
    return result.scalars().first() is not None


async def save_raw_packet(
    db: AsyncSession,
    device_uid: Optional[str],
    message_id: Optional[int],
    packet_data: Dict[str, Any]
) -> RawPacket:
    db_packet = RawPacket(
        device_uid=device_uid,
        message_id=message_id,
        packet_data=packet_data
    )
    db.add(db_packet)
    await db.flush()
    return db_packet


async def process_vts_telemetry(db: AsyncSession, packet: VTSPacket) -> Dict[str, Any]:
    device_uid = str(packet.uid)
    message_id = packet.info.msgid
    packet_data = packet.model_dump()
    
    # 1. Duplicate check
    is_duplicate = await check_duplicate_packet(db, device_uid, message_id, packet_data)
    if is_duplicate:
        logger.warning(f"Duplicate VTS packet received: device={device_uid}, msgid={message_id}. Skipping processing.")
        return {"result": True, "msg": "Duplicate Packet Ignored"}

    # 2. Get or Auto-Register Vehicle
    vehicle = await get_vehicle_by_device_uid(db, device_uid)
    if not vehicle:
        logger.info(f"Auto-registering new vehicle for device UID: {device_uid}")
        vehicle = Vehicle(
            device_uid=device_uid,
            vehicle_name=f"Vehicle {device_uid}",
            vehicle_type="Unknown"
        )
        db.add(vehicle)
        await db.flush()
        
    # 3. Parse packet attributes
    # Convert Unix timestamp to naive UTC datetime
    timestamp = datetime.fromtimestamp(packet.info.dt, tz=timezone.utc).replace(tzinfo=None)
    
    # Build metadata from extra sensors
    extra_data = {
        "txn": packet.info.txn,
        "msgkey": packet.info.msgkey,
        "gps_details": {
            "fix": packet.gps.fix,
            "sat": packet.gps.sat,
            "dir": packet.gps.dir,
            "odo": packet.gps.odo
        }
    }
    
    if packet.io:
        extra_data["io"] = packet.io.model_dump()
    if packet.pwr:
        extra_data["pwr"] = packet.pwr.model_dump()
    if packet.dbg:
        extra_data["dbg"] = packet.dbg.model_dump()
        
    # 4. Insert parsed location record
    db_location = Location(
        vehicle_id=vehicle.id,
        latitude=packet.gps.loc[0],
        longitude=packet.gps.loc[1],
        speed=packet.gps.speed,
        altitude=packet.gps.alt,
        timestamp=timestamp,
        extra_data=extra_data
    )
    db.add(db_location)
    
    # 5. Update vehicle's last_seen
    db_last_seen = vehicle.last_seen
    if db_last_seen and db_last_seen.tzinfo is not None:
        db_last_seen = db_last_seen.astimezone(timezone.utc).replace(tzinfo=None)
    elif db_last_seen:
        db_last_seen = db_last_seen.replace(tzinfo=None)

    if not db_last_seen or timestamp > db_last_seen:
        vehicle.last_seen = timestamp
        
    # 6. Save raw packet for log history & audit
    await save_raw_packet(db, device_uid=device_uid, message_id=message_id, packet_data=packet_data)

    # 7. Decode events and warnings from packet
    await decode_and_save_event(db, vehicle.id, packet)

    # 7.1 Evaluate coordinate for ongoing trips
    ign = packet.io.ign if packet.io else None
    await evaluate_coordinate_for_trip(
        db,
        vehicle_id=vehicle.id,
        lat=packet.gps.loc[0],
        lon=packet.gps.loc[1],
        speed=packet.gps.speed,
        timestamp=timestamp,
        ign=ign
    )

    # 8. Check for pending commands to deliver to the device in the response
    cmd_stmt = select(DeviceCommand).where(
        DeviceCommand.vehicle_id == vehicle.id,
        DeviceCommand.status == CommandStatus.PENDING
    ).order_by(asc(DeviceCommand.created_at)).limit(1)
    cmd_res = await db.execute(cmd_stmt)
    pending_cmd = cmd_res.scalars().first()

    cmd_payload = None
    if pending_cmd:
        # Mark command as SENT and add audit log
        update_data = DeviceCommandUpdate(
            status=CommandStatus.SENT,
            message="Delivered to device in HTTP telemetry response payload"
        )
        await crud_command.update_status(db, command_id=pending_cmd.id, status_update=update_data)
        
        if pending_cmd.command_value:
            cmd_payload = f"{pending_cmd.command_name}={pending_cmd.command_value}"
        else:
            cmd_payload = pending_cmd.command_name
    
    # Commit transaction
    await db.commit()
    logger.info(f"Successfully processed VTS telemetry packet for vehicle={vehicle.id}, device={device_uid}, msgid={message_id}")
    
    response_payload = {"result": True, "msg": "Data Success"}
    if cmd_payload:
        response_payload["cmd"] = cmd_payload
    return response_payload
