from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import CommandStatus


class CommandLog(Base):
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("device_commands.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SqlEnum(CommandStatus, name="commandstatus"), nullable=False, index=True)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    # Relationships
    command = relationship("DeviceCommand", back_populates="audit_logs")
    vehicle = relationship("Vehicle")

    def __repr__(self):
        return f"<CommandLog id={self.id} command_id={self.command_id} status='{self.status}'>"
