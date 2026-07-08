from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    command_type = Column(String, nullable=False, index=True) # e.g., "Restart Device"
    payload = Column(String, nullable=True) # JSON payload parameters
    
    status = Column(String, default="Queued", nullable=False, index=True)
    # Valid states: "Queued", "Sending", "Delivered", "Acknowledged", "Executing", "Completed", "Failed", "Timed Out", "Cancelled"

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="device_commands")
    audit_logs = relationship("CommandLog", back_populates="command", cascade="all, delete-orphan")

    # --- BACKWARD COMPATIBILITY PROPERTIES ---
    @property
    def command_name(self) -> str:
        return self.command_type

    @command_name.setter
    def command_name(self, val: str):
        self.command_type = val

    @property
    def command_value(self) -> Optional[str]:
        return self.payload

    @command_value.setter
    def command_value(self, val: Optional[str]):
        self.payload = val

    @property
    def executed_at(self) -> Optional[datetime]:
        return self.completed_at

    @executed_at.setter
    def executed_at(self, val: Optional[datetime]):
        self.completed_at = val

    @property
    def vehicle_name(self) -> Optional[str]:
        return self.vehicle.vehicle_name if self.vehicle else None

    def __repr__(self):
        return f"<DeviceCommand id={self.id} vehicle_id={self.vehicle_id} command_type='{self.command_type}' status='{self.status}'>"
