# Postman Testing Guide & API Coverage Report

This folder contains the official production-quality Postman collection and environment files for testing the Welogical Vehicle Tracking System (VTS) backend API.

---

## 1. Files Included

* **[`VTS_Collection.postman_collection.json`](./VTS_Collection.postman_collection.json)**: Complete Postman Collection v2.1 containing structured API requests, parameter schemas, realistic mock values, test assertions, and variable chaining scripts.
* **[`VTS_Environment.postman_environment.json`](./VTS_Environment.postman_environment.json)**: Postman Environment variables configuration mapping base host and dynamic test parameters.

---

## 2. API Coverage Report

All major domain entrypoints of the VTS backend are covered by the collection's verification scripts:

| Domain Folder | Request Name | Method | Path | Test Verification Assertions |
|:---|:---|:---:|:---|:---|
| **Health Check** | GET Root Welcome | `GET` | `/` | Status code 200, latency < 1000ms, response payload attributes |
| | GET Health Status | `GET` | `/health` | Status code 200, liveness, DB connection state validation |
| **Vehicles** | Create Vehicle | `POST` | `/vehicles` | Status code 201, registers `VEHICLE_ID` and `DEVICE_UID` variables |
| | Create Duplicate Vehicle | `POST` | `/vehicles` | Status code 409, conflict message verification |
| | List Vehicles | `GET` | `/vehicles` | Status code 200, returns array response |
| | Get Vehicle by ID | `GET` | `/vehicles/:id` | Status code 200, fetches correct matching ID |
| | Update Vehicle | `PUT` | `/vehicles/:id` | Status code 200, validates updated fields |
| | Delete/Archive Vehicle | `DELETE` | `/vehicles/:id` | Status code 200, soft-deletion status Archived check |
| **Drivers** | Create Driver | `POST` | `/drivers` | Status code 201, registers `DRIVER_ID` variable |
| | List Drivers | `GET` | `/drivers` | Status code 200, array output validation |
| | Get Driver by ID | `GET` | `/drivers/:id` | Status code 200, fetches matching profile |
| | Update Driver | `PUT` | `/drivers/:id` | Status code 200, validates updated email |
| | Delete Driver | `DELETE` | `/drivers/:id` | Status code 200, deletes driver profile |
| **Driver Assignments** | Assign Driver to Vehicle | `POST` | `/vehicles/:id/assign/:id`| Status code 200, maps active assignment, saves `ASSIGNMENT_ID` |
| | Get Active Assignment | `GET` | `/vehicles/:id/assignments/active` | Status code 200, resolves status Active |
| | Release Driver from Vehicle| `POST` | `/vehicles/:id/release` | Status code 200, sets status to Completed |
| | Get Vehicle Assignment History| `GET` | `/vehicles/:id/assignments/history`| Status code 200, history list |
| **Locations** | Log Standard Location | `POST` | `/locations` | Status code 201, saves `LOCATION_ID` |
| | Get Latest Location | `GET` | `/locations/latest/:id` | Status code 200, checks coordinates structure |
| | Get Location History | `GET` | `/locations/history/:id` | Status code 200, datetime windows filter validation |
| | List All Locations | `GET` | `/locations` | Status code 200, database explorer list |
| **Telemetry Ingestion** | Ingest Telemetry Packet | `POST` | `/vts/telemetry` | Status code 200, checks VTS protocol structure, handles duplicate filtering |
| | List Raw Packets | `GET` | `/vts/raw-packets` | Status code 200, raw logs debugger monitor |
| **Commands** | Queue New Command | `POST` | `/commands` | Status code 201, saves `COMMAND_ID`, sets status PENDING |
| | List Commands Queue | `GET` | `/commands` | Status code 200, pending queues list |
| | Mark Command as Sent | `PUT` | `/commands/:id/send` | Status code 200, transitions status to SENT |
| | Mark Command as Executed | `PUT` | `/commands/:id/execute` | Status code 200, transitions status to EXECUTED |
| | Mark Command as Failed | `PUT` | `/commands/:id/fail` | Status code 200, transitions status to FAILED |
| | Get Command Logs | `GET` | `/commands/:id/logs` | Status code 200, lifecycle audit records |
| | Delete Command | `DELETE`| `/commands/:id` | Status code 200, deletes command |
| **Configurations** | Create Configuration | `POST` | `/configurations` | Status code 201, saves APN and timezone config, registers `CONFIG_ID` |
| | Get Config by Vehicle | `GET` | `/configurations/:id` | Status code 200, configurations retrieval |
| | Update Configuration | `PUT` | `/configurations/:id` | Status code 200, checks updated speed limit threshold |
| | Delete Configuration | `DELETE`| `/configurations/:id` | Status code 200, profile delete |
| **Events** | List Events Stats | `GET` | `/events/stats` | Status code 200, checks severity breakdown |
| | List Recent Events | `GET` | `/events/recent` | Status code 200, warnings stream array |
| **Trips** | List Vehicle Trips | `GET` | `/vehicles/:id/trips` | Status code 200, registers first active `TRIP_ID` variable |
| | Rebuild Trips from History | `POST`| `/vehicles/:id/trips/rebuild`| Status code 200, generates chronological segments |
| | Get Trip Summary Analytics | `GET` | `/vehicles/:id/trips/:id/summary`| Status code 200, validates driver score calculations |
| | Get Trip Replay playback | `GET` | `/vehicles/:id/trips/:id/replay`| Status code 200, downsampled points replay |
| | Get Trip GeoJSON format | `GET` | `/vehicles/:id/trips/:id/geojson`| Status code 200, LineString schema validation |
| | Export Trip CSV file | `GET` | `/vehicles/:id/trips/:id/export` | Status code 200, streams CSV table data attachment |
| **Route Cache** | Snap Path Map Matching | `POST` | `/routes/snap-path` | Status code 200, returns matched polyline coordinates |

---

## 3. Testing Guide & Variable Chaining

The collection uses **Postman pre-request and test scripts** to achieve sequential API automation:
1. **Host config**: The environment variable `BASE_URL` targets `https://welogical-vehicle-tracking-system.onrender.com` by default. You can change this to `http://localhost:8000` to test locally.
2. **Variable Chaining**:
   - Creating a Vehicle automatically extracts the resulting integer ID and saves it to the `VEHICLE_ID` environment variable.
   - Creating a Driver saves `DRIVER_ID`.
   - Creating a Command saves `COMMAND_ID`, etc.
   - Subsequent calls (like updates, gets, or releases) automatically consume these variables (e.g. `{{VEHICLE_ID}}`), allowing you to execute the entire collection runner in one-click without copy-pasting resource keys.

---

## 4. How to Import and Run

1. Open **Postman Desktop** or **Postman Web**.
2. Click **Import** in the top left workspace panel.
3. Drag and drop both [`VTS_Collection.postman_collection.json`](./VTS_Collection.postman_collection.json) and [`VTS_Environment.postman_environment.json`](./VTS_Environment.postman_environment.json) into the import area.
4. Select **Import** to add them to your active collection registry.
5. In the top right environment dropdown of Postman, select **`Vehicle Tracking System - Production`**.
6. Hover over the collection name **`Vehicle Tracking System API`**, click the ellipsis `...` icon, and select **Run Collection**.
7. Click the blue **Run Vehicle Tracking System API** button to run all tests sequentially.
