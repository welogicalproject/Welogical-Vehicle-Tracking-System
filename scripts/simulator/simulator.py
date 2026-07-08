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
    routes_dir = os.environ.get("ROUTE_DIRECTORY")
    if not routes_dir:
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
## Vehicle State definitions
class VehicleStateEnum:
    PARKED = "Parked"
    IDLE = "Idle"
    DRIVING = "Driving"
    STOPPED_IN_TRAFFIC = "Stopped in Traffic"
    POWER_FAILURE = "Power Failure"
    RECOVERING = "Recovering"

class EngineStateEnum:
    OFF = "OFF"
    STARTING = "STARTING"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

class VehicleProfile:
    """Stores behavior configuration profiles for simulated vehicles."""
    def __init__(self, name, cruising_speed_min, cruising_speed_max, max_speed, 
                 accel_rate, brake_rate, traffic_stop_prob, engine_start_prob, 
                 engine_stop_prob, power_failure_prob, battery_health, driving_style,
                 fuel_capacity=60.0):
        self.name = name
        self.cruising_speed_min = cruising_speed_min
        self.cruising_speed_max = cruising_speed_max
        self.max_speed = max_speed
        self.accel_rate = accel_rate
        self.brake_rate = brake_rate
        self.traffic_stop_prob = traffic_stop_prob
        self.engine_start_prob = engine_start_prob
        self.engine_stop_prob = engine_stop_prob
        self.power_failure_prob = power_failure_prob
        self.battery_health = battery_health # 0.0 - 1.0 (influences battery capacity decay)
        self.driving_style = driving_style # "calm", "normal", "aggressive"
        self.fuel_capacity = fuel_capacity

# Define standard behavioral profiles
VEHICLE_PROFILES = [
    VehicleProfile("Calm City Driver", 30.0, 45.0, 60.0, 1.5, 2.5, 0.05, 0.05, 0.08, 0.00, 0.98, "calm", 50.0),
    VehicleProfile("Highway Vehicle", 70.0, 90.0, 110.0, 3.5, 4.0, 0.02, 0.08, 0.05, 0.01, 0.95, "normal", 70.0),
    VehicleProfile("Delivery Vehicle", 25.0, 55.0, 80.0, 2.5, 3.0, 0.20, 0.12, 0.15, 0.01, 0.90, "normal", 60.0),
    VehicleProfile("Old Vehicle", 35.0, 60.0, 85.0, 2.0, 2.8, 0.08, 0.05, 0.08, 0.04, 0.65, "aggressive", 55.0)
]

# --- VEHICLE DIGITAL TWIN INDEPENDENT SUBSYSTEMS ---

class PowerSystem:
    """Manages main supply voltage, backup battery levels, and power cuts."""
    def __init__(self, profile: VehicleProfile):
        self.profile = profile
        self.main_power_ok = True
        self.power_failure_cooldown = random.randint(30, 80)
        self.power_failure_ticks = 0
        self.mvolt = 12.4
        self.volt = 4180.0
        self.power_transition_pending = False

    def update(self, state, current_ign):
        if state != VehicleStateEnum.POWER_FAILURE:
            self.power_failure_cooldown -= 1
            if self.power_failure_cooldown <= 0:
                if random.random() < self.profile.power_failure_prob:
                    self.main_power_ok = False
                    self.power_failure_ticks = random.randint(5, 12)
                    self.power_transition_pending = True
                    return
        else:
            self.power_failure_ticks -= 1
            if self.power_failure_ticks <= 0:
                self.main_power_ok = True
                self.power_transition_pending = True
                self.power_failure_cooldown = random.randint(30, 80)

        # Alternator charging vs settled discharge
        if not self.main_power_ok:
            self.mvolt = 0.0
            drain_rate = random.uniform(8.0, 18.0) * (2.0 - self.profile.battery_health)
            self.volt = max(3500.0, self.volt - drain_rate)
        else:
            target_mvolt = random.uniform(13.8, 14.2) if current_ign == 1 else random.uniform(12.2, 12.6)
            diff = target_mvolt - self.mvolt
            self.mvolt += max(-0.08, min(0.08, diff))
            if self.volt < 4200.0:
                self.volt = min(4200.0, self.volt + random.uniform(5.0, 15.0))

