from app.services.simulator.physics.engine import EngineStateEnum

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
