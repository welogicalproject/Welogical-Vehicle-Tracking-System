<<<<<<< HEAD
# Vehicle Tracking System (VTS) - Backend & Dashboard

A premium, modular fleet monitoring solution composed of a **FastAPI** backend (storing telemetry in **PostgreSQL**) and a responsive **Next.js 15** analytics dashboard.

---

## Folder Structure

```
GPS_Project/
├── alembic.ini             # Alembic configuration
├── .env                    # Local environment settings
├── requirements.txt        # Backend dependencies
├── README.md               # Setup and usage guide
├── alembic/                # Migration scripts
│   ├── env.py
│   └── versions/
│       ├── 001_initial_migration.py
│       └── 002_timezone_aware.py
├── app/                    # FastAPI Backend Source
│   ├── main.py             # Entry point
│   ├── database.py         # DB connection manager
│   ├── config.py           # Configuration loader
│   ├── exceptions.py       # API Error handlers
│   ├── logging_config.py   # Colored stdout logger
│   ├── models/             # SQLAlchemy schemas
│   ├── schemas/            # Pydantic schemas
│   ├── crud/               # DB operation logic
│   └── routers/            # Router endpoints
├── postman/                # Postman collections
└── dashboard/              # Next.js Dashboard Frontend (NEW)
    ├── package.json        # Dependencies (React, Recharts, Lucide, Tailwind)
    ├── tsconfig.json       # TypeScript configuration
    ├── next.config.js      # Environment mapping
    ├── tailwind.config.js  # Dark theme configuration
    ├── postcss.config.js   # PostCSS configuration
    ├── app/                # Next.js pages & styling
    │   ├── layout.tsx      # Sidebar navigation wrapper
    │   ├── page.tsx        # Page 1: Overview
    │   ├── globals.css     # Global styles & glassmorphism tokens
    │   ├── vehicles/
    │   │   ├── page.tsx    # Page 2: Vehicle Management
    │   │   └── [id]/
    │   │       └── page.tsx # Page 3: Vehicle Details
    │   ├── packets/
    │   │   └── page.tsx    # Page 4: Raw Packet Monitor
    │   ├── analytics/
    │   │   └── page.tsx    # Page 5: Telemetry Analytics
    │   └── explorer/
    │       └── page.tsx    # Page 6: Database Explorer
    ├── components/         # React Components
    │   ├── sidebar.tsx     # Navigation sidebar
    │   └── ui/             # Layout components (Card, Table, Button, etc.)
    └── lib/
        ├── api.ts          # API fetch client
        └── utils.ts        # Helper functions (cn classnames merger)
=======
# Welogical Vehicle Tracking System (VTS)

## 1. Project Overview
**Purpose:** A real-time vehicle tracking and fleet management system.
**Objectives:** Provide an end-to-end solution for capturing telemetry, tracking vehicles, processing trips, assigning drivers, enforcing geofences, sending OTA commands, and calculating driving scores.
**Problem Statement:** Fleet operators need a unified dashboard to monitor live locations, analyze historical trips, enforce geo-fencing, and monitor driver behavior safely and efficiently.
**Key Features:**
- Real-time GPS location ingestion and visualization via Next.js and Google Maps.
- Automated trip calculation, stop detection, and driving score generation.
- Real-time Google Routes API integration for optimized route distance/duration.
- Comprehensive driver, vehicle, and device configuration management.
- Over-the-air (OTA) device command scheduling and logging.
**System Capabilities:** High-throughput async ingestion via FastAPI, persistent reliable storage with PostgreSQL, and a responsive Next.js 15 dashboard.

---

## 2. Complete System Architecture
**Overall architecture:**
The system comprises a FastAPI Python backend serving REST APIs, a PostgreSQL database for persistent storage (accessed asynchronously via asyncpg/SQLAlchemy), and a React/Next.js frontend.
**Data Flow:**
GPS Tracker -> HTTP POST -> FastAPI Backend -> Validation (Pydantic) -> PostgreSQL (Raw Packets, Locations, Events) -> Background processing (Trip analytics) -> Next.js Frontend.

```mermaid
graph TD
    GPS[GPS Trackers / Telemetry Simulator] -->|HTTP POST JSON| API[FastAPI Backend]
    API --> DB[(PostgreSQL Database)]
    API <-->|HTTP GET/POST| WEB[Next.js Dashboard]
    WEB --> USER[Fleet Manager / User]
    API -->|Fetch Routes| GOOGLE[Google Routes API]
