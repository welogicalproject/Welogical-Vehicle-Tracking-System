#!/usr/bin/env python3
"""
VTS Telemetry Simulator
Simulates multiple vehicles executing routes assigned by the backend.
No external dependencies required (uses built-in urllib.request).
"""

import os
import sys
import time
import math
import random
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Force stdout to use UTF-8 encoding in environments with CP1252 defaults (Windows cmd.exe)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- CONFIGURATION FROM ENVIRONMENT VARIABLES / DEFAULTS ---
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")
SEND_INTERVAL_SECONDS = float(os.environ.get("SEND_INTERVAL_SECONDS", "10"))
RUN_FOREVER = os.environ.get("RUN_FOREVER", "True").lower() in ("true", "1", "yes")

# Base vehicle profiles for registration (no waypoints/route coordinates)
DEFAULT_VEHICLES = [
    {"device_uid": "VTS-001", "vehicle_name": "Surat Express", "vehicle_type": "Truck"},
    {"device_uid": "VTS-002", "vehicle_name": "Ahmedabad Shuttle", "vehicle_type": "Bus"},
    {"device_uid": "VTS-003", "vehicle_name": "Vadodara Cargo", "vehicle_type": "Truck"},
    {"device_uid": "VTS-004", "vehicle_name": "Valsad Courier", "vehicle_type": "Car"},
    {"device_uid": "VTS-005", "vehicle_name": "Rajkot Logistics", "vehicle_type": "Van"},
]


# --- GEOGRAPHIC MATH HELPERS ---
def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate direction bearing in degrees from point 1 to point 2."""
    d_lon = math.radians(lon2 - lon1)
    r_lat1 = math.radians(lat1)
    r_lat2 = math.radians(lat2)
    
    y = math.sin(d_lon) * math.cos(r_lat2)
    x = math.cos(r_lat1) * math.sin(r_lat2) - math.sin(r_lat1) * math.cos(r_lat2) * math.cos(d_lon)
    
    brng = math.atan2(y, x)
    brng = math.degrees(brng)
    return float(round((brng + 360) % 360, 1))


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates."""
    r_earth = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


# --- API CLIENT FUNCTIONS (URLLIB) ---
def api_request(path, method="GET", data=None):
    """Make HTTP requests to FastAPI backend with urllib."""
    url = f"{API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Connection": "close"
    }
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_content = response.read().decode("utf-8")
            return response.status, json.loads(res_content) if res_content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
        except Exception:
            err_json = err_msg
        return e.code, {"error": err_json}
    except urllib.error.URLError as e:
        return 0, {"error": str(e.reason)}
    except Exception as e:
        return 0, {"error": str(e)}


# --- REGISTER DEFAULT VEHICLES ---
def register_vehicles():
    """Query vehicles and register missing default profiles."""
    print("[INFO] Checking vehicle registration on backend...")
    status_code, response = api_request("/vehicles", "GET")
    
    uid_to_id = {}
    existing_uids = set()
    if status_code == 200 and isinstance(response, list):
        for v in response:
            existing_uids.add(v.get("device_uid"))
            uid_to_id[v.get("device_uid")] = v.get("id")
    else:
        print(f"[WARN] Failed to list existing vehicles (status: {status_code}). Proceeding anyway.")
        
    for v_meta in DEFAULT_VEHICLES:
        uid = v_meta["device_uid"]
        if uid not in existing_uids:
            print(f"[REGISTER] Registering default profile: {uid} ({v_meta['vehicle_name']})")
            reg_payload = {
                "device_uid": uid,
                "vehicle_name": v_meta["vehicle_name"],
                "vehicle_type": v_meta["vehicle_type"]
            }
            status_reg, response_reg = api_request("/vehicles", "POST", reg_payload)
            if status_reg == 201:
                print(f"[OK] Registered vehicle {uid} successfully.")
                uid_to_id[uid] = response_reg.get("id")
            else:
                print(f"[ERROR] Failed to register vehicle {uid} (status: {status_reg}).")
        else:
            print(f"[EXISTS] Vehicle {uid} is already registered (ID: {uid_to_id[uid]}).")
            
    return uid_to_id


