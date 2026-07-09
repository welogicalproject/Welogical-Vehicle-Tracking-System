import random
from app.services.simulator.physics.profiles import VehicleProfile

# Vehicle State definitions
class VehicleStateEnum:
    PARKED = "Parked"
    IDLE = "Idle"
    DRIVING = "Driving"
    STOPPED_IN_TRAFFIC = "Stopped in Traffic"
    POWER_FAILURE = "Power Failure"
    RECOVERING = "Recovering"

class VehicleMotion:
    """
    Manages the vehicle's motion state machine, speed profile, and route progression.
    Consumed by VehicleState and GPSSystem to compute positions and transitions.
    """
    def __init__(self, profile: VehicleProfile, speed_multiplier, loop_route, path, distances, total_path_distance):
        self.profile = profile
        self.speed_multiplier = speed_multiplier
        self.loop_route = loop_route

        # Route geometry (shared with GPSSystem.update via motion reference)
        self.waypoints = path
        self.distances = distances
        self.total_path_distance = total_path_distance

        # Position tracking along route
        self.current_distance_offset = random.uniform(0.0, total_path_distance)
        self.forward = random.choice([True, False])
        self.completed = False

        # Speed state
        self.speed = 0.0
        self.prev_speed = 0.0

        # Motion state machine
        self.state = VehicleStateEnum.PARKED
        self._parked_ticks = random.randint(2, 8)
        self._target_speed = 0.0

    def update_state(self, main_power_ok):
        """Advance the motion state machine one tick."""
        import logging
        logger = logging.getLogger("vts.simulator.motion")

        if not main_power_ok:
            prev_state = self.state
            self.state = VehicleStateEnum.POWER_FAILURE
            logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Power Failure)")
            return

        if self.state == VehicleStateEnum.POWER_FAILURE:
            prev_state = self.state
            self.state = VehicleStateEnum.RECOVERING
            logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Power Restored)")
            return

        if self.state == VehicleStateEnum.RECOVERING:
            prev_state = self.state
            self.state = VehicleStateEnum.PARKED
            logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Recovery completed)")
            return

        # If loop_route is enabled, force the vehicle to remain in Driving state.
        if self.loop_route:
            if self.state != VehicleStateEnum.DRIVING:
                prev_state = self.state
                self.state = VehicleStateEnum.DRIVING
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: loop_route=True, forcing driving mode)")
                self._target_speed = random.uniform(
                    self.profile.cruising_speed_min, self.profile.cruising_speed_max
                )
            return

        if self.state == VehicleStateEnum.PARKED:
            self._parked_ticks -= 1
            if self._parked_ticks <= 0:
                prev_state = self.state
                self.state = VehicleStateEnum.IDLE
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Parked ticks expired)")
                self._parked_ticks = random.randint(2, 8)
            return

        if self.state == VehicleStateEnum.IDLE:
            # Randomly start driving or stay idle
            if random.random() < self.profile.engine_start_prob:
                prev_state = self.state
                self.state = VehicleStateEnum.DRIVING
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Engine started)")
                self._target_speed = random.uniform(
                    self.profile.cruising_speed_min, self.profile.cruising_speed_max
                )
            elif random.random() < self.profile.engine_stop_prob:
                prev_state = self.state
                self.state = VehicleStateEnum.PARKED
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Engine stopped)")
                self._parked_ticks = random.randint(4, 16)
            return

        if self.state == VehicleStateEnum.DRIVING:
            # Occasional traffic stop
            if random.random() < self.profile.traffic_stop_prob:
                prev_state = self.state
                self.state = VehicleStateEnum.STOPPED_IN_TRAFFIC
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Traffic stop)")
                return
            # Occasional engine stop
            if random.random() < self.profile.engine_stop_prob * 0.3:
                prev_state = self.state
                self.state = VehicleStateEnum.IDLE
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Engine idling)")
            return

        if self.state == VehicleStateEnum.STOPPED_IN_TRAFFIC:
            if random.random() < 0.35:
                prev_state = self.state
                self.state = VehicleStateEnum.DRIVING
                logger.info(f"Simulator State Transition: {prev_state} -> {self.state} (Reason: Traffic cleared)")
            return

    def update_speed(self, stopped_by_immobilizer):
        """Update speed toward target based on motion state and immobilizer."""
        self.prev_speed = self.speed

        if stopped_by_immobilizer or self.state in (
            VehicleStateEnum.PARKED,
            VehicleStateEnum.POWER_FAILURE,
            VehicleStateEnum.RECOVERING,
        ):
            # Decelerate to zero
            self.speed = max(0.0, self.speed - self.profile.brake_rate * 2.0)
            return

        if self.state == VehicleStateEnum.IDLE:
            self._target_speed = 0.0
        elif self.state == VehicleStateEnum.STOPPED_IN_TRAFFIC:
            self._target_speed = 0.0
        elif self.state == VehicleStateEnum.DRIVING:
            if self._target_speed <= 0.0:
                self._target_speed = random.uniform(
                    self.profile.cruising_speed_min, self.profile.cruising_speed_max
                )

        diff = self._target_speed - self.speed
        if diff > 0:
            self.speed = min(self._target_speed, self.speed + self.profile.accel_rate)
        elif diff < 0:
            self.speed = max(self._target_speed, self.speed - self.profile.brake_rate)

        # Hard cap at profile max speed
        self.speed = min(self.speed, self.profile.max_speed)
