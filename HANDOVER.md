# Project Handover Document

This document serves as the official engineering handover for the Welogical Vehicle Tracking System (VTS). It provides the next developer or intern taking ownership with the context required to understand, maintain, and extend the project securely and confidently.

---

## 1. Project Overview
- **Purpose:** A real-time vehicle tracking platform for ingesting GPS telemetry and managing fleets.
- **Business Objective:** Provide fleet operators with actionable insights through automated trip generation, driving score calculations, and real-time mapping.
- **Current Implementation Status:** Stable `v1.1.0` release. The core pipeline (device -> backend -> database -> frontend) is fully operational with real-time state synchronization.
- **Major Capabilities:**
  - High-throughput asynchronous GPS packet ingestion.
  - Automated Trip and Event (Overspeed/Idle) generation logic.
  - Google Routes API integration for true road distance calculation.
  - Full management of Vehicles, Drivers, and Driver Assignments.
  - Next.js Dashboard for live monitoring and historical reporting.
  - Live WebSocket channels for telemetry updates, vehicle lifecycle states, and events.
  - Database schema integrity checks on startup.

---

## 2. Current Project Status
- **Completed Features:** GPS ingestion, Trip analytics, Event tracking, Driver assignment, Google Routes caching, REST API layer, Database migrations, Next.js Dashboard, WebSockets synchronization (`telemetry`, `vehicles`, `events` topics), global state provider (`FleetProvider`), and visual starting coordinates initializer.
- **Stable Components:** The FastAPI backend endpoints, SQLAlchemy models, Alembic migrations, Pydantic schemas, React context hooks, and map engine adapter layer.
- **Components Still Under Development:** While the API supports Over-The-Air (OTA) device commands (`device_commands` table), the hardware-specific socket layer to transmit commands to physical devices is mocked/pending vendor-specific protocols.
- **Known Limitations:** OTA command execution is simulation-only. Configuration options are locally persisted or environment-backed.

---

## 3. Repository Structure
- **`app/`**: The FastAPI Python backend (models, routers, schemas, CRUD, services).
- **`dashboard/`**: The Next.js 15 React frontend application.
- **`alembic/`**: Database schema migration scripts.
- **`scripts/`**: Developer utilities, including the `telemetry_simulator.py`.

*For an exhaustive breakdown of every file, please review [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md).*

---

## 4. Documentation Index
The project has been exhaustively documented. Read them in this recommended order:

| Document | Purpose |
|----------|---------|
| [README.md](./README.md) | High-level project overview. |
| [LOCAL_SETUP.md](./docs/LOCAL_SETUP.md) | Step-by-step local installation guide. |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System architecture and data flow diagrams. |
| [DATABASE.md](./docs/DATABASE.md) | Database schema, relationships, and ER diagrams. |
| [API_REFERENCE.md](./docs/API_REFERENCE.md) | REST API endpoints, methods, and JSON payloads. |
| [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) | Comprehensive folder organization. |
| [DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md) | Internal engineering onboarding and conventions. |
| [CHANGELOG.md](./CHANGELOG.md) | Version history and released features. |
| [HANDOVER.md](./HANDOVER.md) | This company handover package. |

---

## 5. Development Environment
To work on this project locally, you must have the following installed:
- **Operating System:** Windows, macOS, or Linux.
- **Python:** `v3.10` or higher (Backend).
- **Node.js:** `v20.x` LTS or higher (Frontend).
- **PostgreSQL:** `v14` or higher (Database).
- **Git:** Version control.

*Detailed installation instructions can be found in [LOCAL_SETUP.md](./docs/LOCAL_SETUP.md).*

---

## 6. Running the Project
- **Database:** Ensure PostgreSQL is running and `vts_db` exists. Apply migrations with `alembic upgrade head`.
- **Backend:** Run inside a Python virtual environment using `uvicorn app.main:app --reload` from the root directory.
- **Frontend:** Run `npm run dev` from inside the `dashboard/` directory.
- **Simulator:** Run `python scripts/telemetry_simulator.py` to generate fake GPS traffic.

---

