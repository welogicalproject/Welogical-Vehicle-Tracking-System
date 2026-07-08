from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class NotificationHistory(Base):
    __tablename__ = "notification_histories"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    severity = Column(String, nullable=False, index=True) # "Critical", "Warning", "Info"
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    source_event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)
    acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
    source_event = relationship("Event")

    def __repr__(self):
        return f"<NotificationHistory id={self.id} title='{self.title}' resolved={self.resolved}>"
