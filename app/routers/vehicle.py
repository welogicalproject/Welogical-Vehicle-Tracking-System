from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleTrackingSnapshot
import app.crud.vehicle as crud_vehicle

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_new_vehicle(vehicle_in: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Register a new vehicle with a unique device hardware identifier."""
    return await crud_vehicle.create_vehicle(db, vehicle_in)


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieve a list of registered vehicles with optional pagination."""
    return await crud_vehicle.get_vehicles(db, skip=skip, limit=limit)


@router.get("/tracking/snapshots", response_model=List[VehicleTrackingSnapshot])
async def list_vehicle_tracking_snapshots(
    start_time: Optional[datetime] = Query(None, description="Route history start timestamp"),
    end_time: Optional[datetime] = Query(None, description="Route history end timestamp"),
    limit_per_vehicle: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve fleet tracking summaries with latest telemetry, route history, events, commands, and health state."""
    return await crud_vehicle.get_tracking_snapshots(
        db,
        start_time=start_time,
        end_time=end_time,
        limit_per_vehicle=limit_per_vehicle
    )


@router.get("/{vehicle_id}/tracking", response_model=VehicleTrackingSnapshot)
async def get_vehicle_tracking_snapshot(
    vehicle_id: int,
    start_time: Optional[datetime] = Query(None, description="Route history start timestamp"),
    end_time: Optional[datetime] = Query(None, description="Route history end timestamp"),
    limit_per_vehicle: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a tracking summary for a single vehicle."""
    snapshots = await crud_vehicle.get_tracking_snapshots(
        db,
        vehicle_id=vehicle_id,
        start_time=start_time,
        end_time=end_time,
        limit_per_vehicle=limit_per_vehicle
    )
    return snapshots[0]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle_by_id(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific vehicle by its primary ID."""
    return await crud_vehicle.get_vehicle(db, vehicle_id)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle_by_id(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update profile parameters of an existing vehicle."""
    return await crud_vehicle.update_vehicle(db, vehicle_id, vehicle_in)


@router.delete("/{vehicle_id}", response_model=VehicleResponse)
async def delete_vehicle_by_id(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a vehicle and all its associated location telemetry records."""
    return await crud_vehicle.delete_vehicle(db, vehicle_id)


# Driver Assignment Routes
from fastapi import HTTPException
from app.schemas.driver_assignment import DriverAssignmentResponse
import app.crud.driver as crud_driver

@router.post("/{vehicle_id}/assign/{driver_id}", response_model=DriverAssignmentResponse)
async def assign_driver_to_vehicle(vehicle_id: int, driver_id: int, db: AsyncSession = Depends(get_db)):
    """Assign a driver to a vehicle (closes any previous active assignments)."""
    try:
        return await crud_driver.create_assignment(db, vehicle_id, driver_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{vehicle_id}/release", response_model=Optional[DriverAssignmentResponse])
async def release_driver_from_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Release the currently assigned driver from the vehicle."""
    asg = await crud_driver.release_assignment(db, vehicle_id)
    if not asg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active assignment found for this vehicle")
    return asg

@router.get("/{vehicle_id}/assignments/active", response_model=Optional[DriverAssignmentResponse])
async def get_active_driver_assignment(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Get the current active driver assignment for the vehicle."""
    return await crud_driver.get_active_assignment_by_vehicle(db, vehicle_id)

@router.get("/{vehicle_id}/assignments/history", response_model=List[DriverAssignmentResponse])
async def get_driver_assignment_history(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Get all historical driver assignments for the vehicle."""
    return await crud_driver.get_assignment_history_by_vehicle(db, vehicle_id)