class EngineSystem:
    """Simulates engine thermal properties, load limits, and state machines."""
    def __init__(self, profile: VehicleProfile):
        self.profile = profile
        self.state = EngineStateEnum.OFF
        self.coolant_temperature = 25.0  # Starts ambient
        self.load = 0.0
        self.state_ticks = 0

    def update(self, ign, motion_state, speed, max_speed, accel):
        # Engine state machine
        if self.state == EngineStateEnum.OFF:
            if ign == 1:
                self.state = EngineStateEnum.STARTING
                self.state_ticks = 1
        elif self.state == EngineStateEnum.STARTING:
            self.state_ticks -= 1
            if self.state_ticks <= 0:
                self.state = EngineStateEnum.IDLE
        elif self.state == EngineStateEnum.IDLE:
            if ign == 0:
                self.state = EngineStateEnum.STOPPING
                self.state_ticks = 1
            elif motion_state == VehicleStateEnum.DRIVING and speed > 1.0:
                self.state = EngineStateEnum.RUNNING
        elif self.state == EngineStateEnum.RUNNING:
            if ign == 0:
                self.state = EngineStateEnum.STOPPING
                self.state_ticks = 1
            elif motion_state in (VehicleStateEnum.IDLE, VehicleStateEnum.STOPPED_IN_TRAFFIC) or speed <= 1.0:
                self.state = EngineStateEnum.IDLE
        elif self.state == EngineStateEnum.STOPPING:
            self.state_ticks -= 1
            if self.state_ticks <= 0:
                self.state = EngineStateEnum.OFF

        # Target-based Thermal Model: temp += (target - current) * thermal_rate
        target_temp = 25.0
        thermal_rate = 0.05
        if self.state in (EngineStateEnum.STARTING, EngineStateEnum.IDLE, EngineStateEnum.RUNNING):
            target_temp = 90.0
            if self.state == EngineStateEnum.RUNNING:
                target_temp += (self.load / 100.0) * 8.0
            thermal_rate = 0.06
        else:
            target_temp = 25.0
            thermal_rate = 0.03

        self.coolant_temperature += (target_temp - self.coolant_temperature) * thermal_rate
        self.coolant_temperature = max(25.0, min(105.0, self.coolant_temperature))

        # Engine load calculations
        if self.state in (EngineStateEnum.OFF, EngineStateEnum.STOPPING):
            self.load = 0.0
        elif self.state in (EngineStateEnum.STARTING, EngineStateEnum.IDLE):
            self.load = random.uniform(8.0, 15.0)
        elif self.state == EngineStateEnum.RUNNING:
            base_load = 15.0
            speed_factor = (speed / max_speed) * 45.0
            accel_factor = max(-10.0, min(25.0, accel * 8.0))
            self.load = max(5.0, min(100.0, base_load + speed_factor + accel_factor))

class TransmissionSystem:
    """Selects appropriate gear based on speed, load, and acceleration."""
    def __init__(self):
        self.gear = "P"

    def update(self, engine_state, speed, load, accel):
        if engine_state == EngineStateEnum.OFF:
            self.gear = "P"
            return
        if engine_state in (EngineStateEnum.STARTING, EngineStateEnum.STOPPING):
            self.gear = "N"
            return
        if speed == 0.0:
            self.gear = "N" if engine_state == EngineStateEnum.IDLE else "D1"
            return

        # Heavy loads hold lower gears longer (shift later)
        load_modifier = (load / 100.0) * 8.0
        accel_modifier = max(0.0, accel * 2.0)
        shift_offset = load_modifier + accel_modifier

        if speed < 15.0 + shift_offset:
            self.gear = "D1"
        elif speed < 30.0 + shift_offset:
            self.gear = "D2"
        elif speed < 45.0 + shift_offset:
            self.gear = "D3"
        elif speed < 60.0 + shift_offset:
            self.gear = "D4"
        elif speed < 75.0 + shift_offset:
            self.gear = "D5"
        else:
            self.gear = "D6"

class RPMSystem:
    """Calculates engine RPM depending on speed, selected gear, and engine load."""
    def __init__(self):
        self.rpm = 0

    def update(self, engine_state, gear, speed, load, accel):
        if engine_state == EngineStateEnum.OFF:
            self.rpm = 0
            return
        if engine_state == EngineStateEnum.STARTING:
            self.rpm = random.randint(1100, 1300)  # Crank starter spike
            return
        if engine_state == EngineStateEnum.STOPPING:
            self.rpm = max(0, self.rpm - 300)
            return
        if engine_state == EngineStateEnum.IDLE or gear in ("P", "N"):
            self.rpm = random.randint(750, 850)
            return

        gear_num = 1
        if len(gear) > 1 and gear[1].isdigit():
            gear_num = int(gear[1])

        base_ratio = 130.0 / gear_num
        target_rpm = 1000.0 + (speed * base_ratio)
        target_rpm += (load / 100.0) * 800.0
        target_rpm += max(-200.0, min(600.0, accel * 150.0))

        # Output smooth RPM curves (shifting gear keeps it in bands)
        self.rpm = int(max(800.0, min(5500.0, target_rpm)))

