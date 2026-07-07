# Welogical Vehicle Tracking System - Backend Deployment Guide

This document describes the procedures and requirements for deploying the VTS FastAPI backend to a production environment.

## 1. Prerequisites & Environment Setup
Ensure the following environment variables are securely injected into your production environment (e.g., Render Dashboard, AWS Secrets Manager, Vercel Env Settings):

| Environment Variable | Description | Example / Default |
|----------------------|-------------|-------------------|
| `APP_ENV` | Environment name | `production` |
| `DEBUG` | FastAPI debugging mode | `false` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `https://your-frontend-app.vercel.app` |
| `DATABASE_URL` | Sync database connection URL (standard Postgres scheme) | `postgresql://user:password@host:5432/db` |
| `ASYNC_DATABASE_URL` | Async database connection URL (asyncpg scheme) | `postgresql+asyncpg://user:password@host:5432/db` (Optional, auto-derived if omitted) |
| `GOOGLE_ROUTES_ENABLED` | Toggle Google Maps routes snapping API integration | `false` |
| `GOOGLE_ROUTES_API_KEY` | Google Routes API client credential | `AIzaSy...` (Optional, only if enabled) |

### 1.1 Database Schema Standardization
Some managed PostgreSQL instances (e.g., Supabase, AWS RDS, Render DB) return connection URIs starting with `postgres://` which is deprecated in modern SQLAlchemy setups. The backend automatically catches this and standardizes it to `postgresql://` on startup.

If you do not specify `ASYNC_DATABASE_URL`, the backend automatically generates it by mapping the connection details to the `postgresql+asyncpg://` scheme.

---

## 2. Database Migrations (Alembic)
Best practices dictate that database schema changes should be managed carefully to avoid locking production tables during deployments.

### 2.1 Applying Migrations Manually (Recommended)
You can run migrations from a secure administration terminal or CI/CD pipeline using the Alembic command:
```bash
alembic upgrade head
```
Or, you can run the validation script from the project root:
```bash
python scripts/db_validate.py
```
This script will apply Alembic migrations programmatically to the database specified in your env configuration and inspect the schema to verify that all necessary telemetry, configuration, and event logs tables exist.

### 2.2 Applying Migrations via Render Pre-Deploy (Optional)
If you wish to auto-run migrations before Uvicorn starts during deployment on Render, uncomment the following line in `render.yaml`:
```yaml
preDeployCommand: alembic upgrade head
```
*Note: Ensure your database connection has full DDL privileges to execute `CREATE TABLE` and `ALTER TABLE` operations.*

---

## 3. Running with Docker
A `Dockerfile` is provided in the repository root for containerized environments (such as AWS ECS, Google Cloud Run, or Render Docker services).

### 3.1 Build the Image
```bash
docker build -t vts-backend:latest .
```

### 3.2 Run the Container
```bash
docker run -d -p 8000:8000 \
  -e APP_ENV=production \
  -e DEBUG=false \
  -e CORS_ORIGINS="https://your-frontend-app.vercel.app" \
  -e DATABASE_URL="postgresql://user:password@host:5432/db" \
  vts-backend:latest
```
