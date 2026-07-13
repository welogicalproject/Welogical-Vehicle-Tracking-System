# Welogical Vehicle Tracking System (VTS) - Backend & Dashboard

A premium, modular fleet monitoring solution composed of a **FastAPI** backend (storing telemetry in **PostgreSQL**) and a responsive **Next.js 15** analytics dashboard.

---

## 1. Project Overview
* **Purpose:** A real-time vehicle tracking and fleet management platform.
* **Objectives:** Provide an end-to-end solution for capturing telemetry, tracking vehicles, processing trips, assigning drivers, enforcing geofences, sending OTA commands, and calculating driving scores.
* **Problem Statement:** Fleet operators need a unified dashboard to monitor live locations, analyze historical trips, enforce geo-fencing, and monitor driver behavior safely and efficiently.
* **Key Features:**
  - Real-time GPS location ingestion and visualization via Next.js and Google Maps.
  - Automated trip calculation, stop detection, and driving score generation.
  - Real-time Google Routes API integration for optimized route distance/duration.
  - Comprehensive driver, vehicle, and device configuration management.
  - Over-the-air (OTA) device command scheduling and logging.
* **System Capabilities:** High-throughput async ingestion via FastAPI, persistent reliable storage with PostgreSQL, and a responsive Next.js 15 dashboard.

---

## 2. Complete System Architecture
* **Overall Architecture:** The application follows a decoupled 3-tier architecture. Hardware devices send JSON over HTTP to a FastAPI backend. The backend strictly validates data, stores it in PostgreSQL asynchronously via asyncpg, and broadcasts updates over WebSockets. The Next.js client establishes live WebSocket channels to keep the UI in sync, consuming REST endpoints for manual configurations.
* **Data Flow:**
  GPS Tracker / Simulator -> HTTP POST -> FastAPI Backend -> Validation (Pydantic) -> PostgreSQL (Raw Packets, Locations, Events) & WebSockets -> Live Global state context -> Next.js Frontend.

```mermaid
graph TD
    GPS[GPS Trackers / Telemetry Simulator] -->|HTTP POST JSON| API[FastAPI Backend]
    API --> DB[(PostgreSQL Database)]
    API <-->|HTTP & WebSockets| WEB[Next.js Dashboard]
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
```

---

## 3. Repository Folder Structure

```
Welogical-Vehicle-Tracking-System/
├── alembic.ini             # Alembic configuration
├── .env                    # Local environment settings
├── requirements.txt        # Backend dependencies
├── README.md               # Setup and usage guide
├── alembic/                # Migration scripts
│   ├── env.py
│   └── versions/           # Incremental schema versions (001_initial to 22a74425feb4)
├── app/                    # FastAPI Backend Source
│   ├── main.py             # Entry point
│   ├── database.py         # DB connection manager
│   ├── config.py           # Configuration loader
│   ├── exceptions.py       # API Error handlers
│   ├── logging_config.py   # Colored logger
│   ├── models/             # SQLAlchemy schemas
│   ├── schemas/            # Pydantic schemas
│   ├── crud/               # DB operation logic
│   ├── routers/            # Router endpoints
│   └── utils/
│       └── migrations.py   # Startup database check
├── postman/                # Postman collections
└── dashboard/              # Next.js Dashboard Frontend
    ├── package.json        # Dependencies (React, Recharts, Lucide, Tailwind)
    ├── tsconfig.json       # TypeScript configuration
    ├── next.config.js      # Environment mapping
    ├── tailwind.config.js  # Dark theme configuration
    ├── app/                # Next.js pages & styling
    │   ├── layout.tsx      # Root layout, wraps FleetProvider
    │   ├── page.tsx        # Page 1: Overview
    │   ├── globals.css     # Global styles & tokens
    │   ├── vehicles/
    │   │   └── page.tsx    # Page 2: Vehicle Inventory
    │   ├── tracking/
    │   │   └── page.tsx    # Page 3: Live Map Tracking & Coordinates Initializer
    │   ├── trips/
    │   │   └── page.tsx    # Page 4: Trip Management & behavior scores
    │   ├── analytics/
    │   │   └── page.tsx    # Page 5: Telemetry Analytics
    │   └── explorer/
    │       └── page.tsx    # Page 6: Database Explorer
    ├── components/         # React Components
    │   ├── sidebar.tsx     # Navigation sidebar
    │   ├── header.tsx      # Header containing live notifications bell and admin profiles
    │   └── ui/             # Card, Table, Button, etc.
    ├── context/
    │   └── FleetContext.tsx # Global context & WebSocket manager (Single Source of truth)
    └── lib/
        ├── api.ts          # API fetch client
        └── utils.ts        # Helper functions (cn classnames merger)
```

