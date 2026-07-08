from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.device_command import DeviceCommand
from app.models.command_log import CommandLog
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["Commands"])


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class CreateCommandBody(BaseModel):
    """
    JSON body accepted by POST /commands.

    Accepts BOTH naming conventions for backward compatibility:
      - New API:  command_type  / payload
      - Legacy:   command_name  / command_value

    The legacy aliases are resolved first so existing frontend code that
    still sends { command_name, command_value } continues to work without
    any frontend changes.
    """
    vehicle_id: int

    # Primary field names (new contract)
    command_type: Optional[str] = Field(None, description="Command type e.g. 'Restart Device'")
    payload: Optional[str] = Field(None, description="Optional command parameter value")

    # Legacy aliases (old contract — kept for backward compatibility)
    command_name: Optional[str] = Field(None, description="Legacy alias for command_type")
    command_value: Optional[str] = Field(None, description="Legacy alias for payload")

    def resolved_command_type(self) -> str:
        """Return command_type, falling back to command_name."""
        val = self.command_type or self.command_name
        if not val:
            raise ValueError("Either command_type or command_name must be provided.")
        return val

    def resolved_payload(self) -> Optional[str]:
        """Return payload, falling back to command_value."""
        return self.payload or self.command_value


class CompleteCommandBody(BaseModel):
    """Optional JSON body for PATCH /commands/{id}/complete."""
    response: Optional[str] = Field(None, description="Execution result message from device")


class FailCommandBody(BaseModel):
    """JSON body for PATCH /commands/{id}/fail."""
    error: str = Field(..., description="Error message returned by device")


# ---------------------------------------------------------------------------
# Shared serialiser
# ---------------------------------------------------------------------------

def _serialize(c: DeviceCommand) -> dict:
    """
    Serialize a DeviceCommand row.
    Includes BOTH new field names (command_type / payload) and legacy aliases
    (command_name / command_value) so old and new frontend code both work.
    """
    return {
        "id": c.id,
        "vehicle_id": c.vehicle_id,
        # New field names
        "command_type": c.command_type,
        "payload": c.payload,
        # Legacy aliases — map new columns back to old names
        "command_name": c.command_type,
        "command_value": c.payload,
        # Status (new vocabulary: Queued → Delivered → Acknowledged → Completed)
        "status": c.status,
        # Timestamps
        "created_at": str(c.created_at),
        "sent_at": str(c.sent_at) if c.sent_at else None,
        "acknowledged_at": str(c.acknowledged_at) if c.acknowledged_at else None,
        # Legacy alias for executed_at
        "executed_at": str(c.completed_at) if c.completed_at else None,
        "completed_at": str(c.completed_at) if c.completed_at else None,
        # Result fields
        "response": c.response,
        "error_message": c.error_message,
    }


# ---------------------------------------------------------------------------
# GET /commands
# ---------------------------------------------------------------------------

@router.get("/commands")
async def list_commands(
    vehicle_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve queued device commands with optional vehicle / status filters."""
    stmt = select(DeviceCommand)
    if vehicle_id is not None:
        stmt = stmt.where(DeviceCommand.vehicle_id == vehicle_id)
    if status is not None:
        stmt = stmt.where(DeviceCommand.status == status)

    stmt = stmt.order_by(desc(DeviceCommand.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return [_serialize(c) for c in result.scalars().all()]


# ---------------------------------------------------------------------------
# GET /commands/{command_id}
# ---------------------------------------------------------------------------

@router.get("/commands/{command_id}")
async def get_command_by_id(command_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a single command record by ID."""
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")
    return _serialize(c)


# ---------------------------------------------------------------------------
# POST /commands  ← THE BUG WAS HERE
# ---------------------------------------------------------------------------

@router.post("/commands", status_code=status.HTTP_201_CREATED)
async def create_command(
    body: CreateCommandBody,        # ← Pydantic model: reads JSON body, not query params
    db: AsyncSession = Depends(get_db),
):
    """
    Queue a new device command. Accepts JSON body.

    Supports both naming conventions:
      { "vehicle_id": 1, "command_type": "Restart Device", "payload": null }
      { "vehicle_id": 1, "command_name": "RESUME",         "command_value": "30" }
    """
    cmd_type = body.resolved_command_type()
    cmd_payload = body.resolved_payload()

    c = DeviceCommand(
        vehicle_id=body.vehicle_id,
        command_type=cmd_type,
        payload=cmd_payload,
        status="Queued",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)

    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status,
    })

    return _serialize(c)


