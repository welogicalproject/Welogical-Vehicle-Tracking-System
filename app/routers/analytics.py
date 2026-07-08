from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from app.database import get_db
from app.models.fleet_daily_summary import FleetDailySummary
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.maintenance_summary import MaintenanceSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/fleet/today")
async def get_fleet_analytics_today(db: AsyncSession = Depends(get_db)):
    """
    Retrieve fleet daily summary statistics for the current date.
    """
    today_date = date.today()
    result = await db.execute(
        select(FleetDailySummary).where(FleetDailySummary.date == today_date)
    )
    summary = result.scalars().first()
    if not summary:
        # Graceful fallback values
        return {
            "date": str(today_date),
            "total_distance_km": 0.0,
            "total_fuel_consumed_l": 0.0,
            "total_engine_hours": 0.0,
            "total_driving_hours": 0.0,
            "total_idle_hours": 0.0,
            "active_vehicles": 0,
            "fleet_max_speed": 0.0
        }
        
    return {
        "date": str(summary.date),
        "total_distance_km": summary.total_distance_km,
        "total_fuel_consumed_l": summary.total_fuel_consumed_l,
        "total_engine_hours": summary.total_engine_hours,
        "total_driving_hours": summary.total_driving_hours,
        "total_idle_hours": summary.total_idle_hours,
        "active_vehicles": summary.active_vehicles,
        "fleet_max_speed": summary.fleet_max_speed
    }

@router.get("/vehicle/{vehicle_id}/today")
async def get_vehicle_analytics_today(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve single vehicle daily summary stats for the current date.
    """
    today_date = date.today()
    result = await db.execute(
        select(VehicleDailySummary).where(
            (VehicleDailySummary.vehicle_id == vehicle_id) & 
            (VehicleDailySummary.date == today_date)
        )
    )
    summary = result.scalars().first()
    if not summary:
        # Graceful fallback values
        return {
            "vehicle_id": vehicle_id,
            "date": str(today_date),
            "distance_gps_km": 0.0,
            "fuel_consumed_liters": 0.0,
            "engine_runtime_hours": 0.0,
            "driving_hours": 0.0,
            "idle_hours": 0.0,
            "max_speed": 0.0
        }
        
    return {
        "vehicle_id": summary.vehicle_id,
        "date": str(summary.date),
        "distance_gps_km": summary.distance_gps_km,
        "fuel_consumed_liters": summary.fuel_consumed_liters,
        "engine_runtime_hours": summary.engine_runtime_hours,
        "driving_hours": summary.driving_hours,
        "idle_hours": summary.idle_hours,
        "max_speed": summary.max_speed
    }

@router.get("/maintenance/vehicle/{vehicle_id}/today")
async def get_vehicle_maintenance_today(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve single vehicle daily maintenance and health indicators for the current date.
    """
    today_date = date.today()
    result = await db.execute(
        select(MaintenanceSummary).where(
            (MaintenanceSummary.vehicle_id == vehicle_id) & 
            (MaintenanceSummary.date == today_date)
        )
    )
    summary = result.scalars().first()
    if not summary:
        return {
            "vehicle_id": vehicle_id,
            "date": str(today_date),
            "remaining_service_distance_km": 10000.0,
            "remaining_service_days": 365,
            "estimated_next_service_date": str(today_date + timedelta(days=365)),
            "oil_life_pct": 100.0,
            "brake_wear_pct": 0.0,
            "tyre_health_pct": 100.0,
            "battery_health_pct": 100.0,
            "cooling_system_health": "Good",
            "engine_health_index": 100.0,
            "overall_vehicle_health_score": 100.0
        }
        
    return {
        "vehicle_id": summary.vehicle_id,
        "date": str(summary.date),
        "remaining_service_distance_km": summary.remaining_service_distance_km,
        "remaining_service_days": summary.remaining_service_days,
        "estimated_next_service_date": str(summary.estimated_next_service_date) if summary.estimated_next_service_date else None,
        "oil_life_pct": summary.oil_life_pct,
        "brake_wear_pct": summary.brake_wear_pct,
        "tyre_health_pct": summary.tyre_health_pct,
        "battery_health_pct": summary.battery_health_pct,
        "cooling_system_health": summary.cooling_system_health,
        "engine_health_index": summary.engine_health_index,
        "overall_vehicle_health_score": summary.overall_vehicle_health_score
    }
