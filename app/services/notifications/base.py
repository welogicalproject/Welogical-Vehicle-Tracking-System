import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.event import Event

class NotificationContext:
    """
    Context arguments passed to validation rules containing the active database session,
    the matching event details, and driver identifiers if resolved.
    """
    def __init__(self, db: Session, event: Event, driver_id: Optional[int] = None):
        self.db = db
        self.event = event
        self.driver_id = driver_id


class BaseNotificationRule:
    """
    Base notification validation rule interface. Determines if an Event triggers
    a notification alert.
    """
    name: str = "BaseRule"
    event_type: str = "" # Event type to match (e.g. "Overspeed")
    severity: str = "Info"

    def match(self, context: NotificationContext) -> bool:
        """
        Returns True if the event matches the rule's trigger criteria.
        """
        return context.event.event_type == self.event_type

    def create_notification_payload(self, context: NotificationContext) -> dict:
        """
        Returns a dict containing 'title' and 'message' for the alert.
        """
        raise NotImplementedError("Rules must override create_notification_payload().")