# ---------------------------------------------------------------------------
# POST /commands/{command_id}/cancel
# ---------------------------------------------------------------------------

@router.post("/commands/{command_id}/cancel")
async def cancel_command(command_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a queued or in-flight command."""
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
        "error_message": "Command cancelled by dispatcher",
    })
    return {"status": "success", "message": "Command successfully cancelled."}


# ---------------------------------------------------------------------------
# DELETE /commands/{command_id}  (called by frontend api.deleteCommand)
# ---------------------------------------------------------------------------

@router.delete("/commands/{command_id}", status_code=status.HTTP_200_OK)
async def delete_command(command_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a command record permanently.
    Called by the frontend's api.deleteCommand() helper.
    """
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")

    await db.delete(c)
    await db.commit()
    return {"status": "success", "message": "Command deleted."}


# ---------------------------------------------------------------------------
# GET /commands/{command_id}/logs  (called by frontend api.getCommandLogs)
# ---------------------------------------------------------------------------

@router.get("/commands/{command_id}/logs")
async def get_command_logs(command_id: int, db: AsyncSession = Depends(get_db)):
    """Return the audit log entries for a specific command."""
    result = await db.execute(
        select(CommandLog)
        .where(CommandLog.command_id == command_id)
        .order_by(CommandLog.created_at.asc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "command_id": log.command_id,
            "vehicle_id": log.vehicle_id,
            "status": log.status,
            "message": log.message,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]


# ---------------------------------------------------------------------------
# Quick-action endpoints (path param = vehicle_id, no body needed)
# ---------------------------------------------------------------------------

@router.post("/vehicles/{vehicle_id}/restart")
async def restart_vehicle_device(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Queue a 'Restart Device' command to the target tracker."""
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Restart Device", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status,
    })
    return {"status": "success", "command_id": c.id}


@router.post("/vehicles/{vehicle_id}/immobilize")
async def immobilize_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Queue an 'Immobilize Vehicle' relay cut-off command."""
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Immobilize Vehicle", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status,
    })
    return {"status": "success", "command_id": c.id}


@router.post("/vehicles/{vehicle_id}/restore")
async def restore_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Queue a 'Restore Vehicle' relay reconnect command."""
    c = DeviceCommand(vehicle_id=vehicle_id, command_type="Restore Vehicle", status="Queued")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await ws_manager.broadcast("commands", {
        "event": "command_created",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "command_type": c.command_type,
        "status": c.status,
    })
    return {"status": "success", "command_id": c.id}


# ---------------------------------------------------------------------------
# Tracker bidirectional ACK / status transitions
# ---------------------------------------------------------------------------

@router.patch("/commands/{command_id}/acknowledge")
async def acknowledge_command_state(command_id: int, db: AsyncSession = Depends(get_db)):
    """Transition command status to Acknowledged (called by device/simulator)."""
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
        "status": c.status,
    })
    return {"status": "success"}


@router.patch("/commands/{command_id}/complete")
async def complete_command_state(
    command_id: int,
    body: CompleteCommandBody = CompleteCommandBody(),
    # Also accept response as a query param for simulator backward compat
    response_qs: Optional[str] = Query(None, alias="response"),
    db: AsyncSession = Depends(get_db),
):
    """Transition command status to Completed (called by device/simulator)."""
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")

    c.status = "Completed"
    c.completed_at = datetime.utcnow()
    c.response = body.response or response_qs or "Execution success"
    await db.commit()

    await ws_manager.broadcast("commands", {
        "event": "command_completed",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "status": c.status,
        "response": c.response,
    })
    return {"status": "success"}


@router.patch("/commands/{command_id}/fail")
async def fail_command_state(
    command_id: int,
    body: FailCommandBody = None,
    error_qs: Optional[str] = Query(None, alias="error"),
    db: AsyncSession = Depends(get_db),
):
    """Transition command status to Failed (called by device/simulator)."""
    result = await db.execute(select(DeviceCommand).where(DeviceCommand.id == command_id))
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found.")

    error_msg = (body.error if body else None) or error_qs or "Unknown failure"
    c.status = "Failed"
    c.error_message = error_msg
    await db.commit()

    await ws_manager.broadcast("commands", {
        "event": "command_failed",
        "command_id": c.id,
        "vehicle_id": c.vehicle_id,
        "status": c.status,
        "error_message": c.error_message,
    })
    return {"status": "success"}
