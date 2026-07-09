# Helper functions for geographic math and route snap/interpolation

import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate direction bearing in degrees from point 1 to point 2."""
    d_lon = math.radians(lon2 - lon1)
    r_lat1 = math.radians(lat1)
    r_lat2 = math.radians(lat2)
    
    y = math.sin(d_lon) * math.cos(r_lat2)
    x = math.cos(r_lat1) * math.sin(r_lat2) - math.sin(r_lat1) * math.cos(r_lat2) * math.cos(d_lon)
    
    brng = math.atan2(y, x)
    brng = math.degrees(brng)
    return float(round((brng + 360) % 360, 1))

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates."""
    r_earth = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c

def interpolate_waypoints(waypoints, points_per_segment=40):
    """Generate intermediate coordinates between waypoints for smooth movements."""
    full_path = []
    if not waypoints:
        return full_path
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i+1]
        for step in range(points_per_segment):
            alpha = step / points_per_segment
            lat = lat1 + (lat2 - lat1) * alpha
            lon = lon1 + (lon2 - lon1) * alpha
            full_path.append((lat, lon))
    full_path.append(waypoints[-1])
    return full_path
