import logging
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.models.location import Location

logger = logging.getLogger("vts.events")

# --- Event engine payload data classes ---
class EventRuleResult:
    def __init__(self, event_type: str, txn: str, severity: str, description: str, prev_val: Any = None, curr_val: Any = None, metadata: dict = None):
        self.event_type = event_type
        self.txn = txn
        self.severity = severity
        self.description = description
        self.prev_val = prev_val
        self.curr_val = curr_val
        self.metadata = metadata or {}

class BaseEventRule:
    """
    Abstract interface for modular event detection rules.
    """
    event_type: str = ""
    txn: str = ""
    severity: str = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        raise NotImplementedError()

# --- Helper property extraction logic ---
def _get_ign(loc: Location) -> Optional[int]:
    extra = loc.extra_data
    return extra.get("io", {}).get("ign") if extra else None

def _get_speed(loc: Location) -> float:
    return loc.speed

def _get_heading(loc: Location) -> float:
    extra = loc.extra_data
    return extra.get("gps_details", {}).get("dir") if extra else 0.0

def _get_main_power(loc: Location) -> Optional[int]:
    extra = loc.extra_data
    return extra.get("pwr", {}).get("main") if extra else None

def _get_backup_voltage(loc: Location) -> Optional[float]:
    extra = loc.extra_data
    volt = extra.get("pwr", {}).get("volt") if extra else None
    if volt is not None:
        return volt / 1000.0
    return extra.get("power", {}).get("backup_voltage") if extra else None

def _get_fuel_pct(loc: Location) -> Optional[float]:
    extra = loc.extra_data
    return extra.get("fuel", {}).get("percentage") if extra else None

def _get_fuel_level(loc: Location) -> Optional[float]:
    extra = loc.extra_data
    return extra.get("fuel", {}).get("level") if extra else None

def _get_fix(loc: Location) -> Optional[str]:
    extra = loc.extra_data
    return extra.get("gps_details", {}).get("fix") if extra else None

def _get_coolant(loc: Location) -> Optional[float]:
    extra = loc.extra_data
    return extra.get("engine", {}).get("coolant_temperature") if extra else None

def _get_odo(loc: Location) -> Optional[float]:
    extra = loc.extra_data
    return extra.get("gps_details", {}).get("odo") if extra else None

# --- Specific rule implementations ---

class IgnitionOnRule(BaseEventRule):
    event_type = "Ignition On"
    txn = "J"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_ign = _get_ign(prev_loc)
        curr_ign = _get_ign(curr_loc)
        if prev_ign == 0 and curr_ign == 1:
            return EventRuleResult(self.event_type, self.txn, self.severity, "Vehicle ignition turned ON", "OFF", "ON")
        return None

class IgnitionOffRule(BaseEventRule):
    event_type = "Ignition Off"
    txn = "J"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_ign = _get_ign(prev_loc)
        curr_ign = _get_ign(curr_loc)
        if prev_ign == 1 and curr_ign == 0:
            return EventRuleResult(self.event_type, self.txn, self.severity, "Vehicle ignition turned OFF", "ON", "OFF")
        return None

class VehicleStartedRule(BaseEventRule):
    event_type = "Vehicle Started"
    txn = "F"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_speed = _get_speed(prev_loc)
        curr_speed = _get_speed(curr_loc)
        curr_ign = _get_ign(curr_loc)
        if prev_speed <= 0.1 and curr_speed > 0.1 and curr_ign == 1:
            return EventRuleResult(self.event_type, self.txn, self.severity, f"Vehicle started moving. Speed: {curr_speed:.1f} km/h", "Stopped", "Moving")
        return None

class VehicleStoppedRule(BaseEventRule):
    event_type = "Vehicle Stopped"
    txn = "G"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_speed = _get_speed(prev_loc)
        curr_speed = _get_speed(curr_loc)
        if prev_speed > 0.1 and curr_speed <= 0.1:
            return EventRuleResult(self.event_type, self.txn, self.severity, "Vehicle came to a complete halt", "Moving", "Stopped")
        return None

class OverspeedRule(BaseEventRule):
    event_type = "Overspeed"
    txn = "D"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_speed = _get_speed(prev_loc)
        curr_speed = _get_speed(curr_loc)
        if prev_speed <= 100.0 and curr_speed > 100.0:
            return EventRuleResult(self.event_type, self.txn, self.severity, f"Overspeed warning: speed {curr_speed:.1f} km/h exceeded limit of 100 km/h", f"{prev_speed:.1f} km/h", f"{curr_speed:.1f} km/h")
        return None

class HarshBrakingRule(BaseEventRule):
    event_type = "Harsh Braking"
    txn = "S"
    severity = "Critical"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_speed = _get_speed(prev_loc)
        curr_speed = _get_speed(curr_loc)
        # Drop of more than 15 km/h between messages or protocol txn flag 'S'
        is_harsh = (prev_speed - curr_speed > 15.0) or (curr_loc.extra_data and curr_loc.extra_data.get("txn") == "S")
        if is_harsh and curr_speed < prev_speed:
            return EventRuleResult(self.event_type, self.txn, self.severity, f"Harsh braking event. Decelerated from {prev_speed:.1f} to {curr_speed:.1f} km/h", f"{prev_speed:.1f}", f"{curr_speed:.1f}")
        return None

