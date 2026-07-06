from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import CommandStatus


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    command_name = Column(String, nullable=False)
    command_value = Column(String, nullable=True)
    status = Column(SqlEnum(CommandStatus, name="commandstatus"), default=CommandStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="device_commands")
    audit_logs = relationship("CommandLog", back_populates="command", cascade="all, delete-orphan")

    @property
    def vehicle_name(self) -> str:
        return self.vehicle.vehicle_name if self.vehicle else None

    def __repr__(self):
        return f"<DeviceCommand id={self.id} vehicle_id={self.vehicle_id} command='{self.command_name}' status='{self.status}'>"
