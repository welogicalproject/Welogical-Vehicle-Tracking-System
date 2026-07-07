import json
import os

def generate_collection():
    collection = {
        "info": {
            "_postman_id": "8a3d5e9c-4f81-4bda-bc6c-7f5b82c16301",
            "name": "Vehicle Tracking System API",
            "description": "Production-quality API testing collection for Welogical Vehicle Tracking System backend.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }

    # Helper function to generate standard test scripts
    def make_test_event(status_code=200, checks=None, save_vars=None):
        exec_lines = [
            f'pm.test("Status is {status_code}", function () {{',
            f'    pm.response.to.have.status({status_code});',
            '});',
            '',
            'pm.test("Response time < 1000ms", function () {',
            '    pm.expect(pm.response.responseTime).to.be.below(1000);',
            '});',
            '',
            'pm.test("Content-Type is JSON", function () {',
            '    pm.response.to.have.header("Content-Type");',
            '    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");',
            '});'
        ]
        
        if checks:
            exec_lines.append('')
            exec_lines.append('pm.test("Validate response body schema", function () {')
            exec_lines.append('    var jsonData = pm.response.json();')
            for check in checks:
                exec_lines.append(f'    {check}')
            exec_lines.append('});')

        if save_vars:
            exec_lines.append('')
            exec_lines.append('// Variable chaining')
            exec_lines.append('var jsonData = pm.response.json();')
            for var_name, path in save_vars.items():
                exec_lines.append(f'pm.environment.set("{var_name}", {path});')

        return {
            "listen": "test",
            "script": {
                "exec": exec_lines,
                "type": "text/javascript"
            }
        }

    # 1. Folder: Health
    health_items = [
        {
            "name": "GET Root Welcome",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("online");',
                'pm.expect(jsonData).to.have.property("docs_url");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/",
                    "host": ["{{BASE_URL}}"],
                    "path": [""]
                },
                "description": "Endpoint returning API service info and active status."
            }
        },
        {
            "name": "GET Health Status",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("healthy");',
                'pm.expect(jsonData.database).to.eql("connected");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/health",
                    "host": ["{{BASE_URL}}"],
                    "path": ["health"]
                },
                "description": "Liveness and database connection status healthcheck."
            }
        }
    ]
    collection["item"].append({
        "name": "Health Check",
        "item": health_items
    })

    # 2. Folder: Vehicles
    vehicle_items = [
        {
            "name": "Create Vehicle",
            "event": [make_test_event(201, [
                'pm.expect(jsonData).to.have.property("id");',
                'pm.expect(jsonData.device_uid).to.eql("ESP32-DEMO-001");'
            ], {"VEHICLE_ID": "jsonData.id", "DEVICE_UID": "jsonData.device_uid"})],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "device_uid": "ESP32-DEMO-001",
                        "vehicle_name": "Toyota Corolla",
                        "vehicle_type": "Sedan",
                        "vehicle_number": "GJ05AB1234",
                        "manufacturer": "Toyota",
                        "model": "Corolla",
                        "year": 2024,
                        "vin": "1NXBR32E64Z123456",
                        "imei": "864009040001234",
                        "sim_number": "+919876543210",
                        "fuel_type": "Petrol",
                        "capacity": 50.0,
                        "status": "Enabled",
                        "notes": "ESP32 primary tracking unit test vehicle"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/vehicles",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles"]
                },
                "description": "Registers a new tracking vehicle in the fleet management system."
            }
        },
        {
            "name": "Create Duplicate Vehicle (Conflict 409)",
            "event": [make_test_event(409, [
                'pm.expect(jsonData.success).to.eql(false);',
                'pm.expect(jsonData.detail).to.include("already exists");'
            ])],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "device_uid": "ESP32-DEMO-001",
                        "vehicle_name": "Toyota Corolla Duplicate",
                        "vehicle_type": "Sedan"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/vehicles",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles"]
                },
                "description": "Validates that submitting a duplicate device_uid returns HTTP 409 Conflict."
            }
        },
        {
            "name": "List Vehicles",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles?skip=0&limit=100",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles"],
                    "query": [
                        {"key": "skip", "value": "0"},
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "Lists all fleet tracking vehicles."
            }
        },
        {
            "name": "Get Vehicle by ID",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.id).to.eql(parseInt(pm.environment.get("VEHICLE_ID")));'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}"]
                },
                "description": "Retrieves the full profile metadata of a vehicle."
            }
        },
        {
            "name": "Get Non-existent Vehicle (Not Found 404)",
            "event": [make_test_event(404, [
                'pm.expect(jsonData.success).to.eql(false);'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/999999",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "999999"]
                },
                "description": "Validates that querying a non-existent vehicle ID returns HTTP 404 Not Found."
            }
        },
        {
            "name": "Update Vehicle",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.vehicle_name).to.eql("Toyota Corolla Updated");'
            ])],
            "request": {
                "method": "PUT",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "vehicle_name": "Toyota Corolla Updated",
                        "capacity": 55.0
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}"]
                },
                "description": "Updates profile configurations for a vehicle."
            }
        },
        {
            "name": "Delete/Archive Vehicle",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("Archived");'
            ])],
            "request": {
                "method": "DELETE",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}"]
                },
                "description": "Soft-deletes a vehicle by transitioning its status to Archived."
            }
        }
    ]
    collection["item"].append({
        "name": "Vehicles",
        "item": vehicle_items
    })

    # 3. Folder: Drivers
    driver_items = [
        {
            "name": "Create Driver",
            "event": [make_test_event(201, [
                'pm.expect(jsonData).to.have.property("id");',
                'pm.expect(jsonData.driver_name).to.eql("John Doe");'
            ], {"DRIVER_ID": "jsonData.id"})],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "driver_name": "John Doe",
                        "phone_number": "9876543210",
                        "email": "john.doe@example.com",
                        "license_number": "DL-54321098765",
                        "license_expiry": "2030-12-31T00:00:00Z",
                        "emergency_contact": "Jane Doe: 9876543211",
                        "status": "Active"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/drivers",
                    "host": ["{{BASE_URL}}"],
                    "path": ["drivers"]
                },
                "description": "Registers a new driver profile."
            }
        },
        {
            "name": "List Drivers",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/drivers?skip=0&limit=100",
                    "host": ["{{BASE_URL}}"],
                    "path": ["drivers"],
                    "query": [
                        {"key": "skip", "value": "0"},
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "Lists all driver profiles."
            }
        },
        {
            "name": "Get Driver by ID",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.id).to.eql(parseInt(pm.environment.get("DRIVER_ID")));'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/drivers/{{DRIVER_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["drivers", "{{DRIVER_ID}}"]
                },
                "description": "Retrieves the full profile details of a driver."
            }
        },
        {
            "name": "Update Driver",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.email).to.eql("john.updated@example.com");'
            ])],
            "request": {
                "method": "PUT",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "email": "john.updated@example.com",
                        "emergency_contact": "Jane Doe: 9876543212"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/drivers/{{DRIVER_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["drivers", "{{DRIVER_ID}}"]
                },
                "description": "Updates contact details of a driver."
            }
        },
        {
            "name": "Delete Driver",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.id).to.eql(parseInt(pm.environment.get("DRIVER_ID")));'
            ])],
            "request": {
                "method": "DELETE",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/drivers/{{DRIVER_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["drivers", "{{DRIVER_ID}}"]
                },
                "description": "Permanently deletes a driver from registry."
            }
        }
    ]
    collection["item"].append({
        "name": "Drivers",
        "item": driver_items
    })

    # 4. Folder: Driver Assignments
    assignment_items = [
        {
            "name": "Assign Driver to Vehicle",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.have.property("id");',
                'pm.expect(jsonData.status).to.eql("Active");'
            ], {"ASSIGNMENT_ID": "jsonData.id"})],
            "request": {
                "method": "POST",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/assign/{{DRIVER_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "assign", "{{DRIVER_ID}}"]
                },
                "description": "Establishes a tracking linkage mapping an active driver to a vehicle."
            }
        },
        {
            "name": "Get Active Assignment",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("Active");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/assignments/active",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "assignments", "active"]
                },
                "description": "Gets current active assignment mapping for a vehicle."
            }
        },
        {
            "name": "Release Driver from Vehicle",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("Completed");',
                'pm.expect(jsonData.released_at).to.not.be.null;'
            ])],
            "request": {
                "method": "POST",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/release",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "release"]
                },
                "description": "Closes the current active assignment for a vehicle."
            }
        },
        {
            "name": "Get Vehicle Assignment History",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/assignments/history",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "assignments", "history"]
                },
                "description": "Retrieves the complete historical assignments log for a vehicle."
            }
        }
    ]
    collection["item"].append({
        "name": "Driver Assignments",
        "item": assignment_items
    })

    # 5. Folder: Locations
    location_items = [
        {
            "name": "Log Standard Location",
            "event": [make_test_event(201, [
                'pm.expect(jsonData).to.have.property("id");'
            ], {"LOCATION_ID": "jsonData.id"})],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "vehicle_id": 1,
                        "latitude": 21.17024,
                        "longitude": 72.83106,
                        "speed": 45.5,
                        "altitude": 12.0,
                        "timestamp": "2026-07-07T10:00:00Z",
                        "extra_data": {
                            "txn": "A",
                            "io": {"ign": 1}
                        }
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/locations",
                    "host": ["{{BASE_URL}}"],
                    "path": ["locations"]
                },
                "description": "Logs a coordinates log payload, updating the vehicle's last_seen field."
            }
        },
        {
            "name": "Get Latest Location",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.have.property("latitude");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/locations/latest/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["locations", "latest", "{{VEHICLE_ID}}"]
                },
                "description": "Queries the most recent coordinates record for a vehicle."
            }
        },
        {
            "name": "Get Location History",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/locations/history/{{VEHICLE_ID}}?limit=50",
                    "host": ["{{BASE_URL}}"],
                    "path": ["locations", "history", "{{VEHICLE_ID}}"],
                    "query": [{"key": "limit", "value": "50"}]
                },
                "description": "Gets historical tracking coordinates range for a vehicle."
            }
        },
        {
            "name": "List All Locations",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/locations?limit=100",
                    "host": ["{{BASE_URL}}"],
                    "path": ["locations"],
                    "query": [{"key": "limit", "value": "100"}]
                },
                "description": "Lists all locations across all vehicles (Database explorer)."
            }
        }
    ]
    collection["item"].append({
        "name": "Locations",
        "item": location_items
    })

    # 6. Folder: Telemetry
    telemetry_items = [
        {
            "name": "Ingest Telemetry Packet (VTS Protocol)",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.result).to.eql(true);',
                'pm.expect(jsonData.msg).to.eql("Data Success");'
            ])],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "uid": "ESP32-DEMO-001",
                        "info": {
                            "dt": 1783425600,
                            "txn": "A",
                            "msgkey": 0,
                            "msgid": 45
                        },
                        "gps": {
                            "fix": "A",
                            "loc": [21.17024, 72.83106],
                            "speed": 50.2,
                            "sat": 9,
                            "alt": 15.0,
                            "dir": 90.0,
                            "odo": 15200.0
                        },
                        "io": {
                            "box": 0,
                            "ign": 1,
                            "gpi": 0,
                            "status": 0,
                            "analog": [12000]
                        },
                        "pwr": {
                            "main": 1,
                            "batt": 1,
                            "volt": 4200.0,
                            "mvolt": 12.5
                        },
                        "dbg": {
                            "status": [0],
                            "ver": ["1.0", "1.0"],
                            "lib": "VTS-v1.0"
                        }
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/vts/telemetry",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vts", "telemetry"]
                },
                "description": "Ingests a telemetry packet conforming to the VTS Protocol Description."
            }
        },
        {
            "name": "List Raw Packets",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vts/raw-packets?limit=50",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vts", "raw-packets"],
                    "query": [{"key": "limit", "value": "50"}]
                },
                "description": "Lists raw payloads captured in the debug monitor raw_packets registry."
            }
        }
    ]
    collection["item"].append({
        "name": "Telemetry Ingestion",
        "item": telemetry_items
    })

    # 7. Folder: Commands
    command_items = [
        {
            "name": "Queue New Command",
            "event": [make_test_event(201, [
                'pm.expect(jsonData).to.have.property("id");',
                'pm.expect(jsonData.status).to.eql("PENDING");'
            ], {"COMMAND_ID": "jsonData.id"})],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "vehicle_id": 1,
                        "command_name": "PRD",
                        "command_value": "10"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/commands",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands"]
                },
                "description": "Queues a new command for a device. Initial status is PENDING."
            }
        },
        {
            "name": "List Commands Queue",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands?limit=50",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands"],
                    "query": [{"key": "limit", "value": "50"}]
                },
                "description": "Lists historical queued commands."
            }
        },
        {
            "name": "Mark Command as Sent",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("SENT");'
            ])],
            "request": {
                "method": "PUT",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands/{{COMMAND_ID}}/send",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands", "{{COMMAND_ID}}", "send"]
                },
                "description": "Transitions a command status from PENDING to SENT."
            }
        },
        {
            "name": "Mark Command as Executed",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("EXECUTED");'
            ])],
            "request": {
                "method": "PUT",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands/{{COMMAND_ID}}/execute",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands", "{{COMMAND_ID}}", "execute"]
                },
                "description": "Transitions command state to EXECUTED, triggering system events."
            }
        },
        {
            "name": "Mark Command as Failed",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.status).to.eql("FAILED");'
            ])],
            "request": {
                "method": "PUT",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands/{{COMMAND_ID}}/fail?message=No response timeout",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands", "{{COMMAND_ID}}", "fail"],
                    "query": [{"key": "message", "value": "No response timeout"}]
                },
                "description": "Transitions command state to FAILED."
            }
        },
        {
            "name": "Get Command Logs",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands/{{COMMAND_ID}}/logs",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands", "{{COMMAND_ID}}", "logs"]
                },
                "description": "Retrieves the historical audit log of transitions for a command."
            }
        },
        {
            "name": "Delete Command",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.id).to.eql(parseInt(pm.environment.get("COMMAND_ID")));'
            ])],
            "request": {
                "method": "DELETE",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/commands/{{COMMAND_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["commands", "{{COMMAND_ID}}"]
                },
                "description": "Removes a command from the transmission queue."
            }
        }
    ]
    collection["item"].append({
        "name": "Commands",
        "item": command_items
    })

    # 8. Folder: Configurations
    config_items = [
        {
            "name": "Create Configuration",
            "event": [make_test_event(201, [
                'pm.expect(jsonData).to.have.property("id");',
                'pm.expect(jsonData.server_ip).to.eql("121.242.100.50");'
            ], {"CONFIG_ID": "jsonData.id"})],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "vehicle_id": 1,
                        "server_ip": "121.242.100.50",
                        "server_port": 5000,
                        "apn": "iot.airtel.com",
                        "timezone": "+05:30",
                        "reporting_interval": 30,
                        "speed_limit": 80.0,
                        "feature_flags": {"geofence": True, "ignition_alert": True},
                        "firmware_version": "v1.2.3",
                        "hardware_version": "v3.0"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/configurations",
                    "host": ["{{BASE_URL}}"],
                    "path": ["configurations"]
                },
                "description": "Registers device/ingestion settings profile for a vehicle."
            }
        },
        {
            "name": "Get Configuration by Vehicle",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.vehicle_id).to.eql(parseInt(pm.environment.get("VEHICLE_ID") || 1));'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/configurations/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["configurations", "{{VEHICLE_ID}}"]
                },
                "description": "Retrieves the device configuration settings profile."
            }
        },
        {
            "name": "Update Configuration",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.speed_limit).to.eql(90.0);'
            ])],
            "request": {
                "method": "PUT",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "speed_limit": 90.0,
                        "reporting_interval": 15
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/configurations/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["configurations", "{{VEHICLE_ID}}"]
                },
                "description": "Updates hardware parameters for the device profile."
            }
        },
        {
            "name": "Delete Configuration",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.vehicle_id).to.eql(parseInt(pm.environment.get("VEHICLE_ID") || 1));'
            ])],
            "request": {
                "method": "DELETE",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/configurations/{{VEHICLE_ID}}",
                    "host": ["{{BASE_URL}}"],
                    "path": ["configurations", "{{VEHICLE_ID}}"]
                },
                "description": "Deletes configurations profile registry."
            }
        }
    ]
    collection["item"].append({
        "name": "Configurations",
        "item": config_items
    })

    # 9. Folder: Events
    event_items = [
        {
            "name": "List Events Stats",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.have.property("critical");',
                'pm.expect(jsonData).to.have.property("total");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/events/stats",
                    "host": ["{{BASE_URL}}"],
                    "path": ["events", "stats"]
                },
                "description": "Retrieves total event counts sliced by critical/warning/info severity levels."
            }
        },
        {
            "name": "List Recent Events",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/events/recent?limit=10",
                    "host": ["{{BASE_URL}}"],
                    "path": ["events", "recent"],
                    "query": [{"key": "limit", "value": "10"}]
                },
                "description": "Lists the most recent telemetry warnings and system alert events."
            }
        }
    ]
    collection["item"].append({
        "name": "Events",
        "item": event_items
    })

    # 10. Folder: Trips
    trip_items = [
        {
            "name": "List Vehicle Trips",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.be.an("array");'
            ], {"TRIP_ID": "jsonData.length > 0 ? jsonData[0].id : null"})],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips?limit=10",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips"],
                    "query": [{"key": "limit", "value": "10"}]
                },
                "description": "Lists historical trip logs generated for a vehicle."
            }
        },
        {
            "name": "Rebuild Trips from History",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.result).to.eql(true);',
                'pm.expect(jsonData.trips_created).to.be.a("number");'
            ])],
            "request": {
                "method": "POST",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips/rebuild",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips", "rebuild"]
                },
                "description": "Idempotently recalculates and regenerates all trips for a vehicle."
            }
        },
        {
            "name": "Get Trip Summary Analytics",
            "event": [make_test_event(200, [
                'pm.expect(jsonData).to.have.property("driver_score");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips/{{TRIP_ID}}/summary",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips", "{{TRIP_ID}}", "summary"]
                },
                "description": "Retrieves analytics summary metrics including stop events and driver scores."
            }
        },
        {
            "name": "Get Trip Replay playback",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.points).to.be.an("array");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips/{{TRIP_ID}}/replay?multiplier=1",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips", "{{TRIP_ID}}", "replay"],
                    "query": [{"key": "multiplier", "value": "1"}]
                },
                "description": "Retrieves playback coordinates list with downsampling logic."
            }
        },
        {
            "name": "Get Trip GeoJSON format",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.type).to.eql("Feature");',
                'pm.expect(jsonData.geometry.type).to.eql("LineString");'
            ])],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips/{{TRIP_ID}}/geojson",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips", "{{TRIP_ID}}", "geojson"]
                },
                "description": "Generates standard GeoJSON geometry for dashboard maps integrations."
            }
        },
        {
            "name": "Export Trip CSV file",
            "event": [make_test_event(200)],
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{BASE_URL}}/vehicles/{{VEHICLE_ID}}/trips/{{TRIP_ID}}/export",
                    "host": ["{{BASE_URL}}"],
                    "path": ["vehicles", "{{VEHICLE_ID}}", "trips", "{{TRIP_ID}}", "export"]
                },
                "description": "Exports coordinate logs and speed metrics for a trip as a downloadable CSV."
            }
        }
    ]
    collection["item"].append({
        "name": "Trips",
        "item": trip_items
    })

    # 11. Folder: Route Cache
    route_items = [
        {
            "name": "Snap Path (Map Matching API)",
            "event": [make_test_event(200, [
                'pm.expect(jsonData.coordinates).to.be.an("array");'
            ])],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "waypoints": [
                            [21.17024, 72.83106],
                            [21.18524, 72.84506]
                        ],
                        "travel_mode": "DRIVE"
                    }, indent=2)
                },
                "url": {
                    "raw": "{{BASE_URL}}/routes/snap-path",
                    "host": ["{{BASE_URL}}"],
                    "path": ["routes", "snap-path"]
                },
                "description": "Snaps custom coordinates to road network using the Google Routes snap cache."
            }
        }
    ]
    collection["item"].append({
        "name": "Route Cache",
        "item": route_items
    })

    return collection