## 7. Configuration
All environment-specific configuration is handled via a `.env` file located in the project root.
- **Environment Files:** Never commit `.env` to Git. Use `.env.example` as a template.
- **Secrets:** Database passwords and external API keys are loaded dynamically by `app/config.py` using Pydantic Settings.
- **Google Services:** The `GOOGLE_ROUTES_API_KEY` is required if `GOOGLE_ROUTES_ENABLED` is set to true. Ensure the associated Google Cloud project has billing enabled and quotas configured to prevent cost overruns.

---

## 8. Architecture Summary
The application follows a decoupled 3-tier architecture. Hardware devices send JSON over HTTP to a FastAPI backend. The backend strictly validates data, stores it in PostgreSQL asynchronously via asyncpg, and performs background trip evaluations. The Next.js client renders the UI by consuming the FastAPI endpoints via standard HTTP REST calls.

*Diagrams available in [ARCHITECTURE.md](./docs/ARCHITECTURE.md).*

---

## 9. Database Summary
The database is highly relational. The core entity is the `Vehicle`. Vehicles have many `Locations` (GPS pings). The business logic dynamically groups `Locations` into `Trips`. Anomalies trigger `Events`. The database utilizes `alembic` to safely manage schema drift over time.

*Complete schema definition available in [DATABASE.md](./docs/DATABASE.md).*

---

## 10. API Summary
The REST API is versioned at `/api/v1/`. It exposes CRUD operations for entities (`/vehicles`, `/drivers`) and ingestion endpoints for telemetry (`/locations/raw`). It generates an automatic OpenAPI specification (Swagger) available at `/docs` when the server is running.

*Complete endpoint definitions available in [API_REFERENCE.md](./docs/API_REFERENCE.md).*

---

## 11. Deployment Notes
- **Prerequisites:** A production-grade PostgreSQL instance (e.g., AWS RDS), a Python WSGI/ASGI server (e.g., Gunicorn wrapping Uvicorn), and a Node.js hosting provider (e.g., Vercel, AWS ECS).
- **Database Migrations:** You **must** run `alembic upgrade head` against the production database before booting the backend application.
- **Configuration:** Ensure the production server has all variables from `.env.example` injected into its environment securely (e.g., AWS Secrets Manager, Vercel Environment Variables).

---

## 12. Maintenance Guide
- **Adding APIs:** Define the Pydantic schema first, build the CRUD logic, and then expose it in a Router.
- **Modifying the Database:** Edit the SQLAlchemy model in `app/models/`, run `alembic revision --autogenerate`, verify the generated script, and apply it.
- **Adding UI Pages:** Create a new folder/`page.tsx` within the `dashboard/app/` directory utilizing the Next.js App Router.

*For strict coding standards and a PR checklist, see the [DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md).*

---

## 13. Known Limitations
- **Polling UI:** The frontend Dashboard currently utilizes client-side polling to refresh live map data.
- **Authentication:** The current repository does not implement user authentication (JWT/OAuth) or Role-Based Access Control (RBAC). The API is currently open for internal network use.
- **Hardware Integration:** The backend receives generic JSON payloads. Specific proprietary hardware protocols (e.g., Teltonika TCP parsers) must be implemented via a translation layer before hitting `/locations/raw`.

---

## 14. Future Improvements
1. **WebSocket Integration:** Replace frontend polling with WebSocket connections for true, low-latency live map tracking.
2. **User Authentication:** Implement JWT-based login for fleet managers.
3. **Dockerization:** Create `Dockerfile` and `docker-compose.yml` definitions for seamless local deployments and CI/CD pipelines.
4. **Hardware TCP Servers:** Build dedicated TCP listener microservices to parse proprietary hardware protocols and forward them to the generic FastAPI ingestion endpoint.

---

## 15. Handover Checklist
Before this project is officially transitioned, we verify:
- [x] Documentation is 100% complete.
- [x] Database schema is documented and migrated.
- [x] APIs are fully documented.
- [x] Local setup guide is verified for brand-new machines.
- [x] Secrets are strictly excluded from source control.
- [x] `.gitignore` is correctly configured.
- [x] Repository is clean, stable, and ready for further development.
- [x] Codebase is ready for production deployment configuration.