```

```mermaid
graph TD
    subgraph Data Processing
    RAW[Raw Packet Ingestion] --> LOC[Location Processing]
    LOC --> EVT[Event Generation]
    LOC --> TRIP[Trip Analytics & Stop Detection]
    TRIP --> SCORE[Driving Score Calculation]
    end
>>>>>>> ec9e098 (Add complete project documentation and handover guides)
```

---

<<<<<<< HEAD
## Backend Setup (FastAPI & PostgreSQL)

### 1. PostgreSQL Local Database Setup
Connect to your local PostgreSQL instance and execute:
```sql
CREATE DATABASE vts_db;
```

Verify your credentials in your local `.env` configuration file:
- `DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/vts_db` (for Alembic migrations)
- `ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/vts_db` (for async server connections)

### 2. Install Dependencies & Run Migrations
1. Activate virtual environment and install packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```
3. Run the development web server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app --reload-dir alembic --reload-include "*.py" --reload-exclude venv --reload-exclude .git --reload-exclude __pycache__ --reload-exclude dashboard/node_modules --reload-exclude dashboard/.next
   ```
   FastAPI will start on [http://localhost:8000](http://localhost:8000).

---

## Frontend Setup (Next.js Dashboard)

### 1. Installation
1. Navigate to the `dashboard/` directory in a new terminal:
   ```bash
   cd dashboard
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```

### 2. Start the Frontend Web Server
1. Launch the Next.js development server:
   ```bash
   npm run dev
   ```
   The dashboard will start on [http://localhost:3000](http://localhost:3000).

---

## Dashboard Pages & Features

### Page 1: Dashboard Overview
- **Key Widgets**: Metric cards tracking total vehicles, total logged coordinates, total raw packets, active online count, and the latest ingest timestamp.
- **Auto-polling**: Automatically fetches latest fleet statistics every 10 seconds.
- **Activity Table**: Lists registered vehicles sorted by most recently seen, including vehicle status badges.

### Page 2: Vehicle Management
- **Search & Filters**: Search vehicles by name or device hardware UID. Filter inventory lists by vehicle type using a dropdown selector.
- **Badge Indicators**:
  - `Online` (green, pulsing): active telemetry received in the last 5 minutes.
  - `Idle` (amber): last seen active between 5 and 30 minutes ago.
  - `Offline` (red): last seen over 30 minutes ago or never connected.

### Page 3: Vehicle Details (`/vehicles/[id]`)
- **Profile Info**: Static metadata representing the vehicle's profile.
- **Latest Logs**: Active metrics showing last coordinates, speed, and altitude.
- **History Table**: Chronological table showing the vehicle's last 50 telemetry points.
- **Metrics Stats**: Calculated average and maximum speeds along with cumulative points count.

### Page 4: Raw Packet Monitor
- **Ingestion Log**: Displays row records of parsed telemetry log packages from `raw_packets`.
- **JSON Viewer**: Click on any row in the table to expand a styled JSON viewer displaying the complete nested payload data.

### Page 5: Telemetry Analytics
- **Speed Timeline**: Chart depicting speed over time for coordinates updates.
- **Ingest Volume**: Area chart tracking logged points per calendar day.
- **Distribution Chart**: Bar graph comparing cumulative location packages produced by each vehicle.

### Page 6: Database Explorer
- **Direct SQL Tables View**: Explores table rows directly from `vehicles`, `locations`, and `raw_packets`.
- **Paging Controllers**: Uses `Previous` and `Next` buttons to shift database page offsets using standard `skip`/`limit` SQL queries.

=======
## 3. Repository Structure
- **`app/`**: Core FastAPI backend application.
  - `models/`: SQLAlchemy database models (`vehicle.py`, `location.py`, `trip.py`, `driver.py`, `event.py`, `device_config.py`, `device_command.py`, `route_cache.py`, `raw_packet.py`).
  - `routers/`: FastAPI route definitions covering all 10 major API domains.
  - `schemas/`: Pydantic validation schemas.
  - `crud/`: Database interaction logic (Create, Read, Update, Delete).
  - `services/`: Business logic (`trip_analytics.py`, `trip_scoring.py`, `google_routes.py`, `trip_replay.py`).
- **`dashboard/`**: Next.js frontend application.
  - `app/`: Next.js App Router pages (tracking, vehicles, reports, commands, geofences, users, trips).
  - `components/`: Reusable React components.
  - `lib/`, `hooks/`, `types/`: Frontend utilities.
- **`alembic/`**: Database migration scripts for maintaining schema changes.
- **`scripts/`**: Utility scripts (`telemetry_simulator.py`, `db_test.py`, `db_validate.py`, `verify_cache.py`).

---

## 4. Technology Stack
- **Backend:** FastAPI (Python) - Chosen for its speed, asynchronous support, and automatic OpenAPI documentation.
- **Database:** PostgreSQL with SQLAlchemy (Asyncpg) - Relational integrity with high-performance async database access.
- **Migrations:** Alembic - Standard tool for SQLAlchemy schema migrations.
- **Frontend:** Next.js 15, React 19, Tailwind CSS - Modern, fast, and responsive UI framework. Recharts for analytics visualization.
- **Maps:** Google Maps API & Google Routes integration - Reliable mapping and accurate trip route distance/duration calculation.

---

## 5. Installation Guide
**Prerequisites (Fresh Computer):**
- **Git:** Install from [git-scm.com](https://git-scm.com/).
- **Python 3.10+:** Install from [python.org](https://python.org).
- **Node.js 20+:** Install from [nodejs.org](https://nodejs.org/).
- **PostgreSQL 14+:** Install from [postgresql.org](https://postgresql.org/).

Ensure `python`, `node`, `npm`, and `psql` are accessible in your system PATH.

---

## 6. Clone and Setup
```bash
# 1. Clone Repository
git clone https://github.com/welogicalproject/Welogical-Vehicle-Tracking-System.git
cd Welogical-Vehicle-Tracking-System

