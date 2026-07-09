import random
from app.services.simulator.physics.profiles import VehicleProfile

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
        # Prevent circular import by checking state name directly
        if str(state) != "Power Failure":
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
