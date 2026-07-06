from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.route_cache import RouteCache, TripRouteCacheLink, GoogleRouteUsageEvent
from app.schemas.route_cache import (
    RouteCacheCreate,
    RouteCacheUpdate,
    TripRouteCacheLinkCreate,
    TripRouteCacheLinkUpdate,
    GoogleRouteUsageEventCreate,
)
from app.exceptions import EntityNotFoundError


async def get_route_cache(db: AsyncSession, route_cache_id: int) -> RouteCache:
    result = await db.execute(select(RouteCache).where(RouteCache.id == route_cache_id))
    route_cache = result.scalars().first()
    if not route_cache:
        raise EntityNotFoundError(f"Route cache with ID {route_cache_id} not found")
    return route_cache


async def get_route_cache_by_key(db: AsyncSession, cache_key: str) -> Optional[RouteCache]:
    result = await db.execute(select(RouteCache).where(RouteCache.cache_key == cache_key))
    return result.scalars().first()


async def list_route_cache_entries(
    db: AsyncSession,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[RouteCache]:
    query = select(RouteCache)
    if provider is not None:
        query = query.where(RouteCache.provider == provider)
    if status is not None:
        query = query.where(RouteCache.status == status)
    query = query.order_by(desc(RouteCache.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_route_cache(db: AsyncSession, route_cache_in: RouteCacheCreate) -> RouteCache:
    db_route_cache = RouteCache(**route_cache_in.model_dump())
    db.add(db_route_cache)
    await db.commit()
    await db.refresh(db_route_cache)
    return db_route_cache


async def update_route_cache(
    db: AsyncSession,
    route_cache_id: int,
    route_cache_in: RouteCacheUpdate
) -> RouteCache:
    db_route_cache = await get_route_cache(db, route_cache_id)
    update_data = route_cache_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_route_cache, field, value)
    await db.commit()
    await db.refresh(db_route_cache)
    return db_route_cache


async def delete_route_cache(db: AsyncSession, route_cache_id: int) -> RouteCache:
    db_route_cache = await get_route_cache(db, route_cache_id)
    await db.delete(db_route_cache)
    await db.commit()
    return db_route_cache


async def get_trip_route_cache_link(db: AsyncSession, link_id: int) -> TripRouteCacheLink:
    result = await db.execute(select(TripRouteCacheLink).where(TripRouteCacheLink.id == link_id))
    link = result.scalars().first()
    if not link:
        raise EntityNotFoundError(f"Trip route cache link with ID {link_id} not found")
    return link


async def get_current_trip_route_cache_link(db: AsyncSession, trip_id: int) -> Optional[TripRouteCacheLink]:
    result = await db.execute(
        select(TripRouteCacheLink).where(
            TripRouteCacheLink.trip_id == trip_id,
            TripRouteCacheLink.is_current == True
        )
    )
    return result.scalars().first()


async def create_trip_route_cache_link(
    db: AsyncSession,
    link_in: TripRouteCacheLinkCreate
) -> TripRouteCacheLink:
    db_link = TripRouteCacheLink(**link_in.model_dump())
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link


async def update_trip_route_cache_link(
    db: AsyncSession,
    link_id: int,
    link_in: TripRouteCacheLinkUpdate
) -> TripRouteCacheLink:
    db_link = await get_trip_route_cache_link(db, link_id)
    update_data = link_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_link, field, value)
    await db.commit()
    await db.refresh(db_link)
    return db_link


async def delete_trip_route_cache_link(db: AsyncSession, link_id: int) -> TripRouteCacheLink:
    db_link = await get_trip_route_cache_link(db, link_id)
    await db.delete(db_link)
    await db.commit()
    return db_link


async def create_google_route_usage_event(
    db: AsyncSession,
    event_in: GoogleRouteUsageEventCreate
) -> GoogleRouteUsageEvent:
    event_data = event_in.model_dump()
    event_data["metadata_json"] = event_data.pop("metadata", None)
    db_event = GoogleRouteUsageEvent(**event_data)
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


async def list_google_route_usage_events(
    db: AsyncSession,
    period_month: Optional[str] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[GoogleRouteUsageEvent]:
    query = select(GoogleRouteUsageEvent)
    if period_month is not None:
        query = query.where(GoogleRouteUsageEvent.period_month == period_month)
    if event_type is not None:
        query = query.where(GoogleRouteUsageEvent.event_type == event_type)
    query = query.order_by(desc(GoogleRouteUsageEvent.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
