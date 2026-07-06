from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device_config import DeviceConfig
from app.schemas.device_config import DeviceConfigCreate, DeviceConfigUpdate
from app.exceptions import EntityNotFoundError, DuplicateEntityError


async def get_config(db: AsyncSession, vehicle_id: int) -> DeviceConfig:
    result = await db.execute(select(DeviceConfig).where(DeviceConfig.vehicle_id == vehicle_id))
    config = result.scalars().first()
    if not config:
        raise EntityNotFoundError(f"Configuration for vehicle ID {vehicle_id} not found")
    return config


async def get_config_by_id(db: AsyncSession, config_id: int) -> DeviceConfig:
    result = await db.execute(select(DeviceConfig).where(DeviceConfig.id == config_id))
    config = result.scalars().first()
    if not config:
        raise EntityNotFoundError(f"Configuration with ID {config_id} not found")
    return config


async def create_config(db: AsyncSession, config_in: DeviceConfigCreate) -> DeviceConfig:
    # Check if a configuration already exists for the vehicle
    existing_result = await db.execute(select(DeviceConfig).where(DeviceConfig.vehicle_id == config_in.vehicle_id))
    if existing_result.scalars().first():
        raise DuplicateEntityError(f"A configuration for vehicle ID {config_in.vehicle_id} already exists")

    db_config = DeviceConfig(
        vehicle_id=config_in.vehicle_id,
        server_ip=config_in.server_ip,
        server_port=config_in.server_port,
        apn=config_in.apn,
        timezone=config_in.timezone,
        reporting_interval=config_in.reporting_interval,
        speed_limit=config_in.speed_limit,
        feature_flags=config_in.feature_flags,
        firmware_version=config_in.firmware_version,
        hardware_version=config_in.hardware_version
    )
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config


async def update_config(db: AsyncSession, vehicle_id: int, config_in: DeviceConfigUpdate) -> DeviceConfig:
    db_config = await get_config(db, vehicle_id)
    update_data = config_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_config, field, value)
        
    await db.commit()
    await db.refresh(db_config)
    return db_config


async def delete_config(db: AsyncSession, vehicle_id: int) -> DeviceConfig:
    db_config = await get_config(db, vehicle_id)
    await db.delete(db_config)
    await db.commit()
    return db_config


async def list_configs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DeviceConfig]:
    result = await db.execute(select(DeviceConfig).offset(skip).limit(limit))
    return list(result.scalars().all())
