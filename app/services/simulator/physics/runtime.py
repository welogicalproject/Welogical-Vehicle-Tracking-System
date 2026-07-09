class RuntimeTracker:
    """Tracks runtimes, including engine, driving, and idling hours."""
    def __init__(self):
        self.engine_hours = 0.0
        self.driving_hours = 0.0
        self.idle_hours = 0.0
        self.trip_runtime = 0.0

    def update(self, ign, motion_state, send_interval):
        motion_state_str = str(motion_state)
        interval_hours = send_interval / 3600.0
        if ign == 1:
            self.engine_hours += interval_hours

        if motion_state_str == "Driving":
            self.driving_hours += interval_hours
            self.trip_runtime += send_interval
        elif motion_state_str in ("Idle", "Stopped in Traffic"):
            self.idle_hours += interval_hours
            
        if motion_state_str == "Parked":
            self.trip_runtime = 0.0
