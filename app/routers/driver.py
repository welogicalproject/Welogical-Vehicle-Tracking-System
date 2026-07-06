from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
import app.crud.driver as crud_driver

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_new_driver(driver_in: DriverCreate, db: AsyncSession = Depends(get_db)):
    """Create a new driver profile."""
    try:
        return await crud_driver.create_driver(db, driver_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DriverResponse])
async def list_drivers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all driver profiles."""
    return await crud_driver.get_drivers(db, skip=skip, limit=limit)

@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver_by_id(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Get driver details by driver ID."""
    return await crud_driver.get_driver(db, driver_id)

@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver_by_id(driver_id: int, driver_in: DriverUpdate, db: AsyncSession = Depends(get_db)):
    """Update driver details by driver ID."""
    return await crud_driver.update_driver(db, driver_id, driver_in)

@router.delete("/{driver_id}", response_model=DriverResponse)
async def delete_driver_by_id(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a driver profile."""
    return await crud_driver.delete_driver(db, driver_id)


# Driver assignment history routes
from typing import Optional
from app.schemas.driver_assignment import DriverAssignmentResponse

@router.get("/{driver_id}/assignments/active", response_model=Optional[DriverAssignmentResponse])
async def get_driver_active_assignment(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Get the active assignment details for a driver."""
    return await crud_driver.get_active_assignment_by_driver(db, driver_id)

@router.get("/{driver_id}/assignments/history", response_model=List[DriverAssignmentResponse])
async def get_driver_assignment_history(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Get the complete assignment history for a driver."""
    return await crud_driver.get_assignment_history_by_driver(db, driver_id)
