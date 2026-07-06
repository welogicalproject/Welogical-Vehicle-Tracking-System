from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, unique=True, index=True, nullable=False)
    vehicle_name = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    last_seen = Column(DateTime, nullable=True)

    # Extended Fleet Metadata
    vehicle_number = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    vin = Column(String, nullable=True)
    imei = Column(String, nullable=True)
    sim_number = Column(String, nullable=True)
    fuel_type = Column(String, nullable=True)
    capacity = Column(Float, nullable=True)
    status = Column(String, default="Enabled", nullable=False) # "Enabled", "Disabled", "Archived"
    notes = Column(String, nullable=True)

    # Relationships
    locations = relationship("Location", back_populates="vehicle", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="vehicle", cascade="all, delete-orphan")
    device_config = relationship("DeviceConfig", back_populates="vehicle", uselist=False, cascade="all, delete-orphan")
    device_commands = relationship("DeviceCommand", back_populates="vehicle", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")
    assignments = relationship("DriverAssignment", back_populates="vehicle", cascade="all, delete-orphan")

    @property
    def current_driver(self):
        for asg in self.assignments:
            if asg.status == "Active":
                return asg.driver
        return None
    
    def __repr__(self):
        return f"<Vehicle id={self.id} device_uid='{self.device_uid}' name='{self.vehicle_name}'>"
