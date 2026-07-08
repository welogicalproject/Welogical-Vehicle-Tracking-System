import os
import sys
from datetime import date
from fastapi.testclient import TestClient

# Add project root to python path to import app and database
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.main import app
from app.database import SyncSessionLocal
from app.models.fleet_daily_summary import FleetDailySummary
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.vehicle import Vehicle

client = TestClient(app)

def test_analytics_endpoints():
    print("======================================================================")
    print("                 VTS ANALYTICS ENDPOINTS UNIT TESTS                  ")
    print("======================================================================")
    
    db = SyncSessionLocal()
    
    # 1. Fetch or create a test vehicle
    v = db.query(Vehicle).filter_by(device_uid="API-TEST-V01").first()
    if not v:
        v = Vehicle(device_uid="API-TEST-V01", vehicle_name="API Test Vehicle", vehicle_type="Car")
        db.add(v)
        db.commit()
        db.refresh(v)

    # 2. Insert mock summaries for current calendar date
    today_date = date.today()
    
    # Clean previous executions if any
    db.query(FleetDailySummary).filter_by(date=today_date).delete()
    db.query(VehicleDailySummary).filter_by(vehicle_id=v.id, date=today_date).delete()
    db.commit()
    
    v_sum = VehicleDailySummary(
        vehicle_id=v.id,
        date=today_date,
        distance_gps_km=15.6,
        fuel_consumed_liters=1.2,
        engine_runtime_hours=0.5,
        driving_hours=0.4,
        idle_hours=0.1,
        max_speed=65.0
    )
    fleet_sum = FleetDailySummary(
        date=today_date,
        total_distance_km=150.5,
        total_fuel_consumed_l=12.2,
        total_engine_hours=4.5,
        total_driving_hours=3.8,
        total_idle_hours=0.7,
        active_vehicles=4,
        fleet_max_speed=85.0
    )
    db.add(v_sum)
    db.add(fleet_sum)
    db.commit()

    # 3. Test Fleet Endpoint
    print("\n[REQUEST] GET /analytics/fleet/today")
    response = client.get("/analytics/fleet/today")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("Response JSON:", data)
    assert data["total_distance_km"] == 150.5
    assert data["active_vehicles"] == 4
    print("[PASS] Fleet analytics API successfully loaded correct daily metrics.")

    # 4. Test Vehicle Endpoint
    print(f"\n[REQUEST] GET /analytics/vehicle/{v.id}/today")
    response_veh = client.get(f"/analytics/vehicle/{v.id}/today")
    assert response_veh.status_code == 200, f"Expected 200, got {response_veh.status_code}"
    data_veh = response_veh.json()
    print("Response JSON:", data_veh)
    assert data_veh["distance_gps_km"] == 15.6
    assert data_veh["max_speed"] == 65.0
    print("[PASS] Vehicle analytics API successfully loaded correct daily metrics.")

    db.close()
    print("\n======================================================================")
    print("                 ANALYTICS ENDPOINTS UNIT TEST PASSED                ")
    print("======================================================================")

if __name__ == "__main__":
    test_analytics_endpoints()
