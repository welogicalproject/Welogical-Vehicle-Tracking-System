# Post-Deployment Verification Checklist

Use this checklist to verify that the backend is fully operational and integrated with the database and frontend dashboard after deployment.

---

## 1. System Health Verification
- [ ] **Health Endpoint Check**: Visit the health endpoint `/health` on the backend (e.g., `https://your-backend-app.onrender.com/health`).
  - Expected Response:
    ```json
    {
      "status": "healthy",
      "database": "connected"
    }
    ```
- [ ] **System Stats Endpoint**: Visit `/system/stats` to verify database statistics are computed.
  - Expected Response: Returns total count of vehicles, locations, raw packets, online/idle/offline statuses, and latest timestamps.

---

## 2. CORS Verification
- [ ] **Cross-Origin Access**: Verify that your deployed Next.js frontend (e.g., on Vercel) can make GET and POST requests to the backend without CORS errors.
  - Test: Check the browser Console/Network tab on the dashboard loading screen. If requests return a `200 OK` status, CORS is correctly configured.
  - Check: Ensure `CORS_ORIGINS` in your backend environment includes your exact Next.js frontend URL (without trailing slash).

---

## 3. Database Schema Verification
- [ ] **Tables Verification**: Run the programmatic validation script on a terminal pointing to the production database:
  ```bash
  python scripts/db_validate.py
  ```
  - Expected Output:
    ```text
    [db_validate.py] Running Alembic upgrade head...
    [db_validate.py] Alembic upgrade head executed successfully!
    [db_validate.py] Connecting to PostgreSQL to check tables...
    [db_validate.py] Found tables in database: [...]
    [db_validate.py] SUCCESS: All VTS Phase 1 and 2 tables are verified to exist!
    ```

---

## 4. Telemetry & Ingestion Test
- [ ] **Telemetry Ingestion**: Run the simulator with the target `API_URL` pointing to the deployed production API:
  ```bash
  $env:API_URL="https://your-backend-app.onrender.com"
  python scripts/telemetry_simulator.py
  ```
  - Expected Behavior: The simulator prints GPS packet ingestion updates returning `200 OK` responses containing device configs.
  - Check: Look at `/system/stats` on the backend, and notice `total_locations` and `total_raw_packets` incrementing.

---

## 5. Google Routes Cache Integration (If Enabled)
- [ ] **Cache Operations**: Run `scripts/verify_cache.py` to confirm the snapped route cache is operational:
  ```bash
  python scripts/verify_cache.py
  ```
  - Expected Output:
    - Snapped route resolved successfully.
    - Repeated queries resolve via database cache hits logging audit records (`CACHE_HIT`).
