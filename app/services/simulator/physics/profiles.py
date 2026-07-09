# Standard profile structures

class VehicleProfile:
    """Stores behavior configuration profiles for simulated vehicles."""
    def __init__(self, name, cruising_speed_min, cruising_speed_max, max_speed, 
                 accel_rate, brake_rate, traffic_stop_prob, engine_start_prob, 
                 engine_stop_prob, power_failure_prob, battery_health, driving_style,
                 fuel_capacity=60.0):
        self.name = name
        self.cruising_speed_min = cruising_speed_min
        self.cruising_speed_max = cruising_speed_max
        self.max_speed = max_speed
        self.accel_rate = accel_rate
        self.brake_rate = brake_rate
        self.traffic_stop_prob = traffic_stop_prob
        self.engine_start_prob = engine_start_prob
        self.engine_stop_prob = engine_stop_prob
        self.power_failure_prob = power_failure_prob
        self.battery_health = battery_health # 0.0 - 1.0 (influences battery capacity decay)
        self.driving_style = driving_style # "calm", "normal", "aggressive"
        self.fuel_capacity = fuel_capacity

VEHICLE_PROFILES = [
    VehicleProfile("Calm City Driver", 30.0, 45.0, 60.0, 1.5, 2.5, 0.05, 0.05, 0.08, 0.00, 0.98, "calm", 50.0),
    VehicleProfile("Highway Vehicle", 70.0, 90.0, 110.0, 3.5, 4.0, 0.02, 0.08, 0.05, 0.01, 0.95, "normal", 70.0),
    VehicleProfile("Delivery Vehicle", 25.0, 55.0, 80.0, 2.5, 3.0, 0.20, 0.12, 0.15, 0.01, 0.90, "normal", 60.0),
    VehicleProfile("Old Vehicle", 35.0, 60.0, 85.0, 2.0, 2.8, 0.08, 0.05, 0.08, 0.04, 0.65, "aggressive", 55.0)
]