---

## 4. Technology Stack
* **Backend:** FastAPI (Python) - Chosen for its speed, asynchronous support, and automatic OpenAPI documentation.
* **Database:** PostgreSQL with SQLAlchemy (Asyncpg) - Relational integrity with high-performance async database access.
* **Migrations:** Alembic - Standard tool for SQLAlchemy schema migrations.
* **Frontend:** Next.js 15, React 19, Tailwind CSS - Modern, fast, and responsive UI framework. Recharts for analytics visualization.
* **Maps:** Google Maps API & Google Routes integration - Reliable mapping and accurate trip route distance/duration calculation.

---

## 5. Environment Variables
All environment-specific configuration is handled via a `.env` file located in the project root. Never commit `.env` to Git. Use `.env.example` as a template.

| Variable Name | Purpose | Example Value | Required |
|---------------|---------|---------------|----------|
| `APP_NAME` | Name of the backend application | `Vehicle Tracking System Backend` | Yes |
| `APP_ENV` | Environment mode | `development` | Yes |
| `DEBUG` | Enable debug mode | `true` | Yes |
| `HOST` | Backend server host | `0.0.0.0` | Yes |
| `PORT` | Backend server port | `8000` | Yes |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `http://localhost:3000,http://127.0.0.1:3000` | Yes |
| `DATABASE_URL` | Sync database connection URL | `postgresql://user:pass@127.0.0.1:5432/vts_db` | Yes |
| `ASYNC_DATABASE_URL`| Async database connection URL (auto-derived if blank) | `postgresql+asyncpg://user:pass@127.0.0.1:5432/vts_db` | Optional |
| `LOG_LEVEL` | Python logging level | `INFO` | Yes |
| `GOOGLE_ROUTES_ENABLED` | Toggle Google Routes integration | `false` | Yes |
| `GOOGLE_ROUTES_API_KEY` | API Key for Google Routes | `AIzaSy...` | Optional |
| `SAVE_RAW_GOOGLE_RESPONSES` | Save raw JSON responses for debugging | `false` | Yes |
| `GOOGLE_ROUTES_TIMEOUT_SECONDS` | API request timeout limit | `5` | Yes |
| `GOOGLE_ROUTES_MONTHLY_LIMIT` | Monthly quota limit for Routes API | `9500` | Yes |
| `GOOGLE_ROUTES_WARNING_THRESHOLD` | Threshold to trigger API limit warnings | `8000` | Yes |

---

## 6. Running the Project Locally

### Prerequisites
* **Python 3.12.9**
* **Node.js 20+**
* **PostgreSQL 14+**

### Step 1: Database Setup
Connect to your local PostgreSQL instance and execute:
```sql
CREATE DATABASE vts_db;
```

### Step 2: Backend Setup
1. Copy environment template and configure credentials:
   ```bash
   cp .env.example .env
   ```
2. Activate virtual environment and install packages:
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run database migrations:
   ```bash
   alembic upgrade head
   ```
