from app.services.simulator.physics.helpers import haversine_distance, calculate_bearing

class GPSSystem:
    """Interpolates coordinate movements and GPS satellite stats."""
    def __init__(self, start_coord, odometer_start):
        self.latitude = start_coord[0]
        self.longitude = start_coord[1]
        self.heading = 0.0
        self.odometer = odometer_start
        self.satellites = 12
        self.fix = "A"
        self.last_coord = start_coord

    def update(self, speed, motion, send_interval):
        travelled = 0.0
        if speed > 0:
            travelled = (speed * motion.speed_multiplier * 1000.0 / 3600.0) * send_interval
            if motion.forward:
                motion.current_distance_offset += travelled
                if motion.current_distance_offset >= motion.total_path_distance:
                    if motion.loop_route:
                        motion.current_distance_offset = motion.total_path_distance - (motion.current_distance_offset - motion.total_path_distance)
                        motion.forward = False
                    else:
                        motion.current_distance_offset = motion.total_path_distance
                        motion.completed = True
                        motion.speed = 0.0
            else:
                motion.current_distance_offset -= travelled
                if motion.current_distance_offset <= 0.0:
                    if motion.loop_route:
                        motion.current_distance_offset = abs(motion.current_distance_offset)
                        motion.forward = True
                    else:
                        motion.current_distance_offset = 0.0
                        motion.completed = True
                        motion.speed = 0.0

        idx = 0
        while idx < len(motion.distances) - 2 and motion.distances[idx+1] < motion.current_distance_offset:
            idx += 1
            
        d1 = motion.distances[idx]
        d2 = motion.distances[idx+1]
        lat1, lon1 = motion.waypoints[idx]
        lat2, lon2 = motion.waypoints[idx+1]
        segment_dist = d2 - d1
        alpha = (motion.current_distance_offset - d1) / segment_dist if segment_dist > 0.001 else 0.0
        
        lat = lat1 + (lat2 - lat1) * alpha
        lon = lon1 + (lon2 - lon1) * alpha
        curr_coord = (lat, lon)
        
        self.odometer += travelled
        
        dist = haversine_distance(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        if dist > 0.1:
            self.heading = calculate_bearing(self.last_coord[0], self.last_coord[1], curr_coord[0], curr_coord[1])
        else:
            self.heading = 0.0

        self.last_coord = curr_coord
        self.latitude = float(round(curr_coord[0], 6))
        self.longitude = float(round(curr_coord[1], 6))
        self.satellites = 0 if speed < 0 else random_satellites(speed)
        self.fix = "A"

def random_satellites(speed) -> int:
    import random
    return random.randint(9, 15)
