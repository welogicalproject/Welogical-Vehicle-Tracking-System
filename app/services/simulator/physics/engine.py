import random
from app.services.simulator.physics.profiles import VehicleProfile

class EngineStateEnum:
    OFF = "OFF"
    STARTING = "STARTING"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

class EngineSystem:
    """Simulates engine thermal properties, load limits, and state machines."""
    def __init__(self, profile: VehicleProfile):
        self.profile = profile
        self.state = EngineStateEnum.OFF
        self.coolant_temperature = 25.0  # Starts ambient
        self.load = 0.0
        self.state_ticks = 0

    def update(self, ign, motion_state, speed, max_speed, accel):
        # Prevent circular import by stringifying motion state checks
        motion_state_str = str(motion_state)
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
            elif motion_state_str == "Driving" and speed > 1.0:
                self.state = EngineStateEnum.RUNNING
        elif self.state == EngineStateEnum.RUNNING:
            if ign == 0:
                self.state = EngineStateEnum.STOPPING
                self.state_ticks = 1
            elif motion_state_str in ("Idle", "Stopped in Traffic") or speed <= 1.0:
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