# 2. Database Setup (Ensure PostgreSQL is running)
psql -U postgres -c "CREATE DATABASE vts_db;"

# 3. Environment Variables
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 4. Backend Setup
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 5. Frontend Setup
cd dashboard
npm install
```

---

## 7. Environment Variables
| Variable Name | Purpose | Example Value | Required |
|---------------|---------|---------------|----------|
| `APP_NAME` | Name of the backend application | `Vehicle Tracking System Backend` | Yes |
| `APP_ENV` | Environment mode | `development` | Yes |
| `DEBUG` | Enable debug mode | `true` | Yes |
| `HOST` | Backend server host | `0.0.0.0` | Yes |
| `PORT` | Backend server port | `8000` | Yes |
| `DATABASE_URL` | Sync database connection URL | `postgresql://user:pass@127.0.0.1:5432/vts_db` | Yes |
| `ASYNC_DATABASE_URL`| Async database connection URL | `postgresql+asyncpg://user:pass@127.0.0.1:5432/vts_db` | Yes |
| `LOG_LEVEL` | Python logging level | `INFO` | Yes |
| `GOOGLE_ROUTES_ENABLED` | Toggle Google Routes integration | `true` | Yes |
| `GOOGLE_ROUTES_API_KEY` | API Key for Google Routes | `AIzaSy...` | Optional |
| `SAVE_RAW_GOOGLE_RESPONSES` | Save raw JSON responses for debugging | `false` | Yes |
| `GOOGLE_ROUTES_TIMEOUT_SECONDS` | API request timeout limit | `5` | Yes |
| `GOOGLE_ROUTES_MONTHLY_LIMIT` | Monthly quota limit for Routes API | `9500` | Yes |
| `GOOGLE_ROUTES_WARNING_THRESHOLD` | Threshold to trigger API limit warnings | `8000` | Yes |

