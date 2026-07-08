import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.driver_assignment import DriverAssignment
from app.models.notification_history import NotificationHistory
from app.services.notifications.base import BaseNotificationRule, NotificationContext
from app.services.notifications.dispatcher import BaseDispatcher

logger = logging.getLogger("vts.notifications")

class NotificationManager:
    """
    Coordinates and handles mapping of Event logs to live Notification alerts,
    checks for deduplication, persists alerts to NotificationHistory, and dispatches them.
    """
    def __init__(self):
        self.rules: List[BaseNotificationRule] = []
        self.dispatchers: List[BaseDispatcher] = []

    def register_rule(self, rule: BaseNotificationRule):
        self.rules.append(rule)
        logger.info(f"Registered notification rule: '{rule.name}' for Event: '{rule.event_type}'.")

    def register_dispatcher(self, dispatcher: BaseDispatcher):
        self.dispatchers.append(dispatcher)
        logger.info(f"Registered notification dispatcher: '{dispatcher.name}'.")

    def _resolve_driver_id(self, db: Session, vehicle_id: int, timestamp: datetime) -> Optional[int]:
        asg = db.query(DriverAssignment).filter(
            DriverAssignment.vehicle_id == vehicle_id,
            DriverAssignment.assigned_at <= timestamp,
            or_(
                DriverAssignment.released_at >= timestamp,
                DriverAssignment.released_at.is_(None)
            )
        ).order_by(DriverAssignment.assigned_at.desc()).first()
        return asg.driver_id if asg else None

    def _is_duplicate(self, db: Session, vehicle_id: int, title: str, timestamp: datetime) -> bool:
        # Check if identical alert was sent for this vehicle in the last 5 seconds
        last_alert = db.query(NotificationHistory).filter(
            NotificationHistory.vehicle_id == vehicle_id,
            NotificationHistory.title == title
        ).order_by(NotificationHistory.created_at.desc()).first()
        
        if last_alert:
            time_diff = abs((timestamp - last_alert.created_at).total_seconds())
            if time_diff < 5.0:
                return True
        return False

    def evaluate_event(self, db: Session, event: Event) -> List[NotificationHistory]:
        triggered_alerts = []
        driver_id = self._resolve_driver_id(db, event.vehicle_id, event.created_at)
        context = NotificationContext(db, event, driver_id=driver_id)

        for rule in self.rules:
            if rule.match(context):
                payload = rule.create_notification_payload(context)
                title = payload.get("title", f"Alert: {rule.event_type}")
                message = payload.get("message", f"Event generated alert.")
                
                # Check duplication
                if not self._is_duplicate(db, event.vehicle_id, title, event.created_at):
                    # Persist NotificationHistory record
                    notification = NotificationHistory(
                        vehicle_id=event.vehicle_id,
                        driver_id=driver_id,
                        severity=rule.severity,
                        title=title,
                        message=message,
                        source_event_id=event.id,
                        created_at=event.created_at,
                        acknowledged=False,
                        resolved=False
                    )
                    db.add(notification)
                    triggered_alerts.append(notification)
                    
                    # Dispatch to all registered dispatchers
                    for dispatcher in self.dispatchers:
                        try:
                            details = {
                                "vehicle_id": event.vehicle_id,
                                "driver_id": driver_id,
                                "event_id": event.id,
                                "created_at": str(event.created_at)
                            }
                            dispatcher.send(title, message, rule.severity, details)
                        except Exception as e:
                            logger.error(f"Notification dispatcher '{dispatcher.name}' failed to send: {e}", exc_info=True)

        if triggered_alerts:
            db.flush()

        return triggered_alerts