class HarshAccelerationRule(BaseEventRule):
    event_type = "Harsh Acceleration"
    txn = "P"
    severity = "Critical"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_speed = _get_speed(prev_loc)
        curr_speed = _get_speed(curr_loc)
        # Increase of more than 10 km/h between messages or protocol txn flag 'P'
        is_harsh = (curr_speed - prev_speed > 10.0) or (curr_loc.extra_data and curr_loc.extra_data.get("txn") == "P")
        if is_harsh and curr_speed > prev_speed:
            return EventRuleResult(self.event_type, self.txn, self.severity, f"Harsh acceleration event. Accelerated from {prev_speed:.1f} to {curr_speed:.1f} km/h", f"{prev_speed:.1f}", f"{curr_speed:.1f}")
        return None

class SharpTurnRule(BaseEventRule):
    event_type = "Sharp Turn"
    txn = "M"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_dir = _get_heading(prev_loc)
        curr_dir = _get_heading(curr_loc)
        curr_speed = _get_speed(curr_loc)
        dir_diff = abs(curr_dir - prev_dir)
        if dir_diff > 180.0:
            dir_diff = 360.0 - dir_diff
        # Heading change > 45 degrees while moving > 20 km/h
        if dir_diff > 45.0 and curr_speed > 20.0:
            return EventRuleResult(self.event_type, self.txn, self.severity, f"Sharp turn warning at speed {curr_speed:.1f} km/h. Heading delta: {dir_diff:.1f}°", f"{prev_dir:.1f}°", f"{curr_dir:.1f}°")
        return None

class PowerFailureRule(BaseEventRule):
    event_type = "Power Failure"
    txn = "L"
    severity = "Critical"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_pwr = _get_main_power(prev_loc)
        curr_pwr = _get_main_power(curr_loc)
        if prev_pwr == 1 and curr_pwr == 0:
            return EventRuleResult(self.event_type, self.txn, self.severity, "External mains power cut. Running on backup battery.", "Connected", "Disconnected")
        return None

class PowerRestoredRule(BaseEventRule):
    event_type = "Power Restored"
    txn = "L"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_pwr = _get_main_power(prev_loc)
        curr_pwr = _get_main_power(curr_loc)
        if prev_pwr == 0 and curr_pwr == 1:
            return EventRuleResult(self.event_type, self.txn, self.severity, "External mains power restored. Battery charging.", "Disconnected", "Connected")
        return None

class LowBatteryRule(BaseEventRule):
    event_type = "Low Battery"
    txn = "B"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_volt = _get_backup_voltage(prev_loc)
        curr_volt = _get_backup_voltage(curr_loc)
        if prev_volt is not None and curr_volt is not None:
            if prev_volt >= 3.6 and curr_volt < 3.6:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Internal backup battery low: {curr_volt:.2f} V", f"{prev_volt:.2f} V", f"{curr_volt:.2f} V")
        return None

class LowFuelRule(BaseEventRule):
    event_type = "Low Fuel"
    txn = "U"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_fuel = _get_fuel_pct(prev_loc)
        curr_fuel = _get_fuel_pct(curr_loc)
        if prev_fuel is not None and curr_fuel is not None:
            if prev_fuel >= 10.0 and curr_fuel < 10.0:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Fuel level low: {curr_fuel:.1f}% remaining", f"{prev_fuel:.1f}%", f"{curr_fuel:.1f}%")
        return None

class GPSLostRule(BaseEventRule):
    event_type = "GPS Lost"
    txn = "U"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_fix = _get_fix(prev_loc)
        curr_fix = _get_fix(curr_loc)
        if prev_fix == "A" and curr_fix == "V":
            return EventRuleResult(self.event_type, self.txn, self.severity, "GPS lost fix. Triangulation offline.", "Valid (A)", "Invalid (V)")
        return None

class GPSRestoredRule(BaseEventRule):
    event_type = "GPS Restored"
    txn = "U"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_fix = _get_fix(prev_loc)
        curr_fix = _get_fix(curr_loc)
        if prev_fix == "V" and curr_fix == "A":
            return EventRuleResult(self.event_type, self.txn, self.severity, "GPS receiver fix restored.", "Invalid (V)", "Valid (A)")
        return None

class EngineOverTempRule(BaseEventRule):
    event_type = "Engine Over Temperature"
    txn = "V"
    severity = "Critical"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_temp = _get_coolant(prev_loc)
        curr_temp = _get_coolant(curr_loc)
        if prev_temp is not None and curr_temp is not None:
            if prev_temp <= 98.0 and curr_temp > 98.0:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Critical engine overheating alert: coolant temperature reached {curr_temp:.1f}°C", f"{prev_temp:.1f}°C", f"{curr_temp:.1f}°C")
        return None

