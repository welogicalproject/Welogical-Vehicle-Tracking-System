import logging
import time
from datetime import datetime
from typing import Optional
from app.database import AsyncSessionLocal
from app.services.processing_context import TelemetryProcessingContext
from app.services.packet_processor import process_telemetry_packet
from app.services.structured_logger import log_telemetry_stage

logger = logging.getLogger(__name__)

async def run_telemetry_background_job(
    vehicle_id: int,
    device_uid: str,
    packet_data: dict,
    timestamp: datetime,
    msgid: Optional[int],
    start_time_perf: float,
    packet_latency: float
):
    """
    FastAPI BackgroundTasks worker wrapper.
    Creates an isolated database session, constructs context, and executes packet processor.
    """
    logger.debug(f"Starting background job telemetry processing for vehicle={vehicle_id}, msgid={msgid}.")
    
    async with AsyncSessionLocal() as session:
        ctx = TelemetryProcessingContext(
            session=session,
            vehicle_id=vehicle_id,
            device_uid=device_uid,
            packet_data=packet_data,
            timestamp=timestamp,
            msgid=msgid,
            processing_start_time=start_time_perf,
            packet_latency=packet_latency
        )
        
        try:
            await process_telemetry_packet(ctx)
        except Exception as e:
            logger.error(f"Background task execution failed for vehicle={vehicle_id}, msgid={msgid}: {e}", exc_info=True)
            log_telemetry_stage(device_uid, vehicle_id, msgid, "BACKGROUND_WORKER", start_time_perf, "FAILED", exception=e)
        finally:
            await session.close()
            logger.debug(f"Finished background job processing for vehicle={vehicle_id}, msgid={msgid}. Session closed.")
