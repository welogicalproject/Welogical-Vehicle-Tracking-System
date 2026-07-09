import time
import random
from app.services.simulator.physics.gps import GPSSystem
from app.services.simulator.physics.io import IOSystem
from app.services.simulator.physics.power import PowerSystem
from app.services.simulator.physics.fuel import FuelSystem
from app.services.simulator.physics.engine import EngineSystem
from app.services.simulator.physics.transmission import TransmissionSystem
from app.services.simulator.physics.rpm import RPMSystem
from app.services.simulator.physics.runtime import RuntimeTracker

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
