import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from app.config import settings
from app.services.simulator.vehicle_twin import VehicleTwin

logger = logging.getLogger("vts.simulator")

# ---------------------------------------------------------------------------
# Route cache key format for simulator routes stored in the DB route_cache
# table. We use a dedicated provider name so entries are clearly identifiable
# and never clash with real Google Routes cache entries.
#
# Key format:  sim:route:{route_index}
# ---------------------------------------------------------------------------
_SIM_ROUTE_PROVIDER = "simulator"
_SIM_ROUTE_API      = "template_interpolated"


class SimulatorService:
    """
    Service lifecycle manager running entirely inside the FastAPI process.

    Responsibilities:
    - Bootstrap: resolve / auto-register vehicle DB records, build route paths
      (checking the DB-backed route cache first), construct VehicleTwin instances
      and start their async loops.
    - Health watchdog: periodically check every twin task; restart crashed ones.
    - Graceful stop: cancel all twin tasks cleanly.
    - Metrics aggregation: expose per-service counters for the /simulator/metrics
      endpoint.
    """

    def __init__(self):
        self.twins: Dict[str, VehicleTwin] = {}
        self.is_running: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._service_start_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self.is_running:
            return
        logger.info("SimulatorService starting...")
        self.is_running = True
        self._service_start_time = datetime.now(timezone.utc)

        device_uids = [uid.strip() for uid in settings.SIMULATOR_DEVICE_UIDS.split(",") if uid.strip()]
        send_interval = settings.SIMULATOR_SEND_INTERVAL
        speed_multiplier = settings.SIMULATOR_SPEED_MULTIPLIER
        loop_route = settings.SIMULATOR_LOOP_ROUTE

        # ---- DB bootstrap: vehicle persistence + route cache ----
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            uid_to_vehicle = await self._resolve_vehicles(session, device_uids)
            index_to_path  = await self._resolve_routes(session, len(device_uids))

        # ---- Spawn twins ----
        for i, uid in enumerate(device_uids):
            vehicle_rec = uid_to_vehicle.get(uid)
            db_vehicle_id  = vehicle_rec.get("id") if vehicle_rec else None
            vehicle_name   = vehicle_rec.get("vehicle_name") if vehicle_rec else f"Simulated {uid}"
            vehicle_type   = vehicle_rec.get("vehicle_type") if vehicle_rec else ("Truck" if "DEMO" in uid else "Car")

            if uid not in self.twins:
                self.twins[uid] = VehicleTwin(
                    device_uid=uid,
                    send_interval=send_interval,
                    speed_multiplier=speed_multiplier,
                    loop_route=loop_route,
                    index=i,
                    path=index_to_path.get(i),
                    db_vehicle_id=db_vehicle_id,
                    vehicle_name=vehicle_name,
                    vehicle_type=vehicle_type,
                )
            else:
                # Re-use existing twin but refresh its DB identity
                self.twins[uid].db_vehicle_id = db_vehicle_id

            await self.twins[uid].start()

        # ---- Health watchdog ----
        self._monitor_task = asyncio.create_task(self._health_monitor_loop())
        logger.info(f"SimulatorService started ({len(self.twins)} twins)")

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------

    async def stop(self) -> None:
        if not self.is_running:
            return
        logger.info("SimulatorService stopping...")
        self.is_running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        for twin in list(self.twins.values()):
            await twin.stop()

        logger.info("SimulatorService stopped")

    # ------------------------------------------------------------------
    # Restart
    # ------------------------------------------------------------------

    async def restart(self, device_uid: Optional[str] = None) -> None:
        if device_uid:
            if device_uid in self.twins:
                logger.info(f"Restarting VehicleTwin {device_uid}...")
                await self.twins[device_uid].stop()
                await self.twins[device_uid].start()
        else:
            logger.info("Restarting SimulatorService...")
            await self.stop()
            await self.start()

    # ------------------------------------------------------------------
    # Health monitor
    # ------------------------------------------------------------------

    async def _health_monitor_loop(self) -> None:
        """
        Periodically checks every twin's asyncio task. Restarts any twin whose
        task is done (crashed or completed without loop_route). The monitor itself
        is resilient: if it encounters an unexpected exception it logs and continues.
        """
        interval = settings.SIMULATOR_HEALTH_CHECK_INTERVAL
        logger.info(f"Health monitor started (interval={interval}s)")
        while self.is_running:
            try:
                await asyncio.sleep(interval)
                for uid, twin in list(self.twins.items()):
                    task_done = twin._task is None or twin._task.done()
                    # Detect stuck twins: last_tick is older than 3 × send_interval
                    tick_stale = False
                    if twin.last_tick_time and twin.is_running:
                        age = (datetime.now(timezone.utc) - twin.last_tick_time).total_seconds()
                        tick_stale = age > twin.send_interval * 3
                    if task_done or tick_stale:
                        reason = "task finished" if task_done else f"tick stale ({age:.0f}s)"
                        logger.warning(f"[HealthMonitor] VehicleTwin {uid} unhealthy ({reason}). Restarting...")
                        try:
                            await twin.stop()
                        except Exception:
                            pass
                        try:
                            await twin.start()
                            logger.info(f"[HealthMonitor] VehicleTwin {uid} restarted successfully.")
                        except Exception as ex:
                            logger.error(f"[HealthMonitor] Failed to restart twin {uid}: {ex}", exc_info=True)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[HealthMonitor] Unexpected error: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Vehicle persistence helpers
    # ------------------------------------------------------------------

    async def _resolve_vehicles(
        self, session, device_uids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        For each UID:
        - If a DB record exists → reconnect (return existing id/name/type).
        - If missing and SIMULATOR_AUTO_REGISTER=True → create a record.
        Returns a dict of uid → {id, vehicle_name, vehicle_type}.
        """
        from sqlalchemy import select
        from app.models.vehicle import Vehicle

        result: Dict[str, Dict[str, Any]] = {}

        # Fetch all in one query
        stmt = select(Vehicle).where(Vehicle.device_uid.in_(device_uids))
        res = await session.execute(stmt)
        existing = {v.device_uid: v for v in res.scalars().all()}

        for uid in device_uids:
            if uid in existing:
                veh = existing[uid]
                result[uid] = {
                    "id": veh.id,
                    "vehicle_name": veh.vehicle_name,
                    "vehicle_type": veh.vehicle_type,
                }
                logger.info(f"[Bootstrap] Reconnected to existing vehicle {uid} (db_id={veh.id})")
            elif settings.SIMULATOR_AUTO_REGISTER:
                name = f"Simulated {uid}"
                v_type = "Truck" if "DEMO" in uid else "Car"
                new_veh = Vehicle(
                    device_uid=uid,
                    vehicle_name=name,
                    vehicle_type=v_type,
                )
                session.add(new_veh)
                await session.flush()
                result[uid] = {
                    "id": new_veh.id,
                    "vehicle_name": new_veh.vehicle_name,
                    "vehicle_type": new_veh.vehicle_type,
                }
                logger.info(f"[Bootstrap] Auto-registered new vehicle {uid} (db_id={new_veh.id})")
            else:
                logger.warning(f"[Bootstrap] Vehicle {uid} not in DB and SIMULATOR_AUTO_REGISTER=false. Twin will self-register via telemetry pipeline.")
                result[uid] = {}  # Pipeline's auto-register will handle it on first packet

        await session.commit()
        return result

    # ------------------------------------------------------------------
    # Route cache helpers (DB-backed, provider="simulator")
    # ------------------------------------------------------------------

    async def _resolve_routes(
        self, session, num_routes: int
    ) -> Dict[int, List[Tuple[float, float]]]:
        """
        For each route index, attempt to load a cached interpolated path from the
        DB route_cache table (provider="simulator"). If not cached, compute via
        interpolate_waypoints and persist. Returns dict of index → path list.
        """
        from app.models.route_cache import RouteCache
        from app.services.simulator.physics import TEMPLATE_ROUTES, interpolate_waypoints
        from sqlalchemy import select

        paths: Dict[int, List[Tuple[float, float]]] = {}

        for idx in range(num_routes):
            cache_key = f"sim:route:{idx}"
            stmt = select(RouteCache).where(RouteCache.cache_key == cache_key)
            res = await session.execute(stmt)
            cached: Optional[RouteCache] = res.scalars().first()

            if cached and cached.encoded_polyline:
                try:
                    coords = json.loads(cached.encoded_polyline)
                    paths[idx] = [(c[0], c[1]) for c in coords]
                    logger.info(f"[RouteCache] Loaded route {idx} from DB cache ({len(paths[idx])} points)")
                    continue
                except Exception as e:
                    logger.warning(f"[RouteCache] Failed to deserialise cached route {idx}: {e}. Recomputing.")

            # Compute fresh
            waypoints = TEMPLATE_ROUTES[idx % len(TEMPLATE_ROUTES)]
            path = interpolate_waypoints(waypoints, points_per_segment=50)
            paths[idx] = path

            # Persist to DB
            origin = waypoints[0]
            dest   = waypoints[-1]
            coords_json = json.dumps([[p[0], p[1]] for p in path])

            if cached:
                # Update stale record
                cached.encoded_polyline = coords_json
                cached.status = "ready"
            else:
                new_entry = RouteCache(
                    cache_key=cache_key,
                    provider=_SIM_ROUTE_PROVIDER,
                    provider_api=_SIM_ROUTE_API,
                    travel_mode="DRIVE",
                    origin_lat_raw=float(origin[0]),
                    origin_lon_raw=float(origin[1]),
                    destination_lat_raw=float(dest[0]),
                    destination_lon_raw=float(dest[1]),
                    origin_lat_normalized=round(float(origin[0]), 5),
                    origin_lon_normalized=round(float(origin[1]), 5),
                    destination_lat_normalized=round(float(dest[0]), 5),
                    destination_lon_normalized=round(float(dest[1]), 5),
                    options_hash=f"sim-{idx}",
                    request_hash=f"sim-{idx}",
                    encoded_polyline=coords_json,
                    polyline_format="json_lat_lon",
                    distance_meters=int(sum(
                        __import__('math').hypot(
                            (path[i][0] - path[i-1][0]) * 111000,
                            (path[i][1] - path[i-1][1]) * 111000
                        ) for i in range(1, len(path))
                    )),
                    status="ready",
                    created_by="SimulatorService",
                )
                session.add(new_entry)

            await session.flush()
            logger.info(f"[RouteCache] Persisted route {idx} to DB ({len(path)} points)")

        await session.commit()
        return paths

    # ------------------------------------------------------------------
    # Status / metrics
    # ------------------------------------------------------------------

    def status(self) -> List[Dict[str, Any]]:
        return [twin.get_status() for twin in self.twins.values()]

    def metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all managed twins."""
        total_packets = sum(t.packets_sent for t in self.twins.values())
        total_errors  = sum(t.error_count for t in self.twins.values())
        total_cmds    = sum(t.commands_processed for t in self.twins.values())
        uptime = 0.0
        if self._service_start_time:
            uptime = (datetime.now(timezone.utc) - self._service_start_time).total_seconds()

        # Fleet-level PPS
        pps = round(total_packets / uptime, 4) if uptime > 0 and total_packets > 0 else 0.0

        # Average latencies across twins that have data
        pipeline_samples = [t.avg_pipeline_latency_ms for t in self.twins.values() if t.avg_pipeline_latency_ms > 0]
        db_samples       = [t.avg_db_latency_ms for t in self.twins.values() if t.avg_db_latency_ms > 0]
        avg_pipeline = round(sum(pipeline_samples) / len(pipeline_samples), 2) if pipeline_samples else 0.0
        avg_db       = round(sum(db_samples) / len(db_samples), 2) if db_samples else 0.0

        return {
            "service_running": self.is_running,
            "uptime_seconds": round(uptime, 1),
            "twins_total": len(self.twins),
            "twins_running": sum(1 for t in self.twins.values() if t.is_running),
            "packets_sent": total_packets,
            "packets_per_second": pps,
            "commands_processed": total_cmds,
            "error_count": total_errors,
            "average_pipeline_latency_ms": avg_pipeline,
            "average_db_latency_ms": avg_db,
        }


# Singleton instance
simulator_service = SimulatorService()
