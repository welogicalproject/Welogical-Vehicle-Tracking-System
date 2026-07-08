import os
import sys
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import Base
from app.models.location import Location
from app.models.event import Event
from app.models.vehicle import Vehicle
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.maintenance_summary import MaintenanceSummary
from app.services.analytics.base import PipelineContext
from app.services.analytics.processors.maintenance import MaintenanceProcessor

def test_maintenance_processor():
    print("======================================================================")
    print("                 VTS MAINTENANCE PROCESSOR UNIT TESTS                 ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Register mock Vehicle
    v = Vehicle(
        device_uid="HEALTH-TEST-V01",
        vehicle_name="Health Demo Truck",
        vehicle_type="Truck",
    )
    db.add(v)
    db.commit()

    # 3. Insert telemetry locations for today to set odometer
    today = date.today()
    start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=8)
    
    # Set odometer to 15,300.0 km (exactly 5,300 km into the 10,000 km service interval)
    loc = Location(
        vehicle_id=v.id,
        latitude=12.9716,
        longitude=77.5946,
        speed=45.0,
        timestamp=start_time,
        extra_data={
            "gps_details": {"odo": 15300000.0, "fix": "A"} # 15,300,000 meters
        }
    )
    db.add(loc)
    db.commit()

    # 4. Insert mock events today (1 Overheat, 1 Low Battery)
    ev_overheat = Event(
        vehicle_id=v.id,
        txn="V",
        event_type="Engine Over Temperature",
        description="Coolant reached 99.5C",
        severity="Critical",
        created_at=start_time + timedelta(minutes=15)
    )
    ev_battery = Event(
        vehicle_id=v.id,
        txn="B",
        event_type="Low Battery",
        description="Voltage drop warning",
        severity="Warning",
        created_at=start_time + timedelta(minutes=30)
    )
    db.add(ev_overheat)
    db.add(ev_battery)
    db.commit()

    # 5. Insert mock VehicleDailySummary for daily runtimes (3.0 engine hours)
    veh_sum = VehicleDailySummary(
        vehicle_id=v.id,
        date=today,
        distance_gps_km=50.0,
        fuel_consumed_liters=6.0,
        engine_runtime_hours=3.0,
        driving_hours=2.5,
        idle_hours=0.5,
        max_speed=80.0
    )
    db.add(veh_sum)
    db.commit()

    # 6. Execute MaintenanceProcessor (Stage 2)
    processor = MaintenanceProcessor()
    context = PipelineContext(run_date=today, start_id=1, end_id=100)
    
    success = processor.process(context, db)
    assert success is True, "MaintenanceProcessor process reported failure."

    # 7. Verify compiled health summary
    summary = db.query(MaintenanceSummary).filter_by(vehicle_id=v.id, date=today).first()
    assert summary is not None, "MaintenanceSummary record was not created."

    print("\n--- Health Summary Verification ---")
    print(f"Remaining Distance: {summary.remaining_service_distance_km:.1f} km (Expected: 4700.0 km)")
    print(f"Remaining Days:     {summary.remaining_service_days} days   (Expected: 171 days)")
    print(f"Oil Life %:         {summary.oil_life_pct:.1f}%      (Expected: 47.0%)")
    print(f"Coolant Health:     {summary.cooling_system_health}   (Expected: Critical)")
    print(f"Battery Health %:   {summary.battery_health_pct:.1f}%      (Expected: 95.0%)")
    print(f"Engine Health %:    {summary.engine_health_index:.1f}%      (Expected: 84.7%)")
    
    # Assert parameters
    # Service interval is 10,000 km. Odometer is 15,300 km. Remaining: 10,000 - (15,300 % 10,000) = 4,700 km.
    assert abs(summary.remaining_service_distance_km - 4700.0) < 0.01
    assert summary.remaining_service_days == 171
    assert abs(summary.oil_life_pct - 47.0) < 0.01
    assert summary.cooling_system_health == "Critical"
    
    # Battery health: 100 - (1 low battery * 5.0) = 95.0%
    assert abs(summary.battery_health_pct - 95.0) < 0.01

    # Engine health: 100 - (1 overheat * 15.0) - (0 harsh actions * 2.0) - (3.0 engine hours * 0.1) = 84.7%
    assert abs(summary.engine_health_index - 84.7) < 0.01

    # Assert weighted overall score:
    # (Oil Life = 47 * 0.15) + (Brake SoH = 76.5 * 0.15) + (Tyre SoH = 61.75 * 0.15) + (Battery SoH = 95 * 0.20) + (Engine SoH = 84.7 * 0.35)
    # 7.05 + 11.475 + 9.2625 + 19.0 + 29.645 = 76.43%
    print(f"Overall Score:      {summary.overall_vehicle_health_score:.2f}%     (Expected: ~76.43%)")
    assert abs(summary.overall_vehicle_health_score - 76.43) < 0.1
    print("[PASS] Maintenance health indicators and Overall Score matched calculations.")

    # 8. Test Overwrite capabilities
    # Advance odometer by 100km in next run
    loc2 = Location(
        vehicle_id=v.id,
        latitude=12.9716,
        longitude=77.5946,
        speed=45.0,
        timestamp=start_time + timedelta(hours=1),
        extra_data={
            "gps_details": {"odo": 15400000.0, "fix": "A"} # 15,400,000 meters (+100 km)
        }
    )
    db.add(loc2)
    db.commit()

    success_retry = processor.process(context, db)
    assert success_retry is True

    summary_updated = db.query(MaintenanceSummary).filter_by(vehicle_id=v.id, date=today).first()
    print(f"Updated Remaining Distance: {summary_updated.remaining_service_distance_km:.1f} km (Expected: 4600.0 km)")
    assert abs(summary_updated.remaining_service_distance_km - 4600.0) < 0.01
    print("[PASS] Incremental daily updates overwrite previous database values successfully.")

    db.close()
    print("\n======================================================================")
    print("                 MAINTENANCE PROCESSOR TESTS PASSED                   ")
    print("======================================================================")

if __name__ == "__main__":
    test_maintenance_processor()
