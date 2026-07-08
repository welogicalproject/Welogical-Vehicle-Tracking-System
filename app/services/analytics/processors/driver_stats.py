import logging
import time
from math import sin, cos, sqrt, atan2, radians
from typing import Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, desc
from app.models.location import Location
from app.models.event import Event
from app.models.driver_assignment import DriverAssignment
from app.models.driver_daily_summary import DriverDailySummary
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

# --- CONFIGURABLE DRIVER SAFETY DEDUCTIONS ---
SAFETY_DEDUCTION_OVERSPEED = 5.0
SAFETY_DEDUCTION_HARSH_BRAKE = 10.0
SAFETY_DEDUCTION_HARSH_ACCEL = 8.0
SAFETY_DEDUCTION_SHARP_TURN = 5.0
SAFETY_DEDUCTION_OVERHEAT = 15.0
SAFETY_DEDUCTION_POWER_FAIL = 12.0

# --- CONFIGURABLE DRIVER ECO DEDUCTIONS ---
ECO_DEDUCTION_IDLE_HOUR = 4.0
ECO_DEDUCTION_HARSH_ACCEL = 5.0
ECO_DEDUCTION_HIGH_RPM_EVENT = 2.5
ECO_DEDUCTION_HIGH_FUEL_BURN = 0.5

