from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device_command import DeviceCommand
from app.models.command_log import CommandLog
from app.models.enums import CommandStatus
from app.schemas.device_command import DeviceCommandCreate, DeviceCommandUpdate
from app.exceptions import EntityNotFoundError


async def get_command(db: AsyncSession, command_id: int) -> DeviceCommand:
    result = await db.execute(
        select(DeviceCommand)
        .options(selectinload(DeviceCommand.vehicle))
        .where(DeviceCommand.id == command_id)
    )
    command = result.scalars().first()
    if not command:
        raise EntityNotFoundError(f"Command with ID {command_id} not found")
    return command


async def list_commands(
    db: AsyncSession,
    vehicle_id: Optional[int] = None,
    status: Optional[CommandStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[DeviceCommand]:
    query = select(DeviceCommand).options(selectinload(DeviceCommand.vehicle))
    
    if vehicle_id is not None:
        query = query.where(DeviceCommand.vehicle_id == vehicle_id)
    if status is not None:
        query = query.where(DeviceCommand.status == status)
        
    query = query.order_by(desc(DeviceCommand.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_command(db: AsyncSession, command_in: DeviceCommandCreate) -> DeviceCommand:
    # 1. Create command
    db_command = DeviceCommand(
        vehicle_id=command_in.vehicle_id,
        command_name=command_in.command_name,
        command_value=command_in.command_value,
        status=CommandStatus.PENDING
    )
    db.add(db_command)
    await db.flush()  # Flush to get the auto-generated ID

    # 2. Add audit log
    db_log = CommandLog(
        command_id=db_command.id,
        vehicle_id=db_command.vehicle_id,
        status=CommandStatus.PENDING,
        message=f"Command queued: {db_command.command_name}={db_command.command_value}" if db_command.command_value else f"Command queued: {db_command.command_name}"
    )
    db.add(db_log)
    
    await db.commit()
    await db.refresh(db_command)
    return db_command


async def update_status(db: AsyncSession, command_id: int, status_update: DeviceCommandUpdate) -> DeviceCommand:
    # 1. Update command state
    db_command = await get_command(db, command_id)
    old_status = db_command.status
    new_status = status_update.status
    
    db_command.status = new_status
    
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    if new_status == CommandStatus.SENT:
        db_command.sent_at = now_naive
    elif new_status in (CommandStatus.EXECUTED, CommandStatus.FAILED):
        db_command.executed_at = now_naive
        
    # 2. Add audit log
    log_msg = status_update.message or f"Status changed from {old_status} to {new_status}"
    db_log = CommandLog(
        command_id=db_command.id,
        vehicle_id=db_command.vehicle_id,
        status=new_status,
        message=log_msg
    )
    db.add(db_log)
    
    # 3. Trigger events / config updates based on execution success/failure
    if new_status == CommandStatus.EXECUTED:
        from app.services.event_decoder import handle_command_execution
        await handle_command_execution(db, db_command)
    elif new_status == CommandStatus.FAILED:
        from app.services.event_decoder import trigger_system_event
        await trigger_system_event(
            db,
            vehicle_id=db_command.vehicle_id,
            txn="Q",
            event_type="Command Failed",
            description=f"Device command {db_command.command_name} execution failed: {log_msg}",
            severity="Warning"
        )

    await db.commit()
    await db.refresh(db_command)
    return db_command


async def delete_command(db: AsyncSession, command_id: int) -> DeviceCommand:
    db_command = await get_command(db, command_id)
    await db.delete(db_command)
    await db.commit()
    return db_command


# Command Logs list
async def get_command_logs(db: AsyncSession, command_id: int) -> List[CommandLog]:
    result = await db.execute(
        select(CommandLog)
        .where(CommandLog.command_id == command_id)
        .order_by(CommandLog.created_at.asc())
    )
    return list(result.scalars().all())
