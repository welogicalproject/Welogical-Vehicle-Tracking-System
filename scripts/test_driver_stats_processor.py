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
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.models.driver_daily_summary import DriverDailySummary
from app.services.analytics.base import PipelineContext
from app.services.analytics.processors.driver_stats import DriverStatsProcessor

def test_driver_stats_processor():
    print("======================================================================")
    print("                 VTS DRIVER STATS PROCESSOR UNIT TESTS               ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Create mock Driver
    d1 = Driver(
        driver_name="Test Driver 01",
        phone_number="555-0101",
        license_number="DL-9998887",
        license_expiry=datetime.now() + timedelta(days=365),
        emergency_contact="Jane Doe",
    )
    db.add(d1)
    db.commit()

    # 3. Create active assignment for driver d1 today (8:00 AM to 5:00 PM)
    today = date.today()
    start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=8)
    end_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=17)

    asg = DriverAssignment(
        vehicle_id=1,
        driver_id=d1.id,
        assigned_at=start_time,
        released_at=end_time,
        status="Completed"
    )
    db.add(asg)
    db.commit()

    # 4. Insert telemetry locations inside the active assignment interval
    # Log 1: 9:00 AM
    loc1 = Location(
        vehicle_id=1,
        latitude=12.9716,
        longitude=77.5946,
        speed=45.0,
        timestamp=start_time + timedelta(hours=1),
        extra_data={
            "gps_details": {"odo": 50000000.0, "fix": "A"}, # 50,000 km
            "engine": {
                "engine_hours": 120.0,
                "driving_hours": 100.0,
                "idle_hours": 20.0,
                "coolant_temperature": 82.0,
                "rpm": 2200
            },
            "fuel": {"level": 80.0, "percentage": 80.0}
        }
    )
    # Log 2: 10:00 AM (Vehicle drove 60 km, burned 6.0L fuel, idle for 0.2h, driving for 0.8h)
    loc2 = Location(
        vehicle_id=1,
        latitude=13.0,
        longitude=77.6,
        speed=105.0, # Overspeeding!
        timestamp=start_time + timedelta(hours=2),
        extra_data={
            "gps_details": {"odo": 50060000.0, "fix": "A"}, # 50,060 km (+60 km)
            "engine": {
                "engine_hours": 121.0,
                "driving_hours": 100.8,
                "idle_hours": 20.2,
                "coolant_temperature": 85.0,
                "rpm": 3800 # High RPM (>3500)
            },
            "fuel": {"level": 74.0, "percentage": 74.0} # 6.0L used
        }
    )
    db.add(loc1)
    db.add(loc2)
    db.commit()

    # 5. Insert events triggered during this driver's assignment
    ev_overspeed = Event(
        vehicle_id=1,
        txn="D",
        event_type="Overspeed",
        description="Speed limit exceeded",
        severity="Warning",
        created_at=start_time + timedelta(hours=1, minutes=45)
    )
    ev_brake = Event(
        vehicle_id=1,
        txn="S",
        event_type="Harsh Braking",
        description="Harsh deceleration detected",
        severity="Critical",
        created_at=start_time + timedelta(hours=1, minutes=50)
    )
    db.add(ev_overspeed)
    db.add(ev_brake)
    db.commit()

    # 6. Execute DriverStatsProcessor (Stage 2)
    processor = DriverStatsProcessor()
    context = PipelineContext(run_date=today, start_id=1, end_id=100)
    
    success = processor.process(context, db)
    assert success is True, "DriverStatsProcessor process reported failure."

    # 7. Verify aggregated daily summary
    summary = db.query(DriverDailySummary).filter_by(driver_id=d1.id, date=today).first()
    assert summary is not None, "DriverDailySummary record was not created."
    
    print("\n--- Summary Verification ---")
    print(f"Distance Driven: {summary.distance_driven_km:.1f} km (Expected: 60.0 km)")
    print(f"Fuel Consumed:   {summary.fuel_used_l:.1f} L   (Expected: 6.0 L)")
    print(f"Engine Runtime:  {summary.engine_hours:.1f} hrs (Expected: 1.0 hrs)")
    print(f"Overspeed Count: {summary.overspeed_count}     (Expected: 1)")
    print(f"Harsh Braking:   {summary.harsh_braking_count}     (Expected: 1)")
    
    # Assert metrics
    assert abs(summary.distance_driven_km - 60.0) < 0.01
    assert abs(summary.fuel_used_l - 6.0) < 0.01
    assert abs(summary.engine_hours - 1.0) < 0.01
    assert summary.overspeed_count == 1
    assert summary.harsh_braking_count == 1

    # Assert Safety Score:
    # 100 - (1 * SAFETY_DEDUCTION_OVERSPEED) - (1 * SAFETY_DEDUCTION_HARSH_BRAKE)
    # 100 - 5.0 - 10.0 = 85.0
    print(f"Safety Score:    {summary.safety_score:.1f}    (Expected: 85.0)")
    assert abs(summary.safety_score - 85.0) < 0.01
    print("[PASS] Safety Score deductions matched calculations.")

    # Assert Eco Score:
    # 100 - (0.2 hrs * ECO_DEDUCTION_IDLE_HOUR=4.0) - (0 * Eco Harsh Accel=5) - (1 * Eco High RPM=2.5) - (10.0 - 10.0 economy deduction=0.0)
    # 100 - 0.8 - 0.0 - 2.5 = 96.7
    print(f"Eco Score:       {summary.eco_score:.1f}    (Expected: 96.7)")
    assert abs(summary.eco_score - 96.7) < 0.1
    print("[PASS] Eco Score deductions matched calculations.")

    # 8. Test Repeated Execution (Overwrite support verification)
    loc3 = Location(
        vehicle_id=1,
        latitude=13.02,
        longitude=77.62,
        speed=50.0,
        timestamp=start_time + timedelta(hours=3),
        extra_data={
            "gps_details": {"odo": 50080000.0, "fix": "A"}, # 50,080 km (an extra +20 km)
            "engine": {
                "engine_hours": 122.0,
                "driving_hours": 101.8,
                "idle_hours": 20.2,
                "coolant_temperature": 84.0,
                "rpm": 2300
            },
            "fuel": {"level": 72.0, "percentage": 72.0} # 2.0L used
        }
    )
    db.add(loc3)
    db.commit()

    # Re-run processor to check overwrites
    success_retry = processor.process(context, db)
    assert success_retry is True

    summary_updated = db.query(DriverDailySummary).filter_by(driver_id=d1.id, date=today).first()
    print(f"Updated distance after retry: {summary_updated.distance_driven_km:.1f} km (Expected: 80.0 km)")
    assert abs(summary_updated.distance_driven_km - 80.0) < 0.01
    print("[PASS] Incremental daily updates overwrite previous database values successfully.")

    db.close()
    print("\n======================================================================")
    print("                 DRIVER STATS PROCESSOR TESTS PASSED                 ")
    print("======================================================================")

if __name__ == "__main__":
    test_driver_stats_processor()
