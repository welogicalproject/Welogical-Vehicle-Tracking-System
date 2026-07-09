import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import logging
from sqlalchemy import select, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.raw_packet import RawPacket
from app.models.vehicle import Vehicle
from app.models.device_command import DeviceCommand
from app.models.command_log import CommandLog
from app.schemas.vts import VTSPacket
from app.services.packet_validator import validate_telemetry_packet
from app.services.structured_logger import log_telemetry_stage

logger = logging.getLogger(__name__)

async def run_synchronous_telemetry_pipeline(
    db: AsyncSession,
    packet: VTSPacket
) -> Tuple[Dict[str, Any], Optional[Tuple[int, str, datetime, Optional[int], float]]]:
    """
    Ingest, validate, auto-register vehicle, save raw packets, and check queued commands synchronously.
    Returns HTTP response payload and background task metadata if processing is required.
    """
    start_time = time.perf_counter()
    device_uid = str(packet.uid)
    message_id = packet.info.msgid
    packet_data = packet.model_dump()

    try:
    # 1. Packet validation bounds checking
        t_sub = time.perf_counter()
        packet_time = validate_telemetry_packet(packet)
        logger.info(f"[Ingest Trace - Pipeline] Validation complete. Elapsed: {time.perf_counter() - t_sub:.4f}s")
        log_telemetry_stage(device_uid, None, message_id, "VALIDATE_PACKET", start_time, "SUCCESS")

        # 2. Duplicate detection
        t_sub = time.perf_counter()
        if message_id is not None:
            dup_stmt = select(RawPacket).where(
                and_(
                    RawPacket.device_uid == device_uid,
                    RawPacket.message_id == message_id,
                    RawPacket.packet_data == packet_data
                )
            ).limit(1)
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first() is not None:
                logger.info(f"[Ingest Trace - Pipeline] Duplicate check complete (REJECTED). Elapsed: {time.perf_counter() - t_sub:.4f}s")
                log_telemetry_stage(device_uid, None, message_id, "DUPLICATE_CHECK", start_time, "REJECTED")
                return {"result": True, "msg": "Duplicate Packet Ignored"}, None
        logger.info(f"[Ingest Trace - Pipeline] Duplicate check complete (PASSED). Elapsed: {time.perf_counter() - t_sub:.4f}s")
        
        # 3. Vehicle resolution & auto-registration
        t_sub = time.perf_counter()
        veh_stmt = select(Vehicle).where(Vehicle.device_uid == device_uid)
        veh_res = await db.execute(veh_stmt)
        vehicle = veh_res.scalars().first()
        if not vehicle:
            logger.info(f"Auto-registering vehicle UID: {device_uid}")
            vehicle = Vehicle(
                device_uid=device_uid,
                vehicle_name=f"Vehicle {device_uid}",
                vehicle_type="Unknown"
            )
            db.add(vehicle)
            await db.flush()
            log_telemetry_stage(device_uid, vehicle.id, message_id, "VEHICLE_AUTO_REGISTER", start_time, "SUCCESS")
        logger.info(f"[Ingest Trace - Pipeline] Vehicle resolution complete. Elapsed: {time.perf_counter() - t_sub:.4f}s")

        # 4. Save Raw Packet log immediately
        t_sub = time.perf_counter()
        db_packet = RawPacket(
            device_uid=device_uid,
            message_id=message_id,
            packet_data=packet_data
        )
        db.add(db_packet)
        logger.info(f"[Ingest Trace - Pipeline] Raw packet save complete. Elapsed: {time.perf_counter() - t_sub:.4f}s")
        log_telemetry_stage(device_uid, vehicle.id, message_id, "SAVE_RAW_PACKET", start_time, "SUCCESS")

        # 5. Fetch PENDING commands
        t_sub = time.perf_counter()
        cmd_stmt = select(DeviceCommand).where(
            and_(
                DeviceCommand.vehicle_id == vehicle.id,
                DeviceCommand.status == "Queued"
            )
        ).order_by(asc(DeviceCommand.created_at)).limit(1)
        cmd_res = await db.execute(cmd_stmt)
        pending_cmd = cmd_res.scalars().first()

        cmd_payload = None
        if pending_cmd:
            pending_cmd.status = "Delivered"
            pending_cmd.sent_at = datetime.utcnow()
            
            cmd_log = CommandLog(
                command_id=pending_cmd.id,
                vehicle_id=vehicle.id,
                status="Delivered",
                message="Delivered to device via telemetry response payload"
            )
            db.add(cmd_log)
            
            if pending_cmd.command_value:
                cmd_payload = f"{pending_cmd.command_name}={pending_cmd.command_value}"
            else:
                cmd_payload = pending_cmd.command_name
                
            log_telemetry_stage(device_uid, vehicle.id, message_id, "FETCH_COMMAND", start_time, "SUCCESS")
        logger.info(f"[Ingest Trace - Pipeline] Command fetch complete. Elapsed: {time.perf_counter() - t_sub:.4f}s")

        # 6. Commit single synchronous transaction scope
        t_sub = time.perf_counter()
        await db.commit()
        logger.info(f"[Ingest Trace - Pipeline] Transaction commit complete. Elapsed: {time.perf_counter() - t_sub:.4f}s")
        log_telemetry_stage(device_uid, vehicle.id, message_id, "SYNC_INGEST_COMMIT", start_time, "SUCCESS")

        response_payload = {"result": True, "msg": "Data Success"}
        if cmd_payload:
            response_payload["cmd"] = cmd_payload
            response_payload["cmd_id"] = pending_cmd.id

        # Calculate packet latency in seconds
        now_epoch = datetime.now(timezone.utc).timestamp()
        packet_latency = max(0.0, now_epoch - packet.info.dt)

        background_metadata = (
            vehicle.id,
            device_uid,
            packet_time,
            message_id,
            packet_latency
        )

        return response_payload, background_metadata

    except Exception as e:
        logger.error(f"Ingestion failed synchronously in pipeline: {e}", exc_info=True)
        await db.rollback()
        log_telemetry_stage(device_uid, None, message_id, "SYNC_INGEST", start_time, "FAILED", exception=e)
        raise e
