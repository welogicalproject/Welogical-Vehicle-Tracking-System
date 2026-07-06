# Developer Guide

Welcome to the Welogical Vehicle Tracking System (VTS)! This guide is designed for software engineers joining the project. It focuses on the internal mechanics of the codebase, how things are wired together, and how to safely extend the system.

---

## 1. Project Orientation

### What the project does
The VTS is a real-time tracking platform. It ingests high-frequency GPS coordinate payloads from physical tracking devices, stores them, processes them into distinct "Trips", evaluates driver behavior for infractions (like overspeeding), and displays this data on a real-time web dashboard.

### High-level architecture
- **Backend:** FastAPI (Python) serving REST APIs.
- **Database:** PostgreSQL accessed asynchronously via SQLAlchemy & asyncpg.
- **Frontend:** Next.js 15 (React) using Tailwind CSS.
- **External APIs:** Google Routes API for road-accurate trip distances.

### Core Terminology
- **Raw Packet:** The unmodified JSON string received from the GPS device.
- **Location Ping:** A validated GPS coordinate with speed and timestamp.
- **Trip:** A logical journey from a start location to an end location. Trips are dynamically calculated; a trip "starts" when the vehicle moves fast enough and "ends" when it idles long enough.
- **Event:** A significant occurrence (e.g., `OVERSPEED`, `LONG_IDLE`).
- **Driving Score:** A 0-100 metric calculated per trip, dropping points based on generated Events.
- **Driver Assignment:** The temporary link between a human driver and a vehicle.

---

## 2. How to Read the Codebase

Do not try to read everything at once. We recommend following the data flow:

1. **`app/config.py` & `.env.example`**: Start here to see what external settings configure the app.
2. **`app/models/`**: Read the SQLAlchemy models to understand the database schema and relationships. This is the foundation of the app.
3. **`app/schemas/`**: See how Pydantic translates raw JSON into safe Python objects.
4. **`app/crud/`**: Look at how the models and schemas are used to perform database operations.
5. **`app/services/`**: This is where the heavy lifting happens. Read `trip_analytics.py` to understand how raw locations are converted into Trips and Events.
6. **`app/routers/`**: See how the CRUD and Service layers are exposed as REST APIs.
7. **`app/main.py`**: Understand how all the routers and exception handlers are glued together into the FastAPI app.
8. **`dashboard/`**: Finally, move to the frontend to see how Next.js consumes the APIs.

*Why this order?* Following the architecture from the database up to the UI ensures you understand *what* data exists before you try to understand *how* it is displayed.

---

## 3. Backend Code Walkthrough

### Request Lifecycle
When a request hits the backend:
1. It enters `main.py` and matches a route in `app/routers/`.
2. **Dependency Injection:** The router requests an active database session (`db: AsyncSession = Depends(get_db)`). FastAPI provides this automatically.
3. **Validation:** FastAPI validates the incoming JSON against the Pydantic schema defined in `app/schemas/`.
4. **Service / CRUD Layer:** The router passes the validated schema and DB session to a function in `app/crud/` or `app/services/`.
5. **Business Logic:** The service executes logic, commits to the database, and returns an ORM model.
6. **Response:** FastAPI automatically serializes the returned ORM model back to JSON based on the `response_model` defined in the route.

### Database Session Flow
We use `asyncpg`. Every request receives an isolated `AsyncSession`. We do *not* pass sessions globally. The session is committed inside the CRUD/Service functions, or rolled back if an exception occurs.

### Error Handling & Logging
Custom exceptions are defined in `app/exceptions.py` and registered globally in `main.py`. If a CRUD operation fails to find a record, it should raise an `HTTPException(404)`. All significant actions use the python `logging` module configured via `app/logging_config.py`.

---

## 4. Frontend Code Walkthrough

### Routing and Layouts
The frontend uses the Next.js **App Router**. 
- The root layout (`dashboard/app/layout.tsx`) wraps the entire app, providing the global navigation sidebar and CSS imports.
- Subfolders in `dashboard/app/` (e.g., `trips/`, `vehicles/`) represent distinct URLs (`/trips`, `/vehicles`). Each contains a `page.tsx`.

### Components and API Integration
- Complex UI elements are extracted to `dashboard/components/`.
- Data is typically fetched inside `useEffect` hooks in client components, utilizing standard standard browser `fetch()` calls.

### State Management
State is kept localized using React's `useState`. We do not currently use heavy global state managers (like Redux) to keep the architecture simple.

