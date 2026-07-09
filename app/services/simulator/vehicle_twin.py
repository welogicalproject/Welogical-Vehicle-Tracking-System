import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.services.simulator.physics import (
    VEHICLE_PROFILES,
    TEMPLATE_ROUTES,
    VehicleMotion,
    PowerSystem,
    EngineSystem,
    TransmissionSystem,
    RPMSystem,
    FuelSystem,
    GPSSystem,
    IOSystem,
    EventGenerator,
    TelemetryBuilder,
    haversine_distance,
    interpolate_waypoints
)

logger = logging.getLogger("vts.simulator")


class VehicleTwin:
    """
    Virtual Digital Twin encapsulating all simulated hardware, vehicle,
    and environmental subsystems. Keeps the physical model in sync and serializes
    to a standard Telemetry Specification v2 payload on step().

    Accepts an optional pre-computed path (list of (lat, lon) tuples) and an
    optional db_vehicle_id so SimulatorService can reconnect to an existing DB
    record without duplicating vehicle rows.
    """

    def __init__(
        self,
        device_uid: str,
        send_interval: float = 10.0,
        speed_multiplier: float = 1.0,
        loop_route: bool = True,
        index: int = 0,
        path: Optional[List[Tuple[float, float]]] = None,
        db_vehicle_id: Optional[int] = None,
        vehicle_name: Optional[str] = None,
        vehicle_type: Optional[str] = None,
    ):
        self.device_uid: str = device_uid
        self.send_interval: float = send_interval
        self.speed_multiplier: float = speed_multiplier
        self.loop_route: bool = loop_route
        self.is_running: bool = False
        self.start_time: Optional[datetime] = None
        self.last_tick_time: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None

        # Persistent DB identity — set by SimulatorService on reconnect
        self.db_vehicle_id: Optional[int] = db_vehicle_id
        self.vehicle_name: str = vehicle_name or f"Simulated {device_uid}"
        self.vehicle_type: str = vehicle_type or ("Truck" if "DEMO" in device_uid else "Car")

        self.alt_base = random.choice([15.0, 39.0, 53.0, 128.0])
        self.stopped_by_immobilizer = False
        self.completed = False
        self.msg_id = 1
        self.latest_packet: Dict[str, Any] = {}

        # Metrics counters
        self.packets_sent: int = 0
        self.error_count: int = 0
        self.commands_processed: int = 0
        self.events_generated: int = 0
        self.notifications_generated: int = 0
        self._pipeline_latency_samples: List[float] = []  # ms, rolling window 50
        self._db_latency_samples: List[float] = []        # ms, rolling window 50

        # Resolve path: use supplied path or fall back to interpolated template
        if path and len(path) > 1:
            self.path = path
        else:
            waypoints = TEMPLATE_ROUTES[index % len(TEMPLATE_ROUTES)]
            self.path = interpolate_waypoints(waypoints, points_per_segment=50)

        # Precompute cumulative distances along the segment path
        self.distances = [0.0]
        for i in range(1, len(self.path)):
            prev = self.path[i - 1]
            curr = self.path[i]
            dist_seg = haversine_distance(prev[0], prev[1], curr[0], curr[1])
            self.distances.append(self.distances[-1] + dist_seg)
        self.total_path_distance = self.distances[-1]

        # Simulator State Persistence: Bootstrap from last recorded position
        last_latitude: Optional[float] = None
        last_longitude: Optional[float] = None
        last_speed: float = 0.0
        last_odometer: float = float(random.randint(150000, 500000))
        last_ign: int = 0

        if db_vehicle_id is not None:
            try:
                # Query the latest recorded location synchronously or using context managers
                from app.database import SessionLocal
                with SessionLocal() as session:
                    from app.models.location import Location
                    from sqlalchemy import select
                    stmt = select(Location).where(Location.vehicle_id == db_vehicle_id).order_by(Location.timestamp.desc()).limit(1)
                    loc_res = session.execute(stmt).scalars().first()
                    if loc_res:
                        last_latitude = loc_res.latitude
                        last_longitude = loc_res.longitude
                        last_speed = loc_res.speed
                        if loc_res.extra_data and "gps" in loc_res.extra_data:
                            last_odometer = loc_res.extra_data["gps"].get("odo", last_odometer)
                        if loc_res.extra_data and "io" in loc_res.extra_data:
                            last_ign = loc_res.extra_data["io"].get("ign", 0)
            except Exception as e:
                logger.error(f"[Persistence] Failed to load last state for twin {device_uid}: {e}")

        # Find closest waypoint segment to snap to last position to prevent discontinuities
        start_offset = 0.0
        forward_dir = True
        
        if last_latitude is not None and last_longitude is not None:
            # Snap to closest point on self.path to determine offset
            min_dist = float("inf")
            closest_idx = 0
            for i, pt in enumerate(self.path):
                d = haversine_distance(last_latitude, last_longitude, pt[0], pt[1])
                if d < min_dist:
                    min_dist = d
                    closest_idx = i
            
            # Audit deviation limits
            if min_dist > 100.0:
                logger.warning(
                    f"[Persistence] Snap distance ({min_dist:.1f}m) exceeds 100m limit for twin {device_uid}. "
                    f"Previous waypoint: ({last_latitude:.6f}, {last_longitude:.6f}), "
                    f"Restored waypoint: ({self.path[closest_idx][0]:.6f}, {self.path[closest_idx][1]:.6f}). "
                    f"Reason for fallback: To prevent route teleportation, snapping to closest valid waypoint but forcing starting coordinates to last known coordinates."
                )
                # Force starting coordinate exactly to previous position to maintain complete continuity
                start_pt = (last_latitude, last_longitude)
            else:
                logger.info(
                    f"[Persistence] Snapped twin {device_uid} successfully. "
                    f"Previous waypoint: ({last_latitude:.6f}, {last_longitude:.6f}), "
                    f"Restored waypoint: ({self.path[closest_idx][0]:.6f}, {self.path[closest_idx][1]:.6f}). "
                    f"Distance between previous and restored position: {min_dist:.1f}m"
                )
                start_pt = self.path[closest_idx]

            start_offset = self.distances[closest_idx]
        else:
            # First boot fallback: random cruising offset
            start_offset = random.uniform(0.0, self.total_path_distance)
            forward_dir = random.choice([True, False])
            start_pt = self.path[0]

        # Twin Subsystems Initializations
        self.profile = VEHICLE_PROFILES[index % len(VEHICLE_PROFILES)]
        self.power_sys = PowerSystem(self.profile)
        self.motion_sys = VehicleMotion(
            self.profile, self.speed_multiplier, self.loop_route,
            self.path, self.distances, self.total_path_distance
        )
        self.motion_sys.current_distance_offset = start_offset
        self.motion_sys.forward = forward_dir
        self.motion_sys.speed = last_speed

        self.gps_sys = GPSSystem(start_pt, last_odometer)
        self.io_sys = IOSystem()
        self.io_sys.ignition = last_ign
        self.fuel_sys = FuelSystem(self.profile, capacity_liters=self.profile.fuel_capacity)
        self.engine_sys = EngineSystem(self.profile)
        self.trans_sys = TransmissionSystem()
        self.rpm_sys = RPMSystem()
        from app.services.simulator.physics.runtime import RuntimeTracker
        self.runtime_sys = RuntimeTracker()
        self.event_gen = EventGenerator()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self.is_running:
            return
        logger.info(f"Starting twin {self.device_uid}")
        self.is_running = True
        self.start_time = datetime.now(timezone.utc)
        self.last_tick_time = self.start_time
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Twin started successfully.")
        logger.info(f"Started VehicleTwin {self.device_uid} (db_id={self.db_vehicle_id})")

    async def stop(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(f"VehicleTwin {self.device_uid} stopped")

    def set_custom_route(self, route_coords: List[Tuple[float, float]]):
        """Dynamically override the current route path and reset motion/GPS state."""
        if not route_coords or len(route_coords) < 2:
            raise ValueError("Route must contain at least 2 coordinate pairs.")
        self.path = route_coords
        
        # Precompute cumulative distances along the segment path
        self.distances = [0.0]
        for i in range(1, len(self.path)):
            prev = self.path[i - 1]
            curr = self.path[i]
            dist_seg = haversine_distance(prev[0], prev[1], curr[0], curr[1])
            self.distances.append(self.distances[-1] + dist_seg)
        self.total_path_distance = self.distances[-1]

        # Reset subsystems with new path
        self.motion_sys.waypoints = self.path
        self.motion_sys.distances = self.distances
        self.motion_sys.total_path_distance = self.total_path_distance
        self.motion_sys.current_distance_offset = 0.0  # start from origin
        self.motion_sys.forward = True
        self.motion_sys.completed = False
        
        self.gps_sys.latitude = self.path[0][0]
        self.gps_sys.longitude = self.path[0][1]
        self.gps_sys.last_coord = self.path[0]
        self.gps_sys.heading = 0.0
        self.completed = False
        
        logger.info(f"VehicleTwin {self.device_uid} assigned new custom route of {len(self.path)} points ({self.total_path_distance:.1f} meters)")

    # ------------------------------------------------------------------
    # Physics Step
    # ------------------------------------------------------------------

    def step(self) -> Optional[Dict[str, Any]]:
        if self.completed:
            return None

        # Update Subsystems (dependency order matters)
        self.motion_sys.update_state(self.power_sys.main_power_ok)
        self.power_sys.update(self.motion_sys.state, self.io_sys.ignition)
        self.motion_sys.update_speed(self.stopped_by_immobilizer)

        speed = self.motion_sys.speed

        # GPS and position mapping
        self.gps_sys.update(speed, self.motion_sys, self.send_interval)
        self.completed = self.motion_sys.completed

        # IO, Engine, Gears, RPM, Fuel & Runtime updates
        self.io_sys.update(self.motion_sys.state, self.fuel_sys.fuel_pct)
        accel = speed - self.motion_sys.prev_speed

        self.engine_sys.update(self.io_sys.ignition, self.motion_sys.state, speed, self.profile.max_speed, accel)
        self.trans_sys.update(self.engine_sys.state, speed, self.engine_sys.load, accel)
        self.rpm_sys.update(self.engine_sys.state, self.trans_sys.gear, speed, self.engine_sys.load, accel)
        self.fuel_sys.update(self.motion_sys.state, speed, self.motion_sys.prev_speed, self.engine_sys.load, self.rpm_sys.rpm, self.send_interval)
        self.runtime_sys.update(self.io_sys.ignition, self.motion_sys.state, self.send_interval)

        txn = self.event_gen.determine_txn(self.io_sys.ignition, self.power_sys, speed)

        # Assemble packet
        packet = TelemetryBuilder.build_packet(
            uid=self.device_uid,
            msg_id=self.msg_id,
            txn=txn,
            speed=speed,
            gps=self.gps_sys,
            io=self.io_sys,
            pwr=self.power_sys,
            fuel=self.fuel_sys,
            engine=self.engine_sys,
            trans=self.trans_sys,
            rpm=self.rpm_sys,
            runtime=self.runtime_sys,
            alt_base=self.alt_base
        )
        self.latest_packet = packet
        self.msg_id += 1
        return packet

    # ------------------------------------------------------------------
    # Main telemetry loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        from app.database import AsyncSessionLocal
        from app.schemas.vts import VTSPacket
        from app.services.telemetry_pipeline import run_synchronous_telemetry_pipeline
        from app.services.background_jobs import run_telemetry_background_job

        while self.is_running:
            tick_start = time.perf_counter()
            try:
                self.last_tick_time = datetime.now(timezone.utc)
                logger.info(f"Twin tick...")
                packet_dict = self.step()
                if packet_dict:
                    packet = VTSPacket(**packet_dict)

                    db_t0 = time.perf_counter()
                    async with AsyncSessionLocal() as session:
                        response_payload, bg_metadata = await run_synchronous_telemetry_pipeline(session, packet)
                    db_elapsed_ms = (time.perf_counter() - db_t0) * 1000.0
                    self._record_db_latency(db_elapsed_ms)

                    if bg_metadata:
                        vehicle_id, device_uid, packet_time, msgid, packet_latency = bg_metadata
                        await run_telemetry_background_job(
                            vehicle_id=vehicle_id,
                            device_uid=device_uid,
                            packet_data=packet.model_dump(),
                            timestamp=packet_time,
                            msgid=msgid,
                            start_time_perf=tick_start,
                            packet_latency=packet_latency
                        )
                        # Sync db_vehicle_id from first successful pipeline if not set
                        if self.db_vehicle_id is None:
                            self.db_vehicle_id = vehicle_id

                        elapsed_ms = (time.perf_counter() - tick_start) * 1000.0
                        self._record_pipeline_latency(elapsed_ms)
                        self.packets_sent += 1
                        logger.info(
                            f"VehicleTwin {self.device_uid} seq={packet.info.msgid} "
                            f"speed={packet.gps.speed:.1f} location stored processing={elapsed_ms:.1f}ms"
                        )

                    if response_payload and "cmd" in response_payload:
                        cmd_id = response_payload.get("cmd_id")
                        cmd_str = response_payload["cmd"]
                        if cmd_id:
                            asyncio.create_task(self._process_command(cmd_id, cmd_str))

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(f"Twin stopped unexpectedly: {e}", exc_info=True)
                logger.error(f"VehicleTwin {self.device_uid} Telemetry pipeline failed: {e}", exc_info=True)
                logger.info(f"VehicleTwin {self.device_uid} error handler: Continuing next tick...")

            await asyncio.sleep(self.send_interval)

    # ------------------------------------------------------------------
    # Command processing — full status lifecycle, zero HTTP
    # ------------------------------------------------------------------

    async def _process_command(self, cmd_id: int, cmd_str: str) -> None:
        """
        Processes an intercepted command, transitioning statuses and executing
        physical state changes. All DB updates go directly via AsyncSessionLocal.
        Zero HTTP loopback.
        """
        from app.database import AsyncSessionLocal
        from app.models.device_command import DeviceCommand
        from app.models.command_log import CommandLog
        from app.services.websocket_manager import ws_manager
        from sqlalchemy import select

        logger.info(f"VehicleTwin {self.device_uid} Received command {cmd_str}")

        async def update_status(
            status_name: str,
            message: str = None,
            response_val: str = None,
            err_msg: str = None,
        ):
            async with AsyncSessionLocal() as session:
                try:
                    stmt = select(DeviceCommand).where(DeviceCommand.id == cmd_id)
                    res = await session.execute(stmt)
                    cmd = res.scalars().first()
                    if cmd:
                        cmd.status = status_name
                        if status_name == "Acknowledged":
                            cmd.acknowledged_at = datetime.utcnow()
                        elif status_name == "Completed":
                            cmd.completed_at = datetime.utcnow()
                            cmd.response = response_val or "Execution success"
                        elif status_name == "Failed":
                            cmd.error_message = err_msg or "Execution failed"

                        log_entry = CommandLog(
                            command_id=cmd_id,
                            vehicle_id=cmd.vehicle_id,
                            status=status_name,  # plain string — column is now String
                            message=message
                        )
                        session.add(log_entry)
                        await session.commit()

                        await ws_manager.broadcast("commands", {
                            "event": f"command_{status_name.lower().replace(' ', '_')}",
                            "command_id": cmd_id,
                            "vehicle_id": cmd.vehicle_id,
                            "status": status_name,
                            "response": cmd.response,
                            "error_message": cmd.error_message
                        })
                except Exception as ex:
                    logger.error(
                        f"Failed to update command {cmd_id} to status={status_name}: {ex}",
                        exc_info=True
                    )

        try:
            # 1. Acknowledged
            logger.info(f"Acknowledged command {cmd_id}")
            await update_status("Acknowledged", "Command acknowledged by simulated vehicle twin.")
            await asyncio.sleep(0.5)

            # 2. Executing (in-flight state)
            logger.info(f"Executing command {cmd_id}")
            await update_status("Executing", "Executing hardware command action.")
            await asyncio.sleep(2.0)

            # Parse and dispatch
            parts = cmd_str.split("=")
            cmd_name = parts[0].strip().upper()
            cmd_val = parts[1].strip() if len(parts) > 1 else None

            response_text = "Success"
            if cmd_name in ("STOPV", "IMMOBILIZE VEHICLE"):
                self.stopped_by_immobilizer = True
                self.motion_sys.speed = 0.0
                response_text = "Vehicle relay disabled (Immobilized)"
            elif cmd_name in ("STARTV", "RESTORE VEHICLE"):
                self.stopped_by_immobilizer = False
                response_text = "Vehicle relay enabled (Restored)"
            elif cmd_name in ("PRD", "CHANGE REPORTING INTERVAL") and cmd_val:
                try:
                    self.send_interval = float(cmd_val)
                    response_text = f"Interval changed to {cmd_val}s"
                except ValueError:
                    raise ValueError(f"Invalid interval value: {cmd_val}")
            elif cmd_name in ("REBOOT", "RESET", "RESTART DEVICE"):
                self.msg_id = 1
                self.stopped_by_immobilizer = False
                response_text = "Device reboot sequence initiated"
            elif cmd_name == "PING":
                response_text = "Pong"
            else:
                raise NotImplementedError(f"Unsupported command action: {cmd_name}")

            # 3. Completed
            logger.info(f"Completed command {cmd_id}")
            await update_status("Completed", "Hardware command completed successfully.", response_val=response_text)
            self.commands_processed += 1

        except Exception as e:
            logger.error(f"Command execution failed on twin {self.device_uid}: {e}", exc_info=True)
            await update_status("Failed", "Hardware command execution failed.", err_msg=str(e))

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    def _record_pipeline_latency(self, ms: float) -> None:
        self._pipeline_latency_samples.append(ms)
        if len(self._pipeline_latency_samples) > 50:
            self._pipeline_latency_samples.pop(0)

    def _record_db_latency(self, ms: float) -> None:
        self._db_latency_samples.append(ms)
        if len(self._db_latency_samples) > 50:
            self._db_latency_samples.pop(0)

    @property
    def avg_pipeline_latency_ms(self) -> float:
        if not self._pipeline_latency_samples:
            return 0.0
        return round(sum(self._pipeline_latency_samples) / len(self._pipeline_latency_samples), 2)

    @property
    def avg_db_latency_ms(self) -> float:
        if not self._db_latency_samples:
            return 0.0
        return round(sum(self._db_latency_samples) / len(self._db_latency_samples), 2)

    @property
    def packets_per_second(self) -> float:
        uptime = self.uptime_seconds
        if uptime <= 0 or self.packets_sent == 0:
            return 0.0
        return round(self.packets_sent / uptime, 4)

    @property
    def uptime_seconds(self) -> float:
        if not self.is_running or not self.start_time:
            return 0.0
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    # ------------------------------------------------------------------
    # Status / introspection
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        task_alive = self._task is not None and not self._task.done()
        return {
            "vehicle_uid": self.device_uid,
            "vehicle_name": self.vehicle_name,
            "vehicle_type": self.vehicle_type,
            "db_vehicle_id": self.db_vehicle_id,
            "running": self.is_running,
            "task_alive": task_alive,
            "task_id": str(id(self._task)) if self._task else None,
            "last_tick": self.last_tick_time.isoformat() if self.last_tick_time else None,
            "uptime": round(self.uptime_seconds, 1),
            "packets_sent": self.packets_sent,
            "packets_per_second": self.packets_per_second,
            "commands_processed": self.commands_processed,
            "error_count": self.error_count,
            "avg_pipeline_latency_ms": self.avg_pipeline_latency_ms,
            "avg_db_latency_ms": self.avg_db_latency_ms,
        }
