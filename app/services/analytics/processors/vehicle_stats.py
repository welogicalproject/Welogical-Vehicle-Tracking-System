import logging
import time
from math import sin, cos, sqrt, atan2, radians
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.location import Location
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

class VehicleStatsProcessor(BaseProcessor):
    """
    Stage 1 processor accumulating daily raw telemetry parameters (distance, runtimes, speed, fuel consumed)
    per vehicle.
    """
    name = "VehicleStatsProcessor"
    stage = 1

    def process(self, context: PipelineContext, db: Session) -> bool:
        start_time = time.time()
        
        # 1. Fetch raw locations in checkpoint scope
        locations = db.query(Location).filter(
            Location.id >= context.start_location_id,
            Location.id <= context.end_location_id
        ).order_by(Location.vehicle_id, Location.timestamp.asc()).all()

        if not locations:
            logger.info("VehicleStatsProcessor: No new locations found in range.")
            return True

        # Group sequential packets per vehicle_id
        vehicle_groups = defaultdict(list)
        for loc in locations:
            vehicle_groups[loc.vehicle_id].append(loc)

        vehicles_processed = 0
        packets_processed = len(locations)

        for vehicle_id, locs in vehicle_groups.items():
            # Fetch existing or instantiate new daily vehicle record
            summary = db.query(VehicleDailySummary).filter_by(
                vehicle_id=vehicle_id,
                date=context.date
            ).first()

            if not summary:
                summary = VehicleDailySummary(
                    vehicle_id=vehicle_id,
                    date=context.date,
                    distance_gps_km=0.0,
                    fuel_consumed_liters=0.0,
                    engine_runtime_hours=0.0,
                    driving_hours=0.0,
                    idle_hours=0.0,
                    max_speed=0.0
                )
                db.add(summary)
                db.flush()

            # A. Calculate GPS Distance increment
            first_odo = self._get_odo(locs[0])
            last_odo = self._get_odo(locs[-1])
            delta_dist = 0.0

            if first_odo is not None and last_odo is not None and last_odo >= first_odo:
                delta_dist = (last_odo - first_odo) / 1000.0
            else:
                # Haversine coordinate-to-coordinate calculations (fallback / missing odo)
                for i in range(1, len(locs)):
                    lat1, lon1 = locs[i-1].latitude, locs[i-1].longitude
                    lat2, lon2 = locs[i].latitude, locs[i].longitude
                    if lat1 == lat2 and lon1 == lon2:
                        continue  # ignore duplicates
                    delta_dist += self._haversine(lat1, lon1, lat2, lon2)

            # B. Calculate engine runtimes (engine, driving, idle hours)
            first_eh, first_dh, first_ih = self._get_engine_hours(locs[0])
            last_eh, last_dh, last_ih = self._get_engine_hours(locs[-1])
            delta_engine = 0.0
            delta_driving = 0.0
            delta_idle = 0.0

            if first_eh is not None and last_eh is not None and last_eh >= first_eh:
                delta_engine = last_eh - first_eh
                delta_driving = (last_dh - first_dh) if last_dh is not None else 0.0
                delta_idle = (last_ih - first_ih) if last_ih is not None else 0.0
            else:
                # Fallback to time-difference logic between consecutive events
                for i in range(1, len(locs)):
                    t_diff = (locs[i].timestamp - locs[i-1].timestamp).total_seconds() / 3600.0
                    # Ignore calculations if packets have anomalies / long offline intervals
                    if t_diff > 0.5:
                        t_diff = 0.0
                    
                    ign = locs[i].extra_data.get("io", {}).get("ign") if locs[i].extra_data else None
                    if ign is None:
                        ign = 1 if locs[i].speed > 0 else 0
                    
                    if ign == 1:
                        delta_engine += t_diff
                        if locs[i].speed > 0.0:
                            delta_driving += t_diff
                        else:
                            delta_idle += t_diff

            # C. Max Speed comparison
            batch_max_speed = max(loc.speed for loc in locs)

            # D. Fuel consumption decrement accumulation
            delta_fuel = 0.0
            prev_fuel = None
            for loc in locs:
                fuel = self._get_fuel_level(loc)
                if fuel is not None:
                    if prev_fuel is not None:
                        diff = prev_fuel - fuel
                        if diff > 0.0:  # Fuel decreased
                            # Clamp abnormal drops (e.g. sensor drift or refuels)
                            if diff < 5.0:
                                delta_fuel += diff
                    prev_fuel = fuel

            # Update cumulative values
            summary.distance_gps_km += delta_dist
            summary.fuel_consumed_liters += delta_fuel
            summary.engine_runtime_hours += delta_engine
            summary.driving_hours += delta_driving
            summary.idle_hours += delta_idle
            summary.max_speed = max(summary.max_speed, batch_max_speed)

            db.add(summary)
            context.processed_vehicle_ids.add(vehicle_id)
            vehicles_processed += 1

        elapsed_time = time.time() - start_time
        logger.info(
            f"VehicleStatsProcessor: Aggregated {vehicles_processed} vehicles and {packets_processed} locations "
            f"in {elapsed_time:.3f}s. Processing Date: {context.date}."
        )
        return True

    def _get_odo(self, loc: Location):
        extra = loc.extra_data
        if extra and "gps" in extra:
            return extra["gps"].get("odo")
        return None

    def _get_engine_hours(self, loc: Location):
        extra = loc.extra_data
        if extra and "engine" in extra:
            eng = extra["engine"]
            return eng.get("engine_hours"), eng.get("driving_hours"), eng.get("idle_hours")
        return None, None, None

    def _get_fuel_level(self, loc: Location):
        extra = loc.extra_data
        if extra and "fuel" in extra:
            return extra["fuel"].get("level")
        # Fallback for analog metrics
        analog = extra.get("io", {}).get("analog") if extra else None
        if analog and len(analog) > 2:
            return float(analog[2]) / 100.0
        return None

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return 6371.0 * c  # Kilometers
