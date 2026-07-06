import asyncio
import os
import sys
from sqlalchemy import select, and_

# Add project root to python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import AsyncSessionLocal
from app.models.trip import Trip
from app.models.route_cache import RouteCache, TripRouteCacheLink, GoogleRouteUsageEvent
from app.services.route_cache import get_or_compute_trip_route

async def verify_cache():
    print("====================================================")
    print("STARTING GOOGLE ROUTES CACHE VERIFICATION")
    print("====================================================")

    async with AsyncSessionLocal() as db:
        # 1. Fetch first completed trip
        stmt = select(Trip).where(Trip.is_active == False).limit(1)
        res = await db.execute(stmt)
        trip = res.scalars().first()

        if not trip:
            print("⚠ Error: No completed trips in database to verify route cache.")
            return

        print(f"Targeting Trip ID: {trip.id} for Vehicle ID: {trip.vehicle_id}")

        # 2. Count existing links for this trip
        link_stmt = select(TripRouteCacheLink).where(TripRouteCacheLink.trip_id == trip.id)
        link_res = await db.execute(link_stmt)
        initial_links = len(link_res.scalars().all())
        print(f"Initial cache links in DB for this trip: {initial_links}")

        # 3. Simulate first fetch (Cache Miss or Cached Hit)
        print("\nStep 1: Attempting to retrieve snapped route...")
        try:
            route = await get_or_compute_trip_route(db, trip.vehicle_id, trip.id)
            print(f"✓ Snapped route resolved successfully. Status: {route.status}, Cache Key: {route.cache_key}")
        except Exception as e:
            print(f"Note: API client raised expected exception (e.g. disabled key/offline test): {e}")

        # 4. Simulate second fetch (Must result in Cache Hit)
        print("\nStep 2: Performing second retrieve on same trip...")
        # Clear DB session cache to force reload from PostgreSQL
        db.expire_all()
        
        try:
            route_second = await get_or_compute_trip_route(db, trip.vehicle_id, trip.id)
            print(f"✓ Snapped route resolved successfully on second fetch. Status: {route_second.status}")
        except Exception as e:
            print(f"Note: API client raised exception: {e}")

        # 5. Check Audit logs
        usage_stmt = select(GoogleRouteUsageEvent).where(GoogleRouteUsageEvent.trip_id == trip.id).order_by(GoogleRouteUsageEvent.created_at.desc())
        usage_res = await db.execute(usage_stmt)
        events = usage_res.scalars().all()
        
        print("\nStep 3: Verification Log Results:")
        for idx, event in enumerate(events):
            print(f"  [{idx}] Type: {event.event_type} | Status: {event.status} | Created At: {event.created_at}")

        # Verify Cache Hit is present
        cache_hits = [e for e in events if e.event_type == "CACHE_HIT"]
        if cache_hits:
            print("\n✓ SUCCESS: Verification confirmed. Repeated queries resolved via database cache hits.")
        else:
            print("\n⚠ Warning: No CACHE_HIT audit events logged. Verify settings and run script again.")

if __name__ == "__main__":
    asyncio.run(verify_cache())
