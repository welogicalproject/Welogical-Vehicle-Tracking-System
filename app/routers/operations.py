from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.fleet_operations import VehicleOperations, FleetOperationsLive

router = APIRouter(prefix="/operations", tags=["Operations"])

@router.get("/fleet/live")
async def get_fleet_live_operations(db: AsyncSession = Depends(get_db)):
    """
    Retrieve real-time aggregated fleet dispatch KPIs and status values.
    """
    result = await db.execute(select(FleetOperationsLive).limit(1))
    summary = result.scalars().first()
    if not summary:
        return {
            "vehicles_driving": 0,
            "vehicles_idling": 0,
            "vehicles_parked": 0,
            "vehicles_offline": 0,
            "active_trips": 0,
            "fleet_availability_pct": 100.0,
            "fleet_utilization_pct": 0.0,
            "vehicles_requiring_attention": 0,
            "critical_alerts_count": 0,
            "warning_alerts_count": 0,
            "last_updated": None
        }
        
    return {
        "vehicles_driving": summary.vehicles_driving,
        "vehicles_idling": summary.vehicles_idling,
        "vehicles_parked": summary.vehicles_parked,
        "vehicles_offline": summary.vehicles_offline,
        "active_trips": summary.active_trips,
        "fleet_availability_pct": summary.fleet_availability_pct,
        "fleet_utilization_pct": summary.fleet_utilization_pct,
        "vehicles_requiring_attention": summary.vehicles_requiring_attention,
        "critical_alerts_count": summary.critical_alerts_count,
        "warning_alerts_count": summary.warning_alerts_count,
        "last_updated": str(summary.last_updated) if summary.last_updated else None
    }

@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_live_operations(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve current warning flags, active trip, assigned driver, and health for a single vehicle.
    """
    result = await db.execute(
        select(VehicleOperations).where(VehicleOperations.vehicle_id == vehicle_id)
    )
    summary = result.scalars().first()
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live operations state for vehicle ID {vehicle_id} not found."
        )
        
    return {
        "vehicle_id": summary.vehicle_id,
        "status": summary.status,
        "gps_lost": summary.gps_lost,
        "low_fuel": summary.low_fuel,
        "low_battery": summary.low_battery,
        "maintenance_due": summary.maintenance_due,
        "power_failure": summary.power_failure,
        "engine_overheat": summary.engine_overheat,
        "active_trip_id": summary.active_trip_id,
        "current_driver_name": summary.current_driver_name,
        "current_health_score": summary.current_health_score,
        "last_updated": str(summary.last_updated) if summary.last_updated else None
    }
