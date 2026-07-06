import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import AsyncSessionLocal
from app.services.google_routes import call_google_routes_api, parse_google_duration
from app.services.route_cache import get_or_compute_trip_route, calculate_normalized_key
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from sqlalchemy import select

async def run_test():
    print("--- Starting Route Services Verification ---")
    
    # 1. Test Duration Parsing
    assert parse_google_duration("123s") == 123
    assert parse_google_duration("3600.5s") == 3600
    assert parse_google_duration(None) is None
    print("✓ parse_google_duration verification passed.")

    # 2. Test Hashing & Normalization
    key1, opt1, req1, lat1, lon1, d_lat1, d_lon1 = calculate_normalized_key(22.307212, 73.181232, 22.312343, 73.194563)
    key2, opt2, req2, lat2, lon2, d_lat2, d_lon2 = calculate_normalized_key(22.307214, 73.181230, 22.312341, 73.194561)
    
    # Precise rounding to 5 decimals should make these keys match
    assert key1 == key2
    assert opt1 == opt2
    assert req1 == req2
    assert lat1 == 22.30721
    assert lon1 == 73.18123
    print("✓ Normalized cache hashing verification passed.")

    # 3. Test Service Ingestion (Requires database connection)
    async with AsyncSessionLocal() as db:
        # Fetch first completed trip in DB
        trip_stmt = select(Trip).where(Trip.is_active == False).limit(1)
        res = await db.execute(trip_stmt)
        trip = res.scalars().first()
        
        if not trip:
            print("⚠ No completed trips found in database. Skipping API client integration test.")
            return

        print(f"Testing Snap-Route for Trip ID: {trip.id}, Vehicle ID: {trip.vehicle_id}")
        
        # Test concurrent requests lock handling
        print("Spawning 3 concurrent requests to check LockRegistry protection...")
        async def run_task():
            async with AsyncSessionLocal() as session:
                return await get_or_compute_trip_route(session, trip.vehicle_id, trip.id)

        tasks = [run_task(), run_task(), run_task()]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        
        # Check if any errors occurred
        success_count = 0
        exceptions = []
        for r in results:
            if isinstance(r, Exception):
                exceptions.append(r)
            else:
                success_count += 1
                
        print(f"Concurrent requests completed: {success_count} succeeded, {len(exceptions)} exceptions raised.")
        for exc in exceptions:
            print(f"Exception details: {exc}")

if __name__ == "__main__":
    asyncio.run(run_test())
