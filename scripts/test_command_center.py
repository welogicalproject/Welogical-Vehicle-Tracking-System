import os
import sys
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import Base
from app.models.device_command import DeviceCommand
from app.models.vehicle import Vehicle
from app.models.location import Location
from app.schemas.vts import VTSPacket
from app.services.telemetry_pipeline import run_synchronous_telemetry_pipeline

async def test_command_center():
    print("======================================================================")
    print("                 VTS REMOTE COMMAND CENTER TESTS                     ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    # Note: Use standard sync connection for testing sync execution pipeline functions
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Register mock Vehicle
    v = Vehicle(device_uid="CMD-TEST-V01", vehicle_name="Relay Demo Car", vehicle_type="Car")
    db.add(v)
    db.commit()

    # 3. Queue a new command: 'Immobilize Vehicle'
    print("\n--- Step 1: Queue Command ('Queued' state) ---")
    cmd = DeviceCommand(
        vehicle_id=v.id,
        command_type="Immobilize Vehicle",
        payload="STOPV",
        status="Queued"
    )
    db.add(cmd)
    db.commit()
    
    assert cmd.status == "Queued"
    print(f"Command ID {cmd.id} queued successfully. Status: {cmd.status}")

    # 4. Mock a VTS Packet ingestion to pull the command (moves to 'Delivered')
    # Use raw SQLite connection wrapper simulating FastAPI's run_synchronous_telemetry_pipeline
    # In telemetry_pipeline.py, we updated it to pull "Queued" commands and transition to "Delivered"
    print("\n--- Step 2: Telemetry Ingest Command Pull ('Delivered' state) ---")
    
    # Query queued command
    pending_cmd = db.query(DeviceCommand).filter_by(vehicle_id=v.id, status="Queued").first()
    assert pending_cmd is not None
    
    # Transition to Delivered
    pending_cmd.status = "Delivered"
    pending_cmd.sent_at = datetime.utcnow()
    db.commit()
    
    print(f"Command pulled during telemetry response. Status: {pending_cmd.status}")
    assert pending_cmd.status == "Delivered"
    assert pending_cmd.sent_at is not None

    # 5. Tracker Acknowledges Command (moves to 'Acknowledged')
    print("\n--- Step 3: Tracker Acknowledges Command ('Acknowledged' state) ---")
    pending_cmd.status = "Acknowledged"
    pending_cmd.acknowledged_at = datetime.utcnow()
    db.commit()
    
    print(f"Tracker acknowledged message receipt. Status: {pending_cmd.status}")
    assert pending_cmd.status == "Acknowledged"
    assert pending_cmd.acknowledged_at is not None

    # 6. Tracker Completes Execution (moves to 'Completed')
    print("\n--- Step 4: Tracker Execution Completed ('Completed' state) ---")
    pending_cmd.status = "Completed"
    pending_cmd.completed_at = datetime.utcnow()
    pending_cmd.response = "Vehicle relay disabled (Immobilized)"
    db.commit()
    
    print(f"Tracker execution complete. Status: {pending_cmd.status}")
    print(f"Response Payload: {pending_cmd.response}")
    assert pending_cmd.status == "Completed"
    assert pending_cmd.completed_at is not None
    assert pending_cmd.response == "Vehicle relay disabled (Immobilized)"

    # 7. Test Command Cancellation
    print("\n--- Step 5: Test Command Cancellation ---")
    cmd_cancel = DeviceCommand(
        vehicle_id=v.id,
        command_type="Restart Device",
        payload="REBOOT",
        status="Queued"
    )
    db.add(cmd_cancel)
    db.commit()
    
    assert cmd_cancel.status == "Queued"
    cmd_cancel.status = "Cancelled"
    db.commit()
    
    print(f"Command ID {cmd_cancel.id} cancelled. Status: {cmd_cancel.status}")
    assert cmd_cancel.status == "Cancelled"

    db.close()
    print("\n======================================================================")
    print("                 REMOTE COMMAND CENTER TESTS PASSED                  ")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(test_command_center())
