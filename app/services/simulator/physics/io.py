class IOSystem:
    """Manages digital input signals and analog channel values."""
    def __init__(self):
        self.ignition = 0
        self.box = 0
        self.gpi = 0
        self.analog = [12100, 4800, 0]

    def update(self, motion_state, fuel_pct):
        motion_state_str = str(motion_state)
        self.ignition = 1 if motion_state_str in ("Idle", "Driving", "Stopped in Traffic") else 0
        self.box = 0
        self.gpi = 0
        # fuel percentage mapped to analog[2] scaled by 100 (percentage 0-100)
        self.analog = [12100, 4800, int(fuel_pct * 100)]
