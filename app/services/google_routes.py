import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Concurrency protection registry
class LockRegistry:
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_lock(self, key: str) -> asyncio.Lock:
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def remove_lock(self, key: str):
        async with self._global_lock:
            if key in self._locks and not self._locks[key].locked():
                self._locks.pop(key, None)

lock_registry = LockRegistry()


def parse_google_duration(duration_str: Optional[str]) -> Optional[int]:
    """
    Parse Google's duration string (e.g., '123s' or '3600s') to seconds integer.
    """
    if not duration_str:
        return None
    try:
        if duration_str.endswith("s"):
            return int(float(duration_str[:-1]))
        return int(float(duration_str))
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse Google duration string '{duration_str}': {e}")
        return None


async def call_google_routes_api(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    waypoints: Optional[list] = None
) -> Dict[str, Any]:
    """
    Directly call Google Routes API v2 with request timeouts, timeouts, and transient retries.
    Throws ValueError for permanent errors (400, ZERO_RESULTS) or transient error after exhaustion.
    """
    if not settings.GOOGLE_ROUTES_API_KEY:
        raise ValueError("Google Routes API Key is not configured in settings.")

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_ROUTES_API_KEY,
        "X-Goog-FieldMask": "routes.polyline.encodedPolyline,routes.distanceMeters,routes.duration,routes.staticDuration"
    }

    # Construct request body
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_lon
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination_lat,
                    "longitude": destination_lon
                }
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE"
    }

    if waypoints:
        body["intermediates"] = [
            {
                "location": {
                    "latLng": {
                        "latitude": wp[0],
                        "longitude": wp[1]
                    }
                }
            }
            for wp in waypoints[:23]  # Stay within Google's 25-waypoint limit (origin + dest + 23 intermediates)
        ]

    # Setup timeout
    timeout_config = httpx.Timeout(
        timeout=float(settings.GOOGLE_ROUTES_TIMEOUT_SECONDS),
        connect=3.0
    )

    max_retries = 3
    retry_delay = 0.5

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Calling Google Routes API, attempt {attempt}/{max_retries}...")
                response = await client.post(url, json=body, headers=headers)
                
                # Check status
                if response.status_code == 400:
                    # Parse error details if possible
                    err_data = response.json()
                    err_msg = err_data.get("error", {}).get("message", "Invalid Request coordinates.")
                    logger.error(f"Permanent Google Routes API 400 Error: {err_msg}")
                    raise ValueError(f"Google Routes API bad request: {err_msg}")
                
                if response.status_code == 403 or response.status_code == 401:
                    logger.error("Authentication/Authorization failed with Google Routes API.")
                    raise ValueError("Google Routes API authentication failed.")

                response.raise_for_status()
                
                data = response.json()
                routes = data.get("routes", [])
                if not routes:
                    # Google API returned empty list (No route between origin and destination)
                    logger.warning("Google Routes API returned empty routes array (ZERO_RESULTS).")
                    return {"status": "ZERO_RESULTS", "raw_response": data}

                # Happy Path
                route = routes[0]
                encoded_polyline = route.get("polyline", {}).get("encodedPolyline")
                if not encoded_polyline:
                    logger.warning("Google Routes API returned route but encodedPolyline is missing.")
                    return {"status": "ZERO_RESULTS", "raw_response": data}

                distance = route.get("distanceMeters")
                duration_str = route.get("duration")
                static_duration_str = route.get("staticDuration")

                parsed_duration = parse_google_duration(duration_str)
                parsed_static_duration = parse_google_duration(static_duration_str)

                return {
                    "status": "SUCCESS",
                    "encoded_polyline": encoded_polyline,
                    "distance_meters": distance,
                    "duration_seconds": parsed_duration,
                    "static_duration_seconds": parsed_static_duration,
                    "raw_response": data
                }

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
                logger.warning(f"Transient HTTP connection error during Google Routes API request (attempt {attempt}): {e}")
                if attempt == max_retries:
                    raise IOError(f"Google Routes API request failed after {max_retries} connection timeouts: {e}")
            except httpx.HTTPStatusError as e:
                # Retry on transient 5xx server errors
                if e.response.status_code >= 500:
                    logger.warning(f"Transient HTTP 5xx error from Google Routes (attempt {attempt}): status={e.response.status_code}")
                    if attempt == max_retries:
                        raise IOError(f"Google Routes API failed with internal server error: {e}")
                else:
                    # Permanent 4xx client errors (excluding 400/403 handled above)
                    logger.error(f"Permanent HTTP error from Google Routes: status={e.response.status_code}, details={e.response.text}")
                    raise ValueError(f"Google Routes API request failed permanently: status={e.response.status_code}")
            
            # Wait with exponential backoff before retry
            await asyncio.sleep(retry_delay)
            retry_delay *= 2

    raise IOError("Google Routes API request failed: exhausted retry logic.")
