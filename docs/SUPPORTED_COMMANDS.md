# VTS Supported Commands Reference

This document classifies all commands defined in the VTS Protocol specification, grouping them by their implementation support status, hardware requirements, and simulator capabilities.

---

## 1. Supported Now (Active Configuration)
These commands are fully supportable by the VTS Event Engine & Command Queue backend and can be configured through the dashboard.

| Command | Description | Configuration Mapping | Usage Example |
| :--- | :--- | :--- | :--- |
| **PRD** | Data transmission period (reporting interval in seconds) | `device_configs.reporting_interval` | `PRD=60` |
| **ESS** | Excess speed limit setting (threshold in km/h) | `device_configs.speed_limit` | `ESS=80` |
| **STARTV**| Immobilizer Command: Enable starter/fuel flow relay | Triggers `Immobilizer Event` | `STARTV` |
| **STOPV** | Immobilizer Command: Disable starter/fuel flow relay | Triggers `Immobilizer Event` (Critical) | `STOPV` |

---

## 2. Simulator Only (Diagnostics)
These commands can be simulated by the Python telemetry simulator scripts to test the telemetry roundtrip and system resets.

| Command | Description | Action Behavior | Usage Example |
| :--- | :--- | :--- | :--- |
| **REBOOT**| Reboots the device (resets the sequential message counter) | Restarts simulator msg counter to `1` | `REBOOT` |
| **RESET** | Restarts device and reverts temporary run settings | Clears simulator state buffers | `RESET` |

---

## 3. Future Roadmap (System updates)
These commands are reserved for future core FOTA (Firmware Over-The-Air) deployment features.

| Command | Description | Action Behavior | Usage Example |
| :--- | :--- | :--- | :--- |
| **OTA** | Flash device firmware from binary URL | Initiates FOTA upgrade stream | `OTA=http://server/fw.bin` |
| **FWCHECK**| Check for updates on target server | Queries firmware metadata | `FWCHECK=now` |
| **FWCONFIG**| Retrieve active FOTA server credentials | Returns URL and port configuration | `FWCONFIG` |

---

## 4. Hardware Required (Physical Peripherals)
These commands require physical hardware components (dry contacts, MEMS sensors, analog sensors, relays) to function. They can, however, be simulated in the JSON payload fields.

| Command Group | Commands | Description | Hardware Requirement |
| :--- | :--- | :--- | :--- |
| **GPIO Pin mapping** | `IOCONF`, `IOATTACH`, `IOVAL` | Setup logic levels and attach events | Physical GPIO pins (ESP32/Scout+) |
| **Accelerometer (IMU)**| `IMU`, `HBRK`, `HACC` | Setup threshold g-forces for harsh driving | MEMS Accelerometer (e.g. MPU6050) |
| **Biometric Scan** | `BIOCONF` | Manage enrolled fingerprint reader logs | Fingerprint sensor over UART |
| **RFID / iButton** | `RFCONF`, `IBCONF` | Manage tag scanning timeout values | RFID Reader / 1-Wire iButton probe |
| **UART Transparent** | `UMODE`, `TPCFG` | Open secondary raw serial-to-TCP socket | Secondary UART transceiver (RS485/RS232) |
| **Analog Fuel Gauge** | `FCFG` | Setup analog fuel float variables | RS485 fuel sensor probe |
| **Temperature** | `TEMPTH`, `RHTH`, `SENSOR`| Setup temperature/humidity threshold limits | 1-Wire DS18B20 or DHT22 sensors |

---

## 5. Duplicate Event Protection Design (Task 11)

To prevent duplicate event generation on high-frequency telemetry ingestion:
* We have introduced the `msgid` column in the `events` table (mapped to the VTS sequential packet `msgid` counter).
* Uniqueness is defined by the composite tuple: `(vehicle_id, txn, msgid)`.
* Before writing a decoded event during telemetry processing, the backend queries the `events` table:
  ```python
  stmt = select(Event).where(
      Event.vehicle_id == vehicle_id,
      Event.txn == txn,
      Event.msgid == msgid
  )
  ```
  If a record is found, the event generation is skipped. This prevents duplicate event writes while allowing the raw packet to still be recorded in `raw_packets` for audit trail tracking.
