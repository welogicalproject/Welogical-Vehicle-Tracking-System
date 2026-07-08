import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.fleet_daily_summary import FleetDailySummary
from app.services.analytics.base import PipelineContext
from app.services.analytics.processors.fleet_stats import FleetStatsProcessor
from app.database import Base

def setup_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_fleet_stats_empty():
    print("\n--- Test Case: Empty day (no vehicles) ---")
    db = setup_test_db()
    processor = FleetStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=1, end_id=100)
    
    success = processor.process(context, db)
    assert success is True
    db.commit()
    
    fleet_sum = db.query(FleetDailySummary).filter_by(date=context.date).first()
    assert fleet_sum is not None
    assert fleet_sum.active_vehicles == 0
    assert fleet_sum.total_distance_km == 0.0
    assert fleet_sum.total_fuel_consumed_l == 0.0
    print("[PASS] Empty day successfully generated 0-metric summary.")

def test_fleet_stats_single():
    print("\n--- Test Case: Single vehicle summary ---")
    db = setup_test_db()
    
    # Insert one vehicle summary
    s1 = VehicleDailySummary(
        vehicle_id=1,
        date=date(2026, 7, 8),
        distance_gps_km=42.5,
        fuel_consumed_liters=3.4,
        engine_runtime_hours=1.2,
        driving_hours=1.0,
        idle_hours=0.2,
        max_speed=85.0
    )
    db.add(s1)
    db.commit()
    
    processor = FleetStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=1, end_id=100)
    processor.process(context, db)
    db.commit()
    
    fleet_sum = db.query(FleetDailySummary).filter_by(date=context.date).first()
    assert fleet_sum.active_vehicles == 1
    assert fleet_sum.total_distance_km == 42.5
    assert fleet_sum.total_fuel_consumed_l == 3.4
    assert fleet_sum.total_engine_hours == 1.2
    assert fleet_sum.fleet_max_speed == 85.0
    print("[PASS] Fleet summary matches single vehicle metrics correctly.")

def test_fleet_stats_multiple_and_repeated():
    print("\n--- Test Case: Multiple vehicles and repeated updates ---")
    db = setup_test_db()
    
    s1 = VehicleDailySummary(
        vehicle_id=1,
        date=date(2026, 7, 8),
        distance_gps_km=10.0,
        fuel_consumed_liters=1.0,
        engine_runtime_hours=0.5,
        driving_hours=0.4,
        idle_hours=0.1,
        max_speed=50.0
    )
    s2 = VehicleDailySummary(
        vehicle_id=2,
        date=date(2026, 7, 8),
        distance_gps_km=25.0,
        fuel_consumed_liters=2.5,
        engine_runtime_hours=1.5,
        driving_hours=1.2,
        idle_hours=0.3,
        max_speed=95.0
    )
    db.add(s1)
    db.add(s2)
    db.commit()
    
    processor = FleetStatsProcessor()
    context = PipelineContext(run_date=date(2026, 7, 8), start_id=1, end_id=100)
    
    # Execution 1
    processor.process(context, db)
    db.commit()
    
    fleet_sum = db.query(FleetDailySummary).filter_by(date=context.date).first()
    assert fleet_sum.active_vehicles == 2
    assert fleet_sum.total_distance_km == 35.0
    assert fleet_sum.total_fuel_consumed_l == 3.5
    assert fleet_sum.fleet_max_speed == 95.0
    
    # Repeated Execution (simulate updates / changes to vehicle summaries)
    s2.distance_gps_km = 30.0
    s2.max_speed = 100.0
    db.add(s2)
    db.commit()
    
    # Execution 2 (overwrites values)
    processor.process(context, db)
    db.commit()
    
    fleet_sum_updated = db.query(FleetDailySummary).filter_by(date=context.date).first()
    assert fleet_sum_updated.active_vehicles == 2
    assert fleet_sum_updated.total_distance_km == 40.0 # 10.0 + 30.0
    assert fleet_sum_updated.fleet_max_speed == 100.0
    print("[PASS] Repeated execution successfully re-calculates aggregates without duplicates.")

if __name__ == "__main__":
    test_fleet_stats_empty()
    test_fleet_stats_single()
    test_fleet_stats_multiple_and_repeated()
    print("\n[OK] ALL FLEET STATS PROCESSOR TESTS PASSED SUCCESSFULLY.")
