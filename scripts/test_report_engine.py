import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import Base
from app.services.reports import get_report_manager, ReportContext
from app.models.fleet_daily_summary import FleetDailySummary
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.driver_daily_summary import DriverDailySummary
from app.models.maintenance_summary import MaintenanceSummary

def test_report_engine():
    print("======================================================================")
    print("                 VTS REPORT ENGINE INTEGRATION TESTS                 ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Insert mock data
    today = date.today()
    
    # Fleet summary
    f_sum = FleetDailySummary(
        date=today,
        total_distance_km=120.0,
        total_fuel_consumed_l=15.0,
        total_engine_hours=10.0,
        total_driving_hours=8.0,
        total_idle_hours=2.0,
        active_vehicles=2,
        fleet_max_speed=95.0
    )
    db.add(f_sum)

    # Vehicle summary (Vehicle ID = 1)
    v_sum = VehicleDailySummary(
        vehicle_id=1,
        date=today,
        distance_gps_km=80.0,
        fuel_consumed_liters=10.0,
        engine_runtime_hours=6.0,
        driving_hours=5.0,
        idle_hours=1.0,
        max_speed=90.0
    )
    db.add(v_sum)

    # Driver summary (Driver ID = 1)
    d_sum = DriverDailySummary(
        driver_id=1,
        date=today,
        distance_driven_km=80.0,
        engine_hours=6.0,
        driving_hours=5.0,
        idle_hours=1.0,
        fuel_used_l=10.0,
        avg_fuel_economy_kpl=8.0,
        max_speed_kmh=90.0,
        avg_speed_kmh=50.0,
        overspeed_count=0,
        harsh_braking_count=0,
        harsh_acceleration_count=0,
        sharp_turn_count=0,
        safety_score=100.0,
        eco_score=95.0
    )
    db.add(d_sum)

    # Maintenance summary
    m_sum = MaintenanceSummary(
        vehicle_id=1,
        date=today,
        remaining_service_distance_km=4500.0,
        remaining_service_days=160,
        estimated_next_service_date=today,
        oil_life_pct=45.0,
        brake_wear_pct=30.0,
        tyre_health_pct=80.0,
        battery_health_pct=95.0,
        cooling_system_health="Good",
        engine_health_index=90.0,
        overall_vehicle_health_score=85.0
    )
    db.add(m_sum)
    db.commit()

    # 3. Instantiate ReportManager
    manager = get_report_manager()
    print(f"Total report builders loaded: {len(manager.builders)}")
    assert len(manager.builders) == 7

    # 4. Generate Daily Fleet Report
    print("\n--- Generating Daily Fleet Report ---")
    context_fleet = ReportContext(db=db, start_date=today, end_date=today)
    report_fleet = manager.generate_report("DailyFleet", context_fleet)
    print("Title:", report_fleet["report_title"])
    assert report_fleet["report_title"] == "Daily Fleet Report"
    assert len(report_fleet["kpi_section"]) > 0
    print("[PASS] Fleet report generated successfully.")

    # 5. Generate Vehicle Performance Report
    print("\n--- Generating Vehicle Performance Report ---")
    context_veh = ReportContext(db=db, start_date=today, end_date=today, vehicle_id=1)
    report_veh = manager.generate_report("VehiclePerformance", context_veh)
    print("Title:", report_veh["report_title"])
    assert "Vehicle Performance Report" in report_veh["report_title"]
    print("[PASS] Vehicle performance report generated successfully.")

    # 6. Generate Driver Performance Report
    print("\n--- Generating Driver Performance Report ---")
    context_drv = ReportContext(db=db, start_date=today, end_date=today, driver_id=1)
    report_drv = manager.generate_report("DriverPerformance", context_drv)
    print("Title:", report_drv["report_title"])
    assert "Driver Performance Report" in report_drv["report_title"]
    print("[PASS] Driver performance report generated successfully.")

    # 7. Generate Maintenance Report
    print("\n--- Generating Maintenance Report ---")
    context_maint = ReportContext(db=db, start_date=today, end_date=today)
    report_maint = manager.generate_report("Maintenance", context_maint)
    print("Title:", report_maint["report_title"])
    assert report_maint["report_title"] == "Maintenance Report"
    print("[PASS] Maintenance report generated successfully.")

    db.close()
    print("\n======================================================================")
    print("                 REPORT ENGINE INTEGRATION TESTS PASSED               ")
    print("======================================================================")

if __name__ == "__main__":
    test_report_engine()
