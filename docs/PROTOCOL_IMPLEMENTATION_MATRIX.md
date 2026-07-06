# Protocol Implementation Matrix (VTS Protocol v2.2)

This matrix documents the implementation status of all VTS protocol features (fields, parameters, and transaction codes) as of Phase 1, indicating what is already parsed, missing, requires hardware, or can be simulated.

---

## 1. Transmission Packet Identifiers (txn)

| Protocol Feature | Current Status | Already Implemented | Partially Implemented | Missing | Hardware Required | Can Simulate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A** - Vehicle Moving (Periodic) | Supported | Yes | | | | Yes |
| **B** - Overspeeding (Periodic) | Supported | Yes | | | | Yes |
| **C** - Speed Normal (Event) | Supported | Yes | | | | Yes |
| **D** - Speed Limit Exceeded (Event) | Supported | Yes | | | | Yes |
| **E** - Vehicle Stopped (Periodic) | Supported | Yes | | | | Yes |
| **F** - Motion Start (Event) | Supported | Yes | | | | Yes |
| **G** - Motion Stop (Event) | Supported | Yes | | | | Yes |
| **H** - GSM Location / Tilt Alert | Supported | Yes | | | | Yes |
| **I** - GPS First Fix (Event) | Supported | Yes | | | | Yes |
| **J** - Ignition Changed (Event) | Supported | Yes | | | | Yes |
| **K** - Enclosure/Box Open (Event) | Supported | Yes | | | | Yes |
| **L** - Power Changed (Event) | Supported | Yes | | | | Yes |
| **M** - Harsh Turn (Event) | Supported | Yes | | | | Yes |
| **N** - SOS Pressed (Event) | Supported | Yes | | | | Yes |
| **O** - Digital Input Changed (Event) | Supported | Yes | | | | Yes |
| **P** - Over Acceleration (Event) | Supported | Yes | | | | Yes |
| **Q** - Parameter Changed (Event) | Supported | Yes | | | | Yes |
| **R** - Parameter Query (Event) | Supported | Yes | | | | Yes |
| **S** - Harsh Brake (Event) | Supported | Yes | | | | Yes |
| **T** - Immobilizer Event | Supported | Yes | | | | Yes |
| **U** - GPS Status Event | Supported | Yes | | | | Yes |
| **V** - Temperature Alert (Event) | Supported | Yes | | | | Yes |
| **W** - New ID Detected (RFID/Fingerprint) | Supported | Yes | | | | Yes |
| **X** - Geofence Event | Supported | Yes | | | | Yes |
| **Y** - Trip Event | Supported | Yes | | | | Yes |
| **Z** - Firmware Update Event (FOTA) | Supported | Yes | | | | Yes |

*Note: All transaction codes (`txn`) are currently accepted and stored in the `locations.extra_data["txn"]` JSONB field. However, in Step 5 we will build the formal event decoder to map and write records to the new `events` table.*

---

## 2. Ingestion Fields & Parameters

| Protocol Feature | Current Status | Already Implemented | Partially Implemented | Missing | Hardware Required | Can Simulate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **uid** (Device Hardware ID) | Implemented | Yes | | | | Yes |
| **info.dt** (Epoch Timestamp) | Implemented | Yes | | | | Yes |
| **info.txn** (Tx Reason Code) | Implemented | Yes | | | | Yes |
| **info.msgkey** (Msg Key Type) | Implemented | Yes | | | | Yes |
| **info.msgid** (Msg Counter) | Implemented | Yes | | | | Yes |
| **info.cmdkey** (Command ID) | Partial | | Yes | | | Yes |
| **info.cmdval** (Command Value) | Partial | | Yes | | | Yes |
| **gps.fix** (GPS Validity flag) | Implemented | Yes | | | Yes | Yes |
| **gps.loc** (Coords array `[lat, lon]`) | Implemented | Yes | | | Yes | Yes |
| **gps.speed** (Speed in km/h) | Implemented | Yes | | | Yes | Yes |
| **gps.sat** (Satellites in view) | Implemented | Yes | | | Yes | Yes |
| **gps.alt** (Altitude in meters) | Implemented | Yes | | | Yes | Yes |
| **gps.dir** (Bearing in degrees) | Implemented | Yes | | | Yes | Yes |
| **gps.odo** (Odometer in meters) | Implemented | Yes | | | | Yes |
| **io.box** (Enclosure status) | Implemented | Yes | | | Yes | Yes |
| **io.ign** (Ignition Status On/Off) | Implemented | Yes | | | Yes | Yes |
| **io.gpi** (General Purpose Inputs) | Implemented | Yes | | | Yes | Yes |
| **io.status** (Status Flags) | Implemented | Yes | | | | Yes |
| **io.analog** (Analog in millivolts) | Implemented | Yes | | | Yes | Yes |
| **io.fuel** (Fuel Level sensor object) | Missing | | | Yes | Yes | Yes |
| **io.sensor** (Temp sensor array object) | Missing | | | Yes | Yes | Yes |
| **pwr.main** (Mains Input On/Off) | Implemented | Yes | | | Yes | Yes |
| **pwr.batt** (Battery Status Connected) | Implemented | Yes | | | Yes | Yes |
| **pwr.volt** (Battery voltage in mV) | Implemented | Yes | | | Yes | Yes |
| **pwr.mvolt** (Mains voltage in Volts) | Implemented | Yes | | | Yes | Yes |
| **dbg.status** (Debug status codes) | Implemented | Yes | | | | Yes |
| **dbg.ver** (Firmware versions) | Implemented | Yes | | | | Yes |
| **dbg.lib** (Firmware library ID) | Implemented | Yes | | | | Yes |

---

## 3. Simulator Capability & Hardware Requirements

### Features Requiring Physical Hardware (In Production)
1. **Satellite Counts and Signal Strength (`gps.sat`, `dbg.status[2]`)**: Determined by physical satellite tracking capability.
2. **True Analog Inputs (`io.analog`)**: Requires analog physical connections (e.g. to fuel float sensors or temperature probes).
3. **GPIO Pin Transitions (`io.gpi`)**: Requires dry-contact wiring toggling voltages on ESP32 or Scout+ hardware.
4. **Physical Box Enclosure Openings (`io.box`)**: Requires physical micro-switches inside device casing.

### Simulation Capabilities (Software-only)
* All of the above states can be fully simulated in our `scripts/telemetry_simulator.py` script by generating mock numerical sequences, varying boolean states, and injecting specific `txn` code markers inside the JSON POST requests.
* **Alert Engine triggers** (overspeed, temperature alarms, geofence breaches, harsh driving behaviors) are generated by logic rules analyzing the parsed JSON fields.
