#!/usr/bin/env python3
"""
VTS Telemetry Simulator
Simulates multiple vehicles sending live telemetry packets to the VTS backend API.
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
NUMBER_OF_VEHICLES = int(os.environ.get("NUMBER_OF_VEHICLES", "5"))
SEND_INTERVAL_SECONDS = float(os.environ.get("SEND_INTERVAL_SECONDS", "10"))
PACKETS_PER_VEHICLE = int(os.environ.get("PACKETS_PER_VEHICLE", "100"))
RUN_FOREVER = os.environ.get("RUN_FOREVER", "True").lower() in ("true", "1", "yes")

# Base geographic coordinates and routes for Gujarat cities
VEHICLES_DATA = [
    {
        "device_uid": "VTS-001",
        "vehicle_name": "Surat Express",
        "vehicle_type": "Truck",
        "alt_base": 15.0,
        "waypoints": [
            (21.1702, 72.8311),  # Surat Center
            (21.2100, 72.8550),  # Adajan
            (21.2600, 72.8900),  # Amroli
            (21.3200, 72.9300),  # Sayan
            (21.3900, 72.9700),  # Kim
        ]
    },
    {
        "device_uid": "VTS-002",
        "vehicle_name": "Ahmedabad Shuttle",
        "vehicle_type": "Bus",
        "alt_base": 53.0,
        "waypoints": [
            (23.0225, 72.5714),  # Ahmedabad Center
            (23.0550, 72.6000),  # Naroda
            (23.1000, 72.6400),  # Kathwada
            (23.1600, 72.6900),  # Singarwa
            (23.2200, 72.7400),  # Kanbha
        ]
    },
    {
        "device_uid": "VTS-003",
        "vehicle_name": "Vadodara Cargo",
        "vehicle_type": "Truck",
        "alt_base": 39.0,
        "waypoints": [
            (22.3072, 73.1812),  # Vadodara Center
            (22.3400, 73.2100),  # Sama
            (22.3900, 73.2500),  # Channi
            (22.4400, 73.2900),  # Ranoli
            (22.5000, 73.3400),  # Vasad
        ]
    },
    {
        "device_uid": "VTS-004",
        "vehicle_name": "Valsad Courier",
        "vehicle_type": "Car",
        "alt_base": 12.0,
        "waypoints": [
            (20.5993, 72.9342),  # Valsad Center
            (20.6300, 72.9600),  # Dungri
            (20.6800, 73.0000),  # Bilimora
            (20.7300, 73.0400),  # Amalsad
            (20.7900, 73.0900),  # Navsari
        ]
    },
    {
        "device_uid": "VTS-005",
        "vehicle_name": "Rajkot Logistics",
        "vehicle_type": "Van",
        "alt_base": 128.0,
        "waypoints": [
            (22.3039, 70.8022),  # Rajkot Center
            (22.3350, 70.8300),  # Madhapar
            (22.3800, 70.8700),  # Shapar
            (22.4300, 70.9100),  # Kuvadva
            (22.4900, 70.9600),  # Wankaner
        ]
    }
]

# Limit vehicles based on configuration
VEHICLES_DATA = VEHICLES_DATA[:max(1, min(NUMBER_OF_VEHICLES, len(VEHICLES_DATA)))]

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

def interpolate_waypoints(waypoints, points_per_segment=40):
    """Generate intermediate coordinates between waypoints for smooth movements."""
    full_path = []
    if not waypoints:
        return full_path
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i+1]
        for step in range(points_per_segment):
            alpha = step / points_per_segment
            lat = lat1 + (lat2 - lat1) * alpha
            lon = lon1 + (lon2 - lon1) * alpha
            full_path.append((lat, lon))
    full_path.append(waypoints[-1])
    return full_path

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

# --- REGISTER VEHICLES IF MISSING ---
def register_vehicles():
    """Query vehicles and register missing ones, returning a mapping of device_uid to database ID."""
    print("[INFO] Checking vehicle registration on backend...")
    status_code, response = api_request("/vehicles", "GET")
    
    uid_to_id = {}
    existing_uids = set()
    if status_code == 200 and isinstance(response, list):
        for v in response:
            existing_uids.add(v.get("device_uid"))
            uid_to_id[v.get("device_uid")] = v.get("id")
    else:
        print(f"[WARN] Failed to list existing vehicles (status: {status_code}, error: {response.get('error')}). Proceeding anyway.")
        
    for v_meta in VEHICLES_DATA:
        uid = v_meta["device_uid"]
        if uid not in existing_uids:
            print(f"[REGISTER] Registering vehicle {uid} ({v_meta['vehicle_name']})")
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
                print(f"[ERROR] Failed to register vehicle {uid} (status: {status_reg}, error: {response_reg.get('error')}).")
        else:
            print(f"[EXISTS] Vehicle {uid} is already registered.")
            
    return uid_to_id

# --- SIMULATOR CONTROLLER ---
class VehicleState:
    """Represents a simulated vehicle tracking its current state and position."""
    def __init__(self, meta):
        self.device_uid = meta["device_uid"]
        self.vehicle_name = meta["vehicle_name"]
        self.vehicle_type = meta["vehicle_type"]
        self.alt_base = meta["alt_base"]
        
        self.db_id = None
        self.stopped_by_immobilizer = False
        self.send_interval = SEND_INTERVAL_SECONDS
        
        # Load snapped path coordinates from the backend router
        status, response = api_request("/routes/snap-path", "POST", {
            "waypoints": meta["waypoints"],
            "travel_mode": "DRIVE"
        })
        if status == 200 and "coordinates" in response:
            self.path = [(c["lat"], c["lng"]) for c in response["coordinates"]]
            print(f"[{self.device_uid}] Loaded snapped road path with {len(self.path)} points.")
        else:
            print(f"[{self.device_uid}] Route snapping failed (status: {status}). Falling back to linear interpolation.")
            self.path = interpolate_waypoints(meta["waypoints"], points_per_segment=50)
        
        # Precompute cumulative distances along the segment path list
        self.distances = [0.0]
        for i in range(1, len(self.path)):
            prev = self.path[i-1]
            curr = self.path[i]
            dist_seg = haversine_distance(prev[0], prev[1], curr[0], curr[1])
            self.distances.append(self.distances[-1] + dist_seg)
        self.total_path_distance = self.distances[-1]
        
        # Start at a random distance offset along the path
        self.current_distance_offset = random.uniform(0.0, self.total_path_distance)
        self.forward = random.choice([True, False])
        
        # Initial odometer (random value between 150km and 500km in meters)
        self.odometer = float(random.randint(150000, 500000))
        
        self.msg_id = 1
        self.last_coord = self.path[0]
        self.speed = 50.0  # km/h
        self.stop_ticks = 0

    def step(self):
        """Advances state and returns a VTSPacket payload."""
        # 1. Handle command overrides
        if self.stopped_by_immobilizer:
            self.speed = 0.0
            self.stop_ticks = 0
        else:
            # Simulate traffic light / stop scenario (5% probability of stopping)
            if self.stop_ticks > 0:
                self.stop_ticks -= 1
                self.speed = 0.0
            elif random.random() < 0.05:
                # Stop for 2-3 intervals
                self.stop_ticks = random.randint(2, 3)
                self.speed = 0.0
            else:
                # Fluctuate speed between 35 km/h and 75 km/h
                speed_change = random.uniform(-6, 6)
                self.speed = max(35.0, min(75.0, self.speed + speed_change))
            
        # Move distance offset along the path crawler
        travelled = 0.0
        if self.speed > 0:
            travelled = (self.speed * 1000.0 / 3600.0) * self.send_interval
            if self.forward:
                self.current_distance_offset += travelled
                if self.current_distance_offset >= self.total_path_distance:
                    self.current_distance_offset = self.total_path_distance - (self.current_distance_offset - self.total_path_distance)
                    self.forward = False
            else:
                self.current_distance_offset -= travelled
                if self.current_distance_offset <= 0.0:
                    self.current_distance_offset = abs(self.current_distance_offset)
                    self.forward = True
                    
        # Interpolate coordinates along the segment offset
        idx = 0
        while idx < len(self.distances) - 2 and self.distances[idx+1] < self.current_distance_offset:
            idx += 1
            
        d1 = self.distances[idx]
        d2 = self.distances[idx+1]
        lat1, lon1 = self.path[idx]
        lat2, lon2 = self.path[idx+1]
        segment_dist = d2 - d1
        if segment_dist > 0.001:
            alpha = (self.current_distance_offset - d1) / segment_dist
        else:
            alpha = 0.0
            
        lat = lat1 + (lat2 - lat1) * alpha
        lon = lon1 + (lon2 - lon1) * alpha
        curr_coord = (lat, lon)
        
        # Log simulator engine status details
        print(f"[{self.device_uid}] Engine Status: Snapped Points={len(self.path)}, Coord Index={idx}, Travelled Offset={self.current_distance_offset:.1f} m, Speed={self.speed:.1f} km/h")
        
        # Odometer calculation
        self.odometer += travelled
        
        # Direction / Bearing calculation
        dist = haversine_distance(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        if dist > 0.1:
            direction = calculate_bearing(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        else:
            direction = 0.0
            
        self.last_coord = curr_coord
        
        # Altitude variation
        altitude = self.alt_base + random.uniform(-2.5, 2.5)
        
        # Satellite variation
        satellites = random.randint(9, 15)
        
        # Digital inputs (box state closed, ignition is 1 if speed > 0 else 0)
        ign = 1 if self.speed > 0 else 0
        
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
        
        self.msg_id += 1
        return packet

# --- MAIN LOOP ---
def main():
    print("=" * 60)
    print("[START] VTS Telemetry Simulator Starting...")
    print(f"Backend API URL: {API_URL}")
    print(f"Number of Vehicles: {len(VEHICLES_DATA)}")
    print(f"Send Interval: {SEND_INTERVAL_SECONDS} seconds")
    print(f"Running mode: {'Continuous Loop (Forever)' if RUN_FOREVER else f'{PACKETS_PER_VEHICLE} packets per vehicle'}")
    print("=" * 60)
    
    # 1. Register vehicles and build uid-to-id map
    uid_to_id = register_vehicles()
    
    # 2. Instantiate vehicles simulation state
    simulated_vehicles = []
    for meta in VEHICLES_DATA:
        state = VehicleState(meta)
        state.db_id = uid_to_id.get(meta["device_uid"])
        simulated_vehicles.append(state)
    
    print("\n[LOOP] Starting telemetry transmission loop. Press Ctrl+C to terminate.\n")
    
    packet_count = 0
    while True:
        for vehicle in simulated_vehicles:
            packet = vehicle.step()
            
            # Send packet via POST
            status_code, response = api_request("/vts/telemetry", "POST", packet)
            
            # ANSI log output formatting
            cyan = "\033[96m"
            green = "\033[92m"
            red = "\033[91m"
            reset = "\033[0m"
            
            uid = vehicle.device_uid
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
                print(f"[{cyan}{uid}{reset}] COMMAND RECEIVED FROM SERVER: {green}{cmd}{reset}")
                
                # Parse command parameters
                parts = cmd.split("=")
                cmd_name = parts[0].upper()
                cmd_val = parts[1] if len(parts) > 1 else None
                
                # Simulate device execution overrides
                if cmd_name == "STOPV":
                    vehicle.stopped_by_immobilizer = True
                    vehicle.speed = 0.0
                    print(f"[{cyan}{uid}{reset}] Hardware state: Immobilizer ENGAGED. Speed set to 0.")
                elif cmd_name == "STARTV":
                    vehicle.stopped_by_immobilizer = False
                    print(f"[{cyan}{uid}{reset}] Hardware state: Immobilizer DISENGAGED. Resuming motion.")
                elif cmd_name == "PRD" and cmd_val:
                    try:
                        vehicle.send_interval = float(cmd_val)
                        print(f"[{cyan}{uid}{reset}] Hardware state: Transmit interval adjusted to {cmd_val} seconds.")
                    except ValueError:
                        pass
                elif cmd_name == "REBOOT":
                    vehicle.msg_id = 1
                    print(f"[{cyan}{uid}{reset}] Hardware state: Device rebooting. Message counter reset.")
                elif cmd_name == "RESET":
                    vehicle.msg_id = 1
                    vehicle.stopped_by_immobilizer = False
                    print(f"[{cyan}{uid}{reset}] Hardware state: Factory default settings restored.")
                
                # Query server to retrieve the command database ID to mark it EXECUTED
                if vehicle.db_id:
                    cmd_status_code, cmd_response = api_request(f"/commands?vehicle_id={vehicle.db_id}&status=SENT", "GET")
                    if cmd_status_code == 200 and isinstance(cmd_response, list):
                        # Find the matching command
                        matched_cmd = None
                        for c in cmd_response:
                            if c.get("command_name") == cmd_name:
                                matched_cmd = c
                                break
                        
                        if matched_cmd:
                            cmd_id = matched_cmd.get("id")
                            # Put execute status
                            exec_status_code, _ = api_request(
                                f"/commands/{cmd_id}/execute?message=Simulated execution on virtual hardware successful",
                                "PUT"
                            )
                            if exec_status_code == 200:
                                print(f"[{cyan}{uid}{reset}] Command {cmd_name} (ID: {cmd_id}) execution reported successfully to backend.")
                            else:
                                print(f"[{cyan}{uid}{reset}] FAILED to update command {cmd_name} execution status on backend.")
                        else:
                            print(f"[{cyan}{uid}{reset}] Warning: Delivered command '{cmd_name}' not found in SENT status list.")
            
        packet_count += 1
        if not RUN_FOREVER and packet_count >= PACKETS_PER_VEHICLE:
            print(f"\n[OK] Completed transmission of {PACKETS_PER_VEHICLE} steps. Stopping simulator.")
            break
            
        # Pause before next tick
        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] Telemetry Simulator stopped by user.")
        sys.exit(0)
