from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    txn = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)  # "Critical", "Warning", "Info"
    msgid = Column(Integer, nullable=True, index=True)  # msgid for duplicate event check
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="events")

    @property
    def vehicle_name(self) -> str:
        return self.vehicle.vehicle_name if self.vehicle else None

    @property
    def device_uid(self) -> str:
        return self.vehicle.device_uid if self.vehicle else None

    def __repr__(self):
        return f"<Event id={self.id} vehicle_id={self.vehicle_id} type='{self.event_type}' severity='{self.severity}'>"
