import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import AsyncSessionLocal
from app.crud.location import get_location_history
from app.crud.vehicle import get_vehicles

async def run_regression_test():
    print("Initializing timezone regression tests...")
    
    async with AsyncSessionLocal() as session:
        # Fetch an existing vehicle ID to test query execution path
        vehicles = await get_vehicles(session, limit=1)
        if not vehicles:
            print("No vehicles found in database. Please register at least one vehicle to test query path.")
            return
            
        vehicle_id = vehicles[0].id
        print(f"Testing query paths using vehicle_id: {vehicle_id}")
        
        # Test Case 1: Naive UTC datetimes
        naive_start = datetime(2026, 6, 23, 0, 0, 0)
        naive_end = datetime(2026, 6, 24, 0, 0, 0)
        try:
            res = await get_location_history(session, vehicle_id=vehicle_id, start_time=naive_start, end_time=naive_end)
            print("✅ TEST 1 PASSED: Query with naive datetimes executed successfully. Records found:", len(res))
        except Exception as e:
            print("❌ TEST 1 FAILED: Query with naive datetimes raised exception:", e)
            
        # Test Case 2: Timezone-aware UTC datetimes (ending with Z)
        aware_utc_start = datetime(2026, 6, 23, 0, 0, 0, tzinfo=timezone.utc)
        aware_utc_end = datetime(2026, 6, 24, 0, 0, 0, tzinfo=timezone.utc)
        try:
            res = await get_location_history(session, vehicle_id=vehicle_id, start_time=aware_utc_start, end_time=aware_utc_end)
            print("✅ TEST 2 PASSED: Query with UTC aware datetimes (Z) executed successfully. Records found:", len(res))
        except Exception as e:
            print("❌ TEST 2 FAILED: Query with UTC aware datetimes (Z) raised exception:", e)

        # Test Case 3: Timezone-aware datetimes with local offsets (e.g. +05:30)
        local_tz = timezone(timedelta(hours=5, minutes=30))
        aware_offset_start = datetime(2026, 6, 23, 0, 0, 0, tzinfo=local_tz)
        aware_offset_end = datetime(2026, 6, 24, 0, 0, 0, tzinfo=local_tz)
        try:
            res = await get_location_history(session, vehicle_id=vehicle_id, start_time=aware_offset_start, end_time=aware_offset_end)
            print("✅ TEST 3 PASSED: Query with offset-aware datetimes (+05:30) executed successfully. Records found:", len(res))
        except Exception as e:
            print("❌ TEST 3 FAILED: Query with offset-aware datetimes (+05:30) raised exception:", e)

        # Test Case 4: Missing/Empty bounds
        try:
            res = await get_location_history(session, vehicle_id=vehicle_id, start_time=None, end_time=None)
            print("✅ TEST 4 PASSED: Query with empty time bounds executed successfully. Records found:", len(res))
        except Exception as e:
            print("❌ TEST 4 FAILED: Query with empty time bounds raised exception:", e)

if __name__ == "__main__":
    asyncio.run(run_regression_test())
