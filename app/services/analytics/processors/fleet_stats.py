import logging
import time
from sqlalchemy.orm import Session
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.fleet_daily_summary import FleetDailySummary
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

class FleetStatsProcessor(BaseProcessor):
    """
    Stage 3 processor aggregating per-day fleet statistics from VehicleDailySummary records.
    """
    name = "FleetStatsProcessor"
    stage = 3

    def process(self, context: PipelineContext, db: Session) -> bool:
        start_time = time.time()

        # 1. Fetch daily summaries for all vehicles on target date
        vehicle_summaries = db.query(VehicleDailySummary).filter_by(date=context.date).all()
        
        # 2. Accumulate values
        total_dist = 0.0
        total_fuel = 0.0
        total_engine = 0.0
        total_driving = 0.0
        total_idle = 0.0
        max_speed = 0.0
        active_count = len(vehicle_summaries)

        for summary in vehicle_summaries:
            total_dist += summary.distance_gps_km
            total_fuel += summary.fuel_consumed_liters
            total_engine += summary.engine_runtime_hours
            total_driving += summary.driving_hours
            total_idle += summary.idle_hours
            max_speed = max(max_speed, summary.max_speed)

        # 3. Retrieve or instantiate the FleetDailySummary record
        fleet_summary = db.query(FleetDailySummary).filter_by(date=context.date).first()
        if not fleet_summary:
            fleet_summary = FleetDailySummary(date=context.date)
            db.add(fleet_summary)
            db.flush()

        # Update metrics (overwriting supports incremental re-calculations)
        fleet_summary.total_distance_km = total_dist
        fleet_summary.total_fuel_consumed_l = total_fuel
        fleet_summary.total_engine_hours = total_engine
        fleet_summary.total_driving_hours = total_driving
        fleet_summary.total_idle_hours = total_idle
        fleet_summary.active_vehicles = active_count
        fleet_summary.fleet_max_speed = max_speed

        db.add(fleet_summary)
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"FleetStatsProcessor: Aggregated stats for {active_count} vehicles on {context.date} in {elapsed_time:.3f}s. "
            f"Totals: Dist={total_dist:.2f}km, Fuel={total_fuel:.2f}L, Engine={total_engine:.2f}h, MaxSpeed={max_speed:.1f}km/h."
        )
        return True
