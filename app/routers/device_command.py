from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.device_command import DeviceCommand
from app.models.command_log import CommandLog
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["Commands"])

@router.get("/commands")
async def list_commands(
    vehicle_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve queued device commands with options to filter by vehicle or status.
    """
    stmt = select(DeviceCommand)
    if vehicle_id is not None:
        stmt = stmt.where(DeviceCommand.vehicle_id == vehicle_id)
    if status is not None:
        stmt = stmt.where(DeviceCommand.status == status)
        
    stmt = stmt.order_by(desc(DeviceCommand.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    commands = result.scalars().all()
    return [
        {
            "id": c.id,
            "vehicle_id": c.vehicle_id,
            "command_type": c.command_type,
            "payload": c.payload,
            "status": c.status,
            "created_at": str(c.created_at),
            "sent_at": str(c.sent_at) if c.sent_at else None,
            "acknowledged_at": str(c.acknowledged_at) if c.acknowledged_at else None,
            "completed_at": str(c.completed_at) if c.completed_at else None,
            "response": c.response,
            "error_message": c.error_message
        }
        for c in commands
    ]

@router.get("/commands/{command_id}")
async def get_command_by_id(command_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve single command parameters and status triggers.
    """
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
    return {
        "id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "payload": c.payload,
        "status": c.status,
        "created_at": str(c.created_at),
        "sent_at": str(c.sent_at) if c.sent_at else None,
        "acknowledged_at": str(c.acknowledged_at) if c.acknowledged_at else None,
        "completed_at": str(c.completed_at) if c.completed_at else None,
        "response": c.response,
        "error_message": c.error_message
    }

@router.post("/commands", status_code=status.HTTP_201_CREATED)
async def create_command(
    vehicle_id: int,
    command_type: str,
    payload: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Queue a new command request. Initial state is 'Queued'.
    """
    # Map command_type parameter to legacy values where applicable
    c = DeviceCommand(
        vehicle_id=vehicle_id,
        command_type=command_type,
        payload=payload,
        status="Queued"
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    
    # Broadcast to command topic channel
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status
    })
    
    return {
        "id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "payload": c.payload,
        "status": c.status,
        "created_at": str(c.created_at)
    }

@router.post("/commands/{command_id}/cancel")
async def cancel_command(command_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancel an execution command.
    """
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
    
    c.status = "Cancelled"
    await db.commit()
    
    await ws_manager.broadcast("commands", {
        "event": "command_failed",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status,
        "error_message": "Command cancelled by dispatcher"
    })
    return {"status": "success", "message": "Command successfully cancelled."}

@router.post("/vehicles/{vehicle_id}/restart")
async def restart_vehicle_device(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Queue reboot command to target tracker.
    """
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Restart Device", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status
    })
    return {"status": "success", "command_id": c.id}

@router.post("/vehicles/{vehicle_id}/immobilize")
async def immobilize_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Queue immobilization cut-off command to vehicle relay.
    """
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Immobilize Vehicle", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status
    })
    return {"status": "success", "command_id": c.id}

@router.post("/vehicles/{vehicle_id}/restore")
async def restore_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """
    Queue restore command to reconnect vehicle relay.
    """
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Restore Vehicle", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status
    })
    return {"status": "success", "command_id": c.id}

# --- TRACKER BIDIRECTIONAL ACK / STATUS REST INTERFACES ---
@router.patch("/commands/{command_id}/acknowledge")
async def acknowledge_command_state(command_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
        
    c.status = "Acknowledged"
    c.acknowledged_at = datetime.utcnow()
    await db.commit()
    
    await ws_manager.broadcast("commands", {
        "event": "command_ack",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "status": c.status
    })
    return {"status": "success"}

@router.patch("/commands/{command_id}/complete")
async def complete_command_state(
    command_id: int, 
    response_payload: Optional[str] = Query(None, alias="response"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
        
    c.status = "Completed"
    c.completed_at = datetime.utcnow()
    c.response = response_payload or "Execution success"
    await db.commit()
    
    await ws_manager.broadcast("commands", {
        "event": "command_completed",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "status": c.status,
        "response": c.response
    })
    return {"status": "success"}

@router.patch("/commands/{command_id}/fail")
async def fail_command_state(
    command_id: int,
    error_message: str = Query(..., alias="error"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
        
    c.status = "Failed"
    c.error_message = error_message
    await db.commit()
    
    await ws_manager.broadcast("commands", {
        "event": "command_failed",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "status": c.status,
        "error_message": c.error_message
    })
    return {"status": "success"}
