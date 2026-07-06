# Local Setup Guide

This guide provides extremely detailed, step-by-step instructions to get the Vehicle Tracking System running on a completely fresh machine.

Assume nothing is installed except the operating system.

---

## Step 1: Install Prerequisites

### 1.1 Install Git
- Go to [git-scm.com](https://git-scm.com/downloads) and download the installer for your OS.
- Run the installer and accept all default settings.

### 1.2 Install Python
- Go to [python.org](https://www.python.org/downloads/) and download Python 3.10 or higher.
- **IMPORTANT (Windows):** During installation, check the box that says **"Add Python to PATH"** before clicking Install.

### 1.3 Install Node.js
- Go to [nodejs.org](https://nodejs.org/) and download the LTS version (20.x or higher).
- Run the installer and accept all default settings.

### 1.4 Install PostgreSQL
- Go to [postgresql.org](https://www.postgresql.org/download/) and download the installer.
- During installation, remember the password you set for the default `postgres` user (e.g., `postgres123`).
- Keep the default port as `5432`.

---

## Step 2: Clone the Repository

Open a terminal (Command Prompt, PowerShell, or macOS Terminal) and run:

```bash
git clone https://github.com/welogicalproject/Welogical-Vehicle-Tracking-System.git
cd Welogical-Vehicle-Tracking-System
```

---

## Step 3: Database Setup

You need to create the database that the application will use.

### Windows (Using psql):
Open Command Prompt and run:
```cmd
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres
```
(Adjust the path if you installed a different version). Enter your password when prompted.

### Mac/Linux:
```bash
psql -U postgres
```

### In the psql prompt:
Run the following SQL command to create the database:
```sql
CREATE DATABASE vts_db;
\q
```

---

## Step 4: Configure Environment Variables

The system relies on a `.env` file for secrets.

1. In the project root, copy the example file:
   - **Mac/Linux:** `cp .env.example .env`
   - **Windows:** `copy .env.example .env`
2. Open `.env` in a text editor (like VS Code or Notepad).
3. Find the `DATABASE_URL` and `ASYNC_DATABASE_URL` lines.
4. Update the password (`postgres123`) to whatever password you set during the PostgreSQL installation.

Example:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/vts_db
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5432/vts_db
```

---

## Step 5: Backend Setup & Migrations

Open a terminal in the project root folder.

### 5.1 Create a Virtual Environment
This keeps Python dependencies isolated.
```bash
python -m venv venv
```

### 5.2 Activate the Virtual Environment
- **Windows:**
  ```cmd
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 5.3 Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5.4 Run Database Migrations
This will build all the required tables in your fresh `vts_db` database.
```bash
alembic upgrade head
```

### 5.5 Start the Backend Server
```bash
uvicorn app.main:app --reload
```
Leave this terminal window open. The backend is now running at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

---

## Step 6: Frontend Setup

Open a **new** terminal window and navigate into the `dashboard` folder.

```bash
cd path/to/Welogical-Vehicle-Tracking-System/dashboard
```

### 6.1 Install Node Dependencies
```bash
npm install
```

### 6.2 Start the Frontend Server
```bash
npm run dev
```
Leave this terminal window open. The frontend is now running at `http://localhost:3000`.

---

## Step 7: Verify the Installation

1. Open a web browser and go to `http://localhost:3000`. You should see the dashboard.
2. To test data flow, open a **third** terminal window in the root of the project, activate the virtual environment, and run the simulator:
   ```bash
   venv\Scripts\activate  # (Windows)
   python scripts/telemetry_simulator.py
   ```
3. Watch the terminal output. It will simulate a vehicle driving. Go back to your browser (`http://localhost:3000`), and you should see active vehicles and changing statistics on the dashboard!

Congratulations, your local environment is fully set up!
