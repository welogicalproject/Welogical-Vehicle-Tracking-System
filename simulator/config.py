import os

# API configuration
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://welogical-vehicle-tracking-system.onrender.com"
).rstrip("/")

# Intervals configuration
TELEMETRY_INTERVAL = float(os.environ.get("TELEMETRY_INTERVAL", "10"))
RETRY_INTERVAL = float(os.environ.get("RETRY_INTERVAL", "10"))