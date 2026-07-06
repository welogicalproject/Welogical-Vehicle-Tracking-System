from datetime import datetime, timezone
from app.schemas.vts import VTSPacket
from app.exceptions import VTSProtocolError

def validate_telemetry_packet(packet: VTSPacket):
    """
    Validate telemetry packet parameters for compliance.
    Raises VTSProtocolError if any parameter lies outside valid bounds.
    """
    # 1. Device UID Validation
    uid = str(packet.uid).strip()
    if not uid:
        raise VTSProtocolError("Device UID must not be empty.")

    # 2. Msg ID Validation
    msgid = packet.info.msgid
    if msgid is not None and msgid < 0:
        raise VTSProtocolError(f"Message ID must be non-negative. Received: {msgid}")

    # 3. GPS Coordinates Validation
    lat = packet.gps.loc[0]
    lon = packet.gps.loc[1]
    if lat < -90.0 or lat > 90.0:
        raise VTSProtocolError(f"Latitude must be between -90 and 90. Received: {lat}")
    if lon < -180.0 or lon > 180.0:
        raise VTSProtocolError(f"Longitude must be between -180 and 180. Received: {lon}")

    # 4. Speed & Altitude Bounds
    speed = packet.gps.speed
    if speed < 0.0:
        raise VTSProtocolError(f"Vehicle speed cannot be negative. Received: {speed}")
    
    alt = packet.gps.alt
    if alt < -1000.0 or alt > 10000.0:
        raise VTSProtocolError(f"Altitude out of bounds (-1000m to 10000m). Received: {alt}")

    # 5. Heading/Direction
    heading = packet.gps.dir
    if heading is not None and (heading < 0.0 or heading > 360.0):
        raise VTSProtocolError(f"Heading direction must be between 0 and 360 degrees. Received: {heading}")

    # 6. Timestamp Range Check (UTC epoch)
    packet_time = datetime.fromtimestamp(packet.info.dt, tz=timezone.utc).replace(tzinfo=None)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Check for packets in the far future (more than 1 hour)
    time_diff_future = (packet_time - now_utc).total_seconds()
    if time_diff_future > 3600:
        raise VTSProtocolError(f"Timestamp is in the future: {packet_time} (Current UTC: {now_utc})")
        
    # Check for packets in the far past (before year 2020)
    if packet_time.year < 2020:
        raise VTSProtocolError(f"Timestamp is in the far past: {packet_time} (Minimum year allowed: 2020)")
        
    return packet_time