# --- SIMULATOR CONTROLLER ---
class VehicleState:
    """Represents a simulated vehicle execution using routes assigned by the backend."""
    def __init__(self, device_uid, db_id, vehicle_name, vehicle_type):
        self.device_uid = device_uid
        self.db_id = db_id
        self.vehicle_name = vehicle_name
        self.vehicle_type = vehicle_type
        
        self.stopped_by_immobilizer = False
        self.send_interval = SEND_INTERVAL_SECONDS
        
        # Route Properties (Loaded dynamically from the backend)
        self.route_id = None
        self.route_status = None
        self.path = []  # Ordered list of (lat, lon) coordinates
        self.current_index = 0
        
        # Initial odometer & message counters
        self.odometer = float(random.randint(150000, 500000))
        self.msg_id = 1
        self.last_coord = (0.0, 0.0)
        self.speed = 0.0  # km/h
        self.stop_ticks = 0

    def query_assigned_route(self):
        """Query the backend to check if an active route has been assigned to this vehicle."""
        if not self.db_id:
            return False

        status, response = api_request(f"/vehicles/{self.db_id}/assigned-route", "GET")
        if status == 200 and "id" in response:
            route_id = response["id"]
            status_str = response.get("status", "Pending")
            
            # Skip if it is the same completed route we already finished
            if route_id == self.route_id and self.route_status == "Completed":
                return False

            # Load the coordinates and initialize index
            points = response.get("points", [])
            # Sort by sequence number to ensure correct path ordering
            sorted_points = sorted(points, key=lambda x: x.get("sequence_number", 0))
            
            self.route_id = route_id
            self.route_status = status_str
            self.path = [(pt["latitude"], pt["longitude"]) for pt in sorted_points]
            self.current_index = 0
            if self.path:
                self.last_coord = self.path[0]
            
            print(f"[ROUTE] Loaded route {self.route_id}")
            print(f"[ROUTE] {len(self.path)} coordinates received")
            print(f"[ROUTE] Starting execution")
            
            # If the route status is Assigned or Pending, transition it to Running
            if self.route_status in ["Assigned", "Pending"]:
                trans_status, _ = api_request(f"/routes/{self.route_id}/status", "PATCH", {"status": "Running"})
                if trans_status == 200:
                    self.route_status = "Running"
                    print(f"[ROUTE] [{self.device_uid}] Transitioned route ID {self.route_id} to Running.")
            
            return True
        else:
            # Clear state if no active route is found
            if self.route_id is not None:
                print(f"[ROUTE] [{self.device_uid}] Active route removed or unassigned from vehicle.")
                self.route_id = None
                self.route_status = None
                self.path = []
                self.current_index = 0
            return False

    def step(self):
        """Advances state along the path coordinates and returns a VTSPacket payload."""
        # 1. If we don't have an active running route, try to fetch one
        if not self.path or self.route_status == "Completed":
            self.query_assigned_route()
            
        if not self.path or self.route_status == "Completed":
            # No path coordinates or already completed; do not move
            self.speed = 0.0
            return None

        # 2. Get current position coordinate from route path
        curr_coord = self.path[self.current_index]
        
        # Calculate distance and bearing from last position to compute speed/direction
        if self.current_index > 0:
            dist_m = haversine_distance(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
            # Speed approximation in km/h based on interval duration
            self.speed = (dist_m / self.send_interval) * 3.6
            self.speed = min(120.0, max(0.0, self.speed)) # Cap speed
            self.odometer += dist_m
            
            if dist_m > 0.1:
                direction = calculate_bearing(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
            else:
                direction = 0.0
        else:
            self.speed = 0.0
            direction = 0.0

        # Handle immobilizer overrides
        if self.stopped_by_immobilizer:
            self.speed = 0.0
        # Altitude and Satellites variation
        altitude = 25.0 + random.uniform(-2.5, 2.5)
        satellites = random.randint(9, 15)
        ign = 1 if self.speed > 0 or self.current_index < len(self.path) - 1 else 0

        # Construct VTS telemetry schema packet
        packet = {
            "uid": self.device_uid,
            "info": {
                "dt": int(time.time()),
                "txn": "E" if self.speed > 0 else "A",
                "msgkey": 0,
                "msgid": self.msg_id,
                "cmdkey": "",
                "cmdval": ""
            },
            "gps": {
                "fix": "A",
                "loc": [float(round(curr_coord[0], 6)), float(round(curr_coord[1], 6))],
                "speed": float(round(self.speed, 2)),
                "sat": satellites,
                "alt": float(round(altitude, 1)),
                "dir": direction,
                "odo": float(round(self.odometer, 1))
            },
            "io": {
                "box": 0,
                "ign": ign,
                "gpi": 0,
                "status": 0,
                "analog": [12100, 4800]
            },
            "pwr": {
                "main": 1,
                "batt": 1,
                "volt": 4180.0,
                "mvolt": 13.8
            },
            "dbg": {
                "status": [1, 0],
                "ver": ["v1.0.2", "h1.1.0"],
                "lib": "VTSSim-v1.0"
            }
        }
        
        # Print progression log
        print(f"[GPS] Point {self.current_index + 1}/{len(self.path)}")

        self.msg_id += 1
        self.last_coord = curr_coord
        
        # Advance index to the next coordinate point
        self.current_index += 1
        if self.current_index >= len(self.path):
            # Route completed!
            self.route_status = "Completed"
            print(f"[ROUTE] Completed")
            # Report Completion status to the backend
            api_request(f"/routes/{self.route_id}/status", "PATCH", {"status": "Completed"})

        return packet


# --- MAIN LOOP ---
def main():
    print("=" * 60)
    print("[START] VTS Telemetry Simulator Starting...")
    print(f"Backend API URL: {API_URL}")
    print(f"Send Interval: {SEND_INTERVAL_SECONDS} seconds")
    print(f"Mode: Backend Managed Routes (Continuous Listening)")
    print("=" * 60)
    
    # 1. Register default vehicles and build uid-to-id map
    uid_to_id = register_vehicles()
    
    # 2. Instantiate vehicles simulation state
    simulated_vehicles = []
    for meta in DEFAULT_VEHICLES:
        uid = meta["device_uid"]
        db_id = uid_to_id.get(uid)
        state = VehicleState(
            device_uid=uid,
            db_id=db_id,
            vehicle_name=meta["vehicle_name"],
            vehicle_type=meta["vehicle_type"]
        )
        # Attempt to load route immediately
        state.query_assigned_route()
        simulated_vehicles.append(state)
    
    print("\n[LOOP] Starting telemetry transmission loop. Press Ctrl+C to terminate.\n")
    
    while True:
        for vehicle in simulated_vehicles:
            packet = vehicle.step()
            uid = vehicle.device_uid
            cyan = "\033[96m"
            green = "\033[92m"
            yellow = "\033[93m"
            red = "\033[91m"
            reset = "\033[0m"

            if packet is None:
                # No active route assigned
                print(f"[{cyan}{uid}{reset}] {yellow}Idle - No active route assigned. Waiting...{reset}")
                continue
            
            # Send packet via POST
            status_code, response = api_request("/vts/telemetry", "POST", packet)
            
            lat, lon = packet["gps"]["loc"]
            speed = packet["gps"]["speed"]
            msgid = packet["info"]["msgid"]
            
            if status_code == 200:
                status_str = f"{green}SUCCESS (200){reset}"
            else:
                err_text = response.get("error", "Unknown error")
                status_str = f"{red}FAILED ({status_code}) - {err_text}{reset}"
                
            print(f"[{cyan}{uid}{reset}] Sent packet #{msgid:04d} | Speed: {speed:5.1f} km/h | Coords: {lat:.6f},{lon:.6f} | Status: {status_str}")
            
            # Check if command is returned in response
            if status_code == 200 and isinstance(response, dict) and response.get("cmd"):
                cmd = response["cmd"]
                print(f"[{cyan}{uid}{reset}] COMMAND RECEIVED: {green}{cmd}{reset}")
                
                # Parse command parameters
                parts = cmd.split("=")
                cmd_name = parts[0].upper()
                
                if cmd_name == "STOPV":
                    vehicle.stopped_by_immobilizer = True
                    vehicle.speed = 0.0
                    print(f"[{cyan}{uid}{reset}] Hardware state: Immobilizer ENGAGED.")
                elif cmd_name == "STARTV":
                    vehicle.stopped_by_immobilizer = False
                    print(f"[{cyan}{uid}{reset}] Hardware state: Immobilizer DISENGAGED.")
            
        # Pause before next tick
        time.sleep(SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] Telemetry Simulator stopped by user.")
        sys.exit(0)
