import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.database import Base
from app.models.event import Event
from app.models.notification_history import NotificationHistory
from app.services.notifications import get_notification_manager

def test_notification_engine():
    print("======================================================================")
    print("                 VTS NOTIFICATION ENGINE UNIT TESTS                  ")
    print("======================================================================")

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Instantiate pre-registered NotificationManager
    manager = get_notification_manager()
    print(f"Total rules pre-registered: {len(manager.rules)}")
    print(f"Total dispatchers registered: {len(manager.dispatchers)}")
    assert len(manager.rules) == 9
    assert len(manager.dispatchers) == 5

    # 3. Create mock Event (Low Fuel warning)
    now = datetime.utcnow()
    ev_fuel = Event(
        id=1,
        vehicle_id=2,
        txn="U",
        event_type="Low Fuel",
        description="Fuel level low (8.5% remaining)",
        severity="Warning",
        created_at=now
    )
    db.add(ev_fuel)
    db.commit()

    # 4. Process event and verify trigger and save logic
    print("\n--- Processing Event: Low Fuel ---")
    alerts = manager.evaluate_event(db, ev_fuel)
    assert len(alerts) == 1, "Expected 1 notification triggered."
    
    n = db.query(NotificationHistory).filter_by(source_event_id=ev_fuel.id).first()
    assert n is not None, "NotificationHistory record not persisted."
    print(f"Persisted Title:   {n.title} (Expected: Low Fuel Alert)")
    print(f"Persisted Message: {n.message}")
    print(f"Acknowledged State: {n.acknowledged} (Expected: False)")
    print(f"Resolved State:     {n.resolved} (Expected: False)")
    
    assert n.title == "Low Fuel Alert"
    assert n.acknowledged is False
    assert n.resolved is False
    print("[PASS] Low Fuel notification persisted and dispatched successfully.")

    # 5. Verify Deduplication protection logic
    print("\n--- Verifying Deduplication Protection ---")
    # Same event triggered again immediately (within 5 seconds)
    alerts_retry = manager.evaluate_event(db, ev_fuel)
    print(f"Triggered Alerts on immediate retry: {len(alerts_retry)} (Expected: 0)")
    assert len(alerts_retry) == 0, "Duplicate check failed, alert should be skipped."
    print("[PASS] Deduplication engine prevented duplicate alert broadcast.")

    db.close()
    print("\n======================================================================")
    print("                 NOTIFICATION ENGINE TESTS PASSED                     ")
    print("======================================================================")

if __name__ == "__main__":
    test_notification_engine()