def generate_environment():
    environment = {
        "id": "c1f7b8a2-8610-410a-bca2-8dbbc910a300",
        "name": "Vehicle Tracking System - Production",
        "values": [
            {
                "key": "BASE_URL",
                "value": "https://welogical-vehicle-tracking-system.onrender.com",
                "type": "secret",
                "enabled": True
            },
            {
                "key": "VEHICLE_ID",
                "value": "1",
                "type": "default",
                "enabled": True
            },
            {
                "key": "DRIVER_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "ASSIGNMENT_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "LOCATION_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "COMMAND_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "CONFIG_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "TRIP_ID",
                "value": "",
                "type": "default",
                "enabled": True
            },
            {
                "key": "DEVICE_UID",
                "value": "ESP32-DEMO-001",
                "type": "default",
                "enabled": True
            }
        ],
        "_postman_variable_scope": "environment"
    }
    return environment

if __name__ == "__main__":
    postman_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postman")
    os.makedirs(postman_dir, exist_ok=True)

    col_path = os.path.join(postman_dir, "VTS_Collection.postman_collection.json")
    env_path = os.path.join(postman_dir, "VTS_Environment.postman_environment.json")

    with open(col_path, "w") as f:
        json.dump(generate_collection(), f, indent=2)
    print(f"Generated Postman Collection at: {col_path}")

    with open(env_path, "w") as f:
        json.dump(generate_environment(), f, indent=2)
    print(f"Generated Postman Environment at: {env_path}")