class RefuelingStartedRule(BaseEventRule):
    event_type = "Refueling Started"
    txn = "R"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_fuel_level = _get_fuel_level(prev_loc)
        curr_fuel_level = _get_fuel_level(curr_loc)
        if prev_fuel_level is not None and curr_fuel_level is not None:
            # Fuel level increased by more than 3.0 Liters between sequential logs
            if curr_fuel_level - prev_fuel_level > 3.0:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Refueling detected. Fuel increased by {curr_fuel_level - prev_fuel_level:.1f}L", f"{prev_fuel_level:.1f} L", f"{curr_fuel_level:.1f} L")
        return None

class RefuelingCompletedRule(BaseEventRule):
    event_type = "Refueling Completed"
    txn = "R"
    severity = "Info"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        if not prev_loc: return None
        prev_fuel = _get_fuel_level(prev_loc)
        curr_fuel = _get_fuel_level(curr_loc)
        # Stabilized fuel level after increasing or ignition ON transition
        if prev_fuel is not None and curr_fuel is not None:
            prev_ign = _get_ign(prev_loc)
            curr_ign = _get_ign(curr_loc)
            if prev_ign == 0 and curr_ign == 1 and curr_fuel > prev_fuel + 5.0:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Refueling complete. Final fuel level: {curr_fuel:.1f} L", f"{prev_fuel:.1f} L", f"{curr_fuel:.1f} L")
        return None

class MaintenanceDueRule(BaseEventRule):
    event_type = "Maintenance Due"
    txn = "Q"
    severity = "Warning"

    def evaluate(self, prev_loc: Optional[Location], curr_loc: Location) -> Optional[EventRuleResult]:
        prev_odo = _get_odo(prev_loc) if prev_loc else None
        curr_odo = _get_odo(curr_loc)
        if prev_odo is not None and curr_odo is not None:
            # Crossed a 10,000 km threshold (10,000,000 meters)
            prev_milestone = int(prev_odo / 10000000)
            curr_milestone = int(curr_odo / 10000000)
            if curr_milestone > prev_milestone:
                return EventRuleResult(self.event_type, self.txn, self.severity, f"Odometer milestone crossed: {int(curr_odo / 1000)} km. Scheduled service due.", f"{int(prev_odo / 1000)} km", f"{int(curr_odo / 1000)} km")
        return None

# --- Main EventEngine class coordinator ---

class EventEngine:
    """
    Coordinates and executes state change validation rules on sequential telemetry nodes.
    Registers generated event entries to PostgreSQL database while preventing retries duplication.
    """
    def __init__(self):
        self.rules: List[BaseEventRule] = []
        self._load_default_rules()

    def register_rule(self, rule: BaseEventRule):
        self.rules.append(rule)

    def _load_default_rules(self):
        self.register_rule(IgnitionOnRule())
        self.register_rule(IgnitionOffRule())
        self.register_rule(VehicleStartedRule())
        self.register_rule(VehicleStoppedRule())
        self.register_rule(OverspeedRule())
        self.register_rule(HarshBrakingRule())
        self.register_rule(HarshAccelerationRule())
        self.register_rule(SharpTurnRule())
        self.register_rule(PowerFailureRule())
        self.register_rule(PowerRestoredRule())
        self.register_rule(LowBatteryRule())
        self.register_rule(LowFuelRule())
        self.register_rule(GPSLostRule())
        self.register_rule(GPSRestoredRule())
        self.register_rule(EngineOverTempRule())
        self.register_rule(RefuelingStartedRule())
        self.register_rule(RefuelingCompletedRule())
        self.register_rule(MaintenanceDueRule())

    async def _is_duplicate(self, db: AsyncSession, vehicle_id: int, event_type: str, timestamp: datetime) -> bool:
        stmt = select(Event).where(
            (Event.vehicle_id == vehicle_id) & 
            (Event.event_type == event_type)
        ).order_by(desc(Event.created_at)).limit(1)
        
        res = await db.execute(stmt)
        last_ev = res.scalars().first()
        if last_ev:
            time_diff = abs((timestamp - last_ev.created_at).total_seconds())
            if time_diff < 5.0:
                return True
        return False

    async def process_telemetry(self, db: AsyncSession, prev_loc: Optional[Location], curr_loc: Location) -> List[Event]:
        events_created = []
        
        for rule in self.rules:
            try:
                res = rule.evaluate(prev_loc, curr_loc)
                if res:
                    is_dup = await self._is_duplicate(db, curr_loc.vehicle_id, res.event_type, curr_loc.timestamp)
                    if not is_dup:
                        description = f"{res.description} (Previous: {res.prev_val} -> Current: {res.curr_val})"
                        
                        db_event = Event(
                            vehicle_id=curr_loc.vehicle_id,
                            txn=res.txn,
                            event_type=res.event_type,
                            description=description,
                            severity=res.severity,
                            created_at=curr_loc.timestamp
                        )
                        db.add(db_event)
                        events_created.append(db_event)
            except Exception as e:
                logger.error(f"EventEngine rule error on '{rule.event_type}': {e}", exc_info=True)
                
        if events_created:
            await db.flush()
            
        return events_created
