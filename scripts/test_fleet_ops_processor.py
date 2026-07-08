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
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.models.trip import Trip
from app.models.maintenance_summary import MaintenanceSummary
from app.models.fleet_operations import VehicleOperations, FleetOperationsLive
from app.services.analytics.base import PipelineContext
from app.services.analytics.processors.fleet_ops import FleetOperationsProcessor

def test_fleet_ops_processor():
    print("======================================================================")
    print("                 VTS FLEET OPERATIONS PROCESSOR TESTS                ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Register mock Vehicle 1 and Vehicle 2
    v1 = Vehicle(device_uid="OPS-V01", vehicle_name="Delivery Van 1", vehicle_type="Van")
    v2 = Vehicle(device_uid="OPS-V02", vehicle_name="Delivery Van 2", vehicle_type="Van")
    db.add(v1)
    db.add(v2)
    db.commit()

    # 3. Create active assignment for driver on Vehicle 1
    d = Driver(
        driver_name="Michael Scott",
        phone_number="555-0199",
        license_number="DL-8888",
        license_expiry=datetime.now() + timedelta(days=365),
        emergency_contact="Dwight Schrute",
    )
    db.add(d)
    db.commit()

    now = datetime.utcnow()
    asg = DriverAssignment(
        vehicle_id=v1.id,
        driver_id=d.id,
        assigned_at=now - timedelta(hours=2),
        status="Active"
    )
    db.add(asg)
    db.commit()

    # 4. Insert locations
    # Vehicle 1: Online, Driving, speed=50.0
    loc1 = Location(
        vehicle_id=v1.id,
        latitude=12.97,
        longitude=77.59,
        speed=50.0,
        timestamp=now - timedelta(minutes=2),
        extra_data={"io": {"ign": 1}, "gps_details": {"fix": "A"}}
    )
    # Vehicle 2: Offline (last seen 45 minutes ago)
    loc2 = Location(
        vehicle_id=v2.id,
        latitude=12.98,
        longitude=77.60,
        speed=0.0,
        timestamp=now - timedelta(minutes=45),
        extra_data={"io": {"ign": 0}, "gps_details": {"fix": "A"}}
    )
    db.add(loc1)
    db.add(loc2)
    db.commit()

    # 5. Insert events for Vehicle 1 (1 Warning in last 24 hrs)
    ev = Event(
        vehicle_id=v1.id,
        txn="B",
        event_type="Low Battery",
        description="Battery voltage low",
        severity="Warning",
        created_at=now - timedelta(hours=1)
    )
    db.add(ev)
    db.commit()

    # 6. Execute FleetOperationsProcessor (Stage 3)
    processor = FleetOperationsProcessor()
    context = PipelineContext(run_date=date.today(), start_id=1, end_id=100)
    
    success = processor.process(context, db)
    assert success is True, "FleetOperationsProcessor reported failure."

    # 7. Verify Vehicle 1 Live Operations state
    ops1 = db.query(VehicleOperations).filter_by(vehicle_id=v1.id).first()
    assert ops1 is not None
    print("\n--- Vehicle 1 Status ---")
    print(f"Status:   {ops1.status} (Expected: Driving)")
    print(f"Driver:   {ops1.current_driver_name} (Expected: Michael Scott)")
    assert ops1.status == "Driving"
    assert ops1.current_driver_name == "Michael Scott"

    # Verify Vehicle 2 Live Operations state
    ops2 = db.query(VehicleOperations).filter_by(vehicle_id=v2.id).first()
    assert ops2 is not None
    print("\n--- Vehicle 2 Status ---")
    print(f"Status:   {ops2.status} (Expected: Offline)")
    assert ops2.status == "Offline"

    # 8. Verify Fleet Live Operations state
    fleet_live = db.query(FleetOperationsLive).first()
    assert fleet_live is not None
    print("\n--- Fleet Aggregates ---")
    print(f"Driving:      {fleet_live.vehicles_driving} (Expected: 1)")
    print(f"Offline:      {fleet_live.vehicles_offline} (Expected: 1)")
    print(f"Availability: {fleet_live.fleet_availability_pct:.1f}% (Expected: 50.0%)")
    print(f"Utilization:  {fleet_live.fleet_utilization_pct:.1f}% (Expected: 50.0%)")
    print(f"Warnings:     {fleet_live.warning_alerts_count} (Expected: 1)")
    
    assert fleet_live.vehicles_driving == 1
    assert fleet_live.vehicles_offline == 1
    assert abs(fleet_live.fleet_availability_pct - 50.0) < 0.01
    assert abs(fleet_live.fleet_utilization_pct - 50.0) < 0.01
    assert fleet_live.warning_alerts_count == 1
    print("[PASS] Fleet operations KPIs match expected state values.")

    # 9. Test Overwrites (Vehicle 2 becomes online)
    loc2_new = Location(
        vehicle_id=v2.id,
        latitude=12.98,
        longitude=77.60,
        speed=0.0,
        timestamp=now - timedelta(minutes=1), # Online now
        extra_data={"io": {"ign": 1}, "gps_details": {"fix": "A"}}
    )
    db.add(loc2_new)
    db.commit()

    success_retry = processor.process(context, db)
    assert success_retry is True

    fleet_live_updated = db.query(FleetOperationsLive).first()
    print(f"Updated Offline: {fleet_live_updated.vehicles_offline} (Expected: 0)")
    assert fleet_live_updated.vehicles_offline == 0
    print("[PASS] Operational overwrite updates completed successfully.")

    db.close()
    print("\n======================================================================")
    print("                 FLEET OPERATIONS TESTS PASSED                       ")
    print("======================================================================")

if __name__ == "__main__":
    test_fleet_ops_processor()
