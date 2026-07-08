import os
import sys
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.models.location import Location
from app.models.vehicle import Vehicle
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.analytics_checkpoint import AnalyticsCheckpoint
from app.services.analytics.base import PipelineContext
from app.services.analytics.processors.vehicle_stats import VehicleStatsProcessor
from app.database import Base

def setup_test_db():
    # SQLite memory database isolates test interactions
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_vehicle_stats_normal():
    print("\n--- Test Case: Normal processing ---")
    db = setup_test_db()
    
    # 1. Insert mock vehicle
    v = Vehicle(device_uid="UNIT-TEST-V01", vehicle_name="Test Car", vehicle_type="Car")
    db.add(v)
    db.commit()
    
    # 2. Insert sequential locations (with V2 Spec extra_data metrics)
    now = datetime(2026, 7, 8, 10, 0, 0)
    l1 = Location(
        vehicle_id=v.id,
        latitude=12.9716,
        longitude=77.5946,
        speed=0.0,
        altitude=920.0,
        timestamp=now,
        extra_data={
            "io": {"ign": 1},
            "gps": {"odo": 100000.0},
            "engine": {"engine_hours": 10.0, "driving_hours": 5.0, "idle_hours": 5.0},
            "fuel": {"level": 40.0}
        }
    )
    # Location 2: 10 seconds later, moving at 60 km/h, odo increased, fuel decreased
    l2 = Location(
        vehicle_id=v.id,
        latitude=12.9726,
        longitude=77.5956,
        speed=60.0,
        altitude=920.0,
        timestamp=now + timedelta(seconds=10),
        extra_data={
            "io": {"ign": 1},
            "gps": {"odo": 100160.0},
            "engine": {"engine_hours": 10.0028, "driving_hours": 5.0028, "idle_hours": 5.0},
            "fuel": {"level": 39.95}
        }
    )
    db.add(l1)
    db.add(l2)
    db.commit()
    
    # Run processor
    processor = VehicleStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=l1.id, end_id=l2.id)
    
    success = processor.process(context, db)
    assert success is True
    db.commit()
    
    # Verify daily summary metrics
    summary = db.query(VehicleDailySummary).filter_by(vehicle_id=v.id, date=context.date).first()
    assert summary is not None
    print(f"Daily summary metrics: {summary}")
    
    # Odo delta: (100160 - 100000) / 1000 = 0.16 km
    assert abs(summary.distance_gps_km - 0.16) < 0.001
    
    # Engine runtime delta: 10.0028 - 10.0 = 0.0028 hours
    assert abs(summary.engine_runtime_hours - 0.0028) < 0.0001
    
    # Driving runtime delta: 5.0028 - 5.0 = 0.0028 hours
    assert abs(summary.driving_hours - 0.0028) < 0.0001
    
    # Fuel consumed: 40.0 - 39.95 = 0.05 L
    assert abs(summary.fuel_consumed_liters - 0.05) < 0.001
    
    # Max speed: 60.0
    assert summary.max_speed == 60.0
    print("[PASS] Normal processing test successfully verified all delta aggregations.")

def test_vehicle_stats_duplicates():
    print("\n--- Test Case: Duplicate telemetry ---")
    db = setup_test_db()
    
    v = Vehicle(device_uid="UNIT-TEST-V02", vehicle_name="Test Car 2", vehicle_type="Car")
    db.add(v)
    db.commit()
    
    now = datetime(2026, 7, 8, 11, 0, 0)
    # Duplicate packets with identical metrics
    l1 = Location(
        vehicle_id=v.id,
        latitude=12.9716,
        longitude=77.5946,
        speed=0.0,
        altitude=920.0,
        timestamp=now,
        extra_data={
            "io": {"ign": 1},
            "gps": {"odo": 100000.0},
            "engine": {"engine_hours": 10.0, "driving_hours": 5.0, "idle_hours": 5.0},
            "fuel": {"level": 40.0}
        }
    )
    l2 = Location(
        vehicle_id=v.id,
        latitude=12.9716,
        longitude=77.5946,
        speed=0.0,
        altitude=920.0,
        timestamp=now, 
        extra_data={
            "io": {"ign": 1},
            "gps": {"odo": 100000.0},
            "engine": {"engine_hours": 10.0, "driving_hours": 5.0, "idle_hours": 5.0},
            "fuel": {"level": 40.0}
        }
    )
    db.add(l1)
    db.add(l2)
    db.commit()
    
    processor = VehicleStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=l1.id, end_id=l2.id)
    processor.process(context, db)
    db.commit()
    
    summary = db.query(VehicleDailySummary).filter_by(vehicle_id=v.id, date=context.date).first()
    assert summary.distance_gps_km == 0.0
    assert summary.fuel_consumed_liters == 0.0
    assert summary.engine_runtime_hours == 0.0
    print("[PASS] Duplicate metrics successfully filtered, yielding zero delta increments.")

def test_vehicle_stats_empty():
    print("\n--- Test Case: Empty batch range ---")
    db = setup_test_db()
    processor = VehicleStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=999, end_id=1000)
    success = processor.process(context, db)
    assert success is True
    print("[PASS] Empty batches exit cleanly without exceptions.")

if __name__ == "__main__":
    test_vehicle_stats_normal()
    test_vehicle_stats_duplicates()
    test_vehicle_stats_empty()
    print("\n[OK] ALL VEHICLE STATS PROCESSOR TESTS PASSED SUCCESSFULLY.")