---

## 8. Database Documentation
Detailed in [DATABASE.md](./docs/DATABASE.md). Contains fully documented models for vehicles, drivers, driver assignments, locations, trips, events, device_configs, device_commands, command_logs, raw_packets, and route_caches.

---

## 9. API Documentation
Detailed in [API_REFERENCE.md](./docs/API_REFERENCE.md). Covers endpoints for `/vehicles`, `/locations`, `/trips`, `/events`, `/drivers`, `/device_config`, `/device_command`, `/routes`, and `/health`.

---

## 10. Project Workflow
1. **Device:** GPS tracker sends JSON telemetry payload.
2. **Backend:** FastAPI receives data at `/api/v1/locations/raw`.
3. **Database:** Saves to `raw_packets` and validates into `locations`.
4. **Analytics:** Evaluates for overspeeding, stops, and trip boundaries. Deducts from driving score on infractions. Updates `trips` and `events`.
5. **Google Routes:** If configured, fetches true road distance for trips and caches in `route_cache`.
6. **Frontend:** Dashboard fetches active trips, driver assignments, and live locations to display on the map.

---

## 11. Running the Project
**Backend:**
```bash
# Ensure virtual environment is activated
uvicorn app.main:app --reload
# Access Swagger API documentation at http://localhost:8000/docs
```
**Frontend:**
```bash
cd dashboard
npm run dev
# Access the Dashboard at http://localhost:3000
```
**Telemetry Simulator:**
```bash
# Simulate live driving data (Run from project root)
python scripts/telemetry_simulator.py
```

---

## 12. Development Guide
- **Adding an API:** Create schema in `app/schemas/`, CRUD operations in `app/crud/`, route in `app/routers/`, then include the router via `app.include_router` in `app/main.py`.
- **Adding a Database Model:** Create class in `app/models/`, import into `app/models/__init__.py`, generate migration with `alembic revision --autogenerate -m "msg"`, then apply with `alembic upgrade head`.
- **Adding a Frontend Page:** Add a new directory under `dashboard/app/` (e.g., `dashboard/app/new-feature/page.tsx`).

---

## 13. Troubleshooting Guide
- *Database Connection Error:* Ensure PostgreSQL service is running on port 5432 and credentials in `.env` perfectly match.
- *Alembic Target Database is not up to date:* Run `alembic upgrade head` before starting the server.
- *CORS Errors:* Ensure the frontend URL matches the `allow_origins` array configured in `app/main.py`.
- *Google Routes Failing:* Check `GOOGLE_ROUTES_API_KEY` in `.env`. Ensure billing is enabled on the Google Cloud Console.

---

## 14. Deployment Guide
Prerequisites: Docker, Nginx, PostgreSQL server.
Currently intended for local or cloud deployment using standard WSGI/ASGI servers (e.g. Uvicorn wrapped in Gunicorn) for the backend and Vercel/Node for the Next.js frontend. PostgreSQL should be managed by a robust cloud provider (e.g., AWS RDS).

---

## 15. Security
- Secrets and `.env` files are ignored by git (via `.gitignore`) and are never committed.
- Incoming GPS payloads are strictly validated using Pydantic.
- API keys (like Google Maps) are loaded dynamically via environment variables.

---

## 16. Future Improvements
- Implement JWT Authentication, User Accounts, and Role-Based Access Control (RBAC).
- Dockerize the application (create `docker-compose.yml`) for instant one-click deployment.
- Integrate WebSockets for pushing real-time live-tracking location updates to the frontend instead of client-side polling.

---

## 17. Contributing
Developers should follow the existing PEP8 standards for Python (FastAPI) and ESLint conventions for Next.js. All database schema changes must be accompanied by an Alembic migration.

---

## 18. License
Copyright (c) Welogical. All rights reserved.
>>>>>>> ec9e098 (Add complete project documentation and handover guides)
