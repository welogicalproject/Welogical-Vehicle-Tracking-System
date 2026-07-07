#!/usr/bin/env python3
"""
VTS Telemetry Simulator
Simulates multiple vehicles sending live telemetry packets to the VTS backend API.
Supports route replay, command execution, auto-registration, and live status dashboard.
No external dependencies required (uses built-in standard libraries).
"""

import os
import sys
import time
import math
import random
import json
import argparse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Force stdout to use UTF-8 encoding in environments with CP1252 defaults (Windows cmd.exe)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Global Configuration Placeholder (resolved dynamically in main)
API_URL = "https://welogical-vehicle-tracking-system.onrender.com"
LOG_LEVEL = "DASHBOARD"
SPEED_MULTIPLIER = 1.0
LOOP_ROUTE = True

# --- DETAILED GUJARAT TEMPLATE ROUTES (FALLBACKS) ---
TEMPLATE_ROUTES = [
    # Route 1: Surat Center to Kim
    [
        (21.1702, 72.8311),  # Surat Center
        (21.2100, 72.8550),  # Adajan
        (21.2600, 72.8900),  # Amroli
        (21.3200, 72.9300),  # Sayan
        (21.3900, 72.9700),  # Kim
    ],
    # Route 2: Ahmedabad Center to Kanbha
    [
        (23.0225, 72.5714),  # Ahmedabad Center
        (23.0550, 72.6000),  # Naroda
        (23.1000, 72.6400),  # Kathwada
        (23.1600, 72.6900),  # Singarwa
        (23.2200, 72.7400),  # Kanbha
    ],
    # Route 3: Vadodara Center to Vasad
    [
        (22.3072, 73.1812),  # Vadodara Center
        (22.3400, 73.2100),  # Sama
        (22.3900, 73.2500),  # Channi
        (22.4400, 73.2900),  # Ranoli
        (22.5000, 73.3400),  # Vasad
    ],
    # Route 4: Valsad Center to Navsari
    [
        (20.5993, 72.9342),  # Valsad Center
        (20.6300, 72.9600),  # Dungri
        (20.6800, 73.0000),  # Bilimora
        (20.7300, 73.0400),  # Amalsad
        (20.7900, 73.0900),  # Navsari
    ],
    # Route 5: Rajkot Center to Wankaner
    [
        (22.3039, 70.8022),  # Rajkot Center
        (22.3350, 70.8300),  # Madhapar
        (22.3800, 70.8700),  # Shapar
        (22.4300, 70.9100),  # Kuvadva
        (22.4900, 70.9600),  # Wankaner
    ]
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

# --- CONFIG AND FILE LOADERS ---
def load_dotenv(filepath):
    """Zero-dependency parser for .env files."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = val
        except Exception as e:
            print(f"[WARN] Failed to read environment file {filepath}: {e}")

def load_route_from_file(filepath):
    """Loads waypoints list from GPX, CSV, or JSON route files."""
    if not os.path.exists(filepath):
        return None
        
    ext = os.path.splitext(filepath)[1].lower()
    waypoints = []
    
    try:
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, list) and len(item) >= 2:
                        waypoints.append((float(item[0]), float(item[1])))
                    elif isinstance(item, dict):
                        lat = item.get("lat") or item.get("latitude")
                        lon = item.get("lon") or item.get("lng") or item.get("longitude")
                        if lat is not None and lon is not None:
                            waypoints.append((float(lat), float(lon)))
        elif ext == ".csv":
            import csv
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = [h.lower() for h in reader.fieldnames] if reader.fieldnames else []
                lat_col = next((h for h in headers if "lat" in h), None)
                lon_col = next((h for h in headers if "lon" in h or "lng" in h), None)
                
                if lat_col and lon_col:
                    orig_lat_col = reader.fieldnames[headers.index(lat_col)]
                    orig_lon_col = reader.fieldnames[headers.index(lon_col)]
                    for row in reader:
                        waypoints.append((float(row[orig_lat_col]), float(row[orig_lon_col])))
                else:
                    f.seek(0)
                    row_reader = csv.reader(f)
                    for row in row_reader:
                        if row and any(c.isalpha() for c in row[0]):
                            continue  # Skip header
                        if len(row) >= 2:
                            try:
                                waypoints.append((float(row[0]), float(row[1])))
                            except ValueError:
                                continue
        elif ext in (".gpx", ".xml"):
            tree = ET.parse(filepath)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"
            
            for trkpt in root.findall(f".//{ns}trkpt"):
                lat = trkpt.get("lat")
                lon = trkpt.get("lon")
                if lat is not None and lon is not None:
                    waypoints.append((float(lat), float(lon)))
            if not waypoints:
                for wpt in root.findall(f".//{ns}wpt"):
                    lat = wpt.get("lat")
                    lon = wpt.get("lon")
                    if lat is not None and lon is not None:
                        waypoints.append((float(lat), float(lon)))
                        
        if waypoints:
            return waypoints
    except Exception as e:
        print(f"[ERROR] Failed to load route file {filepath}: {e}")
    return None

def find_local_route_files():
    """Locates any JSON, CSV, or GPX files in the local routes folder."""
    routes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes")
    if not os.path.exists(routes_dir):
        return []
    files = []
    for f in os.listdir(routes_dir):
        if f.lower().endswith((".json", ".csv", ".gpx")):
            files.append(os.path.join(routes_dir, f))
    return sorted(files)

# --- HTTP CLIENT WITH AUTO-RETRY ---
def api_request(path, method="GET", data=None, max_retries=None, backoff_seconds=2.0):
    """
    Make HTTP requests to FastAPI backend with urllib.
    Automatically retries on connection failure (status 0) or server errors (5xx).
    If max_retries is None, retries indefinitely (helps with Render startup cold-starts).
    """
    url = f"{API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Connection": "close"
    }
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_content = response.read().decode("utf-8")
                return response.status, json.loads(res_content) if res_content else {}
        except urllib.error.HTTPError as e:
            # 4xx Client errors represent bad request schemas or validation errors - do not retry
            if 400 <= e.code < 500:
                err_msg = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_msg)
                except Exception:
                    err_json = err_msg
                return e.code, {"error": err_json}
            # 5xx Server errors - retry
            status_code = e.code
            err_text = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            # Network offline / host not reachable
            status_code = 0
            err_text = str(e.reason)
        except Exception as e:
            status_code = 0
            err_text = str(e)

        # Evaluate retry bounds
        if max_retries is not None and attempt >= max_retries:
            return status_code, {"error": f"Failed after {attempt} attempts. Error: {err_text}"}
            
        if LOG_LEVEL != "DASHBOARD":
            print(f"[RETRY] Backend down ({err_text}). Retrying endpoint {path} in {backoff_seconds:.1f}s...")
            
        time.sleep(backoff_seconds)
        backoff_seconds = min(10.0, backoff_seconds * 1.5)

# --- SIMULATION STATE ---
class VehicleState:
    def __init__(self, device_uid, waypoints, send_interval, speed_multiplier, loop_route):
        self.device_uid = device_uid
        self.vehicle_name = f"Simulated {device_uid}"
        self.vehicle_type = "Truck" if "DEMO" in device_uid else "Car"
        self.alt_base = random.choice([15.0, 39.0, 53.0, 128.0])
        
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
        
        # Load snapped path coordinates from the backend router
        if len(waypoints) > 50:
            self.path = waypoints
            if LOG_LEVEL != "DASHBOARD":
                print(f"[{self.device_uid}] Loaded high-density route file directly with {len(self.path)} coordinates.")
        else:
            # Attempt to fetch snapped route from backend (indefinite retry during setup)
            if LOG_LEVEL != "DASHBOARD":
                print(f"[{self.device_uid}] Requesting road snapping from server...")
            status, response = api_request("/routes/snap-path", "POST", {
                "waypoints": waypoints,
                "travel_mode": "DRIVE"
            }, max_retries=3)
            
            if status == 200 and "coordinates" in response:
                self.path = [(c["lat"], c["lng"]) for c in response["coordinates"]]
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[{self.device_uid}] Route snapped successfully. {len(self.path)} points resolved.")
            else:
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[{self.device_uid}] Route snapping failed. Performing linear interpolation.")
                self.path = interpolate_waypoints(waypoints, points_per_segment=50)
                
        # Precompute cumulative distances along the segment path
        self.distances = [0.0]
        for i in range(1, len(self.path)):
            prev = self.path[i-1]
            curr = self.path[i]
            dist_seg = haversine_distance(prev[0], prev[1], curr[0], curr[1])
            self.distances.append(self.distances[-1] + dist_seg)
        self.total_path_distance = self.distances[-1]
        
        # Start at a random offset along the path
        self.current_distance_offset = random.uniform(0.0, self.total_path_distance)
        self.forward = random.choice([True, False])
        self.odometer = float(random.randint(150000, 500000))
        self.last_coord = self.path[0]
        self.speed = 50.0  # km/h
        self.stop_ticks = 0
        self.latitude = 0.0
        self.longitude = 0.0
        self.heading = 0.0

    def step(self):
        """Advances state and returns a VTSPacket payload."""
        if self.completed:
            return None
            
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
            # Calculate distance travelled factoring in the speed multiplier
            travelled = (self.speed * self.speed_multiplier * 1000.0 / 3600.0) * self.send_interval
            if self.forward:
                self.current_distance_offset += travelled
                if self.current_distance_offset >= self.total_path_distance:
                    if self.loop_route:
                        self.current_distance_offset = self.total_path_distance - (self.current_distance_offset - self.total_path_distance)
                        self.forward = False
                    else:
                        self.current_distance_offset = self.total_path_distance
                        self.completed = True
                        self.speed = 0.0
            else:
                self.current_distance_offset -= travelled
                if self.current_distance_offset <= 0.0:
                    if self.loop_route:
                        self.current_distance_offset = abs(self.current_distance_offset)
                        self.forward = True
                    else:
                        self.current_distance_offset = 0.0
                        self.completed = True
                        self.speed = 0.0
                        
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
        
        # Odometer calculation
        self.odometer += travelled
        
        # Direction / Bearing calculation
        dist = haversine_distance(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        if dist > 0.1:
            direction = calculate_bearing(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        else:
            direction = 0.0
            
        self.last_coord = curr_coord
        self.latitude = float(round(curr_coord[0], 6))
        self.longitude = float(round(curr_coord[1], 6))
        self.heading = direction
        
        altitude = self.alt_base + random.uniform(-2.5, 2.5)
        satellites = random.randint(9, 15)
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
        
        return packet

# --- COMMAND EXECUTION AND ACK ---
def acknowledge_command(vehicle, cmd_name):
    """Finds command record in SENT status on backend and marks it EXECUTED."""
    if not vehicle.db_id:
        return False
        
    status_code, response = api_request(f"/commands?vehicle_id={vehicle.db_id}&status=SENT", "GET", max_retries=2)
    if status_code == 200 and isinstance(response, list):
        matched_cmd = None
        for c in response:
            if c.get("command_name") == cmd_name:
                matched_cmd = c
                break
                
        if matched_cmd:
            cmd_id = matched_cmd.get("id")
            exec_status_code, _ = api_request(
                f"/commands/{cmd_id}/execute?message=Simulated execution on simulator hardware successful",
                "PUT",
                max_retries=2
            )
            return exec_status_code == 200
    return False

# --- FLEET REGISTRATION ---
def register_fleet(device_uids):
    """Fetches registrations from VTS backend and registers missing devices, returning UID-to-ID mapping."""
    if LOG_LEVEL != "DASHBOARD":
        print("[INFO] Checking vehicle registration on backend...")
    
    # Infinite retry on cold start
    status_code, response = api_request("/vehicles", "GET", max_retries=None)
    
    uid_to_id = {}
    existing_uids = set()
    if status_code == 200 and isinstance(response, list):
        for v in response:
            existing_uids.add(v.get("device_uid"))
            uid_to_id[v.get("device_uid")] = v.get("id")
            
    for uid in device_uids:
        if uid not in existing_uids:
            if LOG_LEVEL != "DASHBOARD":
                print(f"[REGISTER] Registering vehicle {uid} on backend...")
            reg_payload = {
                "device_uid": uid,
                "vehicle_name": f"Simulated {uid}",
                "vehicle_type": "Truck" if "DEMO" in uid else "Car"
            }
            status_reg, response_reg = api_request("/vehicles", "POST", reg_payload, max_retries=3)
            if status_reg == 201:
                uid_to_id[uid] = response_reg.get("id")
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[OK] Registered vehicle {uid} successfully.")
            else:
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[WARN] Auto-registration failed for {uid} (status: {status_reg}). Continuing.")
        else:
            if LOG_LEVEL != "DASHBOARD":
                print(f"[EXISTS] Vehicle {uid} is already registered (DB ID: {uid_to_id[uid]}).")
                
    return uid_to_id

# --- GRAPHIC STATUS DISPLAY (DASHBOARD) ---
def render_dashboard(vehicles):
    """Draws a beautiful, clean status console update screen."""
    # Terminal clear escape code
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
    print(f"Local Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{cyan}----------------------------------------------------------------------{reset}")
    
    for v in vehicles:
        if v.completed:
            status_tag = f"{magenta}COMPLETED{reset}"
        elif v.stopped_by_immobilizer:
            status_tag = f"{red}IMMOBILIZED (Stopped){reset}"
        elif "SUCCESS" in v.last_status:
            status_tag = f"{green}{v.last_status}{reset}"
        elif "FAILED" in v.last_status or "OFFLINE" in v.last_status:
            status_tag = f"{red}{v.last_status}{reset}"
        else:
            status_tag = f"{yellow}{v.last_status}{reset}"
            
        print(f"Vehicle         : {cyan}{v.device_uid}{reset}")
        print(f"Latitude        : {v.latitude:.6f}")
        print(f"Longitude       : {v.longitude:.6f}")
        print(f"Speed           : {v.speed:.1f} km/h")
        print(f"Heading         : {v.heading:.1f}°")
        print(f"Packets Sent    : {v.packets_sent}")
        print(f"Last Response   : {status_tag}")
        print(f"Command Received: {yellow}{v.last_command}{reset}")
        print(f"{cyan}----------------------------------------------------------------------{reset}")
    
    print("Press Ctrl+C to terminate the simulation flow.")
    sys.stdout.flush()

# --- MAIN CONTROLLER ---
def main():
    global API_URL, LOG_LEVEL, SPEED_MULTIPLIER, LOOP_ROUTE
    
    # 1. Fetch CLI and environment config
    config = get_config()
    
    API_URL = config["API_URL"]
    LOG_LEVEL = config["LOG_LEVEL"]
    SPEED_MULTIPLIER = config["SPEED_MULTIPLIER"]
    LOOP_ROUTE = config["LOOP_ROUTE"]
    
    device_uids = config["DEVICE_UIDS"]
    send_interval = config["SEND_INTERVAL"]
    route_files = config["ROUTE_FILES"]
    
    if LOG_LEVEL != "DASHBOARD":
        print("=" * 60)
        print("[START] VTS Telemetry Simulator Starting...")
        print(f"Backend API URL : {API_URL}")
        print(f"Device UID List : {', '.join(device_uids)}")
        print(f"Send Interval   : {send_interval} seconds")
        print(f"Speed Multiplier: {SPEED_MULTIPLIER}x")
        print(f"Loop Route      : {LOOP_ROUTE}")
        print(f"Log Level       : {LOG_LEVEL}")
        print("=" * 60)

    # 2. Register fleet and obtain DB mapping ID
    uid_to_id = register_fleet(device_uids)
    
    # 3. Resolve route files and waypoints
    local_files = find_local_route_files()
    
    simulated_vehicles = []
    for i, uid in enumerate(device_uids):
        waypoints = None
        
        # Priority 1: Specifically passed CLI --route-file matching index
        if i < len(route_files):
            waypoints = load_route_from_file(route_files[i])
            
        # Priority 2: Automatically map file in routes/ folder to vehicle index
        if not waypoints and local_files:
            file_to_load = local_files[i % len(local_files)]
            waypoints = load_route_from_file(file_to_load)
            
        # Priority 3: Built-in route template fallback
        if not waypoints:
            waypoints = TEMPLATE_ROUTES[i % len(TEMPLATE_ROUTES)]
            if LOG_LEVEL != "DASHBOARD":
                print(f"[{uid}] Mapping to fallback route template {i % len(TEMPLATE_ROUTES) + 1}.")
                
        # Initialize vehicle state
        v_state = VehicleState(uid, waypoints, send_interval, SPEED_MULTIPLIER, LOOP_ROUTE)
        v_state.db_id = uid_to_id.get(uid)
        simulated_vehicles.append(v_state)

    if LOG_LEVEL != "DASHBOARD":
        print("\n[LOOP] Starting transmission loop. Press Ctrl+C to terminate.\n")
        
    while True:
        all_completed = True
        
        for vehicle in simulated_vehicles:
            if vehicle.completed:
                continue
            all_completed = False
            
            packet = vehicle.step()
            if not packet:
                continue
                
            # Send packet with retry
            status_code, response = api_request("/vts/telemetry", "POST", packet, max_retries=3)
            
            vehicle.packets_sent += 1
            if status_code == 200:
                vehicle.last_status = "SUCCESS (200)"
                vehicle.msg_id += 1
            else:
                err_text = response.get("error", "Unknown error")
                vehicle.last_status = f"FAILED ({status_code}) - {err_text}"
                
            # Print standard output logs if not in DASHBOARD mode
            if LOG_LEVEL != "DASHBOARD":
                lat, lon = packet["gps"]["loc"]
                speed = packet["gps"]["speed"]
                msgid = packet["info"]["msgid"]
                print(f"[{vehicle.device_uid}] Sent packet #{msgid:04d} | Speed: {speed:5.1f} km/h | Coords: {lat:.6f},{lon:.6f} | Status: {vehicle.last_status}")
                
            # 4. Handle commands returned in HTTP response payload
            if status_code == 200 and isinstance(response, dict) and response.get("cmd"):
                cmd = response["cmd"]
                vehicle.last_command = cmd
                
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[{vehicle.device_uid}] COMMAND RECEIVED: {cmd}")
                    
                parts = cmd.split("=")
                cmd_name = parts[0].upper()
                cmd_val = parts[1] if len(parts) > 1 else None
                
                # Execute simulated action
                if cmd_name == "STOPV":
                    vehicle.stopped_by_immobilizer = True
                    vehicle.speed = 0.0
                elif cmd_name == "STARTV":
                    vehicle.stopped_by_immobilizer = False
                elif cmd_name == "PRD" and cmd_val:
                    try:
                        vehicle.send_interval = float(cmd_val)
                    except ValueError:
                        pass
                elif cmd_name == "REBOOT":
                    vehicle.msg_id = 1
                elif cmd_name == "RESET":
                    vehicle.msg_id = 1
                    vehicle.stopped_by_immobilizer = False
                    
                # Acknowledge execution back to database
                ack_success = acknowledge_command(vehicle, cmd_name)
                if LOG_LEVEL != "DASHBOARD" and ack_success:
                    print(f"[{vehicle.device_uid}] Command {cmd_name} marked EXECUTED on backend.")
                    
        # Update dashboard view if dashboard mode is enabled
        if LOG_LEVEL == "DASHBOARD":
            render_dashboard(simulated_vehicles)
            
        if all_completed:
            if LOG_LEVEL != "DASHBOARD":
                print("\n[OK] All vehicles completed their paths. Exiting.")
            else:
                sys.stdout.write("\nAll vehicles completed. Exiting.\n")
            break
            
        time.sleep(send_interval)

def get_config():
    """Builds config from dotenv files, env variables, and CLI arguments."""
    # Load env files
    search_dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in search_dirs:
        search_dirs.append(parent_dir)
        
    for d in search_dirs:
        load_dotenv(os.path.join(d, ".env"))
        load_dotenv(os.path.join(d, "dashboard", ".env.local"))
        load_dotenv(os.path.join(d, "scripts", "simulator", ".env"))

    # Argument parser
    parser = argparse.ArgumentParser(description="VTS Telemetry Simulator")
    parser.add_argument("--url", dest="API_URL", help="VTS backend URL")
    parser.add_argument("--uid", dest="DEVICE_UID", help="Comma-separated device UID(s)")
    parser.add_argument("--interval", dest="SEND_INTERVAL", type=float, help="Send interval in seconds")
    parser.add_argument("--speed-multiplier", "-s", dest="SPEED_MULTIPLIER", type=float, help="Simulation speed multiplier")
    parser.add_argument("--loop-route", "--loop", dest="LOOP_ROUTE", action="store_true", default=None, help="Loop the route continuously")
    parser.add_argument("--no-loop", dest="NO_LOOP", action="store_true", default=None, help="Do not loop the route")
    parser.add_argument("--route-file", "-r", dest="ROUTE_FILE", help="Comma-separated route file path(s)")
    parser.add_argument("--log-level", "-l", dest="LOG_LEVEL", help="Logging level (DEBUG, INFO, WARN, ERROR, DASHBOARD)")
    
    args = parser.parse_args()

    def resolve(cli_val, env_key, default_val):
        if cli_val is not None:
            return cli_val
        if env_key in os.environ:
            return os.environ[env_key]
        return default_val

    # Resolve variables
    api_url = resolve(args.API_URL, "API_URL", "https://welogical-vehicle-tracking-system.onrender.com").rstrip("/")
    device_uid_str = resolve(args.DEVICE_UID, "DEVICE_UID", "ESP32-DEMO-007")
    device_uids = [u.strip() for u in device_uid_str.split(",") if u.strip()]
    
    interval_str = resolve(args.SEND_INTERVAL, "SEND_INTERVAL", 10.0)
    try:
        send_interval = float(interval_str)
    except ValueError:
        send_interval = 10.0

    speed_mult_str = resolve(args.SPEED_MULTIPLIER, "SPEED_MULTIPLIER", 1.0)
    try:
        speed_multiplier = float(speed_mult_str)
    except ValueError:
        speed_multiplier = 1.0

    # Resolve loop route
    loop_route = True
    if args.NO_LOOP is not None:
        loop_route = False
    elif args.LOOP_ROUTE is not None:
        loop_route = True
    elif "LOOP_ROUTE" in os.environ:
        loop_route = os.environ["LOOP_ROUTE"].lower() in ("true", "1", "yes")

    route_file_str = resolve(args.ROUTE_FILE, "ROUTE_FILE", None)
    route_files = [rf.strip() for rf in route_file_str.split(",") if rf.strip()] if route_file_str else []
    log_level = resolve(args.LOG_LEVEL, "LOG_LEVEL", "DASHBOARD").upper()

    return {
        "API_URL": api_url,
        "DEVICE_UIDS": device_uids,
        "SEND_INTERVAL": send_interval,
        "SPEED_MULTIPLIER": speed_multiplier,
        "LOOP_ROUTE": loop_route,
        "ROUTE_FILES": route_files,
        "LOG_LEVEL": log_level
    }

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\n[STOP] Telemetry Simulator stopped by user.\n")
        sys.exit(0)
