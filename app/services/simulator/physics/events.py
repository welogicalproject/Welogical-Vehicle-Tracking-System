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