4. Run the web server:
   ```bash
   uvicorn app.main:app --reload
   ```
   FastAPI will start on [http://localhost:8000](http://localhost:8000). Access Swagger API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Step 3: Frontend Setup
1. Navigate to the `dashboard/` directory in a new terminal:
   ```bash
   cd dashboard
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Launch the Next.js development server:
   ```bash
   npm run dev
   ```
   The dashboard will start on [http://localhost:3000](http://localhost:3000).

### Step 4: Simulator (Optional)
To generate fake GPS traffic and verify data flow, open a third terminal, activate the venv, and run:
```bash
cd simulator
python simulator.py
```

---

## 7. Dashboard Pages & Features

* **Page 1: Dashboard Overview**
  - Metric cards tracking total vehicles, total logged coordinates, total raw packets, active online count, and the latest ingest timestamp.
  - Auto-polling: Automatically fetches latest fleet statistics every 10 seconds.
  - Activity Table: Lists registered vehicles sorted by most recently seen, including vehicle status badges.
* **Page 2: Vehicle Management**
  - Search & Filters: Search vehicles by name or device hardware UID. Filter inventory lists by vehicle type using a dropdown selector.
  - Badge Indicators: `Online` (green, pulsing), `Idle` (amber), and `Offline` (red) based on last-seen intervals.
* **Page 3: Vehicle Details (`/vehicles/[id]`)**
  - Profile Info: Static metadata representing the vehicle's profile.
  - Latest Logs: Active metrics showing last coordinates, speed, and altitude.
  - History Table: Chronological table showing the vehicle's last 50 telemetry points.
  - Metrics Stats: Calculated average and maximum speeds along with cumulative points count.
* **Page 4: Raw Packet Monitor**
  - Ingestion Log: Displays row records of parsed telemetry log packages from `raw_packets`.
  - JSON Viewer: Click on any row in the table to expand a styled JSON viewer displaying the complete nested payload data.
* **Page 5: Telemetry Analytics**
  - Speed Timeline: Chart depicting speed over time for coordinates updates.
  - Ingest Volume: Area chart tracking logged points per calendar day.
  - Distribution Chart: Bar graph comparing cumulative location packages produced by each vehicle.
* **Page 6: Database Explorer**
  - Direct SQL Tables View: Explores table rows directly from `vehicles`, `locations`, and `raw_packets`.
  - Paging Controllers: Uses `Previous` and `Next` buttons to shift database page offsets using standard `skip`/`limit` SQL queries.

---

## 8. Development & Project Conventions
* **Adding APIs:** Define the Pydantic schema first (`app/schemas/`), build the CRUD logic (`app/crud/`), expose in a Router (`app/routers/`), and register the router inside `app/main.py`.
* **Modifying the Database:** Edit the SQLAlchemy model in `app/models/`, run `alembic revision --autogenerate`, verify the revision file, and apply it.
* **Adding UI Pages:** Create a new folder/`page.tsx` within the `dashboard/app/` directory utilizing Next.js App Router conventions.
* **Code Style:** PEP8 rules for Python (backend) and ESLint rules for TypeScript (frontend). All database modifications must utilize Alembic migration scripts.

---

## 9. Security
- Secrets and `.env` files are ignored by git (via `.gitignore`) and are never committed.
- Incoming GPS payloads are strictly validated using Pydantic.
- API keys (like Google Maps) are loaded dynamically via environment variables.

---

## 10. Future Improvements
- Implement JWT Authentication, User Accounts, and Role-Based Access Control (RBAC).
- Dockerize the application (using `docker-compose.yml`) for instant one-click deployment.
- Integrate WebSockets for pushing real-time live-tracking location updates to the frontend instead of client-side polling.

---

## 11. Support & License
Copyright (c) Welogical. All rights reserved.
For database details, check [DATABASE.md](./docs/DATABASE.md). For REST API definitions, see [API_REFERENCE.md](./docs/API_REFERENCE.md).
