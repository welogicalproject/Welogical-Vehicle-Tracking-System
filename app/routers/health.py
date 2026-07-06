from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.vehicle import Vehicle
from app.models.location import Location
from app.models.raw_packet import RawPacket
import logging

logger = logging.getLogger(__name__)

# Router for health check
router = APIRouter(prefix="/health", tags=["System"])

# Router for dashboard stats
system_router = APIRouter(prefix="/system", tags=["System"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    Performs a quick roundtrip check to verify active database availability.
    """
    db_ok = False
    try:
        # Dry-run execute SELECT 1 to verify PG connectivity
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check database connection failure: {str(e)}", exc_info=True)

    if db_ok:
        return {
            "status": "healthy",
            "database": "connected"
        }
    else:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }


@system_router.get("/stats", status_code=status.HTTP_200_OK)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overview statistics for the VTS Dashboard.
    """
    try:
        # Fetch counts
        vehicle_count = (await db.execute(select(func.count(Vehicle.id)))).scalar_one()
        location_count = (await db.execute(select(func.count(Location.id)))).scalar_one()
        packet_count = (await db.execute(select(func.count(RawPacket.id)))).scalar_one()

        # Fetch latest timestamp
        latest_ts_res = await db.execute(
            select(Location.timestamp).order_by(Location.timestamp.desc()).limit(1)
        )
        latest_timestamp = latest_ts_res.scalar()

        # Online/Idle/Offline thresholds (naive UTC)
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        five_min_ago = now_naive - timedelta(minutes=5)
        thirty_min_ago = now_naive - timedelta(minutes=30)

        # Online (< 5 mins)
        online_count = (await db.execute(
            select(func.count(Vehicle.id)).where(Vehicle.last_seen >= five_min_ago)
        )).scalar_one()

        # Idle (5 to 30 mins)
        idle_count = (await db.execute(
            select(func.count(Vehicle.id)).where(
                (Vehicle.last_seen >= thirty_min_ago) & (Vehicle.last_seen < five_min_ago)
            )
        )).scalar_one()

        # Offline (> 30 mins or never seen)
        offline_count = (await db.execute(
            select(func.count(Vehicle.id)).where(
                (Vehicle.last_seen < thirty_min_ago) | (Vehicle.last_seen.is_(None))
            )
        )).scalar_one()

        return {
            "total_vehicles": vehicle_count,
            "total_locations": location_count,
            "total_raw_packets": packet_count,
            "vehicles_online": online_count,
            "vehicles_idle": idle_count,
            "vehicles_offline": offline_count,
            "latest_timestamp": latest_timestamp
        }
    except Exception as e:
        logger.error(f"Error executing stats queries: {str(e)}", exc_info=True)
        return {
            "total_vehicles": 0,
            "total_locations": 0,
            "total_raw_packets": 0,
            "vehicles_online": 0,
            "vehicles_idle": 0,
            "vehicles_offline": 0,
            "latest_timestamp": None
        }
