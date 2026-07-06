import time
from datetime import datetime, timezone
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.location import Location
from app.models.vehicle import Vehicle
from app.services.event_decoder import decode_and_save_event
from app.services.trip_engine import evaluate_coordinate_for_trip
from app.services.processing_context import TelemetryProcessingContext
from app.services.structured_logger import log_telemetry_stage
from app.schemas.vts import VTSPacket

logger = logging.getLogger(__name__)

async def process_telemetry_packet(ctx: TelemetryProcessingContext):
    """
    Perform heavy post-ingestion processing asynchronously.
    Saves location log, updates vehicle last_seen, runs alerts engine, and evaluates trips.
    """
    start_time = time.perf_counter()
    db = ctx.session
    packet_dict = ctx.packet_data
    
    # Re-construct VTSPacket schema model from dict representation safely
    packet = VTSPacket.model_validate(packet_dict)
    
    try:
        # 1. Fetch Vehicle record in the context session
        veh_stmt = select(Vehicle).where(Vehicle.id == ctx.vehicle_id)
        veh_res = await db.execute(veh_stmt)
        vehicle = veh_res.scalars().first()
        if not vehicle:
            logger.error(f"Vehicle not found in background processing context: ID={ctx.vehicle_id}")
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "FETCH_VEHICLE", start_time, "FAILED")
            return

        # 2. Insert standard Location log
        # Map parameters to extra_data structure
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

        db_location = Location(
            vehicle_id=vehicle.id,
            latitude=packet.gps.loc[0],
            longitude=packet.gps.loc[1],
            speed=packet.gps.speed,
            altitude=packet.gps.alt,
            timestamp=ctx.timestamp,
            extra_data=extra_data
        )
        db.add(db_location)
        log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "LOCATION_INSERT", start_time, "SUCCESS")

        # 3. Update vehicle last_seen
        db_last_seen = vehicle.last_seen
        if db_last_seen and db_last_seen.tzinfo is not None:
            db_last_seen = db_last_seen.astimezone(timezone.utc).replace(tzinfo=None)
        elif db_last_seen:
            db_last_seen = db_last_seen.replace(tzinfo=None)

        if not db_last_seen or ctx.timestamp > db_last_seen:
            vehicle.last_seen = ctx.timestamp
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "UPDATE_LAST_SEEN", start_time, "SUCCESS")

        # 4. Decode Warning & Critical events
        try:
            await decode_and_save_event(db, vehicle.id, packet)
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "EVENT_ENGINE", start_time, "SUCCESS")
        except Exception as e:
            logger.error(f"Event Engine failed inside background job for vehicle={vehicle.id}: {e}", exc_info=True)
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "EVENT_ENGINE", start_time, "FAILED", exception=e)

        # 5. Evaluate ongoing trips state-machine updates
        try:
            ign = packet.io.ign if packet.io else None
            await evaluate_coordinate_for_trip(
                db,
                vehicle_id=vehicle.id,
                lat=packet.gps.loc[0],
                lon=packet.gps.loc[1],
                speed=packet.gps.speed,
                timestamp=ctx.timestamp,
                ign=ign
            )
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "TRIP_ENGINE", start_time, "SUCCESS")
        except Exception as e:
            logger.error(f"Trip Engine failed inside background job for vehicle={vehicle.id}: {e}", exc_info=True)
            log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "TRIP_ENGINE", start_time, "FAILED", exception=e)

        # 6. Commit single consolidated transaction scope
        await db.commit()
        log_telemetry_stage(
            ctx.device_uid, 
            ctx.vehicle_id, 
            ctx.msgid, 
            "COMMIT_TRANSACTION", 
            start_time, 
            "SUCCESS", 
            extra={"packet_latency_sec": ctx.packet_latency}
        )

    except Exception as e:
        logger.error(f"Unexpected error in background processing for vehicle={ctx.vehicle_id}: {e}", exc_info=True)
        await db.rollback()
        log_telemetry_stage(ctx.device_uid, ctx.vehicle_id, ctx.msgid, "ASYNC_PROCESS", start_time, "FAILED", exception=e)
