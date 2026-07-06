# Protocol Command Matrix (VTS Protocol v2.2)

This matrix maps configuration commands and administrative operations defined in the VTS Protocol v2.2 specification, identifying their roles, hardware requirements, and implementation status.

| Command | Description | Configuration Type | Requires Hardware | Can Simulate | Implementation Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **PRD** | Data transmission period (interval in seconds) | Ingestion Interval | Yes | Yes | Supported |
| **APN** | Access Point Name configuration (APN, user, pass) | Cellular Settings | Yes | Yes | Supported |
| **NIP** | Server IP Address or Domain URL | Network Destination | Yes | Yes | Supported |
| **NPT** | Server TCP connection port | Network Port | Yes | Yes | Supported |
| **TZN** | Device timezone offset (e.g. `+05:30`) | Timezone | Yes | Yes | Supported |
| **ESS** | Excess speed limit threshold in km/h | Safety Threshold | Yes | Yes | Supported |
| **IMCONF** | Immobilizer reader/lock settings | Security Settings | Yes | Yes | Supported |
| **FWCONFIG** | Get firmware configuration features | Diagnostic Query | No | Yes | Supported |
| **FEATURE** | Enable/disable system features (e.g. HTTP JSON) | System Config | Yes | Yes | Supported |
| **TIME** | Set system date/time or auto-sync source | Clock Sync | Yes | Yes | Supported |
| **SMS** | Configure admin cellular contact numbers | Contact Settings | Yes | Yes | Supported |
| **PWD** | Set SMS password | Security Settings | No | Yes | Supported |
| **REBOOT** | Reboot device immediately or after delay | System Command | Yes | Yes | Supported |
| **UNO** | Select ID format (IMEI, UID, UNAME) | Protocol Settings | No | Yes | Supported |
| **UNAME** | Custom friendly device name | Device Profile | No | Yes | Supported |
| **OFR** | Query or wipe offline storage logs | Storage Config | Yes | Yes | Supported |
| **DNSCFG** | Configure DNS Servers | Network Settings | Yes | Yes | Supported |
| **WGET** | Download file via HTTP or FTP | File Transfer | Yes | Yes | Supported |
| **DFMT** | Date format setting (EPOCH vs String) | Protocol Settings | No | Yes | Supported |
| **ODM** | Configure initial odometer offset value | Odometer Setup | No | Yes | Supported |
| **STARTV** | Immobilizer Command: Enable starter/fuel flow | Control Relay | Yes | Yes | Supported |
| **STOPV** | Immobilizer Command: Cut starter/fuel flow | Control Relay | Yes | Yes | Supported |
| **HBRK** | Harsh Braking deceleration threshold (g) | Accel Threshold | Yes | Yes | Supported |
| **HACC** | Harsh Acceleration acceleration threshold (g) | Accel Threshold | Yes | Yes | Supported |
| **EVSET** | Enable or disable specific transaction codes | Protocol Settings | No | Yes | Supported |
| **SOS** | Acknowledge SOS event (turns off device LED) | Control Signal | Yes | Yes | Supported |
| **TEMPTH** | Set high and low temperature alarm limits | Sensor Threshold | Yes | Yes | Supported |
| **RHTH** | Set high and low relative humidity limits | Sensor Threshold | Yes | Yes | Supported |
| **SENSOR** | Reset or calibrate temperature offset values | Sensor Config | Yes | Yes | Supported |
| **BUZZ** | Set buzzer trigger categories or toggle states | Peripheral Control | Yes | Yes | Supported |
| **BTYPE** | Configure buzzer alert style (beeper vs hooter) | Peripheral Settings | Yes | Yes | Supported |
| **RFCONF** | Configure RFID Reader mode and timeout values | Reader Config | Yes | Yes | Supported |
| **BIOCONF** | Load or delete biometric fingerprint templates | Reader Config | Yes | Yes | Supported |
| **IBCONF** | Configure iButton reader operations | Reader Config | Yes | Yes | Supported |
| **ADCTUNE** | Configure ADC approximation smooth filtering | ADC Calibration | Yes | Yes | Supported |
| **SIM** | Query SIM ICCID card number | Diagnostic Query | Yes | Yes | Supported |
| **HEADER** | Custom authorization or metadata HTTP headers | Network Security | No | Yes | Supported |
| **FCFG** | Configure fuel sensor models, ports, and offsets | Sensor Config | Yes | Yes | Supported |
| **UMODE** | Configure Auxiliary UART mode (App vs Transparent) | Peripheral Settings | Yes | Yes | Supported |
| **TPCFG** | Configure transparent mode endpoint server details | Network Settings | Yes | Yes | Supported |
| **GEO** | Set circular or rectangular geofence boundaries | Geofence Settings | Yes | Yes | Supported |
| **IOCONF** | Map input/output pins configuration | GPIO Mapping | Yes | Yes | Supported |
| **IOATTACH** | Assign digital output actions to specific events | Relay Automation | Yes | Yes | Supported |
| **IOVAL** | Query or write raw GPIO logic levels | GPIO Control | Yes | Yes | Supported |
| **IMU** | Configure Inertial Measurement Unit triggers | Accel Threshold | Yes | Yes | Supported |
| **STG** | Query all current configurations | Diagnostic Query | No | Yes | Supported |
| **TEST** | Get diagnostic device tests parameters | Diagnostic Query | Yes | Yes | Supported |
| **WHERE** | Query current location (returns via SMS) | Diagnostic Query | Yes | Yes | Supported |
| **GPSINFO** | Query current GPS parsing attributes | Diagnostic Query | Yes | Yes | Supported |
| **LOGLEVEL**| Toggle Bluetooth diagnostic output detail | System diagnostics | Yes | Yes | Supported |
| **FRESET** | Wipe all custom settings and restore factory defaults | System Command | Yes | Yes | Supported |
| **IDENTIFY** | Fetch device UID, IMEI, SIM ID, and FW version | Diagnostic Query | No | Yes | Supported |
| **FWCHECK** | Query for FOTA firmware server updates | System/FOTA | Yes | Yes | Supported |
| **OTA** | Update system firmware from binary file source | System/FOTA | Yes | Yes | Supported |