---

## 5. Database Walkthrough

### Model Relationships
Read `app/models/`. You will notice heavy use of SQLAlchemy's `relationship()` function. For example, `Vehicle` has a one-to-many relationship with `Location`. These relationships allow us to use `selectinload` to eager-load related data without writing manual SQL JOINs.

### Migration Strategy
We use **Alembic**. You should never manually alter the database schema in PostgreSQL.
When you change a file in `app/models/`:
1. Run `alembic revision --autogenerate -m "description"`.
2. Review the generated script in `alembic/versions/` to ensure Alembic didn't make a mistake.
3. Run `alembic upgrade head`.

---

## 6. API Development Guide

**Scenario:** You need to add an endpoint to get a vehicle's current fuel level.
1. **Schema:** Create `VehicleFuelResponse` in `app/schemas/vehicle.py`.
2. **CRUD:** Add `get_vehicle_fuel(db, vehicle_id)` in `app/crud/vehicle.py`.
3. **Router:** In `app/routers/vehicle.py`, add `@router.get("/{vehicle_id}/fuel", response_model=VehicleFuelResponse)`.
4. **Logic:** Call the CRUD function from the Router function and return the data.

---

## 7. Frontend Development Guide

**Scenario:** You need to add a "Fuel Levels" page.
1. **Routing:** Create a folder `dashboard/app/fuel/`.
2. **Page:** Create `dashboard/app/fuel/page.tsx`.
3. **State:** Inside the page, use `useState` to hold an array of vehicles.
4. **Fetch:** Use `useEffect` to call `fetch('http://localhost:8000/api/v1/vehicles/{id}/fuel')`.
5. **Component:** Create a new `FuelChart` component in `dashboard/components/` and import it into your page, passing the fetched state as props.

---

## 8. Feature Development Workflow

*How a feature moves through the stack.*
**Example: Adding a "Maintenance Due" flag to Vehicles.**

1. **Database:** Edit `app/models/vehicle.py`. Add `maintenance_due = Column(Boolean, default=False)`.
2. **Migration:** Run `alembic revision --autogenerate` and `alembic upgrade head`.
3. **Schema:** Edit `app/schemas/vehicle.py`. Add `maintenance_due: bool` to the response schema.
4. **CRUD / API:** The existing `GET /vehicles/` route will automatically include the new field because the schema and ORM model map to each other.
5. **Frontend:** Edit `dashboard/app/vehicles/page.tsx` to render a red warning icon if `vehicle.maintenance_due` is true.

---

## 9. Debugging Guide

- **FastAPI / Backend:** Check the terminal output where Uvicorn is running. All `logging.info` and stack traces will appear there. If an API request fails, check the Swagger UI (`http://localhost:8000/docs`) to ensure your JSON payload matches the required Pydantic schema.
- **Database:** Use `scripts/db_test.py` to isolate connection issues. For logic issues, print the generated SQL by setting `echo=True` on the SQLAlchemy engine.
- **Frontend:** Use the Chrome Developer Tools. Check the "Network" tab to ensure API requests are not returning 404s or 422s.

---

## 10. Coding Standards

- **Python:** Strictly follow PEP8. Use Type Hints (`name: str`) everywhere. 
- **Next.js:** Use functional components and hooks. Prefer Tailwind CSS classes over custom CSS files. Use TypeScript interfaces for all component props.
- **Asynchronous Code:** Do not mix blocking and non-blocking code. Always `await` database calls in the backend.

---

## 11. Development Checklist

Before submitting a Pull Request, ensure:
- [ ] You have run `alembic revision` if you changed any database models.
- [ ] You have tested the new API endpoint in Swagger UI.
- [ ] The Next.js frontend compiles without TypeScript errors (`npm run build`).
- [ ] You have updated `.env.example` if you added new configuration variables.
- [ ] You have added any new endpoints to `API_REFERENCE.md`.

---

## 12. Maintenance Guide

When extending this project in the future, remember:
1. **Don't break the ingestion pipeline:** The `/locations/raw` endpoint must remain extremely fast. Do not add heavy, blocking calculations directly to the router. Offload complex analytics to background tasks or external services.
2. **Respect the Schema:** Rely on Pydantic and TypeScript. If you bypass type validation, you bypass the project's core safety nets.
3. **Database Locks:** When processing trips or updating route caches concurrently, ensure you are utilizing proper database locking (or avoiding race conditions) as demonstrated in the existing Route Cache implementation.
