import os
import sys
from datetime import datetime, timedelta

# Add project root to python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.models.location import Location
from app.services.event_engine import EventEngine

def make_loc(lat=12.9716, lon=77.5946, speed=0.0, heading=0.0, ign=0, main_power=1, volt=4.18, fuel_pct=50.0, fuel_level=25.0, fix="A", coolant=85.0, odo=100000.0, txn="A"):
    extra = {
        "txn": txn,
        "io": {"ign": ign, "analog": [12000, 4180, int(fuel_pct * 100)]},
        "pwr": {"main": main_power, "volt": int(volt * 1000)},
        "gps_details": {"fix": fix, "sat": 12, "dir": heading, "odo": odo},
        "fuel": {"percentage": fuel_pct, "level": fuel_level},
        "engine": {"coolant_temperature": coolant}
    }
    return Location(
        vehicle_id=1,
        latitude=lat,
        longitude=lon,
        speed=speed,
        altitude=920.0,
        timestamp=datetime.utcnow(),
        extra_data=extra
    )

def test_event_rules():
    print("======================================================================")
    print("                 VTS EVENT ENGINE RULES UNIT TESTS                   ")
    print("======================================================================")
    
    engine = EventEngine()
    print(f"Total default event rules loaded: {len(engine.rules)}")
    assert len(engine.rules) == 18

    # 1. Test Ignition On / Off transitions
    print("\n--- Test: Ignition Transitions ---")
    loc_off = make_loc(ign=0)
    loc_on = make_loc(ign=1)
    
    # Off -> On
    rule_on = next(r for r in engine.rules if r.event_type == "Ignition On")
    res_on = rule_on.evaluate(loc_off, loc_on)
    assert res_on is not None
    assert res_on.curr_val == "ON"
    print("[PASS] Ignition On transition detected.")

    # On -> Off
    rule_off = next(r for r in engine.rules if r.event_type == "Ignition Off")
    res_off = rule_off.evaluate(loc_on, loc_off)
    assert res_off is not None
    assert res_off.curr_val == "OFF"
    print("[PASS] Ignition Off transition detected.")

    # 2. Test Movement (Started / Stopped)
    print("\n--- Test: Movement Transitions ---")
    loc_idle = make_loc(speed=0.0, ign=1)
    loc_moving = make_loc(speed=35.0, ign=1)
    
    # Stopped -> Started
    rule_start = next(r for r in engine.rules if r.event_type == "Vehicle Started")
    res_start = rule_start.evaluate(loc_idle, loc_moving)
    assert res_start is not None
    print("[PASS] Vehicle Started transition detected.")

    # Moving -> Stopped
    rule_stop = next(r for r in engine.rules if r.event_type == "Vehicle Stopped")
    res_stop = rule_stop.evaluate(loc_moving, loc_idle)
    assert res_stop is not None
    print("[PASS] Vehicle Stopped transition detected.")

    # 3. Test Overspeed
    print("\n--- Test: Overspeeding ---")
    loc_normal_speed = make_loc(speed=95.0)
    loc_high_speed = make_loc(speed=105.0)
    rule_overspeed = next(r for r in engine.rules if r.event_type == "Overspeed")
    res_over = rule_overspeed.evaluate(loc_normal_speed, loc_high_speed)
    assert res_over is not None
    print("[PASS] Overspeeding alert detected.")

    # 4. Test Harsh Braking & Acceleration
    print("\n--- Test: Harsh Braking & Acceleration ---")
    loc_slow = make_loc(speed=20.0)
    loc_fast = make_loc(speed=40.0)
    
    # Fast -> Slow (Harsh deceleration: 40 to 20 km/h drop)
    rule_brake = next(r for r in engine.rules if r.event_type == "Harsh Braking")
    res_brake = rule_brake.evaluate(loc_fast, loc_slow)
    assert res_brake is not None
    print("[PASS] Harsh Braking speed drop detected.")

    # Slow -> Fast (Harsh acceleration: 20 to 40 km/h spike)
    rule_accel = next(r for r in engine.rules if r.event_type == "Harsh Acceleration")
    res_accel = rule_accel.evaluate(loc_slow, loc_fast)
    assert res_accel is not None
    print("[PASS] Harsh Acceleration speed spike detected.")

    # 5. Test Power cuts & Restoration
    print("\n--- Test: Power Supply Failures ---")
    loc_pwr_ok = make_loc(main_power=1)
    loc_pwr_cut = make_loc(main_power=0)
    
    rule_cut = next(r for r in engine.rules if r.event_type == "Power Failure")
    res_cut = rule_cut.evaluate(loc_pwr_ok, loc_pwr_cut)
    assert res_cut is not None
    print("[PASS] External Power Cut warning detected.")

    rule_restore = next(r for r in engine.rules if r.event_type == "Power Restored")
    res_restore = rule_restore.evaluate(loc_pwr_cut, loc_pwr_ok)
    assert res_restore is not None
    print("[PASS] External Power Restored alert detected.")

    # 6. Test Low Battery & Low Fuel
    print("\n--- Test: Battery and Fuel Alert thresholds ---")
    loc_bat_ok = make_loc(volt=3.8)
    loc_bat_low = make_loc(volt=3.5)
    rule_bat = next(r for r in engine.rules if r.event_type == "Low Battery")
    res_bat = rule_bat.evaluate(loc_bat_ok, loc_bat_low)
    assert res_bat is not None
    print("[PASS] Internal battery low check detected.")

    loc_fuel_ok = make_loc(fuel_pct=15.0)
    loc_fuel_low = make_loc(fuel_pct=8.0)
    rule_fuel = next(r for r in engine.rules if r.event_type == "Low Fuel")
    res_fuel = rule_fuel.evaluate(loc_fuel_ok, loc_fuel_low)
    assert res_fuel is not None
    print("[PASS] Low fuel level alert detected.")

    # 7. Test GPS Fix transition
    print("\n--- Test: GPS Fix Lost / Restored ---")
    loc_gps_ok = make_loc(fix="A")
    loc_gps_lost = make_loc(fix="V")
    
    rule_gps_lost = next(r for r in engine.rules if r.event_type == "GPS Lost")
    res_gps_lost = rule_gps_lost.evaluate(loc_gps_ok, loc_gps_lost)
    assert res_gps_lost is not None
    print("[PASS] GPS Fix Lost transition detected.")

    rule_gps_restored = next(r for r in engine.rules if r.event_type == "GPS Restored")
    res_gps_restored = rule_gps_restored.evaluate(loc_gps_lost, loc_gps_ok)
    assert res_gps_restored is not None
    print("[PASS] GPS Fix Restored transition detected.")

    # 8. Test Coolant heat
    print("\n--- Test: Engine Overheating ---")
    loc_temp_normal = make_loc(coolant=85.0)
    loc_temp_hot = make_loc(coolant=99.5)
    rule_temp = next(r for r in engine.rules if r.event_type == "Engine Over Temperature")
    res_temp = rule_temp.evaluate(loc_temp_normal, loc_temp_hot)
    assert res_temp is not None
    print("[PASS] Engine coolant over temperature detected.")

    # 9. Test Refueling Started
    print("\n--- Test: Refueling ---")
    loc_fuel_empty = make_loc(fuel_level=5.0)
    loc_fuel_added = make_loc(fuel_level=12.0) # increased by 7.0L
    rule_refuel = next(r for r in engine.rules if r.event_type == "Refueling Started")
    res_refuel = rule_refuel.evaluate(loc_fuel_empty, loc_fuel_added)
    assert res_refuel is not None
    print("[PASS] Refueling Started event detected.")

    # 10. Test Maintenance Milestone
    print("\n--- Test: Maintenance Milestones ---")
    loc_odo_before = make_loc(odo=9995000.0) # 9,995 km
    loc_odo_after = make_loc(odo=10005000.0)  # 10,005 km (crossed 10,000 km mark)
    rule_maint = next(r for r in engine.rules if r.event_type == "Maintenance Due")
    res_maint = rule_maint.evaluate(loc_odo_before, loc_odo_after)
    assert res_maint is not None
    print("[PASS] Maintenance milestone boundary cross detected.")

    print("\n======================================================================")
    print("                 EVENT ENGINE RULES TESTS PASSED                      ")
    print("======================================================================")

if __name__ == "__main__":
    test_event_rules()
