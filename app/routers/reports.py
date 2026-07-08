from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from typing import Optional
from app.database import get_db
from app.services.reports import get_report_manager, ReportContext

router = APIRouter(prefix="/reports", tags=["Reports"])

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format '{date_str}'. Expected format: YYYY-MM-DD."
        )

@router.get("/fleet/daily")
async def get_daily_fleet_report(
    date_str: Optional[str] = Query(None, alias="date"),
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Daily Fleet Performance Report.
    """
    req_date = parse_date(date_str)
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, report_date=req_date, start_date=start_dt, end_date=end_dt)
        return get_report_manager().generate_report("DailyFleet", context)
        
    return await db.run_sync(sync_run)

@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_performance_report(
    vehicle_id: int,
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Vehicle Performance Report.
    """
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, start_date=start_dt, end_date=end_dt, vehicle_id=vehicle_id)
        return get_report_manager().generate_report("VehiclePerformance", context)
        
    return await db.run_sync(sync_run)

@router.get("/driver/{driver_id}")
async def get_driver_performance_report(
    driver_id: int,
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Driver Performance Report.
    """
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, start_date=start_dt, end_date=end_dt, driver_id=driver_id)
        return get_report_manager().generate_report("DriverPerformance", context)
        
    return await db.run_sync(sync_run)

@router.get("/maintenance")
async def get_maintenance_report(
    vehicle_id: Optional[int] = Query(None),
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Fleet Maintenance Logs Report.
    """
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, start_date=start_dt, end_date=end_dt, vehicle_id=vehicle_id)
        return get_report_manager().generate_report("Maintenance", context)
        
    return await db.run_sync(sync_run)

@router.get("/events")
async def get_events_report(
    vehicle_id: Optional[int] = Query(None),
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Critical System Events Summary Report.
    """
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, start_date=start_dt, end_date=end_dt, vehicle_id=vehicle_id)
        return get_report_manager().generate_report("EventSummary", context)
        
    return await db.run_sync(sync_run)

@router.get("/fleet/health")
async def get_fleet_health_report(
    date_str: Optional[str] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Fleet-wide Health Index Report.
    """
    req_date = parse_date(date_str)

    def sync_run(session):
        context = ReportContext(db=session, report_date=req_date)
        return get_report_manager().generate_report("FleetHealth", context)
        
    return await db.run_sync(sync_run)

@router.get("/fleet/fuel")
async def get_fleet_fuel_report(
    start_date_str: Optional[str] = Query(None, alias="start_date"),
    end_date_str: Optional[str] = Query(None, alias="end_date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Fleet Fuel Efficiency Report.
    """
    start_dt = parse_date(start_date_str)
    end_dt = parse_date(end_date_str)

    def sync_run(session):
        context = ReportContext(db=session, start_date=start_dt, end_date=end_dt)
        return get_report_manager().generate_report("FuelConsumption", context)
        
    return await db.run_sync(sync_run)