class FuelSystem:
    """Simulates a fuel tank, consumption, range, and gradual refueling."""
    def __init__(self, profile: VehicleProfile, capacity_liters=60.0):
        self.capacity = capacity_liters if capacity_liters and capacity_liters > 0.0 else profile.fuel_capacity
        self.current_fuel = self.capacity * random.uniform(0.40, 0.95)
        self.fuel_pct = (self.current_fuel / self.capacity) * 100.0
        
        self.base_consumption = 8.0
        if profile.driving_style == "aggressive":
            self.base_consumption = 11.5
        elif profile.driving_style == "calm":
            self.base_consumption = 6.5
            
        self.is_refueling = False
        self.fuel_transition_pending = False
        self.fuel_status_log = "NORMAL"

    def update(self, motion_state, speed, prev_speed, load, rpm, send_interval):
        if self.is_refueling:
            refuel_amount = random.uniform(2.5, 4.0)
            self.current_fuel = min(self.capacity, self.current_fuel + refuel_amount)
            self.fuel_pct = (self.current_fuel / self.capacity) * 100.0
            if self.current_fuel >= self.capacity * 0.98:
                self.current_fuel = self.capacity
                self.is_refueling = False
                self.fuel_transition_pending = True
                self.fuel_status_log = "REFUELED"
            return

        if self.fuel_pct < 10.0:
            if motion_state in (VehicleStateEnum.PARKED, VehicleStateEnum.IDLE):
                if random.random() < 0.20:
                    self.is_refueling = True
                    self.fuel_transition_pending = True
                    self.fuel_status_log = "REFUEL_START"
                    return

        if motion_state == VehicleStateEnum.PARKED:
            return

        if motion_state in (VehicleStateEnum.IDLE, VehicleStateEnum.STOPPED_IN_TRAFFIC):
            # Idle fuel consumption sips fuel
            idle_rate = (rpm / 1000.0) * 0.7 * (self.base_consumption / 8.0)
            consumed = (idle_rate / 3600.0) * send_interval
            self.current_fuel = max(0.0, self.current_fuel - consumed)
        elif motion_state == VehicleStateEnum.DRIVING:
            distance_km = (speed / 3600.0) * send_interval
            dynamic_rate = self.base_consumption * (load / 40.0) * (rpm / 2000.0)
            dynamic_rate = max(self.base_consumption * 0.5, min(self.base_consumption * 2.5, dynamic_rate))
            
            accel = speed - prev_speed
            if accel > 4.0:
                dynamic_rate += random.uniform(2.0, 5.0)

            consumed = (dynamic_rate / 100.0) * distance_km
            self.current_fuel = max(0.0, self.current_fuel - consumed)

        self.fuel_pct = (self.current_fuel / self.capacity) * 100.0

    @property
    def estimated_range(self):
        return (self.current_fuel / self.base_consumption) * 100.0

class RuntimeTracker:
    """Tracks runtimes, including engine, driving, and idling hours."""
    def __init__(self):
        self.engine_hours = 0.0
        self.driving_hours = 0.0
        self.idle_hours = 0.0
        self.trip_runtime = 0.0

    def update(self, ign, motion_state, send_interval):
        interval_hours = send_interval / 3600.0
        if ign == 1:
            self.engine_hours += interval_hours

        if motion_state == VehicleStateEnum.DRIVING:
            self.driving_hours += interval_hours
            self.trip_runtime += send_interval
        elif motion_state in (VehicleStateEnum.IDLE, VehicleStateEnum.STOPPED_IN_TRAFFIC):
            self.idle_hours += interval_hours
            
        if motion_state == VehicleStateEnum.PARKED:
            self.trip_runtime = 0.0

