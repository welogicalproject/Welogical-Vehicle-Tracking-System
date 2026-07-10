# VTS Telemetry Simulator Client

This is a standalone, lightweight telemetry simulator client for the Vehicle Tracking System (VTS). It simulates multiple vehicles and executes planned routes assigned dynamically by the backend API.

It operates entirely independent of the backend database or SQLAlchemy codebase and communicates solely through HTTP REST API contracts.

---

## Prerequisites
- **Python 3.8+**
- Standard built-in libraries only (no third-party dependencies are required).

---

## Configuration

You can configure the client behavior using environment variables. If not defined, it falls back to the default values in `config.py`:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `API_BASE_URL` | Base URL of the running VTS backend API | `http://127.0.0.1:8000` |
| `TELEMETRY_INTERVAL` | Time interval (in seconds) between sequential coordinate hops / telemetry packets | `10` |
| `RETRY_INTERVAL` | Interval duration (in seconds) for retry queries checking for newly assigned routes | `10` |

---

## Installation & Running

1. **Verify Python Installation:**
   ```bash
   python --version
   ```

2. **Start the Simulator:**
   Simply run the script with:
   ```bash
   python simulator.py
   ```

3. **Configure via Env (Optional example):**
   *On Windows (CMD):*
   ```cmd
   set API_BASE_URL=http://localhost:8000
   set TELEMETRY_INTERVAL=5
   python simulator.py
   ```
   *On Linux/macOS:*
   ```bash
   API_BASE_URL=http://localhost:8000 TELEMETRY_INTERVAL=5 python3 simulator.py
   ```
