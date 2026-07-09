import random
from app.services.simulator.physics.engine import EngineStateEnum

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
