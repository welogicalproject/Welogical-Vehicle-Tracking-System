from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.schemas.driver import DriverCreate, DriverUpdate
from app.exceptions import EntityNotFoundError

async def get_driver(db: AsyncSession, driver_id: int) -> Driver:
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.assignments).selectinload(DriverAssignment.vehicle))
        .where(Driver.id == driver_id)
    )
    driver = result.scalars().first()
    if not driver:
        raise EntityNotFoundError(f"Driver with ID {driver_id} not found")
    return driver

async def get_drivers(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Driver]:
    result = await db.execute(
        select(Driver)
        .options(selectinload(Driver.assignments).selectinload(DriverAssignment.vehicle))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def create_driver(db: AsyncSession, driver_in: DriverCreate) -> Driver:
    # Duplicate license number check
    lic_check = await db.execute(select(Driver).where(Driver.license_number == driver_in.license_number))
    if lic_check.scalars().first():
        raise ValueError(f"A driver with license number '{driver_in.license_number}' already exists.")

    # Duplicate phone number check
    phone_check = await db.execute(select(Driver).where(Driver.phone_number == driver_in.phone_number))
    if phone_check.scalars().first():
        raise ValueError(f"A driver with phone number '{driver_in.phone_number}' is already registered.")

    db_driver = Driver(
        driver_name=driver_in.driver_name,
        phone_number=driver_in.phone_number,
        email=driver_in.email,
        license_number=driver_in.license_number,
        license_expiry=driver_in.license_expiry.replace(tzinfo=None),
        emergency_contact=driver_in.emergency_contact,
        status=driver_in.status
    )
    db.add(db_driver)
    await db.commit()
<<<<<<< HEAD
    return await get_driver(db, db_driver.id)
=======
    await db.refresh(db_driver)
    return db_driver
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)


async def update_driver(db: AsyncSession, driver_id: int, driver_in: DriverUpdate) -> Driver:
    db_driver = await get_driver(db, driver_id)
    update_data = driver_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "license_expiry" and value is not None:
            value = value.replace(tzinfo=None)
        setattr(db_driver, field, value)
    await db.commit()
<<<<<<< HEAD
    return await get_driver(db, db_driver.id)

=======
    await db.refresh(db_driver)
    return db_driver
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)

async def delete_driver(db: AsyncSession, driver_id: int) -> Driver:
    db_driver = await get_driver(db, driver_id)
    await db.delete(db_driver)
    await db.commit()
    return db_driver


# Driver Assignment operations
from datetime import datetime, timezone
from app.models.vehicle import Vehicle
from app.models.enums import DriverStatus
from app.exceptions import EntityNotFoundError

async def create_assignment(db: AsyncSession, vehicle_id: int, driver_id: int) -> DriverAssignment:
    # 1. Validate vehicle exists and is enabled (not disabled or archived)
    veh_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = veh_result.scalars().first()
    if not vehicle:
        raise EntityNotFoundError(f"Vehicle with ID {vehicle_id} not found")
    if vehicle.status in ("Disabled", "Archived"):
        raise ValueError(f"Cannot assign driver to a vehicle with status '{vehicle.status}'")

    # 2. Validate driver exists and is active
    drv_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = drv_result.scalars().first()
    if not driver:
        raise EntityNotFoundError(f"Driver with ID {driver_id} not found")
    if driver.status != DriverStatus.ACTIVE:
        raise ValueError(f"Cannot assign driver who is '{driver.status}'")

    # 3. Close any previous active assignment for this vehicle
    veh_active_stmt = select(DriverAssignment).where(
        and_(
            DriverAssignment.vehicle_id == vehicle_id,
            DriverAssignment.status == "Active"
        )
    )
    veh_active_res = await db.execute(veh_active_stmt)
    for active_asg in veh_active_res.scalars().all():
        active_asg.status = "Completed"
        active_asg.released_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 4. Close any previous active assignment for this driver
    drv_active_stmt = select(DriverAssignment).where(
        and_(
            DriverAssignment.driver_id == driver_id,
            DriverAssignment.status == "Active"
        )
    )
    drv_active_res = await db.execute(drv_active_stmt)
    for active_asg in drv_active_res.scalars().all():
        active_asg.status = "Completed"
        active_asg.released_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # 5. Create new assignment
    db_assignment = DriverAssignment(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        assigned_at=datetime.now(timezone.utc).replace(tzinfo=None),
        status="Active"
    )
    db.add(db_assignment)
    await db.commit()
<<<<<<< HEAD
    # Eager load the driver details to prevent DetachedInstanceError on serialization
    return await get_active_assignment_by_vehicle(db, vehicle_id)

async def release_assignment(db: AsyncSession, vehicle_id: int) -> Optional[DriverAssignment]:
    stmt = select(DriverAssignment).options(selectinload(DriverAssignment.driver)).where(
=======
    await db.refresh(db_assignment)
    return db_assignment

async def release_assignment(db: AsyncSession, vehicle_id: int) -> Optional[DriverAssignment]:
    stmt = select(DriverAssignment).where(
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
        and_(
            DriverAssignment.vehicle_id == vehicle_id,
            DriverAssignment.status == "Active"
        )
    )
    res = await db.execute(stmt)
    active_asg = res.scalars().first()
    if active_asg:
        active_asg.status = "Completed"
        active_asg.released_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
<<<<<<< HEAD
=======
        await db.refresh(active_asg)
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
    return active_asg

async def get_active_assignment_by_vehicle(db: AsyncSession, vehicle_id: int) -> Optional[DriverAssignment]:
    stmt = select(DriverAssignment).options(selectinload(DriverAssignment.driver)).where(
        and_(
            DriverAssignment.vehicle_id == vehicle_id,
            DriverAssignment.status == "Active"
        )
    )
    res = await db.execute(stmt)
    return res.scalars().first()

async def get_active_assignment_by_driver(db: AsyncSession, driver_id: int) -> Optional[DriverAssignment]:
<<<<<<< HEAD
    stmt = select(DriverAssignment).options(selectinload(DriverAssignment.driver)).where(
=======
    stmt = select(DriverAssignment).where(
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
        and_(
            DriverAssignment.driver_id == driver_id,
            DriverAssignment.status == "Active"
        )
    )
    res = await db.execute(stmt)
    return res.scalars().first()

async def get_assignment_history_by_vehicle(db: AsyncSession, vehicle_id: int) -> List[DriverAssignment]:
    stmt = select(DriverAssignment).options(selectinload(DriverAssignment.driver)).where(
        DriverAssignment.vehicle_id == vehicle_id
    ).order_by(DriverAssignment.assigned_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def get_assignment_history_by_driver(db: AsyncSession, driver_id: int) -> List[DriverAssignment]:
<<<<<<< HEAD
    stmt = select(DriverAssignment).options(selectinload(DriverAssignment.driver)).where(
=======
    stmt = select(DriverAssignment).where(
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
        DriverAssignment.driver_id == driver_id
    ).order_by(DriverAssignment.assigned_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())
<<<<<<< HEAD

=======
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
