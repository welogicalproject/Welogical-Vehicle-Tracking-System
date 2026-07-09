#!/usr/bin/env python3
"""
VTS Standalone Telemetry Simulator  —  LOCAL DEVELOPMENT TOOL ONLY
====================================================================

⚠️  PRODUCTION NOTE: This script is NOT required for Render deployment.
    The backend runs the simulator autonomously via SimulatorService inside
    the FastAPI process when SIMULATOR_ENABLED=true is set.

    This file exists solely as a developer convenience:
    • Run it locally to hit a remote or local API over HTTP.
    • Use it for manual load / regression testing against any environment.
    • The ANSI console dashboard is useful for quick visual inspection.

    All vehicle physics (VehicleMotion, GPSSystem, FuelSystem, etc.) are
    imported from app.services.simulator.physics — that package is the
    single source of truth for physics, shared with the in-process backend
    simulator.  No production physics live in this file.

What stays here intentionally (C — dev-only):
    api_request()       HTTP transport for standalone external mode
    VehicleState        Shadow wrapper with console-rendering state
    register_fleet()    REST-based vehicle registration for standalone mode
    acknowledge_command() REST-based command ACK for standalone mode
    render_dashboard()  ANSI console dashboard for local UX
    get_config()        CLI argparse entry point
    main()              Standalone loop
"""

import os
import sys
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# Resolve package paths to import app modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.simulator.physics import (
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
    interpolate_waypoints,
    VEHICLE_PROFILES
)
from app.services.simulator.physics.runtime import RuntimeTracker

# Re-declare local state enum that console rendering expects
from app.services.simulator.physics.motion import VehicleStateEnum

# Global Configuration Placeholders
API_URL = "https://welogical-vehicle-tracking-system.onrender.com"
LOG_LEVEL = "DASHBOARD"
SPEED_MULTIPLIER = 1.0
LOOP_ROUTE = True

# --- HTTP CLIENT WITH AUTO-RETRY ---
def api_request(path, method="GET", data=None, max_retries=None, backoff_seconds=2.0):
    url = f"{API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Connection": "close"
    }
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    attempt = 0
    import json
    while True:
        attempt += 1
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_content = response.read().decode("utf-8")
                return response.status, json.loads(res_content) if res_content else {}
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                err_msg = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_msg)
                except Exception:
                    err_json = err_msg
                return e.code, {"error": err_json}
            status_code = e.code
            err_text = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            status_code = 0
            err_text = str(e.reason)
        except Exception as e:
            status_code = 0
            err_text = str(e)

        if max_retries is not None and attempt >= max_retries:
            return status_code, {"error": f"Failed after {attempt} attempts. Error: {err_text}"}
            
        if LOG_LEVEL != "DASHBOARD":
            print(f"[RETRY] Backend down ({err_text}). Retrying endpoint {path} in {backoff_seconds:.1f}s...")
            
        time.sleep(backoff_seconds)
        backoff_seconds = min(10.0, backoff_seconds * 1.5)

