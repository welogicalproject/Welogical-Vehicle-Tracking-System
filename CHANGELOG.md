# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.1.0] - 2026-07-12
### System Stabilization & State Synchronization

### Added
- **Global State Context (`FleetProvider`)**: Centralized client-side state as the single source of truth, synchronizing Overview dashboards, vehicle listings, and active map views instantly.
- **Unified WebSocket Service**: Embedded listeners directly inside `FleetProvider` on the `telemetry`, `vehicles`, and `events` topics for real-time updates and silent database reloads.
- **Interactive Initializer Map Click**: Developed a map coordinate initialization workflow with visual banners and confirmation dialogs supporting Nominatim Address search, raw map clicks, and headquarters defaults.
- **Header Action Dropdowns**: Added stateful drop-down wrappers for unread system notification logs (with mark-as-read actions) and active admin account menus (with Sign Out).
- **Drift Prevention Check**: Implemented server startup hooks comparing database migration state against Alembic HEAD to block boot on schema mismatches.

### Fixed
- Fixed dashboard count mismatches after vehicle deletion.
- Solved missing Next.js Suspense boundary errors on `useSearchParams()`.
- Added missing properties (like altitude) and type definitions globally.

## [v1.0.0] - 2026-07-06
### Initial Company Release

### Added

**Core Infrastructure**
- Fully asynchronous FastAPI backend architecture.
- PostgreSQL database integration using `asyncpg` and SQLAlchemy 2.0.
- Database schema version control and migration management using Alembic.
- Pydantic models for robust environment configuration management and API validation.
- Next.js 15 (App Router) React frontend utilizing Tailwind CSS.

**Telemetry & Data Processing**
- Raw GPS packet ingestion endpoint (`/api/v1/locations/raw`) for high-throughput tracking.
- Automated `Trip` logic engine that dynamically generates journeys based on vehicle speed thresholds.
- `Event` detection engine for generating infractions (e.g., `OVERSPEED`, `STOP`, `LONG_IDLE`).
- Algorithmic driving score calculation (0-100) per trip based on accrued infraction penalties.

**Integrations**
- Google Routes API integration for fetching road-accurate trip distances and durations.
- High-performance Route Cache mechanism (MD5 coordinate hashing) to minimize external API costs and latencies.

**Fleet Management**
- Vehicle Management: Full CRUD APIs for registering and configuring tracking devices.
- Driver Management: CRUD APIs for managing personnel.
- Driver Assignments: System for temporarily assigning drivers to specific vehicles with historical assignment tracking.
- Device Configuration: Infrastructure for sending Over-The-Air (OTA) parameter updates to GPS trackers.
- Device Commands: Infrastructure for queuing OTA commands (e.g., Engine Cutoff) and tracking execution logs.

**Dashboard (Frontend)**
- Real-time vehicle overview and status pages.
- Historical trip reports and driving score analytics.
- Integrated map views for plotting coordinates and historical trip routes.

**Documentation**
- `README.md`: Comprehensive project overview and setup instructions.
- `PROJECT_STRUCTURE.md`: Detailed breakdown of the repository folder tree and file responsibilities.
- `LOCAL_SETUP.md`: Foolproof, zero-to-hero local installation guide.
- `ARCHITECTURE.md`: High-level system design and data flow diagrams.
- `API_REFERENCE.md`: Complete REST API endpoint documentation with JSON payloads.
- `DATABASE.md`: Schema definitions, ER diagrams, and Alembic instructions.
- `DEVELOPER_GUIDE.md`: Deep-dive onboarding document for new engineers.
- `HANDOVER.md`: Official project transfer document detailing status and future steps.

### Infrastructure
- Configured `.env.example` to define all required application, database, and external API variables.
- Created `scripts/telemetry_simulator.py` to mock physical GPS devices for local development testing.
- Configured `.gitignore` to protect sensitive files (`.env`), Python caches, and Node modules from being committed.
