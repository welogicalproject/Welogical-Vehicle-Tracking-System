from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.notification_history import NotificationHistory

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
async def list_notifications(
    vehicle_id: Optional[int] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve persisted notifications log matching filters.
    """
    stmt = select(NotificationHistory)
    if vehicle_id is not None:
        stmt = stmt.where(NotificationHistory.vehicle_id == vehicle_id)
    if acknowledged is not None:
        stmt = stmt.where(NotificationHistory.acknowledged == acknowledged)
    if resolved is not None:
        stmt = stmt.where(NotificationHistory.resolved == resolved)
        
    stmt = stmt.order_by(desc(NotificationHistory.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "vehicle_id": n.vehicle_id,
            "driver_id": n.driver_id,
            "severity": n.severity,
            "title": n.title,
            "message": n.message,
            "source_event_id": n.source_event_id,
            "created_at": str(n.created_at),
            "acknowledged": n.acknowledged,
            "resolved": n.resolved
        }
        for n in notifications
    ]

@router.get("/{notification_id}")
async def get_notification_details(notification_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details for a specific notification.
    """
    stmt = select(NotificationHistory).where(NotificationHistory.id == notification_id)
    result = await db.execute(stmt)
    n = result.scalars().first()
    if not n:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification ID {notification_id} not found."
        )
        
    return {
        "id": n.id,
        "vehicle_id": n.vehicle_id,
        "driver_id": n.driver_id,
        "severity": n.severity,
        "title": n.title,
        "message": n.message,
        "source_event_id": n.source_event_id,
        "created_at": str(n.created_at),
        "acknowledged": n.acknowledged,
        "resolved": n.resolved
    }

@router.patch("/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mark a notification alert as acknowledged.
    """
    stmt = select(NotificationHistory).where(NotificationHistory.id == notification_id)
    result = await db.execute(stmt)
    n = result.scalars().first()
    if not n:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification ID {notification_id} not found."
        )
        
    n.acknowledged = True
    await db.commit()
    
    return {"status": "success", "message": f"Notification {notification_id} acknowledged successfully."}

@router.patch("/{notification_id}/resolve")
async def resolve_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mark a notification alert as resolved.
    """
    stmt = select(NotificationHistory).where(NotificationHistory.id == notification_id)
    result = await db.execute(stmt)
    n = result.scalars().first()
    if not n:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification ID {notification_id} not found."
        )
        
    n.resolved = True
    await db.commit()
    
    return {"status": "success", "message": f"Notification {notification_id} resolved successfully."}
