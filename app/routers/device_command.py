from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.device_command import DeviceCommandCreate, DeviceCommandUpdate, DeviceCommandResponse
from app.schemas.command_log import CommandLogResponse
from app.models.enums import CommandStatus
import app.crud.device_command as crud_command

router = APIRouter(prefix="/commands", tags=["Commands"])


@router.get("", response_model=List[DeviceCommandResponse], status_code=status.HTTP_200_OK)
async def list_commands(
    vehicle_id: Optional[int] = Query(None, description="Filter commands by vehicle ID"),
    status_filter: Optional[CommandStatus] = Query(None, alias="status", description="Filter by status: PENDING, SENT, EXECUTED, FAILED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve queued device commands with options to filter by vehicle or status.
    """
    return await crud_command.list_commands(
        db,
        vehicle_id=vehicle_id,
        status=status_filter,
        skip=skip,
        limit=limit
    )


@router.get("/{vehicle_id}", response_model=List[DeviceCommandResponse], status_code=status.HTTP_200_OK)
async def get_commands_by_vehicle(
    vehicle_id: int,
    status_filter: Optional[CommandStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve command queue history associated with a specific vehicle.
    """
    return await crud_command.list_commands(
        db,
        vehicle_id=vehicle_id,
        status=status_filter,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DeviceCommandResponse, status_code=status.HTTP_201_CREATED)
async def queue_new_command(
    command_in: DeviceCommandCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Queue a new command for a vehicle. Initial status is PENDING.
    """
    return await crud_command.create_command(db, command_in=command_in)


@router.put("/{id}/send", response_model=DeviceCommandResponse, status_code=status.HTTP_200_OK)
async def mark_command_as_sent(
    id: int,
    message: Optional[str] = Query(None, description="Descriptive log message detailing delivery context"),
    db: AsyncSession = Depends(get_db)
):
    """
    Transition command status from PENDING to SENT and update delivery timestamp.
    """
    update_data = DeviceCommandUpdate(
        status=CommandStatus.SENT,
        message=message or "Command delivered to device via telemetry response"
    )
    return await crud_command.update_status(db, command_id=id, status_update=update_data)


@router.put("/{id}/execute", response_model=DeviceCommandResponse, status_code=status.HTTP_200_OK)
async def mark_command_as_executed(
    id: int,
    message: Optional[str] = Query(None, description="Descriptive log message detailing execution result"),
    db: AsyncSession = Depends(get_db)
):
    """
    Transition command status from SENT to EXECUTED, set execution timestamp, and trigger associated events.
    """
    update_data = DeviceCommandUpdate(
        status=CommandStatus.EXECUTED,
        message=message or "Acknowledge code received from hardware device"
    )
    return await crud_command.update_status(db, command_id=id, status_update=update_data)


@router.put("/{id}/fail", response_model=DeviceCommandResponse, status_code=status.HTTP_200_OK)
async def mark_command_as_failed(
    id: int,
    message: str = Query(..., description="Details regarding why execution failed"),
    db: AsyncSession = Depends(get_db)
):
    """
    Transition command status to FAILED, record execution timestamp, and trigger audit logging.
    """
    update_data = DeviceCommandUpdate(
        status=CommandStatus.FAILED,
        message=message
    )
    return await crud_command.update_status(db, command_id=id, status_update=update_data)


@router.delete("/{id}", response_model=DeviceCommandResponse, status_code=status.HTTP_200_OK)
async def delete_queued_command(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a command from the queue.
    """
    return await crud_command.delete_command(db, command_id=id)


@router.get("/{id}/logs", response_model=List[CommandLogResponse], status_code=status.HTTP_200_OK)
async def get_command_audit_logs(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the historical lifecycle logs for a specific command.
    """
    return await crud_command.get_command_logs(db, command_id=id)
