# Project Structure

This document details every folder, subfolder, and critical file in the Welogical Vehicle Tracking System repository.

## Root Directory

- **`README.md`**: Main project documentation covering overview, architecture, and setup.
- **`.env.example`**: Template for environment variables. Contains standard keys without sensitive values.
- **`requirements.txt`**: Python pip dependencies for the backend.
- **`alembic.ini`**: Configuration file for Alembic database migrations.

---

## 1. `app/` (Backend Service)
The core FastAPI backend responsible for receiving GPS telemetry, managing the database, processing trips, and serving REST APIs.

- **`main.py`**: The entry point. Initializes FastAPI, configures CORS, registers exception handlers, and mounts all routers.
- **`config.py`**: Uses Pydantic `BaseSettings` to load environment variables from `.env`. Defines configurations for database, app environment, thresholds, and Google Routes.
- **`database.py`**: Configures the async SQLAlchemy engine and session makers.
- **`exceptions.py`**: Custom API exceptions and handlers for consistent error responses.
- **`logging_config.py`**: Configures Python's `logging` module.

### 1.1 `app/models/` (Database Schema)
Defines the SQLAlchemy ORM models.
- **`vehicle.py`**: The `Vehicle` model representing physical tracking devices/trucks.
- **`driver.py`**: The `Driver` model storing driver profiles.
- **`driver_assignment.py`**: Junction table mapping drivers to vehicles over time.
- **`location.py`**: The `Location` model for storing high-frequency GPS ping coordinates.
- **`event.py`**: The `Event` model for specific incidents (e.g., Engine ON, Overspeed, Geofence breach).
- **`trip.py`**: The `Trip` model storing computed journeys, start/end times, distance, and driving scores.
- **`device_command.py` & `command_log.py`**: Models for OTA commands sent to devices.

### 1.2 `app/routers/` (API Endpoints)
Defines the FastAPI route handlers.
- **`vehicle.py`**, **`trip.py`**, **`driver.py`**, **`location.py`**: Standard CRUD API routes mapping HTTP requests to `crud/` methods.
- **`health.py`**: Endpoints for system monitoring and liveness probes.

### 1.3 `app/crud/` (Data Access Layer)
Contains pure database interaction logic (Create, Read, Update, Delete) to keep routers clean.
- Matches the models layer (e.g., `crud_vehicle.py` manages querying vehicles).

### 1.4 `app/schemas/` (Pydantic Models)
Defines the data validation schemas for HTTP request bodies and responses. Ensures robust data typing before it reaches the CRUD layer.

### 1.5 `app/services/` (Business Logic)
Houses complex processing that doesn't belong in CRUD or routers.
- **`trip_analytics.py`**: Evaluates incoming locations to dynamically construct `Trip` records, detect stops, and calculate distances.
- **`trip_scoring.py`**: Algorithm that calculates the 0-100 driving score based on idle time and overspeed events.
- **`google_routes.py`**: Service integration with the external Google Routes API.

---

## 2. `dashboard/` (Frontend Service)
The Next.js 15 React application serving the user interface for fleet managers.

- **`package.json`**: NPM dependencies (React, Next.js, Tailwind, Recharts, Lucide).
- **`tailwind.config.js`**: Tailwind CSS configuration and theme definitions.
- **`next.config.js`**: Next.js compiler settings.

### 2.1 `dashboard/app/` (Next.js App Router)
Contains all page routes and layouts.
- **`layout.tsx`**: The root HTML layout, containing global navigation bars and contexts.
- **`page.tsx`**: The dashboard landing page (overview metrics).
- Subfolders (e.g., `vehicles/`, `tracking/`, `trips/`, `reports/`) contain their respective `page.tsx` defining that specific UI view.

### 2.2 `dashboard/components/` (React Components)
Reusable UI elements (buttons, cards, modals, charts, map views) used across multiple pages.

### 2.3 `dashboard/lib/` & `dashboard/utils/`
Helper functions, API client wrappers, and shared utility scripts for the frontend.

---

## 3. `alembic/` (Database Migrations)
Manages incremental schema updates to the PostgreSQL database.
- **`env.py`**: The Alembic environment configuration that loads SQLAlchemy models and runs migrations.
- **`versions/`**: Contains generated migration scripts (e.g., `create_vehicle_table.py`).

---

## 4. `scripts/` (Utilities)
Standalone Python scripts used for development and testing.
- **`telemetry_simulator.py`**: A vital development tool that simulates GPS trackers by sending fake HTTP POST location data to the backend. Useful for testing trip generation and live tracking without real devices.
- **`db_test.py` & `db_validate.py`**: Scripts to verify database connectivity and integrity.
- **`run_alembic.py`**: Wrapper to execute migrations.

---

## 5. `postman/`
Contains Postman JSON collections that can be imported to manually test the API endpoints during development.
