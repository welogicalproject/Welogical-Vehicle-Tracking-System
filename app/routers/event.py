from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.event import EventResponse
import app.crud.event as crud_event

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_events_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated counts of events by severity (Critical, Warning, Info),
    total count, and today's total count.
    """
    return await crud_event.get_events_stats(db)


@router.get("/recent", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
async def get_recent_fleet_events(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a chronological list of the most recent events logged across all vehicles.
    """
    return await crud_event.get_recent_events(db, limit=limit)


@router.get("", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
async def list_fleet_events(
    vehicle_id: Optional[int] = Query(None, description="Filter events by vehicle ID"),
    event_type: Optional[str] = Query(None, description="Filter events by event type name"),
    severity: Optional[str] = Query(None, description="Filter events by severity: Critical, Warning, Info"),
    start_time: Optional[datetime] = Query(None, description="Filter events starting from ISO timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter events ending at ISO timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort: str = Query("desc", description="Sort by timestamp: asc or desc"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve events matching filters with pagination and sorting.
    """
    return await crud_event.get_events(
        db,
        vehicle_id=vehicle_id,
        event_type=event_type,
        severity=severity,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
        sort=sort
    )


@router.get("/{vehicle_id}", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
async def get_events_by_vehicle(
    vehicle_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity: Critical, Warning, Info"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve chronological events for a specific vehicle.
    """
    return await crud_event.get_vehicle_events(
        db,
        vehicle_id=vehicle_id,
        severity=severity,
        skip=skip,
        limit=limit
    )
