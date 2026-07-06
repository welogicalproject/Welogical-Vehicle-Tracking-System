from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class DeviceConfig(Base):
    __tablename__ = "device_configs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    server_ip = Column(String, nullable=True)
    server_port = Column(Integer, nullable=True)
    apn = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    reporting_interval = Column(Integer, nullable=True)  # PRD in seconds
    speed_limit = Column(Float, nullable=True)  # ESS in km/h
    feature_flags = Column(JSONB, nullable=True)
    firmware_version = Column(String, nullable=True)
    hardware_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="device_config")

    def __repr__(self):
        return f"<DeviceConfig id={self.id} vehicle_id={self.vehicle_id}>"
