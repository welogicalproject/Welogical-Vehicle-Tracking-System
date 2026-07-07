# VTS Telemetry Simulator Guide

The VTS Telemetry Simulator is a zero-dependency Python utility designed to simulate real-time GPS telemetry from tracking devices (like an ESP32) sending data to the Vehicle Tracking System (VTS). 

It is copied and adapted from the proven `GPS_Project` simulator, supporting realistic road movement, command overrides, automatic registration, and live dashboard metrics.

---

## Installation

The simulator uses only Python standard libraries (`urllib`, `json`, `argparse`, `xml.etree`, etc.) and has **zero external package dependencies**.

### Requirements
- Python 3.8+ installed on your system.

---

## Configuration

You can configure the simulator using three levels of precedence (highest to lowest):
1. **Command Line Arguments (CLI)**
2. **Environment Variables**
3. **`.env` files** (searched in the current working directory, project root, or `scripts/simulator/` folder).

### Configuration Options

| Option / Variable Name | CLI Argument | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `API_URL` | `--url` | `https://welogical-vehicle-tracking-system.onrender.com` | Deployed or local VTS backend base URL. |
| `DEVICE_UID` | `--uid` | `ESP32-DEMO-007` | Comma-separated list of device UIDs to simulate. |
| `SEND_INTERVAL` | `--interval` | `10.0` | Ingestion transmit frequency (in seconds). |
| `SPEED_MULTIPLIER` | `-s`, `--speed-multiplier` | `1.0` | Multiplies GPS speed to advance along the route faster. |
| `LOOP_ROUTE` | `--loop` / `--no-loop` | `True` | Loop route continuously back-and-forth (`True`) or stop at end (`False`). |
| `ROUTE_FILE` | `-r`, `--route-file` | *Auto-selected* | Path to a custom route file, or comma-separated list matching vehicles. |
| `LOG_LEVEL` | `-l`, `--log-level` | `DASHBOARD` | Log output style: `DASHBOARD` (refreshing UI), `INFO`, `DEBUG`, `WARN`, `ERROR`. |

---

## Running the Simulator

All commands should be run from the project root directory.

### 1. Run a Single Vehicle
To run a single vehicle `ESP32-DEMO-007` sending to the default Render backend with a refreshing dashboard:
```bash
python scripts/simulator/simulator.py --uid ESP32-DEMO-007
```

### 2. Run Multiple Vehicles
To simulate multiple vehicles moving along independent routes simultaneously:
```bash
python scripts/simulator/simulator.py --uid ESP32-DEMO-007,ESP32-DEMO-008,ESP32-DEMO-009
```
*Note: If no custom routes are supplied, the simulator lists route files in `scripts/simulator/routes/` and assigns them to each device in order.*

### 3. Fast Testing (Speed Multiplier)
To speed up coordinates movement (e.g. 5x faster) and decrease the interval to 5 seconds:
```bash
python scripts/simulator/simulator.py --uid ESP32-DEMO-007 -s 5.0 --interval 5
```

### 4. Direct Route Mapping
To run a vehicle on a specific route file:
```bash
python scripts/simulator/simulator.py --uid ESP32-DEMO-007 --route-file scripts/simulator/routes/surat_to_kim.json
```

---

## Custom Route Files

You can add custom routes to the simulator. Put them in the `scripts/simulator/routes/` directory.

The simulator automatically parses the following formats:
- **JSON**: A list of coordinates, either coordinate lists `[[lat1, lon1], [lat2, lon2]]` or objects `[{"lat": 21.17, "lon": 72.83}]` (also accepts `"latitude"`/`"longitude"` or `"lng"`).
- **CSV**: Columns containing coordinate fields (e.g., `latitude, longitude` or `lat, lon`).
- **GPX**: Standard GPS route tracks containing `<trkpt>` or `<wpt>` waypoint markers.

*High Density Check:* If a route contains more than 50 points, the simulator reads it as a fine-grained path directly. If it has fewer than 50 points, the simulator queries the VTS route cache to snap it to road networks, falling back to linear interpolation if the server is offline.

---

## Remote Backend Commands

The simulator simulates a real ESP32 device's response to remote commands received in the telemetry response payload. It executes and acknowledges the following commands:

- **`STOPV`**: Engages the vehicle immobilizer (sets speed to 0 km/h, stops GPS movement).
- **`STARTV`**: Disengages the immobilizer (resumes normal speed fluctuation and GPS movement).
- **`PRD=X`**: Modifies the telemetry reporting interval to `X` seconds.
- **`REBOOT`**: Simulates hardware power recycle, resetting the internal message sequence counter to `1`.
- **`RESET`**: Restores factory settings, resetting the message sequence and disengaging the immobilizer.

---

## Troubleshooting

### Render Cold-Start Delay
The Render free tier puts web services to sleep after inactivity. On start, the simulator might appear stuck on `Checking vehicle registration on backend...`.
* **Behavior**: This is normal. The simulator has built-in **automatic retry** with exponential backoff. It will wait indefinitely until Render wakes up and then seamlessly begin simulation.

### Screen Flickering in Dashboard Mode
In some legacy Command Prompts, terminal clears might cause flickering.
* **Fix**: Run the simulator with log level `INFO` to fall back to scrolling text logs:
  ```bash
  python scripts/simulator/simulator.py --log-level INFO
  ```

### Stop the Simulator
To terminate the simulator, press **`Ctrl+C`**. It will catch the interrupt and shut down gracefully without raising exceptions.
