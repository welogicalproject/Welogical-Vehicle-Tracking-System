import logging
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.trip import Trip
from app.models.route_cache import RouteCache, TripRouteCacheLink, GoogleRouteUsageEvent
from app.services.google_routes import call_google_routes_api, lock_registry
from app.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_normalized_key(
    origin_lat: float, origin_lon: float,
    destination_lat: float, destination_lon: float,
    travel_mode: str = "DRIVE"
) -> Tuple[str, str, str, float, float, float, float]:
    """
    Round coordinates to 5 decimal places and compute MD5 hashes for caching.
    Returns: (cache_key, options_hash, request_hash, normalized_coords...)
    """
    o_lat = round(origin_lat, 5)
    o_lon = round(origin_lon, 5)
    d_lat = round(destination_lat, 5)
    d_lon = round(destination_lon, 5)

    raw_key = f"google:routes:{travel_mode}:{o_lat:.5f},{o_lon:.5f}:{d_lat:.5f},{d_lon:.5f}"
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    
    options_hash = hashlib.md5(travel_mode.encode("utf-8")).hexdigest()
    request_hash = cache_key  # for simple REST v2 requests, request_hash equals cache_key

    return cache_key, options_hash, request_hash, o_lat, o_lon, d_lat, d_lon


async def log_usage_event(
    db: AsyncSession,
    event_type: str,
    status: str,
    cache_key: Optional[str] = None,
    route_cache_id: Optional[int] = None,
    trip_id: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    error_code: Optional[str] = None,
    metadata_dict: Optional[dict] = None
):
    """
    Log an API usage/cache event in the database for auditing and monthly billing limits.
    """
    try:
        now = utc_now_naive()
        period_month = now.strftime("%Y-%m")
        event = GoogleRouteUsageEvent(
            period_month=period_month,
            event_type=event_type,
            cache_key=cache_key,
            route_cache_id=route_cache_id,
            trip_id=trip_id,
            status=status,
            response_time_ms=response_time_ms,
            error_code=error_code,
            metadata_json=metadata_dict,
            created_at=now
        )
        db.add(event)
        await db.commit()
    except Exception as e:
        # Prevent database logging failure from failing the main route request flow
        logger.error(f"Failed to write GoogleRouteUsageEvent to database: {e}")


