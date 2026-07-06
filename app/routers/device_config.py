from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.device_config import DeviceConfigCreate, DeviceConfigUpdate, DeviceConfigResponse
import app.crud.device_config as crud_config

router = APIRouter(prefix="/configurations", tags=["Configurations"])


@router.get("", response_model=List[DeviceConfigResponse], status_code=status.HTTP_200_OK)
async def list_vehicle_configurations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all registered configurations with pagination.
    """
    return await crud_config.list_configs(db, skip=skip, limit=limit)


@router.get("/{vehicle_id}", response_model=DeviceConfigResponse, status_code=status.HTTP_200_OK)
async def get_configuration_by_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the configuration profile for a specific vehicle by its ID.
    """
    return await crud_config.get_config(db, vehicle_id=vehicle_id)


@router.post("", response_model=DeviceConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_configuration(
    config_in: DeviceConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new device configuration profile associated with a vehicle.
    """
    return await crud_config.create_config(db, config_in=config_in)


@router.put("/{vehicle_id}", response_model=DeviceConfigResponse, status_code=status.HTTP_200_OK)
async def update_vehicle_configuration(
    vehicle_id: int,
    config_in: DeviceConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update configuration parameters of an existing vehicle profile.
    """
    return await crud_config.update_config(db, vehicle_id=vehicle_id, config_in=config_in)


@router.delete("/{vehicle_id}", response_model=DeviceConfigResponse, status_code=status.HTTP_200_OK)
async def delete_vehicle_configuration(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove configuration profile associated with a vehicle.
    """
    return await crud_config.delete_config(db, vehicle_id=vehicle_id)
