from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, desc, asc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.models.vehicle import Vehicle


async def get_events(
    db: AsyncSession,
    vehicle_id: Optional[int] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    sort: str = "desc"
) -> List[Event]:
    query = select(Event).options(selectinload(Event.vehicle))
    
    if vehicle_id is not None:
        query = query.where(Event.vehicle_id == vehicle_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)
    if severity is not None:
        query = query.where(Event.severity == severity)
    if start_time is not None:
        query = query.where(Event.created_at >= start_time)
    if end_time is not None:
        query = query.where(Event.created_at <= end_time)
        
    if sort.lower() == "asc":
        query = query.order_by(asc(Event.created_at))
    else:
        query = query.order_by(desc(Event.created_at))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_recent_events(db: AsyncSession, limit: int = 10) -> List[Event]:
    query = select(Event).options(selectinload(Event.vehicle)).order_by(desc(Event.created_at)).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_vehicle_events(
    db: AsyncSession,
    vehicle_id: int,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Event]:
    query = select(Event).options(selectinload(Event.vehicle)).where(Event.vehicle_id == vehicle_id)
    if severity is not None:
        query = query.where(Event.severity == severity)
    query = query.order_by(desc(Event.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_events_stats(db: AsyncSession) -> dict:
    # 1. Total counts by severity
    critical_query = select(func.count(Event.id)).where(Event.severity == "Critical")
    warning_query = select(func.count(Event.id)).where(Event.severity == "Warning")
    info_query = select(func.count(Event.id)).where(Event.severity == "Info")
    
    # 2. Total overall
    total_query = select(func.count(Event.id))
    
    # 3. Today's count (UTC start of day 00:00:00)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    today_query = select(func.count(Event.id)).where(Event.created_at >= today_start)
    
    critical_count = (await db.execute(critical_query)).scalar_one()
    warning_count = (await db.execute(warning_query)).scalar_one()
    info_count = (await db.execute(info_query)).scalar_one()
    total_count = (await db.execute(total_query)).scalar_one()
    today_count = (await db.execute(today_query)).scalar_one()
    
    return {
        "critical": critical_count,
        "warning": warning_count,
        "info": info_count,
        "today": today_count,
        "total": total_count
    }