class DriverStatsProcessor(BaseProcessor):
    """
    Stage 2 processor compiling per-driver daily statistics, counting event
    transitions, and computing Safety and Eco Scores.
    """
    name = "DriverStatsProcessor"
    stage = 2

    def process(self, context: PipelineContext, db: Session) -> bool:
        start_time = time.time()

        # Define daily datetime window
        date_start = datetime_combine_min(context.date)
        date_end = datetime_combine_max(context.date)

        # 1. Fetch active assignments for the target date
        assignments = db.query(DriverAssignment).filter(
            DriverAssignment.assigned_at <= date_end,
            or_(
                DriverAssignment.released_at >= date_start,
                DriverAssignment.released_at.is_(None)
            )
        ).all()

        if not assignments:
            logger.info(f"DriverStatsProcessor: No active driver assignments on {context.date}.")
            return True

        # Group data per driver to support multi-vehicle handovers on the same day
        driver_stats = defaultdict(lambda: {
            "distance": 0.0,
            "engine_hours": 0.0,
            "driving_hours": 0.0,
            "idle_hours": 0.0,
            "fuel_used": 0.0,
            "max_speed": 0.0,
            "avg_speed_sum": 0.0,
            "avg_speed_count": 0,
            "overspeed_count": 0,
            "harsh_brake_count": 0,
            "harsh_accel_count": 0,
            "sharp_turn_count": 0,
            "ignition_cycles": 0,
            "refueling_count": 0,
            "overheat_count": 0,
            "power_fail_count": 0,
            "high_rpm_count": 0,
        })

        for assignment in assignments:
            driver_id = assignment.driver_id
            vehicle_id = assignment.vehicle_id

            # Crop overlap interval to this calendar day
            interval_start = max(date_start, assignment.assigned_at)
            interval_end = min(date_end, assignment.released_at or date_end)

            # Query locations during the active assignment period
            locs = db.query(Location).filter(
                Location.vehicle_id == vehicle_id,
                Location.timestamp >= interval_start,
                Location.timestamp <= interval_end
            ).order_by(Location.timestamp.asc()).all()

            if not locs:
                continue

            stats = driver_stats[driver_id]

            # A. Distance accumulation
            first_odo = self._get_odo(locs[0])
            last_odo = self._get_odo(locs[-1])
            if first_odo is not None and last_odo is not None and last_odo >= first_odo:
                stats["distance"] += (last_odo - first_odo) / 1000.0
            else:
                # Coordinate Haversine backup
                for i in range(1, len(locs)):
                    lat1, lon1 = locs[i-1].latitude, locs[i-1].longitude
                    lat2, lon2 = locs[i].latitude, locs[i].longitude
                    if lat1 != lat2 or lon1 != lon2:
                        stats["distance"] += self._haversine(lat1, lon1, lat2, lon2)

            # B. Runtime accumulation
            first_eh, first_dh, first_ih = self._get_engine_hours(locs[0])
            last_eh, last_dh, last_ih = self._get_engine_hours(locs[-1])
            if first_eh is not None and last_eh is not None and last_eh >= first_eh:
                stats["engine_hours"] += last_eh - first_eh
                stats["driving_hours"] += (last_dh - first_dh) if last_dh is not None else 0.0
                stats["idle_hours"] += (last_ih - first_ih) if last_ih is not None else 0.0
            else:
                # Time delta backup
                for i in range(1, len(locs)):
                    t_diff = (locs[i].timestamp - locs[i-1].timestamp).total_seconds() / 3600.0
                    if t_diff < 0.5:
                        ign = locs[i].extra_data.get("io", {}).get("ign") if locs[i].extra_data else None
                        if ign is None:
                            ign = 1 if locs[i].speed > 0.1 else 0
                        if ign == 1:
                            stats["engine_hours"] += t_diff
                            if locs[i].speed > 0.1:
                                stats["driving_hours"] += t_diff
                            else:
                                stats["idle_hours"] += t_diff

            # C. Fuel consumption accumulation
            first_fuel = self._get_fuel_level(locs[0])
            last_fuel = self._get_fuel_level(locs[-1])
            if first_fuel is not None and last_fuel is not None:
                stats["fuel_used"] += max(0.0, first_fuel - last_fuel)
            else:
                stats["fuel_used"] += (stats["idle_hours"] * 1.5) + (stats["driving_hours"] * 8.0)

            # D. Speed metrics
            speeds = [l.speed for l in locs]
            stats["max_speed"] = max(stats["max_speed"], max(speeds) if speeds else 0.0)
            stats["avg_speed_sum"] += sum(speeds)
            stats["avg_speed_count"] += len(speeds)

            # E. Normalized events queries
            stats["overspeed_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Overspeed", "Overspeed Alert", "Speed Limit Exceeded"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["harsh_brake_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Harsh Braking", "Harsh Brake"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["harsh_accel_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Harsh Acceleration", "Over Acceleration"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["sharp_turn_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Sharp Turn", "Harsh Turn"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["ignition_cycles"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Ignition On"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["refueling_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Refueling Started", "Refueling Completed"]),
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["overheat_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type == "Engine Over Temperature",
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["power_fail_count"] += db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type == "Power Failure",
                Event.created_at >= interval_start,
                Event.created_at <= interval_end
            ).count()

            stats["high_rpm_count"] += sum(
                1 for l in locs if l.extra_data and l.extra_data.get("engine", {}).get("rpm", 0) > 3500
            )

        # 2. Write daily summary records
        for driver_id, s in driver_stats.items():
            summary = db.query(DriverDailySummary).filter_by(
                driver_id=driver_id,
                date=context.date
            ).first()

            if not summary:
                summary = DriverDailySummary(
                    driver_id=driver_id,
                    date=context.date
                )
                db.add(summary)
                db.flush()

            # Compile values
            summary.distance_driven_km = s["distance"]
            summary.engine_hours = s["engine_hours"]
            summary.driving_hours = s["driving_hours"]
            summary.idle_hours = s["idle_hours"]
            summary.fuel_used_l = s["fuel_used"]
            
            # Weighted avg fuel economy
            summary.avg_fuel_economy_kpl = (s["distance"] / s["fuel_used"]) if s["fuel_used"] > 0 else 0.0
            
            summary.max_speed_kmh = s["max_speed"]
            summary.avg_speed_kmh = (s["avg_speed_sum"] / s["avg_speed_count"]) if s["avg_speed_count"] > 0 else 0.0

            # Event counts
            summary.overspeed_count = s["overspeed_count"]
            summary.overspeed_duration_sec = s["overspeed_count"] * 15 # mock 15s per alert
            summary.harsh_braking_count = s["harsh_brake_count"]
            summary.harsh_acceleration_count = s["harsh_accel_count"]
            summary.sharp_turn_count = s["sharp_turn_count"]
            summary.ignition_cycles = s["ignition_cycles"]
            summary.refueling_count = s["refueling_count"]

            # F. Calculate scores
            safety_deduction = (
                (s["overspeed_count"] * SAFETY_DEDUCTION_OVERSPEED) +
                (s["harsh_brake_count"] * SAFETY_DEDUCTION_HARSH_BRAKE) +
                (s["harsh_accel_count"] * SAFETY_DEDUCTION_HARSH_ACCEL) +
                (s["sharp_turn_count"] * SAFETY_DEDUCTION_SHARP_TURN) +
                (s["overheat_count"] * SAFETY_DEDUCTION_OVERHEAT) +
                (s["power_fail_count"] * SAFETY_DEDUCTION_POWER_FAIL)
            )
            summary.safety_score = max(0.0, 100.0 - safety_deduction)

            eco_deduction = (
                (s["idle_hours"] * ECO_DEDUCTION_IDLE_HOUR) +
                (s["harsh_accel_count"] * ECO_DEDUCTION_HARSH_ACCEL) +
                (s["high_rpm_count"] * ECO_DEDUCTION_HIGH_RPM_EVENT)
            )
            if summary.avg_fuel_economy_kpl > 0.0 and summary.avg_fuel_economy_kpl < 10.0:
                eco_deduction += (10.0 - summary.avg_fuel_economy_kpl) * ECO_DEDUCTION_HIGH_FUEL_BURN

            summary.eco_score = max(0.0, 100.0 - eco_deduction)

            db.add(summary)

        elapsed_time = time.time() - start_time
        logger.info(
            f"DriverStatsProcessor: Aggregated daily driver summaries for {len(driver_stats)} drivers on {context.date} in {elapsed_time:.3f}s."
        )
        return True

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def _get_odo(self, loc: Location) -> Optional[float]:
        extra = loc.extra_data
        return extra.get("gps_details", {}).get("odo") if extra else None

    def _get_engine_hours(self, loc: Location) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        extra = loc.extra_data
        if not extra or "engine" not in extra:
            return None, None, None
        eng = extra["engine"]
        return eng.get("engine_hours"), eng.get("driving_hours"), eng.get("idle_hours")

    def _get_fuel_level(self, loc: Location) -> Optional[float]:
        extra = loc.extra_data
        return extra.get("fuel", {}).get("level") if extra else None

# Helper functions to convert date to datetime min/max limits
def datetime_combine_min(d: date) -> datetime:
    from datetime import datetime, time
    return datetime.combine(d, time.min)

def datetime_combine_max(d: date) -> datetime:
    from datetime import datetime, time
    return datetime.combine(d, time.max)
