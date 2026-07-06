# API Reference

This document outlines the primary REST API endpoints exposed by the FastAPI backend.

**Base URL:** `http://localhost:8000/api/v1`

---

## 1. Vehicles
Manage tracking devices and physical vehicles.

### `GET /vehicles/`
- **Description:** Retrieve a list of all vehicles.
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 1,
      "device_uid": "TRACKER_001",
      "vehicle_name": "Truck A",
      "vehicle_type": "Truck",
      "status": "Enabled",
      "current_driver": {
        "id": 5,
        "driver_name": "John Doe"
      }
    }
  ]
  ```

### `POST /vehicles/`
- **Description:** Register a new vehicle.
- **Request Body:**
  ```json
  {
    "device_uid": "TRACKER_002",
    "vehicle_name": "Van B",
    "vehicle_type": "Van"
  }
  ```
- **Response:** `201 Created`

---

## 2. Locations
Ingest and query GPS telemetry.

### `POST /locations/raw`
- **Description:** Ingest raw GPS payload from a tracker.
- **Request Body:**
  ```json
  {
    "device_uid": "TRACKER_001",
    "latitude": 21.1702,
    "longitude": 72.8311,
    "speed": 45.5,
    "timestamp": "2026-07-06T12:00:00Z"
  }
  ```
- **Response:** `201 Created`

### `GET /locations/history/{vehicle_id}`
- **Description:** Retrieve historical location points for a specific vehicle.
- **Query Params:** `start_time`, `end_time`
- **Response:** `200 OK` (Array of location objects)

---

## 3. Trips
Manage computed journeys.

### `GET /trips/active`
- **Description:** Retrieve all currently active (ongoing) trips.
- **Response:** `200 OK`

### `GET /trips/{trip_id}`
- **Description:** Retrieve details of a specific trip, including events and driving score.
- **Response:** `200 OK`

---

## 4. Drivers
Manage personnel and assignments.

### `POST /drivers/`
- **Description:** Register a new driver.
- **Request Body:**
  ```json
  {
    "driver_name": "Jane Smith",
    "phone_number": "+1234567890",
    "license_number": "LIC987654321"
  }
  ```

### `POST /drivers/assign`
- **Description:** Assign a driver to a vehicle.
- **Request Body:**
  ```json
  {
    "vehicle_id": 1,
    "driver_id": 2
  }
  ```

---

## 5. Events
Query generated alerts and infractions.

### `GET /events/`
- **Description:** Retrieve system events.
- **Query Params:** `vehicle_id`, `event_type` (e.g., `OVERSPEED`, `STOP`), `limit`.
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 100,
      "vehicle_id": 1,
      "event_type": "OVERSPEED",
      "timestamp": "2026-07-06T11:45:00Z",
      "metadata": {"speed": 85.0, "limit": 80.0}
    }
  ]
  ```

---

## 6. Device Configuration & Commands
Manage Over-The-Air (OTA) commands and settings for GPS trackers.

### `POST /device_config/`
- **Description:** Set configuration parameters for a device.
- **Request Body:**
  ```json
  {
    "vehicle_id": 1,
    "parameter": "HEARTBEAT_INTERVAL",
    "value": "60"
  }
  ```

### `POST /device_command/`
- **Description:** Queue a command to be sent to a device.
- **Request Body:**
  ```json
  {
    "vehicle_id": 1,
    "command_type": "ENGINE_CUTOFF"
  }
  ```

---

## 7. Routes (Google Routes API Cache)
Query optimized routes.

### `GET /routes/`
- **Description:** Fetch the cached route distance and duration for an active trip.
- **Query Params:** `trip_id`
- **Response:** `200 OK`
  ```json
  {
    "distance_meters": 15000,
    "duration_seconds": 1800
  }
  ```

---

## 8. System
### `GET /health`
- **Description:** System health check.
- **Response:** `200 OK` `{"status": "healthy", "database": "connected"}`
