import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, desc
from app.models.location import Location
from app.models.event import Event
from app.models.vehicle import Vehicle
from app.models.driver_assignment import DriverAssignment
from app.models.trip import Trip
from app.models.maintenance_summary import MaintenanceSummary
from app.models.fleet_operations import VehicleOperations, FleetOperationsLive
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

class FleetOperationsProcessor(BaseProcessor):
    """
    Stage 3 processor evaluating real-time operational metrics, warning flags,
    active drivers, and compiling live fleet dispatch KPIs.
    """
    name = "FleetOperationsProcessor"
    stage = 3

    def process(self, context: PipelineContext, db: Session) -> bool:
        start_time = time.time()

        # 1. Fetch all registered vehicles
        vehicles = db.query(Vehicle).all()
        if not vehicles:
            logger.info("FleetOperationsProcessor: No vehicles found to analyze.")
            return True

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        five_min_ago = now_naive - timedelta(minutes=5)
        thirty_min_ago = now_naive - timedelta(minutes=30)
        twenty_four_hours_ago = now_naive - timedelta(hours=24)

        # Operational counters
        driving_cnt = 0
        idling_cnt = 0
        parked_cnt = 0
        offline_cnt = 0
        active_trips_cnt = 0
        requiring_attention_cnt = 0

        for vehicle in vehicles:
            vehicle_id = vehicle.id

            # A. Fetch last location log to extract current metrics
            last_loc = db.query(Location).filter(
                Location.vehicle_id == vehicle_id
            ).order_by(Location.timestamp.desc()).first()

            # Determine operational state based on last seen timestamp
            status = "Offline"
            gps_lost_val = False
            low_fuel_val = False
            low_battery_val = False
            power_fail_val = False
            overheat_val = False
            ign = None
            speed = 0.0

            if last_loc:
                ts = last_loc.timestamp
                speed = last_loc.speed
                extra = last_loc.extra_data or {}
                ign = extra.get("io", {}).get("ign")
                
                # Check status categories
                if ts >= five_min_ago:
                    if ign == 1:
                        status = "Driving" if speed > 0.1 else "Idling"
                    else:
                        status = "Parked"
                elif ts >= thirty_min_ago:
                    status = "Idling"
                else:
                    status = "Offline"

                # Check warning indicators
                fix = extra.get("gps_details", {}).get("fix")
                gps_lost_val = (fix == "V")

                fuel_pct = extra.get("fuel", {}).get("percentage")
                if fuel_pct is not None and fuel_pct < 10.0:
                    low_fuel_val = True

                main_pwr = extra.get("pwr", {}).get("main")
                power_fail_val = (main_pwr == 0)

                volt = extra.get("pwr", {}).get("volt")
                if volt is not None and (volt / 1000.0) < 11.5:
                    low_battery_val = True

                coolant = extra.get("engine", {}).get("coolant_temperature")
                if coolant is not None and coolant > 98.0:
                    overheat_val = True
            else:
                status = "Offline"

            # B. Query active driver assignment
            asg = db.query(DriverAssignment).filter(
                DriverAssignment.vehicle_id == vehicle_id,
                DriverAssignment.assigned_at <= now_naive,
                or_(
                    DriverAssignment.released_at >= now_naive,
                    DriverAssignment.released_at.is_(None)
                )
            ).order_by(DriverAssignment.assigned_at.desc()).first()
            driver_name = asg.driver.driver_name if asg and asg.driver else None

            # C. Query active trip ID
            active_trip = db.query(Trip).filter(
                Trip.vehicle_id == vehicle_id,
                Trip.end_time.is_(None)
            ).first()
            active_trip_id = active_trip.id if active_trip else None
            if active_trip_id:
                active_trips_cnt += 1

            # D. Query health summary score
            latest_maint = db.query(MaintenanceSummary).filter(
                MaintenanceSummary.vehicle_id == vehicle_id
            ).order_by(MaintenanceSummary.date.desc()).first()
            
            health_score = latest_maint.overall_vehicle_health_score if latest_maint else 100.0
            maint_due_val = latest_maint.remaining_service_distance_km < 1000.0 if latest_maint else False

            # E. Accumulate state counters
            if status == "Driving":
                driving_cnt += 1
            elif status == "Idling":
                idling_cnt += 1
            elif status == "Parked":
                parked_cnt += 1
            else:
                offline_cnt += 1

            # Check if vehicle requires operational dispatcher attention
            has_alert = (
                gps_lost_val or low_fuel_val or low_battery_val or 
                power_fail_val or overheat_val or maint_due_val or 
                health_score < 70.0
            )
            if has_alert:
                requiring_attention_cnt += 1

            # Update or create VehicleOperations record
            veh_ops = db.query(VehicleOperations).filter_by(vehicle_id=vehicle_id).first()
            if not veh_ops:
                veh_ops = VehicleOperations(vehicle_id=vehicle_id)
                db.add(veh_ops)
                db.flush()

            veh_ops.status = status
            veh_ops.gps_lost = gps_lost_val
            veh_ops.low_fuel = low_fuel_val
            veh_ops.low_battery = low_battery_val
            veh_ops.maintenance_due = maint_due_val
            veh_ops.power_failure = power_fail_val
            veh_ops.engine_overheat = overheat_val
            veh_ops.active_trip_id = active_trip_id
            veh_ops.current_driver_name = driver_name
            veh_ops.current_health_score = health_score
            veh_ops.last_updated = now_naive

            db.add(veh_ops)

        # 2. Query Event table counters for the last 24 hours
        critical_alerts = db.query(Event).filter(
            Event.severity == "Critical",
            Event.created_at >= twenty_four_hours_ago
        ).count()

        warning_alerts = db.query(Event).filter(
            Event.severity == "Warning",
            Event.created_at >= twenty_four_hours_ago
        ).count()

        # 3. Calculate fleet-wide operational metrics
        total_veh = len(vehicles)
        availability_pct = ((total_veh - offline_cnt) / total_veh * 100.0) if total_veh > 0 else 100.0
        utilization_pct = ((driving_cnt + idling_cnt) / total_veh * 100.0) if total_veh > 0 else 0.0

        # Update or create FleetOperationsLive summary record
        fleet_ops = db.query(FleetOperationsLive).first()
        if not fleet_ops:
            fleet_ops = FleetOperationsLive()
            db.add(fleet_ops)
            db.flush()

        fleet_ops.vehicles_driving = driving_cnt
        fleet_ops.vehicles_idling = idling_cnt
        fleet_ops.vehicles_parked = parked_cnt
        fleet_ops.vehicles_offline = offline_cnt
        fleet_ops.active_trips = active_trips_cnt
        fleet_ops.fleet_availability_pct = availability_pct
        fleet_ops.fleet_utilization_pct = utilization_pct
        fleet_ops.vehicles_requiring_attention = requiring_attention_cnt
        fleet_ops.critical_alerts_count = critical_alerts
        fleet_ops.warning_alerts_count = warning_alerts
        fleet_ops.last_updated = now_naive

        db.add(fleet_ops)

        # Broadcast real-time fleet operations aggregates
        import asyncio
        from app.services.websocket_manager import ws_manager
        payload = {
            "vehicles_driving": driving_cnt,
            "vehicles_idling": idling_cnt,
            "vehicles_parked": parked_cnt,
            "vehicles_offline": offline_cnt,
            "active_trips": active_trips_cnt,
            "fleet_availability_pct": availability_pct,
            "fleet_utilization_pct": utilization_pct,
            "vehicles_requiring_attention": requiring_attention_cnt,
            "critical_alerts_count": critical_alerts,
            "warning_alerts_count": warning_alerts,
            "last_updated": str(now_naive)
        }
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast("fleet_operations", payload))
                loop.create_task(ws_manager.broadcast("fleet", payload))
        except RuntimeError:
            pass

        elapsed_time = time.time() - start_time
        logger.info(
            f"FleetOperationsProcessor: Live dispatch metrics compiled in {elapsed_time:.3f}s. "
            f"Active trips={active_trips_cnt}, Driving={driving_cnt}, Offline={offline_cnt}."
        )
        return True
