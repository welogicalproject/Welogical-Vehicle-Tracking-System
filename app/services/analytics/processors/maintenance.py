import logging
import time
from datetime import datetime, date, time as datetime_time, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.location import Location
from app.models.event import Event
from app.models.vehicle import Vehicle
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.maintenance_summary import MaintenanceSummary
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

# --- CONFIGURABLE MAINTENANCE CONSTANTS ---
SERVICE_INTERVAL_KM = 10000.0
SERVICE_INTERVAL_DAYS = 365
BRAKE_WEAR_INTERVAL_KM = 20000.0
TYRE_WEAR_INTERVAL_KM = 40000.0

# --- HEALTH DEDUCTION CONFIGURATIONS ---
HEALTH_DEDUCTION_OVERHEAT = 15.0
HEALTH_DEDUCTION_POWER_FAIL = 5.0
HEALTH_DEDUCTION_LOW_BATTERY = 5.0
HEALTH_DEDUCTION_HARSH_DRIVE = 2.0

class MaintenanceProcessor(BaseProcessor):
    """
    Stage 2 processor compiling daily vehicle maintenance checklists, wear metrics,
    and overall health index ratings.
    """
    name = "MaintenanceProcessor"
    stage = 2

    def process(self, context: PipelineContext, db: Session) -> bool:
        start_time = time.time()

        # Define daily datetime window
        date_start = datetime.combine(context.date, datetime_time.min)
        date_end = datetime.combine(context.date, datetime_time.max)

        # 1. Fetch all registered vehicles
        vehicles = db.query(Vehicle).all()
        if not vehicles:
            logger.info("MaintenanceProcessor: No vehicles registered.")
            return True

        vehicles_processed = 0

        for vehicle in vehicles:
            vehicle_id = vehicle.id

            # Find latest location log today to capture current odometer
            last_loc = db.query(Location).filter(
                Location.vehicle_id == vehicle_id,
                Location.timestamp <= date_end
            ).order_by(Location.timestamp.desc()).first()

            # Retrieve odometer reading
            odo_meters = None
            if last_loc:
                odo_meters = self._get_odo(last_loc)

            # Fallback estimation if odometer is missing
            if odo_meters is None:
                prev_summary = db.query(MaintenanceSummary).filter(
                    MaintenanceSummary.vehicle_id == vehicle_id,
                    MaintenanceSummary.date < context.date
                ).order_by(MaintenanceSummary.date.desc()).first()

                if prev_summary:
                    # Increment from last known remaining distance ratio
                    odo_meters = (SERVICE_INTERVAL_KM - prev_summary.remaining_service_distance_km) * 1000.0
                else:
                    # Deterministic mock baseline per vehicle primary key
                    odo_meters = (vehicle_id * 15300.0 + 120.0) * 1000.0

            odo_km = odo_meters / 1000.0

            # 2. Query event metrics today for deduction parameters
            overheat_count = db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type == "Engine Over Temperature",
                Event.created_at >= date_start,
                Event.created_at <= date_end
            ).count()

            power_fail_count = db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type == "Power Failure",
                Event.created_at >= date_start,
                Event.created_at <= date_end
            ).count()

            low_battery_count = db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type == "Low Battery",
                Event.created_at >= date_start,
                Event.created_at <= date_end
            ).count()

            harsh_drive_count = db.query(Event).filter(
                Event.vehicle_id == vehicle_id,
                Event.event_type.in_(["Harsh Braking", "Harsh Acceleration", "Sharp Turn"]),
                Event.created_at >= date_start,
                Event.created_at <= date_end
            ).count()

            # 3. Perform maintenance wear and health calculations
            
            # A. Remaining Service Distance
            distance_since_service = odo_km % SERVICE_INTERVAL_KM
            remaining_dist = max(0.0, SERVICE_INTERVAL_KM - distance_since_service)

            # B. Remaining Service Days
            remaining_days = max(1, int(SERVICE_INTERVAL_DAYS * (remaining_dist / SERVICE_INTERVAL_KM)))

            # C. Estimated Next Service Date
            next_service_date = context.date + timedelta(days=remaining_days)

            # D. Oil Life %
            oil_life = max(0.0, 100.0 * (remaining_dist / SERVICE_INTERVAL_KM))

            # E. Brake Wear %
            base_brake_wear = (odo_km % BRAKE_WEAR_INTERVAL_KM) / BRAKE_WEAR_INTERVAL_KM * 100.0
            brake_wear = min(100.0, base_brake_wear + (harsh_drive_count * 0.5))

            # F. Tyre Health %
            base_tyre_health = max(0.0, 100.0 - ((odo_km % TYRE_WEAR_INTERVAL_KM) / TYRE_WEAR_INTERVAL_KM * 100.0))
            tyre_health = max(0.0, base_tyre_health - (harsh_drive_count * 0.3))

            # G. Battery Health %
            battery_health = max(0.0, 100.0 - (low_battery_count * HEALTH_DEDUCTION_LOW_BATTERY) - (power_fail_count * HEALTH_DEDUCTION_POWER_FAIL))

            # H. Cooling System Health rating
            cooling_health = "Good"
            if overheat_count > 0:
                cooling_health = "Critical"
            elif harsh_drive_count > 5:
                cooling_health = "Fair"

            # I. Engine Health Index
            engine_deductions = (overheat_count * HEALTH_DEDUCTION_OVERHEAT) + (harsh_drive_count * HEALTH_DEDUCTION_HARSH_DRIVE)
            # Factor cumulative engine runtime hours if available
            veh_summary = db.query(VehicleDailySummary).filter_by(
                vehicle_id=vehicle_id,
                date=context.date
            ).first()
            if veh_summary:
                engine_deductions += (veh_summary.engine_runtime_hours * 0.1) # 0.1% wear per hour
            
            engine_health = max(0.0, 100.0 - engine_deductions)

            # J. Overall Vehicle Health Score (Weighted index)
            overall_health = (
                (oil_life * 0.15) +
                ((100.0 - brake_wear) * 0.15) +
                (tyre_health * 0.15) +
                (battery_health * 0.20) +
                (engine_health * 0.35)
            )
            overall_health = max(0.0, min(100.0, overall_health))

            # 4. Save MaintenanceSummary record
            summary = db.query(MaintenanceSummary).filter_by(
                vehicle_id=vehicle_id,
                date=context.date
            ).first()

            if not summary:
                summary = MaintenanceSummary(
                    vehicle_id=vehicle_id,
                    date=context.date
                )
                db.add(summary)
                db.flush()

            # Populate fields
            summary.remaining_service_distance_km = remaining_dist
            summary.remaining_service_days = remaining_days
            summary.estimated_next_service_date = next_service_date
            summary.oil_life_pct = oil_life
            summary.brake_wear_pct = brake_wear
            summary.tyre_health_pct = tyre_health
            summary.battery_health_pct = battery_health
            summary.cooling_system_health = cooling_health
            summary.engine_health_index = engine_health
            summary.overall_vehicle_health_score = overall_health

            db.add(summary)
            vehicles_processed += 1

        elapsed_time = time.time() - start_time
        logger.info(
            f"MaintenanceProcessor: Compiled daily health summaries for {vehicles_processed} vehicles on {context.date} in {elapsed_time:.3f}s."
        )
        return True

    def _get_odo(self, loc: Location) -> Optional[float]:
        extra = loc.extra_data
        return extra.get("gps_details", {}).get("odo") if extra else None