async def get_or_compute_trip_route(
    db: AsyncSession,
    vehicle_id: int,
    trip_id: int
) -> RouteCache:
    """
    Retrieve cached snapped route or query Google Routes API v2, with concurrency lock,
    audit event logging, and fallback logic.
    """
    # 1. Fetch Trip details
    trip_stmt = select(Trip).where(and_(Trip.id == trip_id, Trip.vehicle_id == vehicle_id))
    trip_res = await db.execute(trip_stmt)
    trip = trip_res.scalars().first()
    if not trip:
        raise EntityNotFoundError(f"Trip ID {trip_id} not found for vehicle {vehicle_id}")

    if trip.is_active:
        raise ValueError("Cannot snap coordinates for an active trip. Trip must be completed.")

    # 2. Check if a current link already exists for this trip
    link_stmt = select(TripRouteCacheLink).where(
        and_(
            TripRouteCacheLink.trip_id == trip_id,
            TripRouteCacheLink.is_current == True
        )
    )
    link_res = await db.execute(link_stmt)
    existing_link = link_res.scalars().first()

    if existing_link:
        # Active Link Found
        cache_stmt = select(RouteCache).where(RouteCache.id == existing_link.route_cache_id)
        cache_res = await db.execute(cache_stmt)
        route_cache = cache_res.scalars().first()
        if route_cache:
            logger.info(f"Cache HIT for trip ID {trip_id} (existing link ID {existing_link.id})")
            await log_usage_event(
                db, event_type="CACHE_HIT", status="SUCCESS",
                cache_key=route_cache.cache_key, route_cache_id=route_cache.id, trip_id=trip_id
            )
            return route_cache

    # 3. Calculate normalization hashes
    cache_key, options_hash, request_hash, o_lat, o_lon, d_lat, d_lon = calculate_normalized_key(
        trip.start_lat, trip.start_lon, trip.end_lat, trip.end_lon
    )

    # 4. Concurrency Protection (Acquire asyncio.Lock for the route key)
    lock = await lock_registry.get_lock(cache_key)
    async with lock:
        # Check DB cache again in case another concurrent request just completed the API call
        stmt = select(RouteCache).where(RouteCache.cache_key == cache_key)
        res = await db.execute(stmt)
        cached_entry = res.scalars().first()

        if cached_entry:
            logger.info(f"Cache HIT (after lock wait) for cache_key {cache_key}")
            # Link trip to this cache entry
            new_link = TripRouteCacheLink(
                trip_id=trip_id,
                route_cache_id=cached_entry.id,
                trip_fingerprint=f"trip_{trip_id}_v_{vehicle_id}",
                route_source="cache_hit",
                is_current=True,
                linked_at=utc_now_naive()
            )
            db.add(new_link)
            await db.commit()
            
            await log_usage_event(
                db, event_type="CACHE_HIT", status="SUCCESS",
                cache_key=cache_key, route_cache_id=cached_entry.id, trip_id=trip_id
            )
            return cached_entry

        # 5. Cache MISS - Perform Google API call
        if not settings.GOOGLE_ROUTES_ENABLED:
            raise ValueError("Google Routes Integration is disabled in settings.")

        start_time = datetime.now()
        api_status = "UNKNOWN"
        error_code = None

        try:
            # Query Google Routes API
            result = await call_google_routes_api(
                origin_lat=trip.start_lat,
                origin_lon=trip.start_lon,
                destination_lat=trip.end_lat,
                destination_lon=trip.end_lon
            )

            api_status = result["status"]  # "SUCCESS" or "ZERO_RESULTS"
            
            db_cache = RouteCache(
                cache_key=cache_key,
                provider="google",
                provider_api="routes",
                route_schema_version=1,
                travel_mode="DRIVE",
                coordinate_precision=5,
                origin_lat_raw=trip.start_lat,
                origin_lon_raw=trip.start_lon,
                destination_lat_raw=trip.end_lat,
                destination_lon_raw=trip.end_lon,
                origin_lat_normalized=o_lat,
                origin_lon_normalized=o_lon,
                destination_lat_normalized=d_lat,
                destination_lon_normalized=d_lon,
                options_hash=options_hash,
                request_hash=request_hash,
                status="success" if api_status == "SUCCESS" else "failed",
                created_at=utc_now_naive(),
                updated_at=utc_now_naive()
            )

            if api_status == "SUCCESS":
                db_cache.encoded_polyline = result["encoded_polyline"]
                db_cache.distance_meters = result["distance_meters"]
                db_cache.duration_seconds = result["duration_seconds"]
                db_cache.static_duration_seconds = result.get("static_duration_seconds")
                db_cache.traffic_duration_seconds = result.get("duration_seconds")
            else:
                # ZERO_RESULTS
                db_cache.invalidated_reason = "ZERO_RESULTS"
                db_cache.invalidated_at = utc_now_naive()

            # Conditionally save raw response summary based on settings
            if settings.SAVE_RAW_GOOGLE_RESPONSES:
                db_cache.provider_response_summary = result["raw_response"]

            db.add(db_cache)
            await db.flush()

            # Link trip to new cache entry
            new_link = TripRouteCacheLink(
                trip_id=trip_id,
                route_cache_id=db_cache.id,
                trip_fingerprint=f"trip_{trip_id}_v_{vehicle_id}",
                route_source="api_call",
                is_current=True,
                linked_at=utc_now_naive()
            )
            db.add(new_link)
            await db.commit()

            # Log Audit usage event
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await log_usage_event(
                db, event_type="API_CALL", status="SUCCESS" if api_status == "SUCCESS" else "FAILED",
                cache_key=cache_key, route_cache_id=db_cache.id, trip_id=trip_id,
                response_time_ms=elapsed_ms, error_code="ZERO_RESULTS" if api_status == "ZERO_RESULTS" else None
            )

            return db_cache

        except Exception as e:
            # DB/Network API error
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            error_code = type(e).__name__
            logger.error(f"Failed to snap route for trip {trip_id}: {e}")
            
            # Audit log usage failure
            await log_usage_event(
                db, event_type="API_CALL", status="FAILED",
                cache_key=cache_key, trip_id=trip_id,
                response_time_ms=elapsed_ms, error_code=error_code,
                metadata_dict={"error_message": str(e)}
            )
            raise e
        finally:
            # Clean up Lock Registry reference once lock release completes
            await lock_registry.remove_lock(cache_key)