# --- STANDALONE VEHICLE STATE WRAPPER ---
class VehicleState:
    """
    Virtual Digital Twin encapsulating all simulated hardware, vehicle,
    and environmental subsystems. Kept in standalone script for console and REST capabilities.
    """
    def __init__(self, device_uid, waypoints, send_interval, speed_multiplier, loop_route, index=0, capacity=60.0):
        self.device_uid = device_uid
        self.vehicle_name = f"Simulated {device_uid}"
        self.vehicle_type = "Truck" if "DEMO" in device_uid else "Car"
        self.alt_base = 35.0
        
        self.db_id = None
        self.stopped_by_immobilizer = False
        self.send_interval = send_interval
        self.speed_multiplier = speed_multiplier
        self.loop_route = loop_route
        self.completed = False
        
        self.msg_id = 1
        self.packets_sent = 0
        self.last_status = "READY"
        self.last_command = "None"

        # Snap path coordinates
        if len(waypoints) > 50:
            self.path = waypoints
        else:
            status, response = api_request("/routes/snap-path", "POST", {
                "waypoints": waypoints,
                "travel_mode": "DRIVE"
            }, max_retries=3)
            
            if status == 200 and "coordinates" in response:
                self.path = [(c["lat"], c["lng"]) for c in response["coordinates"]]
            else:
                self.path = interpolate_waypoints(waypoints, points_per_segment=50)
                
        # Precompute cumulative distances
        self.distances = [0.0]
        for i in range(1, len(self.path)):
            prev = self.path[i-1]
            curr = self.path[i]
            dist_seg = haversine_distance(prev[0], prev[1], curr[0], curr[1])
            self.distances.append(self.distances[-1] + dist_seg)
        self.total_path_distance = self.distances[-1]
        
        # Start offset
        import random
        self.current_distance_offset = random.uniform(0.0, self.total_path_distance)
        self.forward = random.choice([True, False])
        self.odometer = float(random.randint(150000, 500000))
        self.last_coord = self.path[0]
        
        # Twin Subsystems Initializations
        self.profile = VEHICLE_PROFILES[index % len(VEHICLE_PROFILES)]
        self.power_sys = PowerSystem(self.profile)
        self.motion_sys = VehicleMotion(self.profile, speed_multiplier, loop_route, self.path, self.distances, self.total_path_distance)
        self.gps_sys = GPSSystem(self.last_coord, self.odometer)
        self.io_sys = IOSystem()
        self.fuel_sys = FuelSystem(self.profile, capacity_liters=capacity)
        self.engine_sys = EngineSystem(self.profile)
        self.trans_sys = TransmissionSystem()
        self.rpm_sys = RPMSystem()
        self.runtime_sys = RuntimeTracker()
        self.event_gen = EventGenerator()

        # Output states matching old attributes
        self.speed = 0.0
        self.latitude = self.last_coord[0]
        self.longitude = self.last_coord[1]
        self.heading = 0.0

    @property
    def state(self):
        return self.motion_sys.state

    def step(self):
        if self.completed:
            return None

        # Update Subsystems (Dependency update order)
        self.motion_sys.update_state(self.power_sys.main_power_ok)
        self.power_sys.update(self.motion_sys.state, self.io_sys.ignition)
        self.motion_sys.update_speed(self.stopped_by_immobilizer)
        
        self.speed = self.motion_sys.speed
        
        # GPS and position mapping
        self.gps_sys.update(self.speed, self.motion_sys, self.send_interval)
        self.latitude = self.gps_sys.latitude
        self.longitude = self.gps_sys.longitude
        self.heading = self.gps_sys.heading
        self.odometer = self.gps_sys.odometer
        self.completed = self.motion_sys.completed

        # IO, Engine, Gears, RPM, Fuel & Runtime updates
        self.io_sys.update(self.motion_sys.state, self.fuel_sys.fuel_pct)
        accel = self.speed - self.motion_sys.prev_speed
        
        self.engine_sys.update(self.io_sys.ignition, self.motion_sys.state, self.speed, self.profile.max_speed, accel)
        self.trans_sys.update(self.engine_sys.state, self.speed, self.engine_sys.load, accel)
        self.rpm_sys.update(self.engine_sys.state, self.trans_sys.gear, self.speed, self.engine_sys.load, accel)
        self.fuel_sys.update(self.motion_sys.state, self.speed, self.motion_sys.prev_speed, self.engine_sys.load, self.rpm_sys.rpm, self.send_interval)
        self.runtime_sys.update(self.io_sys.ignition, self.motion_sys.state, self.send_interval)
        
        txn = self.event_gen.determine_txn(self.io_sys.ignition, self.power_sys, self.speed)

        # Assemble packet
        packet = TelemetryBuilder.build_packet(
            uid=self.device_uid,
            msg_id=self.msg_id,
            txn=txn,
            speed=self.speed,
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
        return packet

# --- COMMAND EXECUTION AND ACK ---
def acknowledge_command(vehicle, cmd_name, response_text="Success"):
    if not vehicle.db_id:
        return False
    status_code, response = api_request(f"/commands?vehicle_id={vehicle.db_id}&status=Delivered", "GET", max_retries=2)
    if status_code == 200 and isinstance(response, list):
        matched_cmd = None
        for c in response:
            t = c.get("command_type") or ""
            mapped = False
            if cmd_name == "STOPV" and "immobilize" in t.lower():
                mapped = True
            elif cmd_name == "STARTV" and "restore" in t.lower():
                mapped = True
            elif cmd_name == "PRD" and "interval" in t.lower():
                mapped = True
            elif cmd_name in ("REBOOT", "RESET") and "restart" in t.lower():
                mapped = True
            elif cmd_name == t.upper():
                mapped = True
                
            if mapped:
                matched_cmd = c
                break
                
        if matched_cmd:
            cmd_id = matched_cmd.get("id")
            api_request(f"/commands/{cmd_id}/acknowledge", "PATCH", max_retries=2)
            time.sleep(2)
            comp_status, _ = api_request(
                f"/commands/{cmd_id}/complete?response={urllib.parse.quote(response_text)}",
                "PATCH",
                max_retries=2
            )
            return comp_status == 200
    return False

# --- FLEET REGISTRATION ---
def register_fleet(device_uids):
    status_code, response = api_request("/vehicles", "GET", max_retries=None)
    uid_to_id = {}
    uid_to_capacity = {}
    existing_uids = set()
    if status_code == 200 and isinstance(response, list):
        for v in response:
            existing_uids.add(v.get("device_uid"))
            uid_to_id[v.get("device_uid")] = v.get("id")
            uid_to_capacity[v.get("device_uid")] = v.get("capacity")
            
    for uid in device_uids:
        if uid not in existing_uids:
            reg_payload = {
                "device_uid": uid,
                "vehicle_name": f"Simulated {uid}",
                "vehicle_type": "Truck" if "DEMO" in uid else "Car"
            }
            status_reg, response_reg = api_request("/vehicles", "POST", reg_payload, max_retries=3)
            if status_reg == 201:
                uid_to_id[uid] = response_reg.get("id")
                uid_to_capacity[uid] = response_reg.get("capacity")
        else:
            if LOG_LEVEL != "DASHBOARD":
                print(f"[EXISTS] Vehicle {uid} is already registered.")
    return uid_to_id, uid_to_capacity

# --- GRAPHIC STATUS DISPLAY (DASHBOARD) ---
def render_dashboard(vehicles):
    sys.stdout.write("\033[H\033[J")
    cyan = "\033[96m"
    green = "\033[92m"
    yellow = "\033[93m"
    red = "\033[91m"
    magenta = "\033[95m"
    reset = "\033[0m"
    print(f"{cyan}======================================================================{reset}")
    print(f"{cyan}                     VTS TELEMETRY FLEET SIMULATOR                    {reset}")
    print(f"{cyan}======================================================================{reset}")
    print(f"Backend API URL : {yellow}{API_URL}{reset}")
    print(f"Active Fleet    : {yellow}{len(vehicles)} vehicles{reset}")
    print(f"Speed Multiplier: {yellow}{SPEED_MULTIPLIER}x{reset}")
    print(f"Loop Route      : {yellow}{str(LOOP_ROUTE)}{reset}")
    print(f"{cyan}----------------------------------------------------------------------{reset}")
    
    for v in vehicles:
        if v.completed:
            status_tag = f"{magenta}COMPLETED{reset}"
        elif v.stopped_by_immobilizer:
            status_tag = f"{red}IMMOBILIZED (Stopped){reset}"
        elif "SUCCESS" in v.last_status:
            status_tag = f"{green}{v.last_status}{reset}"
        else:
            status_tag = f"{yellow}{v.last_status}{reset}"
            
        print(f"Vehicle         : {cyan}{v.device_uid}{reset}")
        print(f"Latitude        : {v.latitude:.6f}")
        print(f"Longitude       : {v.longitude:.6f}")
        print(f"Speed           : {v.speed:.1f} km/h")
        print(f"Packets Sent    : {v.packets_sent}")
        print(f"Last Response   : {status_tag}")
        print(f"{cyan}----------------------------------------------------------------------{reset}")
    print("Press Ctrl+C to terminate the simulation flow.")
    sys.stdout.flush()

# --- MAIN CONTROLLER ---
def main():
    global API_URL, LOG_LEVEL, SPEED_MULTIPLIER, LOOP_ROUTE
    config = get_config()
    API_URL = config["API_URL"]
    LOG_LEVEL = config["LOG_LEVEL"]
    SPEED_MULTIPLIER = config["SPEED_MULTIPLIER"]
    LOOP_ROUTE = config["LOOP_ROUTE"]
    
    device_uids = config["DEVICE_UIDS"]
    send_interval = config["SEND_INTERVAL"]
    
    uid_to_id, uid_to_capacity = register_fleet(device_uids)
    
    simulated_vehicles = []
    for i, uid in enumerate(device_uids):
        waypoints = TEMPLATE_ROUTES[i % len(TEMPLATE_ROUTES)]
        capacity = uid_to_capacity.get(uid) or 60.0
        v_state = VehicleState(uid, waypoints, send_interval, SPEED_MULTIPLIER, LOOP_ROUTE, index=i, capacity=capacity)
        v_state.db_id = uid_to_id.get(uid)
        simulated_vehicles.append(v_state)
        
    while True:
        all_completed = True
        for vehicle in simulated_vehicles:
            if vehicle.completed:
                continue
            all_completed = False
            packet = vehicle.step()
            if not packet:
                continue
                
            status_code, response = api_request("/vts/telemetry", "POST", packet, max_retries=3)
            vehicle.packets_sent += 1
            if status_code == 200:
                vehicle.last_status = "SUCCESS (200)"
                vehicle.msg_id += 1
            else:
                vehicle.last_status = f"FAILED ({status_code})"
                
            if status_code == 200 and isinstance(response, dict) and response.get("cmd"):
                cmd = response["cmd"]
                vehicle.last_command = cmd
                parts = cmd.split("=")
                cmd_name = parts[0].upper()
                cmd_val = parts[1] if len(parts) > 1 else None
                
                response_text = "Success"
                if cmd_name == "STOPV":
                    vehicle.stopped_by_immobilizer = True
                    vehicle.speed = 0.0
                    response_text = "Vehicle relay disabled (Immobilized)"
                elif cmd_name == "STARTV":
                    vehicle.stopped_by_immobilizer = False
                    response_text = "Vehicle relay enabled (Restored)"
                elif cmd_name == "PRD" and cmd_val:
                    try:
                        vehicle.send_interval = float(cmd_val)
                        response_text = f"Interval changed to {cmd_val}s"
                    except ValueError:
                        pass
                elif cmd_name in ("REBOOT", "RESET"):
                    vehicle.msg_id = 1
                    vehicle.stopped_by_immobilizer = False
                    response_text = "Device reboot sequence initiated"
                    
                acknowledge_command(vehicle, cmd_name, response_text)
                
        if LOG_LEVEL == "DASHBOARD":
            render_dashboard(simulated_vehicles)
            
        if all_completed:
            break
        time.sleep(send_interval)

def get_config():
    parser = argparse.ArgumentParser(description="VTS Telemetry Simulator Standalone Wrapper")
    parser.add_argument("--url", dest="API_URL", default="https://welogical-vehicle-tracking-system.onrender.com")
    parser.add_argument("--uid", dest="DEVICE_UID", default="ESP32-DEMO-007")
    parser.add_argument("--interval", dest="SEND_INTERVAL", type=float, default=10.0)
    parser.add_argument("--speed-multiplier", "-s", dest="SPEED_MULTIPLIER", type=float, default=1.0)
    parser.add_argument("--no-loop", dest="NO_LOOP", action="store_true", default=False)
    parser.add_argument("--log-level", "-l", dest="LOG_LEVEL", default="DASHBOARD")
    args = parser.parse_args()
    
    device_uids = [u.strip() for u in args.DEVICE_UID.split(",") if u.strip()]
    return {
        "API_URL": args.API_URL,
        "DEVICE_UIDS": device_uids,
        "SEND_INTERVAL": args.SEND_INTERVAL,
        "SPEED_MULTIPLIER": args.SPEED_MULTIPLIER,
        "LOOP_ROUTE": not args.NO_LOOP,
        "LOG_LEVEL": args.LOG_LEVEL
    }

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