class GPSSystem:
    """Interpolates coordinate movements and GPS satellite stats."""
    def __init__(self, start_coord, odometer_start):
        self.latitude = start_coord[0]
        self.longitude = start_coord[1]
        self.heading = 0.0
        self.odometer = odometer_start
        self.satellites = 12
        self.fix = "A"
        self.last_coord = start_coord

    def update(self, speed, motion, send_interval):
        travelled = 0.0
        if speed > 0:
            travelled = (speed * motion.speed_multiplier * 1000.0 / 3600.0) * send_interval
            if motion.forward:
                motion.current_distance_offset += travelled
                if motion.current_distance_offset >= motion.total_path_distance:
                    if motion.loop_route:
                        motion.current_distance_offset = motion.total_path_distance - (motion.current_distance_offset - motion.total_path_distance)
                        motion.forward = False
                    else:
                        motion.current_distance_offset = motion.total_path_distance
                        motion.completed = True
                        motion.speed = 0.0
            else:
                motion.current_distance_offset -= travelled
                if motion.current_distance_offset <= 0.0:
                    if motion.loop_route:
                        motion.current_distance_offset = abs(motion.current_distance_offset)
                        motion.forward = True
                    else:
                        motion.current_distance_offset = 0.0
                        motion.completed = True
                        motion.speed = 0.0

        idx = 0
        while idx < len(motion.distances) - 2 and motion.distances[idx+1] < motion.current_distance_offset:
            idx += 1
            
        d1 = motion.distances[idx]
        d2 = motion.distances[idx+1]
        lat1, lon1 = motion.waypoints[idx]
        lat2, lon2 = motion.waypoints[idx+1]
        segment_dist = d2 - d1
        alpha = (motion.current_distance_offset - d1) / segment_dist if segment_dist > 0.001 else 0.0
        
        lat = lat1 + (lat2 - lat1) * alpha
        lon = lon1 + (lon2 - lon1) * alpha
        curr_coord = (lat, lon)
        
        self.odometer += travelled
        
        dist = haversine_distance(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        if dist > 0.1:
            self.heading = calculate_bearing(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        else:
            self.heading = 0.0

        self.last_coord = curr_coord
        self.latitude = float(round(curr_coord[0], 6))
        self.longitude = float(round(curr_coord[1], 6))
        self.satellites = 0 if speed < 0 else random.randint(9, 15)
        self.fix = "A"

class IOSystem:
    """Manages digital input signals and analog channel values."""
    def __init__(self):
        self.ignition = 0
        self.box = 0
        self.gpi = 0
        self.analog = [12100, 4800, 0]

    def update(self, motion_state, fuel_pct):
        self.ignition = 1 if motion_state in (VehicleStateEnum.IDLE, VehicleStateEnum.DRIVING, VehicleStateEnum.STOPPED_IN_TRAFFIC) else 0
        self.box = 0
        self.gpi = 0
        # fuel percentage mapped to analog[2] scaled by 100 (percentage 0-100)
        self.analog = [12100, 4800, int(fuel_pct * 100)]

class EventGenerator:
    """Evaluates ignition changes and power transitions into event codes."""
    def __init__(self):
        self.last_ign = 0
        self.ign_transition_pending = False

    def determine_txn(self, current_ign, power_sys, speed):
        if self.last_ign != current_ign:
            self.ign_transition_pending = True
        self.last_ign = current_ign

        if power_sys.power_transition_pending:
            power_sys.power_transition_pending = False
            return "L"
        elif self.ign_transition_pending:
            self.ign_transition_pending = False
            return "J"
        else:
            return "A" if speed > 0 else "E"

class TelemetryBuilder:
    """Assembles all subsystem states into a Telemetry Spec v2 payload."""
    @staticmethod
    def build_packet(uid, msg_id, txn, speed, gps: GPSSystem, io: IOSystem, pwr: PowerSystem, 
                     fuel: FuelSystem, engine: EngineSystem, trans: TransmissionSystem, rpm: RPMSystem, 
                     runtime: RuntimeTracker, alt_base):
        altitude = alt_base + random.uniform(-2.5, 2.5)
        
        packet = {
            "uid": uid,
            "info": {
                "dt": int(time.time()),
                "txn": txn,
                "msgkey": 0,
                "msgid": msg_id,
                "cmdkey": "",
                "cmdval": ""
            },
            "gps": {
                "fix": gps.fix,
                "loc": [gps.latitude, gps.longitude],
                "speed": float(round(speed, 2)),
                "sat": gps.satellites,
                "alt": float(round(altitude, 1)),
                "dir": gps.heading,
                "odo": float(round(gps.odometer, 1))
            },
            "io": {
                "box": io.box,
                "ign": io.ignition,
                "gpi": io.gpi,
                "status": 0,
                "analog": io.analog
            },
            "pwr": {
                "main": 1 if pwr.main_power_ok else 0,
                "batt": 1,
                "volt": float(round(pwr.volt, 1)),
                "mvolt": float(round(pwr.mvolt, 2))
            },
            "dbg": {
                "status": [1, 0],
                "ver": ["v1.0.2", "h1.1.0"],
                "lib": "VTSSim-v1.0"
            },
            
            # Telemetry Specification v2 subsystem nodes
            "fuel": {
                "capacity": float(round(fuel.capacity, 1)),
                "level": float(round(fuel.current_fuel, 1)),
                "percentage": float(round(fuel.fuel_pct, 1)),
                "consumption": float(round(fuel.base_consumption, 1)),
                "estimated_range": float(round(fuel.estimated_range, 1))
            },
            "power": {
                "main_voltage": float(round(pwr.mvolt, 2)),
                "backup_voltage": float(round(pwr.volt / 1000.0, 2)),
                "charging": 1 if (pwr.main_power_ok and io.ignition == 1) else 0,
                "battery_health": float(round(pwr.profile.battery_health, 2))
            },
            "engine": {
                "coolant_temperature": float(round(engine.coolant_temperature, 1)),
                "rpm": int(rpm.rpm),
                "load": float(round(engine.load, 1)),
                "engine_hours": float(round(runtime.engine_hours, 3)),
                "driving_hours": float(round(runtime.driving_hours, 3)),
                "idle_hours": float(round(runtime.idle_hours, 3)),
                "trip_runtime": float(round(runtime.trip_runtime, 1))
            },
            "network": {
                "gsm_signal": -75 if pwr.main_power_ok else -95,
                "network_type": "4G",
                "operator": "Vodafone"
            }
        }
        return packet

class VehicleState:
    """
    Virtual Digital Twin encapsulating all simulated hardware, vehicle,
    and environmental subsystems. Keeps the physical model in sync and serializes
    to a standard Telemetry Specification v2 payload on step().
    """
    def __init__(self, device_uid, waypoints, send_interval, speed_multiplier, loop_route, index=0, capacity=60.0):
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

        # Backward compatible variables matching caller references
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
    """Finds command record in Delivered status on backend, acknowledges it, waits, and marks Completed."""
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
            
            # 1. Transition to Acknowledged
            api_request(f"/commands/{cmd_id}/acknowledge", "PATCH", max_retries=2)
            
            # 2. Wait 2 seconds to simulate processing delay
            time.sleep(2)
            
            # 3. Transition to Completed
            comp_status, _ = api_request(
                f"/commands/{cmd_id}/complete?response={urllib.parse.quote(response_text)}",
                "PATCH",
                max_retries=2
            )
            return comp_status == 200
            
    return False

# --- FLEET REGISTRATION ---
def register_fleet(device_uids):
    """Fetches registrations from VTS backend and registers missing devices, returning UID-to-ID and UID-to-Capacity mappings."""
    if LOG_LEVEL != "DASHBOARD":
        print("[INFO] Checking vehicle registration on backend...")
    
    # Infinite retry on cold start
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
                uid_to_capacity[uid] = response_reg.get("capacity")
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[OK] Registered vehicle {uid} successfully.")
            else:
                if LOG_LEVEL != "DASHBOARD":
                    print(f"[WARN] Auto-registration failed for {uid} (status: {status_reg}). Continuing.")
        else:
            if LOG_LEVEL != "DASHBOARD":
                print(f"[EXISTS] Vehicle {uid} is already registered (DB ID: {uid_to_id[uid]}).")
                
    return uid_to_id, uid_to_capacity

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
    uid_to_id, uid_to_capacity = register_fleet(device_uids)
    
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
        capacity = uid_to_capacity.get(uid)
        v_state = VehicleState(uid, waypoints, send_interval, SPEED_MULTIPLIER, LOOP_ROUTE, index=i, capacity=capacity)
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
                    
                # Acknowledge execution back to database
                ack_success = acknowledge_command(vehicle, cmd_name, response_text)
                if LOG_LEVEL != "DASHBOARD" and ack_success:
                    print(f"[{vehicle.device_uid}] Command {cmd_name} execution completed on backend.")
                    
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
    device_uid_str = resolve(args.DEVICE_UID, "DEVICE_UIDS", resolve(None, "DEVICE_UID", "ESP32-DEMO-007"))
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
