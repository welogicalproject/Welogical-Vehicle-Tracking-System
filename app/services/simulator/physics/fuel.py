import random
from app.services.simulator.physics.profiles import VehicleProfile

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
        # Prevent circular import by stringifying motion state
        motion_state_str = str(motion_state)

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
            if motion_state_str in ("Parked", "Idle"):
                if random.random() < 0.20:
                    self.is_refueling = True
                    self.fuel_transition_pending = True
                    self.fuel_status_log = "REFUEL_START"
                    return

        if motion_state_str == "Parked":
            return

        if motion_state_str in ("Idle", "Stopped in Traffic"):
            # Idle fuel consumption sips fuel
            idle_rate = (rpm / 1000.0) * 0.7 * (self.base_consumption / 8.0)
            consumed = (idle_rate / 3600.0) * send_interval
            self.current_fuel = max(0.0, self.current_fuel - consumed)
        elif motion_state_str == "Driving":
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
