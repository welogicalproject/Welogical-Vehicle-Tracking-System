from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, BackgroundTasks
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.location import LocationCreate, LocationResponse
from app.schemas.vts import VTSPacket, VTSResponse, RawPacketResponse
from app.models.location import Location
from app.models.raw_packet import RawPacket
import app.crud.location as crud_location
from app.services.telemetry_pipeline import run_synchronous_telemetry_pipeline
from app.services.background_jobs import run_telemetry_background_job

router = APIRouter(tags=["Locations"])


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def log_standard_location(location_in: LocationCreate, db: AsyncSession = Depends(get_db)):
    """
    Log a location point using standard parameters.
    Updates the parent vehicle's last_seen field.
    """
    return await crud_location.create_location(db, location_in)


@router.post(
    "/vts/telemetry",
    response_model=VTSResponse,
    status_code=status.HTTP_200_OK,
    summary="VTS Protocol Telemetry Ingestion"
)
async def log_vts_telemetry(
    packet: VTSPacket,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a JSON packet conforming to the VTS Protocol Description (e.g. sent by ESP32 or device).
    Validates, duplicate checks, stores raw packets, and delivers queued commands synchronously.
    Queues heavy operations (locations logs, event parsing, trip updating) to background worker.
    """
    import logging
    logger = logging.getLogger("app.ingestion")
    uid = str(packet.uid)
    msgid = packet.info.msgid
    
    logger.info(f"[Ingest Trace] RECEIVED packet for device_uid={uid}, msgid={msgid}")
    start_perf = time.perf_counter()
    
    # Run sync pipeline
    logger.info(f"[Ingest Trace] RUNNING synchronous pipeline for device_uid={uid}")
    t_start = time.perf_counter()
    response_payload, bg_metadata = await run_synchronous_telemetry_pipeline(db, packet)
    logger.info(f"[Ingest Trace] SYNC PIPELINE COMPLETE for device_uid={uid}. Elapsed: {time.perf_counter() - t_start:.4f}s")
    
    # Queue background task if packet was not skipped as duplicate
    if bg_metadata:
        vehicle_id, device_uid, packet_time, msgid, packet_latency = bg_metadata
        logger.info(f"[Ingest Trace] QUEUING background task for device_uid={uid}")
        background_tasks.add_task(
            run_telemetry_background_job,
            vehicle_id=vehicle_id,
            device_uid=device_uid,
            packet_data=packet.model_dump(),
            timestamp=packet_time,
            msgid=msgid,
            start_time_perf=start_perf,
            packet_latency=packet_latency
        )
        logger.info(f"[Ingest Trace] BACKGROUND TASK QUEUED for device_uid={uid}")
        
    logger.info(f"[Ingest Trace] RETURNING RESPONSE for device_uid={uid}. Total Ingest Time: {time.perf_counter() - start_perf:.4f}s")
    return response_payload


@router.get("/locations/latest/{vehicle_id}", response_model=LocationResponse)
async def get_latest_vehicle_location(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve the most recently recorded location log for a vehicle."""
    return await crud_location.get_latest_location(db, vehicle_id)


@router.get("/locations/history/{vehicle_id}", response_model=List[LocationResponse])
async def get_vehicle_location_history(
    vehicle_id: int,
    start_time: Optional[datetime] = Query(None, description="ISO-formatted UTC timestamp filter (e.g. 2026-06-23T00:00:00Z)"),
    end_time: Optional[datetime] = Query(None, description="ISO-formatted UTC timestamp filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the chronological location logs history of a vehicle with options to filter by datetime window."""
    return await crud_location.get_location_history(
        db,
        vehicle_id=vehicle_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )


@router.get("/locations", response_model=List[LocationResponse])
async def list_all_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all logged locations across all vehicles with pagination (for Database Explorer)."""
    result = await db.execute(
        select(Location).order_by(Location.timestamp.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/vts/raw-packets", response_model=List[RawPacketResponse])
async def list_raw_packets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve raw telemetry packets logged in raw_packets database (for Debug Monitor)."""
    result = await db.execute(
        select(RawPacket).order_by(RawPacket.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())
